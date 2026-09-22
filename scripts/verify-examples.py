#!/usr/bin/env python3
"""Run the downloadable project in isolation and check outputs with GDAL >= 3.13.

Requires HOP_JAVA_HOME or JAVA_HOME, --hop-home and --ogrinfo. Set GDAL_DATA
and PROJ_DATA for a bundled GDAL installation if needed. No user data is modified.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['shapefile', 'geopackage', 'filegdb', 'flatgeobuf', 'parquet', 'generate',
         'geopackage-add-layer', 'geopackage-append', 'read-shapefile', 'read-filegdb']
EXPECTED = [(1, 'Aare', 430.5, 2600000.0, 1200000.0),
            (2, 'Brücke', 432.25, 2600100.0, 1200050.0),
            (3, 'Park', 428.75, 2600200.0, 1200100.0)]


def check_outputs(folder, ogrinfo):
    reports = {}
    for name in ['sites.shp', 'sites.gpkg', 'sites.gdb', 'sites.fgb', 'sites.parquet',
                 'shapefile-readback.gpkg', 'filegdb-readback.gpkg']:
        result = subprocess.run([ogrinfo, '-json', '-al', '-features', str(folder / name)],
                                check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for layer in data['layers']:
            multiplier = 2 if name == 'sites.gpkg' and layer['name'] == 'sites' else 1
            assert layer['featureCount'] == 3 * multiplier, (name, layer['name'], layer['featureCount'])
            wkt = layer['geometryFields'][0]['coordinateSystem']['wkt']
            assert '2056' in wkt and 'CH1903+' in wkt, (name, wkt)
            rows = []
            for feature in layer['features']:
                prop = {k.lower(): v for k, v in feature['properties'].items()}
                geom = feature['geometry']
                assert geom['type'] == 'Point', (name, geom)
                rows.append((prop['site_id'], prop['name'], prop['height_m'], *geom['coordinates']))
            assert Counter(rows) == Counter(EXPECTED * multiplier), (name, rows)
            reports[name + ':' + layer['name']] = len(rows)
    expected_gen = ''.join(f'{i} {x:.2f} {y:.2f}\n' for i, _, _, x, y in EXPECTED) + 'END\n'
    assert (folder / 'sites.gen').read_text() == expected_gen
    reports['sites.gen'] = 3
    return reports


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hop-home', type=Path)
    p.add_argument('--ogrinfo', required=True)
    p.add_argument('--check-output', type=Path, help='Check an already generated output folder only')
    args = p.parse_args()
    if args.check_output:
        print(json.dumps(check_outputs(args.check_output, args.ogrinfo), indent=2))
        return
    if not args.hop_home:
        p.error('--hop-home is required unless --check-output is used')
    # A space in this path also checks that the published project is portable.
    work = Path(tempfile.mkdtemp(prefix='geohop-validation-'))
    project = work / 'vector formats'
    shutil.copytree(ROOT / 'downloads/vector-formats', project,
                    ignore=lambda path, names: [n for n in names if Path(path).name == 'output' and n != 'README.txt'])
    config = work / 'config'
    config.mkdir()
    (config / 'hop-config.json').write_text(json.dumps({'projectsConfig': {
        'enabled': True, 'projectMandatory': True, 'defaultProject': 'vector-formats',
        'projectConfigurations': [{'projectName': 'vector-formats', 'projectHome': str(project),
                                   'configFilename': 'project-config.json'}]}}))
    env = dict(os.environ, HOP_CONFIG_FOLDER=str(config), HOP_AUDIT_FOLDER=str(work / 'audit'))
    # Keep metadata scoped to the copied project, even if the caller has a Hop environment.
    env['HOP_METADATA_FOLDER'] = str(project / 'metadata')
    hop = args.hop_home.resolve()
    launcher = hop / ('hop-run.bat' if os.name == 'nt' else 'hop-run.sh')
    def run(name):
        cmd = [str(launcher), '-j', 'vector-formats', '-r', 'local', '-f', str(project / (name + '.hpl'))]
        if os.name == 'nt':
            cmd = ['cmd.exe', '/d', '/s', '/c', subprocess.list2cmdline(cmd)]
        with (work / (name + '.log')).open('w') as log:
            result = subprocess.run(cmd, cwd=hop, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        return result.returncode
    print('Validation artifacts:', work, flush=True)
    for name in NAMES:
        assert run(name) == 0, f'{name} failed; see {work}'
        print('PASS', name, flush=True)
    report = check_outputs(project / 'output', args.ogrinfo)
    # A second create must fail without damaging the existing dataset.
    before = (project / 'output/sites.gpkg').read_bytes()
    assert run('geopackage') != 0, 'CREATE_FILE unexpectedly replaced an existing GeoPackage'
    assert (project / 'output/sites.gpkg').read_bytes() == before, 'Existing GeoPackage was modified'
    (work / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print('PASS existing-output protection')


if __name__ == '__main__':
    main()
