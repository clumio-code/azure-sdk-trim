#
# Copyright 2021 Clumio, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Unittests for azure_sdk_trim.py."""

from __future__ import annotations

import pathlib
import unittest
from unittest import mock

import pyfakefs.fake_filesystem_unittest as fake_fs  # type: ignore

from .. import azure_sdk_trim  # type: ignore

# pylint: disable=missing-docstring
# easier patching:
AZURE_SDK_TRIM = azure_sdk_trim.__name__

FAKE_MODELS = {
    '/fake/azure/cli/core/vendored_sdks/subscriptions': (('v2016_06_01',), ('v2019_11_01',)),
    '/fake/azure/mgmt/authorization/': (
        ('v2018_07_01_preview', 'v2018_09_01_preview'),
        ('v2015_06_01', 'v2015_07_01'),
    ),
    '/fake/azure/mgmt/network': (('v2015_06_15',), ('v2020_11_01', 'v2021_02_01')),
    '/fake/azure/mgmt/redhatopenshift': ((), ('v2020_04_30',)),
    '/fake/azure/other': (('v2020_11_01', 'v2021_02_01'), ('v7_0',)),
}
EXPECTED_DIRS = (
    '/fake/azure/cli/core/vendored_sdks',
    '/fake/azure/cli/core/vendored_sdks/subscriptions/v2019_11_01',
    '/fake/azure/mgmt/authorization/v2015_06_01',
    '/fake/azure/mgmt/authorization/v2015_07_01',
    '/fake/azure/mgmt/network/v2020_11_01',
    '/fake/azure/mgmt/network/v2021_02_01',
    '/fake/azure/mgmt/redhatopenshift/v2020_04_30',
    '/fake/azure/other/v7_0',
)


class TestDiskUsage(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(mock.patch.stopall)
        self.m_run = mock.patch('subprocess.run').start()

    def test_disk_usage(self):
        self.m_run.return_value.stdout = '42\t /fake\n'
        self.assertEqual(42 * 1024, azure_sdk_trim.disk_usage(pathlib.Path('/fake')))
        self.m_run.assert_called_once_with(
            ['du', '-ksx', pathlib.Path('/fake')], check=True, capture_output=True, text=True
        )


class TestGetBaseDir(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(mock.patch.stopall)
        self.find_spec = mock.patch('importlib.util.find_spec').start()
        self.spec = mock.Mock('importlib._bootstrap.ModuleSpec')
        self.find_spec.return_value = self.spec

    def test_no_spec(self):
        self.find_spec.return_value = None
        with self.assertRaises(azure_sdk_trim.Error):
            azure_sdk_trim.get_base_dir()
        self.find_spec.assert_called_once_with('azure')

    def test_no_locations(self):
        self.spec.submodule_search_locations = []
        with self.assertRaises(azure_sdk_trim.Error):
            azure_sdk_trim.get_base_dir()
        self.find_spec.assert_called_once_with('azure')

    def test_found_azure(self):
        self.spec.submodule_search_locations = ['/fake']
        self.assertEqual(pathlib.Path('/fake'), azure_sdk_trim.get_base_dir())
        self.find_spec.assert_called_once_with('azure')


class TestPurgeOldReleasesFunctional(fake_fs.TestCase):
    def setUp(self) -> None:
        self.setUpPyfakefs()
        self.disk_usage = mock.patch(f'{AZURE_SDK_TRIM}.disk_usage').start()
        self.disk_usage.return_value = 1
        for directory, versions in FAKE_MODELS.items():
            (extra, keep) = versions
            dir_path = pathlib.Path(directory)
            print('mkdir', dir_path)
            contents = '\n'.join(f'from .{version}.models import *' for version in keep)
            self.fs.create_file(dir_path / 'models.py', contents=contents)
            all_versions = list(extra) + list(keep)
            for version in all_versions:
                self.fs.create_dir(dir_path / version)

    def test_find_api_dirs_not_empty(self):
        self.assertTrue(azure_sdk_trim.find_api_dirs(pathlib.Path('/fake/azure')))

    def test_purge(self):
        fake_azure = pathlib.Path('/fake/azure')
        azure_sdk_trim.purge_old_releases(fake_azure)
        remaining_dirs = tuple(sorted(str(_) for _ in fake_azure.rglob('v*') if _.is_dir()))
        print(remaining_dirs)
        self.maxDiff = None  # pylint: disable=invalid-name
        self.assertEqual(EXPECTED_DIRS, remaining_dirs)
