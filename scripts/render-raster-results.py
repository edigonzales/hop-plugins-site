#!/usr/bin/env python3
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
from matplotlib.colors import Normalize
from osgeo import gdal,ogr,osr
import numpy as np
import argparse
parser=argparse.ArgumentParser(description='Render actual raster tutorial outputs; requires GDAL, NumPy and Matplotlib.')
parser.add_argument('--project',required=True,type=Path,help='Executed project directory reported by verify-raster-examples.py')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];project=args.project;out=root/'assets/examples/raster'
plt.rcParams.update({'font.size':10,'axes.titlesize':13,'figure.facecolor':'white','axes.facecolor':'#f2f5f5','axes.spines.top':False,'axes.spines.right':False})
def raster(ax,name):
 d=gdal.Open(str(project/'output'/name));gt=d.GetGeoTransform();a=d.ReadAsArray();nd=d.GetRasterBand(1).GetNoDataValue();a=np.ma.masked_where(a==nd,a);extent=[gt[0],gt[0]+d.RasterXSize*gt[1],gt[3]+d.RasterYSize*gt[5],gt[3]]
 im=ax.imshow(a,extent=extent,cmap='viridis',vmin=0,vmax=16,interpolation='nearest');ax.set_aspect('equal');ax.ticklabel_format(style='plain',useOffset=False);ax.tick_params(axis='x',rotation=25);ax.set_xlabel('Easting');ax.set_ylabel('Northing');return im
v=ogr.Open(str(project/'data/buildings.gpkg'));features=[f.Clone() for f in v.GetLayer()]
def outlines(ax,only=None):
 for f in features:
  if only is not None and f['building_id']!=only:continue
  geom=f.GetGeometryRef();ring=geom.GetGeometryRef(0);coords=np.array(ring.GetPoints())[:,:2];ax.add_patch(Polygon(coords,fill=False,edgecolor='#dd614a',linewidth=.65))
def save(fig,name):fig.savefig(out/(name+'.png'),dpi=170,bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(6,7),layout='constrained');im=raster(ax,'read-write-geotiff.tif');outlines(ax);ax.set_title('2019 nDSM · original 0.25 m grid\n33 current building footprints');fig.colorbar(im,ax=ax,label='Normalised height (m)',shrink=.65);save(fig,'ndsm-result')
fig,ax=plt.subplots(figsize=(7,6),layout='constrained');im=raster(ax,'clip-bbox.tif');ax.set_title('Bounding-box crop · 1000 × 1000 pixels');fig.colorbar(im,ax=ax,label='Normalised height (m)',shrink=.8);save(fig,'bbox-result')
fig,ax=plt.subplots(figsize=(7,6),layout='constrained');im=raster(ax,'building-20.tif');outlines(ax,20);ax.set_title('Building 20 · masked GeoTIFF\nGrey areas are NoData');fig.colorbar(im,ax=ax,label='Normalised height (m)',shrink=.8);save(fig,'polygon-result')
fig,axes=plt.subplots(1,2,figsize=(10,5),layout='constrained')
f=next(f for f in features if f['building_id']==20);geom=f.GetGeometryRef().Clone();s=osr.SpatialReference();s.ImportFromEPSG(2056);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);t=osr.SpatialReference();t.ImportFromEPSG(3857);t.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);geom.Transform(osr.CoordinateTransformation(s,t));xmin,xmax,ymin,ymax=geom.GetEnvelope()
for ax,method in zip(axes,['nearest','bilinear']):
 im=raster(ax,'reproject-'+method+'.tif');ax.set_xlim(xmin-5,xmax+5);ax.set_ylim(ymin-5,ymax+5);ax.set_title(method.title()+' · EPSG:3857');ax.set_ylabel('Northing' if method=='nearest' else '')
fig.colorbar(im,ax=list(axes),label='Normalised height (m)',shrink=.8);save(fig,'reproject-comparison')
fig,ax=plt.subplots(figsize=(6,7),layout='constrained');d=ogr.Open(str(project/'output/zonal.gpkg'));norm=Normalize(0,12);cmap=plt.get_cmap('viridis')
for f in d.GetLayer():
 coords=np.array(f.GetGeometryRef().GetGeometryRef(0).GetPoints())[:,:2];val=f['height_mean'];ax.add_patch(Polygon(coords,facecolor=cmap(norm(val)) if val is not None else 'none',edgecolor='#dd614a' if val is None else '#35464b',linewidth=1 if val is None else .4))
ax.autoscale_view();ax.set_aspect('equal');ax.ticklabel_format(style='plain',useOffset=False);ax.tick_params(axis='x',rotation=25);ax.set_xlabel('Easting');ax.set_ylabel('Northing');ax.set_title('Building mean heights · EPSG:2056\n29 OK · 4 without valid pixels');fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='Mean normalised height (m)',shrink=.65);ax.legend(handles=[Patch(facecolor='none',edgecolor='#dd614a',label='No valid pixels')],loc='upper right');save(fig,'zonal-map')
