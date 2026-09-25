#!/usr/bin/env python3
"""Set build-time release variables, resolving an empty input to the latest prerelease."""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

REPOSITORY = 'edigonzales/hop-distributions'
RELEASES_URL = f'https://github.com/{REPOSITORY}/releases'


def validate_version(value):
    if not re.fullmatch(r'[0-9][A-Za-z0-9._+-]*', value):
        raise ValueError('Distribution version must start with a digit, omit the leading v, '
                         'and contain only letters, digits, dots, underscores, + or -.')
    return value


def latest_prerelease():
    headers = {'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'hop-plugins-site'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f"Bearer {os.environ['GH_TOKEN']}"
    latest = None
    page = 1
    while True:
        request = Request(
            f'https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}',
            headers=headers)
        with urlopen(request, timeout=30) as response:
            releases = json.load(response)
        if not isinstance(releases, list):
            raise ValueError('GitHub API returned an invalid release list.')
        if not releases:
            break
        for release in releases:
            if release['prerelease'] and not release['draft']:
                published = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
                if latest is None or published > latest[0]:
                    latest = (published, release['tag_name'])
        page += 1
    if latest is None:
        raise ValueError(f'No published prerelease found in {REPOSITORY}.')
    return validate_version(latest[1].removeprefix('v'))


def update_variables(path, version):
    content = path.read_text()
    # This file contains flat, quoted string variables; preserve unrelated lines.
    hop_match = re.search(r'^hop-version:\s*"([^"\n]+)"\s*$', content, re.MULTILINE)
    if hop_match is None:
        raise ValueError('Expected a quoted hop-version in _variables.yml.')
    hop_version = validate_version(hop_match[1])
    archive = f'apache-hop-client-{hop_version}-geo-{version}.zip'
    values = {
        'distribution-version': version,
        'release-url': f'{RELEASES_URL}/tag/v{version}',
        'archive-name': archive,
        'archive-url': f'{RELEASES_URL}/download/v{version}/{archive}',
    }
    for key, value in values.items():
        content, count = re.subn(rf'^{re.escape(key)}:[^\n]*$',
                                 lambda _: f'{key}: {json.dumps(value)}',
                                 content, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f'Expected exactly one {key} in _variables.yml.')
    path.write_text(content)


def main():
    try:
        version = os.environ.get('DISTRIBUTION_VERSION', '').strip()
        version = validate_version(version) if version else latest_prerelease()
        update_variables(Path('_variables.yml'), version)
    except (OSError, URLError, ValueError, KeyError, TypeError) as error:
        print(f'Cannot resolve distribution version: {error}', file=sys.stderr)
        return 1
    print(f'Distribution version: {version}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
