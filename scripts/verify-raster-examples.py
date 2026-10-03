#!/usr/bin/env python3
"""Execute raster tutorials in an isolated extracted project and independently verify results.

Requires Python with GDAL, NumPy and Shapely, Java 21, and --hop-home.
Use --online for the live COG comparison. Never changes the supplied Hop installation.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from osgeo import gdal, ogr, osr
import shapely

gdal.UseExceptions()
ogr.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
OFFLINE = ['read-write-geotiff', 'read-write-cog', 'clip-bbox', 'clip-polygon',
           'reproject-nearest', 'reproject-bilinear', 'zonal']


def read_features(path):
    ds = ogr.Open(str(path))
    layer = ds.GetLayer()
    assert layer.GetSpatialRef().GetAuthorityCode(None) == '2056'
    return {f['building_id']: (dict(f.items()), shapely.from_wkb(bytes(f.GetGeometryRef().ExportToWkb())))
            for f in layer}


def raster(path):
    ds = gdal.Open(str(path))
    band = ds.GetRasterBand(1)
    return ds, band.ReadAsArray(), band.GetNoDataValue()


def values_in_polygon(ds, a, nodata, geom):
    gt = ds.GetGeoTransform()
    x0, y0, x1, y1 = geom.bounds
    c0 = max(0, math.floor((x0 - gt[0]) / gt[1])); c1 = min(a.shape[1], math.ceil((x1 - gt[0]) / gt[1]))
    r0 = max(0, math.floor((y1 - gt[3]) / gt[5])); r1 = min(a.shape[0], math.ceil((y0 - gt[3]) / gt[5]))
    if c1 <= c0 or r1 <= r0:
        return np.array([])
    xx, yy = np.meshgrid(gt[0] + (np.arange(c0, c1) + .5) * gt[1],
                         gt[3] + (np.arange(r0, r1) + .5) * gt[5])
    # intersects includes pixel centres exactly on the polygon boundary.
    inside = shapely.intersects_xy(geom, xx, yy)
    arr = a[r0:r1, c0:c1]
    good = inside & np.isfinite(arr) & (arr != nodata)
    band = ds.GetRasterBand(1)
    scale = band.GetScale() if band.GetScale() is not None else 1
    offset = band.GetOffset() if band.GetOffset() is not None else 0
    return arr[good].astype(float) * scale + offset


def check_zonal(project, name='zonal', expected_count=33):
    sources = read_features(project / 'data/buildings.gpkg')
    results = read_features(project / f'output/{name}.gpkg')
    assert len(sources) == len(results) == expected_count
    assert sources.keys() == results.keys()
    ds, arr, nodata = raster(project / 'data/ndsm-2019.tif')
    report = []
    for ident, (props, geom) in sources.items():
        result, result_geom = results[ident]
        assert result['art_txt'] == props['art_txt'] == 'Gebaeude'
        assert geom.equals_exact(result_geom, 0)
        for key in ['T_Ili_Tid', 'bfs_nr', 'egid', 'building_id']:
            if key in props: assert props[key] == result[key], (ident, key)
        for key in ['importdatum', 'nachfuehrung']:
            if props.get(key): assert props[key][:10] == result[key][:10], (ident, key)
        values = values_in_polygon(ds, arr, nodata, geom)
        assert result['height_count'] == len(values), (ident, len(values), result)
        expected = dict(mean=float(values.mean()), min=float(values.min()), max=float(values.max())) if len(values) else dict(mean=None, min=None, max=None)
        assert result['height_status'] == ('OK' if len(values) else 'NO_VALID_PIXELS')
        for key, value in expected.items():
            if value is None: assert result['height_' + key] is None
            else: assert math.isclose(value, result['height_' + key], rel_tol=1e-8, abs_tol=1e-7), (ident, key, value, result)
        report.append(dict(building_id=ident, count=len(values), status=result['height_status'], **expected))
    return report


def check_rasters(project):
    ds, source, nd = raster(project / 'data/ndsm-2019.tif'); gt = ds.GetGeoTransform()
    for name in ['read-write-geotiff', 'read-write-cog', 'clip-bbox']:
        out, a, outnd = raster(project / f'output/{name}.tif'); ogt = out.GetGeoTransform()
        assert out.GetSpatialRef().GetAuthorityCode(None) == '2056'
        assert out.RasterCount == 1 and outnd == nd
        assert ogt[1] == gt[1] and ogt[5] == gt[5]
        x = round((ogt[0] - gt[0]) / gt[1]); y = round((ogt[3] - gt[3]) / gt[5])
        np.testing.assert_array_equal(a, source[y:y+a.shape[0], x:x+a.shape[1]])
        assert out.GetRasterBand(1).GetOverviewCount() > 0
        if name == 'read-write-cog':
            assert out.GetMetadata('IMAGE_STRUCTURE').get('LAYOUT') == 'COG'
            from osgeo_utils.samples.validate_cloud_optimized_geotiff import validate
            warnings, errors, _ = validate(out, full_check=True)
            assert not errors, (warnings, errors)
    assert len(list((project/'output').glob('building-*.tif'))) == 33
    for ident, (_, geom) in read_features(project/'data/buildings.gpkg').items():
        out, a, outnd = raster(project/f'output/building-{ident}.tif');ogt=out.GetGeoTransform()
        assert out.GetSpatialRef().GetAuthorityCode(None) == '2056'
        assert ogt[1] == gt[1] and ogt[5] == gt[5] and outnd == nd
        x=round((ogt[0]-gt[0])/gt[1]);y=round((ogt[3]-gt[3])/gt[5])
        xx,yy=np.meshgrid(ogt[0]+(np.arange(a.shape[1])+.5)*ogt[1],ogt[3]+(np.arange(a.shape[0])+.5)*ogt[5])
        expected=np.where(shapely.intersects_xy(geom,xx,yy),source[y:y+a.shape[0],x:x+a.shape[1]],nd)
        np.testing.assert_array_equal(a,expected)
    # Independent inverse-coordinate sampling, rather than GDAL's wider downsampling kernel.
    src=ds.GetSpatialRef();src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    for method in ['nearest','bilinear']:
        out,a,outnd=raster(project/f'output/reproject-{method}.tif');ogt=out.GetGeoTransform()
        assert out.GetSpatialRef().GetAuthorityCode(None)=='3857'
        assert ogt[1]==1 and ogt[5]==-1 and outnd==nd
        target=out.GetSpatialRef();target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        trans=osr.CoordinateTransformation(target,src)
        valid=np.argwhere(a!=outnd); valid=valid[::max(1,len(valid)//1500)]
        rng=np.random.default_rng(42);points=np.vstack([valid,np.column_stack([rng.integers(0,a.shape[0],500),rng.integers(0,a.shape[1],500)])])
        for r,c in points:
            x,y,_=trans.TransformPoint(ogt[0]+(c+.5)*ogt[1],ogt[3]+(r+.5)*ogt[5]);u=(x-gt[0])/gt[1]-.5;v=(y-gt[3])/gt[5]-.5
            def sample(u, v):
                if method=='nearest': samples=[(math.floor(v+.5),math.floor(u+.5),1)]
                else:
                    left=math.floor(u);top=math.floor(v);fx=u-left;fy=v-top
                    samples=[(top,left,(1-fx)*(1-fy)),(top,left+1,fx*(1-fy)),(top+1,left,(1-fx)*fy),(top+1,left+1,fx*fy)]
                total=weight=0
                for rr,cc,w in samples:
                    if 0<=rr<source.shape[0] and 0<=cc<source.shape[1] and source[rr,cc]!=nd:
                        total+=float(source[rr,cc])*w;weight+=w
                return total/weight if weight else nd
            # PROJ and this GeoTools build differ by about 4 cm in this datum operation.
            # Bound the comparison to 1/4 source pixel (6.25 cm), not a height tolerance
            # large enough to hide incorrect pixel selection. Same-CRS fixtures below
            # verify both interpolation kernels without datum-operation differences.
            candidates=[sample(u+du,v+dv) for du in np.linspace(-.25,.25,5) for dv in np.linspace(-.25,.25,5)]
            actual=float(a[r,c]);good=[x for x in candidates if x!=nd]
            if actual==outnd: assert nd in candidates, (method,r,c)
            elif method=='nearest': assert any(math.isclose(actual,x,abs_tol=1e-6) for x in good),(method,r,c,actual,candidates)
            else: assert good and min(good)-.002<=actual<=max(good)+.002,(method,r,c,actual,candidates)



def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--hop-home',required=True,type=Path);parser.add_argument('--online',action='store_true');args=parser.parse_args()
    work=Path(tempfile.mkdtemp(prefix='geohop-raster-validation-'))
    with zipfile.ZipFile(ROOT/'downloads/raster-processing.zip') as z:z.extractall(work)
    project=work/'raster processing';(work/'raster-processing').rename(project)
    config=work/'config';config.mkdir()
    (config/'hop-config.json').write_text(json.dumps({'projectsConfig':{'enabled':True,'projectMandatory':True,'defaultProject':'raster-processing','projectConfigurations':[{'projectName':'raster-processing','projectHome':str(project),'configFilename':'project-config.json'}]}}))
    env=dict(os.environ,HOP_CONFIG_FOLDER=str(config),HOP_AUDIT_FOLDER=str(work/'audit'),HOP_METADATA_FOLDER=str(project/'metadata'))
    hop=args.hop_home.resolve()
    def run(name):
        with (work/(name+'.log')).open('w') as log:
            return subprocess.run([str(hop/'hop-run.sh'),'-j','raster-processing','-r','local','-f',str(project/(name+'.hpl'))],cwd=hop,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
    print('Validation artifacts:',work,flush=True)
    for name in OFFLINE+(['zonal-online'] if args.online else []):
        assert run(name)==0, f'{name} failed; see {work}'
        print('PASS',name,flush=True)
    check_rasters(project); report=check_zonal(project)
    if args.online:assert check_zonal(project,'zonal-online')==report
    (work/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS independent raster and statistics checks',dict(Counter(r['status'] for r in report)),flush=True)
    for name,suffix in [('read-write-geotiff','tif'),('zonal','gpkg')]:
        path=project/f'output/{name}.{suffix}';before=hashlib.sha256(path.read_bytes()).digest()
        assert run(name)!=0
        assert hashlib.sha256(path.read_bytes()).digest()==before
    print('PASS existing-output protection',flush=True)
    # Small controlled data: valid zero, NoData, a polygon hole, all-NoData and an outside zone.
    fixture=project/'data/fixture.tif';d=gdal.GetDriverByName('GTiff').Create(str(fixture),3,3,1,gdal.GDT_Float32)
    d.SetGeoTransform((2600000,1,0,1200003,0,-1));s=osr.SpatialReference();s.ImportFromEPSG(2056);d.SetSpatialRef(s)
    d.GetRasterBand(1).SetNoDataValue(-9999);d.GetRasterBand(1).WriteArray(np.array([[0,1,-9999],[3,4,-9999],[-9999,-9999,-9999]],dtype=np.float32));d=None
    zones=project/'data/fixture.gpkg';v=ogr.GetDriverByName('GPKG').CreateDataSource(str(zones));l=v.CreateLayer('buildings',s,ogr.wkbPolygon)
    for name,typ in [('building_id',ogr.OFTInteger64),('art_txt',ogr.OFTString)]:l.CreateField(ogr.FieldDefn(name,typ))
    polygons=[shapely.box(2600000,1200001,2600002,1200003),shapely.box(2600002,1200000,2600003,1200001),shapely.box(2600010,1200010,2600011,1200011),shapely.Polygon([(2600000,1200000),(2600003,1200000),(2600003,1200003),(2600000,1200003)],holes=[[(2600001,1200001),(2600002,1200001),(2600002,1200002),(2600001,1200002)]])]
    for i,g in enumerate(polygons,1):
        f=ogr.Feature(l.GetLayerDefn());f['building_id']=i;f['art_txt']='Gebaeude';f.SetGeometry(ogr.CreateGeometryFromWkb(shapely.to_wkb(g)));l.CreateFeature(f)
    v=None
    base=(project/'zonal.hpl').read_text();(project/'fixture.hpl').write_text(base.replace('/data/buildings.gpkg','/data/fixture.gpkg').replace('/data/ndsm-2019.tif','/data/fixture.tif').replace('/output/zonal.gpkg','/output/fixture.gpkg'))
    assert run('fixture')==0
    result=read_features(project/'output/fixture.gpkg')
    assert result[1][0]['height_count']==4 and result[1][0]['height_mean']==2 and result[1][0]['height_min']==0
    for i in [2,3]:assert result[i][0]['height_count']==0 and result[i][0]['height_mean'] is None and result[i][0]['height_status']=='NO_VALID_PIXELS'
    assert result[4][0]['height_count']==3 and math.isclose(result[4][0]['height_mean'],4/3)
    for method in ['nearest','bilinear']:
        xml=ET.parse(project/f'reproject-{method}.hpl')
        for transform in xml.findall('transform'):
            for key,value in [('source','${PROJECT_HOME}/data/fixture.tif'),('targetCrs','EPSG:2056'),('resolutionX','0.5'),('resolutionY','0.5'),('output',f'${{PROJECT_HOME}}/output/fixture-{method}.tif')]:
                node=transform.find(key)
                if node is not None:node.text=value
        xml.write(project/f'fixture-{method}.hpl',encoding='UTF-8',xml_declaration=True)
        assert run('fixture-'+method)==0
        _,a,_=raster(project/f'output/fixture-{method}.tif')
        assert a.shape==(6,6)
        if method=='nearest':np.testing.assert_array_equal(a,np.repeat(np.repeat(np.array([[0,1,-9999],[3,4,-9999],[-9999,-9999,-9999]]),2,axis=0),2,axis=1))
        else:assert math.isclose(float(a[1,1]),1.0) and math.isclose(float(a[0,1]),.25) and a[0,0]==0 and a[5,5]==-9999
    broken=base.replace('${PROJECT_HOME}/data/ndsm-2019.tif','http://127.0.0.1:1/unavailable.tif').replace('/output/zonal.gpkg','/output/network-error.gpkg')
    (project/'network-error.hpl').write_text(broken);assert run('network-error')!=0
    print('PASS zero, NoData, hole, outside-zone and network-error checks',flush=True)

if __name__=='__main__':main()
