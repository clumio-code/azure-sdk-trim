#!/usr/bin/env python3
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
# Google Style 4 spaces, 100 columns:
#   https://google.github.io/styleguide/pyguide.html
#

"""Simple script to purge mostly useless Azure SDK API versions.

The Azure SDK for python is over 600MB and growing. The main reason for the
size and growth is that each release gets added internally and all prior
release are kept. This is a troublesome design which does not seem to be
addressed in the near future. This deleted most but not all API versions as
multiple versions are required for importing the models. This keep a high
compatibility level while trimming more than half of the space used.

So Long & Thanks For All The Fish.

https://github.com/Azure/azure-sdk-for-python/issues/11149
https://github.com/Azure/azure-sdk-for-python/issues/17801
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Optional, Sequence

from humanize import filesize  # type: ignore

logger = logging.getLogger(__name__)


class Error(Exception):
    """Local Errors."""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose mode.')
    parser.add_argument(
        '--azure_dir',
        type=str,
        help='Optional path to the Azure SDK directory. It will try to find it automatically.',
    )

    return parser.parse_args(argv[1:])


def disk_usage(path: pathlib.Path) -> int:
    """Returns the disk usage size in byte for the given path.

    This depends on the unix 'du' tool to be present.
    """
    process = subprocess.run(['du', '-ksx', path], check=True, capture_output=True, text=True)
    return 1024 * int(process.stdout.split('\t', 1)[0])


def get_base_dir() -> pathlib.Path:
    """Returns the base directory where the Azure SDK is installed."""
    spec = importlib.util.find_spec('azure')
    if spec is None or not spec.submodule_search_locations:
        raise Error('No azure package in the python path.')
    return pathlib.Path(spec.submodule_search_locations[0])


class VersionedApiDir:
    """Class to handle API dirs.

    Such directories will contain one or more version folder such as v7.0,
    v2020_12_01 or v2021_02_01_preview and a file named models.py which will
    imports the models from specific versions. The most recent, default, version
    is assumed to be in that list of imports.

    We scrape the imports lines in the models file to detect that this is a
    multi versioned API with potential folders to be trimmed. The import list is
    use to whitelist the folders we need to keep.
    """

    def __init__(self, path: pathlib.Path):
        self._path = path.parent if path.name == 'models.py' else path
        self._versions: Optional[tuple[str, ...]] = None

    @property
    def path(self) -> pathlib.Path:
        """Returns the path of the API directory."""
        return self._path

    def _parse_models(self) -> tuple[str, ...]:
        """Parse models.py to find which versions are in imported and in use."""
        models_path = self._path / 'models.py'
        if not models_path.exists():
            return ()
        versions: list[str] = []
        # match: re.Match
        for line in models_path.read_text().splitlines():
            if match := re.match(r'from [.](v\d[^.]+)[.]models import *', line):
                versions.append(match.group(1))
        return tuple(versions)

    @property
    def versions(self) -> tuple[str, ...]:
        """Returns the versions declared in models.py."""
        if self._versions is None:
            self._versions = self._parse_models()
        return self._versions

    @property
    def is_versioned(self) -> bool:
        """Return True if this is a versioned API directory."""
        return bool(self.versions)

    def trim_other_versions(self) -> int:
        """Removed the unused versions of the current API."""
        if not self.is_versioned:
            return 0
        deleted = []
        for version_dir in self.path.glob('v*_*'):
            if not version_dir.is_dir():
                continue
            if version_dir.name in self.versions:
                continue
            if not re.match(r'v\d', version_dir.name):
                continue
            shutil.rmtree(version_dir)
            deleted.append(version_dir)
        return len(deleted)


def find_api_dirs(base_dir: pathlib.Path) -> set[VersionedApiDir]:
    """Find the API directories with multiple versions."""
    api_dirs = set()
    for sub_path in base_dir.rglob('models.py'):
        api_dir = VersionedApiDir(sub_path)
        if api_dir.is_versioned:
            api_dirs.add(api_dir)
    return api_dirs


def purge_api_dir(api_dir: VersionedApiDir):
    """Purge unnecessary folders from a versioned API directory."""
    usage = disk_usage(api_dir.path)
    logger.debug('%s is using %s', api_dir.path, filesize.naturalsize(usage))
    deleted = api_dir.trim_other_versions()
    new_usage = disk_usage(api_dir.path)
    logger.debug(
        'Saved %s by deleting %d versions.', filesize.naturalsize(usage - new_usage), deleted
    )


def purge_old_releases(base_dir: pathlib.Path):
    """Purge old SDK versions from the Azure installation directory."""
    usage = disk_usage(base_dir)
    logger.info('%s is using %s.', base_dir, filesize.naturalsize(usage))

    api_dirs = find_api_dirs(base_dir)
    for api_dir in api_dirs:
        purge_api_dir(api_dir)

    new_usage = disk_usage(base_dir)
    logger.info('%s is now using %s.', base_dir, filesize.naturalsize(new_usage))
    logger.info('Saved %s.', filesize.naturalsize(usage - new_usage))


def main(argv: Optional[Sequence[str]] = None):
    """Main."""
    if argv is None:
        argv = sys.argv
    args = parse_args(argv)
    if args.verbose:
        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.DEBUG,
        )
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            format='%(message)s',
            level=logging.INFO,
        )
    base_dir = get_base_dir() if not args.azure_dir else pathlib.Path(args.azure_dir)
    purge_old_releases(base_dir)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
