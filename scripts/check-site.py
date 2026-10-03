#!/usr/bin/env python3
"""Check the rendered website's local links, anchors, images and download bundle."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse
import zipfile
import json
import hashlib
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(); self.refs=[]; self.ids=set()
        self.feed(path.read_text())
    def handle_starttag(self, tag, pairs):
        attrs=dict(pairs)
        if 'id' in attrs:self.ids.add(attrs['id'])
        for key in ('href','src'):
            if key in attrs:self.refs.append(attrs[key])
        if tag=='img':assert attrs.get('alt'), 'Image without alt text'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--site',type=Path,default=Path('_site'));args=p.parse_args()
    site=args.site.resolve();pages={f:Page(f) for f in site.rglob('*.html')};errors=[]
    expected=['index.html','docs.html','plugins.html','examples.html']+['examples/'+n+'.html' for n in ['shapefile','geopackage','filegdb','flatgeobuf','parquet','generate']]
    expected += ['examples/'+n+'.html' for n in ['vector-formats','raster-processing','raster-read-write','raster-clip-bbox','raster-clip-polygon','raster-reproject','raster-zonal','raster-zonal-online']]
    for path in expected:
        assert site.joinpath(path) in pages, path
    for f,page in pages.items():
        content=f.read_text()
        if 'Lorem ipsum' in content or '{{< var ' in content:errors.append(str(f)+': placeholder or unresolved variable')
        for ref in page.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc:continue
            target=(site/unquote(u.path).lstrip('/') if u.path.startswith('/') else f.parent/unquote(u.path)).resolve() if u.path else f
            if target.is_dir():target=target/'index.html'
            if not target.exists():errors.append(f'{f.relative_to(site)}: missing {ref}')
            elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
                errors.append(f'{f.relative_to(site)}: missing anchor {ref}')
    with zipfile.ZipFile(site/'downloads/vector-formats.zip') as z:
        files=z.namelist()
        assert len([n for n in files if n.endswith('.hpl')])==10
        assert 'vector-formats/data/sites.gpkg' in files
        assert 'vector-formats/project-config.json' in files
        assert 'vector-formats/metadata/pipeline-run-configuration/local.json' in files
        assert [n for n in files if '/output/' in n]==['vector-formats/output/README.txt']
        for n in files:
            if n.endswith(('.hpl','.json','.md')):
                assert b'/Users/' not in z.read(n), n
    with zipfile.ZipFile(site/'downloads/raster-processing.zip') as z:
        files=z.namelist();prefix='raster-processing/'
        names=['read-write-geotiff','read-write-cog','clip-bbox','clip-polygon','reproject-nearest','reproject-bilinear','zonal','zonal-online']
        assert sorted(n for n in files if n.endswith('.hpl'))==sorted(prefix+n+'.hpl' for n in names)
        assert [n for n in files if '/output/' in n]==[prefix+'output/README.txt']
        for required in ['project-config.json','metadata/pipeline-run-configuration/local.json','tested-environment.json','data/README.md']:
            assert prefix+required in files
        provenance=json.loads(z.read(prefix+'data/provenance.json'))
        for name,digest in provenance['files'].items():
            assert hashlib.sha256(z.read(prefix+'data/'+name)).hexdigest()==digest,name
        for n in files:
            if n.endswith(('.hpl','.json','.md')):assert b'/Users/' not in z.read(n),n
        for name in ['zonal','zonal-online']:
            pipeline=ET.fromstring(z.read(prefix+name+'.hpl'))
            filt=pipeline.find("transform[type='FilterRows']")
            assert filt.findtext('compare/condition/leftvalue')=='art_txt'
            assert filt.findtext('compare/condition/value/text')=='Gebaeude'
            assert filt.findtext('send_false_to')=='Discard non-buildings'
            reader=pipeline.find("transform[type='SOGIS_RASTER_READER']")
            expected_source=provenance['raster_source'] if name=='zonal-online' else '${PROJECT_HOME}/data/ndsm-2019.tif'
            assert reader.findtext('source')==expected_source
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'buildings.gpkg';database.write_bytes(z.read(prefix+'data/buildings.gpkg'))
            with sqlite3.connect(database) as db:
                assert db.execute('select table_name from gpkg_contents').fetchall()==[('buildings',)]
                assert db.execute('select art_txt,count(*) from buildings group by art_txt').fetchall()==[('Gebaeude',33)]
                assert db.execute('select count(*) from buildings where building_id=T_Id').fetchone()[0]==33
    assert not errors, '\n'.join(errors)
    assert (site/'search.json').exists()
    print(f'PASS: {len(pages)} pages; local links, anchors, images, search index and portable ZIPs')

if __name__=='__main__':main()
