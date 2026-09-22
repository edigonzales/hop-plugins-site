#!/usr/bin/env python3
"""Build the downloadable project without local run outputs or audit files."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
source = root / 'downloads/vector-formats'
files = sorted(source.glob('*.hpl')) + [source / n for n in
    ['README.md', 'LICENSE.txt', 'project-config.json', 'data/README.md',
     'data/sites.csv', 'data/sites.gpkg', 'metadata/pipeline-run-configuration/local.json',
     'output/README.txt']]
with zipfile.ZipFile(root / 'downloads/vector-formats.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        info = zipfile.ZipInfo('vector-formats/' + path.relative_to(source).as_posix(), (2026, 9, 22, 0, 0, 0))
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, path.read_bytes())
print('Packaged', len(files), 'example project files')
