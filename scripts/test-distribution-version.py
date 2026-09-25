#!/usr/bin/env python3
"""Regression checks for manual publishing version selection (no network required)."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

SPEC = importlib.util.spec_from_file_location(
    'distribution', Path(__file__).with_name('set-distribution-version.py'))
distribution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(distribution)
VARIABLES = Path(__file__).resolve().parents[1] / '_variables.yml'


def release(tag, date, prerelease=True, draft=False):
    return dict(tag_name=tag, published_at=date, prerelease=prerelease, draft=draft)


def response(releases):
    return io.BytesIO(json.dumps(releases).encode())


class DistributionTests(unittest.TestCase):
    def test_all_pages_and_publication_order(self):
        pages = [
            response([release('v0.2.1-old', '2026-09-22T00:00:00Z'),
                      release('v9.0.0', '2026-09-25T00:00:00Z', prerelease=False)]),
            response([release('v0.2.1-new', '2026-09-24T00:00:00Z'),
                      release('v0.2.1-draft', None, draft=True)]),
            response([]),
        ]
        with patch.object(distribution, 'urlopen', side_effect=pages) as fetch:
            self.assertEqual(distribution.latest_prerelease(), '0.2.1-new')
        self.assertEqual(fetch.call_count, 3)
        self.assertTrue(fetch.call_args.args[0].full_url.endswith('page=3'))

    def test_no_prereleases(self):
        with patch.object(distribution, 'urlopen', return_value=response([])):
            with self.assertRaisesRegex(ValueError, 'No published prerelease'):
                distribution.latest_prerelease()

    def test_main_selection(self):
        for supplied in ('0.2.1-explicit', '', '  \t '):
            expected = supplied if supplied else '0.2.1-latest'
            if not supplied.strip():
                expected = '0.2.1-latest'
            with self.subTest(supplied=supplied), \
                 patch.dict(distribution.os.environ, {'DISTRIBUTION_VERSION': supplied}), \
                 patch.object(distribution, 'latest_prerelease', return_value='0.2.1-latest') as latest, \
                 patch.object(distribution, 'update_variables') as update, \
                 redirect_stdout(io.StringIO()) as output:
                self.assertEqual(distribution.main(), 0)
                update.assert_called_once_with(Path('_variables.yml'), expected)
                self.assertEqual(latest.call_count, int(not supplied.strip()))
                self.assertIn(expected, output.getvalue())

    def test_invalid_inputs_do_not_write_or_fetch(self):
        for value in ('v0.2.1', '../0.2.1', '0.2.1\nmalicious', '$(echo hello)', '0.2.1/x'):
            with self.subTest(value=value), \
                 patch.dict(distribution.os.environ, {'DISTRIBUTION_VERSION': value}), \
                 patch.object(distribution, 'urlopen') as fetch, \
                 patch.object(distribution, 'update_variables') as update, \
                 redirect_stderr(io.StringIO()):
                self.assertEqual(distribution.main(), 1)
                fetch.assert_not_called()
                update.assert_not_called()

    def test_api_error_fails_without_writing(self):
        with patch.dict(distribution.os.environ, {'DISTRIBUTION_VERSION': ''}), \
             patch.object(distribution, 'urlopen', side_effect=URLError('API unavailable')), \
             patch.object(distribution, 'update_variables') as update, \
             redirect_stderr(io.StringIO()) as error:
            self.assertEqual(distribution.main(), 1)
            self.assertIn('API unavailable', error.getvalue())
            update.assert_not_called()

    def test_consistent_variables_and_preserved_dates(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '_variables.yml'
            original = VARIABLES.read_text()
            path.write_text(original)
            distribution.update_variables(path, '0.2.1-test')
            values = dict(line.split(': ', 1) for line in path.read_text().splitlines())
            values = {key: json.loads(value) for key, value in values.items()}
            self.assertEqual(values['distribution-version'], '0.2.1-test')
            self.assertEqual(values['archive-name'],
                             f"apache-hop-client-{values['hop-version']}-geo-0.2.1-test.zip")
            self.assertTrue(values['release-url'].endswith('/tag/v0.2.1-test'))
            self.assertTrue(values['archive-url'].endswith(
                '/download/v0.2.1-test/' + values['archive-name']))
            for line in original.splitlines():
                if line.startswith(('hop-version:', 'release-date:', 'checked-date:')):
                    self.assertIn(line, path.read_text().splitlines())


if __name__ == '__main__':
    unittest.main()
