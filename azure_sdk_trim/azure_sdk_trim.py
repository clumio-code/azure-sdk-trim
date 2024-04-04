#!/usr/bin/env python3
#
# Copyright 2021. Clumio, Inc.
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

The Azure SDK for python is 1.2GB and growing. The main reason for the size and
growth is that each release gets added internally and all prior releases are
kept. This is a troublesome design that does not seem to be seriously addressed,
even after being reported and acknowledged for several years.

This tool deletes most but not all API versions as multiple versions depend on
each other, and the az cli itself does not always use the latest versions.

This keeps a high-compatibility level while trimming almost half of the space.

Note that the az cli team has since created their own trim_sdk.py script, linked
below.

So Long & Thanks For All The Fish.

https://github.com/Azure/azure-sdk-for-python/issues/11149
https://github.com/Azure/azure-sdk-for-python/issues/17801
https://github.com/Azure/azure-cli/issues/26966
https://github.com/Azure/azure-cli/blob/dev/scripts/trim_sdk.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Sequence

from humanize import filesize

try:
    # Import the az cli profiles module, if present, to detect which SDK versions are used.
    from azure.cli.core import profiles  # type: ignore
except ImportError:
    profiles = None


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


def get_az_cli_versions() -> dict[str, str]:
    """Returns list of SDK versions used by the az cli.

    The az cli has its own opinionated set of old SDKs to deal with. This is
    very unfortunate. We also have to resort to do a runtime import which is a
    bad practice, but we need to access the az CLI internals.
    """
    if profiles is None:
        logger.info('No az cli detected.')
        return {}
    latest = profiles.API_PROFILES['latest']
    versions = {}
    for sdk, version in latest.items():
        if version is None:
            continue
        # Use .removeprefix() instead of .replace() when we drop python 3.8 support.
        sdk_dir = sdk.import_prefix.replace('azure.', '', 1).replace('.', '/')
        version_string = version if isinstance(version, str) else version.default_api_version
        version_dir = 'v' + version_string.replace('.', '_').replace('-', '_')
        versions[sdk_dir] = version_dir
    logger.info('Detected az cli with %d SDKs to keep.', len(versions))
    logger.debug(json.dumps(versions, indent=4, sort_keys=True))
    return versions


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
    import the models from specific versions. The most recent, default, versions
    are assumed to be in that list of imports.

    We scrape the import lines in the models.py file to detect that this is a
    multi-versioned API with potential folders to be trimmed. The import list is
    them used as a keep list.
    """

    def __init__(self, path: pathlib.Path, base_dir: pathlib.Path) -> None:
        self._path = path.parent if path.name == 'models.py' else path
        self._base_dir = base_dir
        self._versions: set[str] | None = None
        self._keep: set[str] = set()

    @property
    def path(self) -> pathlib.Path:
        """Returns the path of the API directory."""
        return self._path

    @property
    def sub_dir(self) -> str:
        """Returns the subdirectory of the API directory."""
        return str(self.path.relative_to(self._base_dir))

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

    def keep(self, versions: str | Sequence[str] = ()):
        """Keep the given versions."""
        self._keep.update((versions,) if isinstance(versions, str) else versions)
        self._versions = None

    @property
    def versions(self) -> set[str]:
        """Returns the versions declared in models.py."""
        if self._versions is None:
            versions = set(self._parse_models())
            versions.update(self._keep)
            self._versions = versions
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
        api_dir = VersionedApiDir(sub_path, base_dir)
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

    cli_versions = get_az_cli_versions()
    api_dirs = find_api_dirs(base_dir)
    for api_dir in api_dirs:
        if api_dir.sub_dir in cli_versions:
            api_dir.keep(cli_versions[api_dir.sub_dir])
        purge_api_dir(api_dir)

    new_usage = disk_usage(base_dir)
    logger.info('%s is now using %s.', base_dir, filesize.naturalsize(new_usage))
    logger.info('Saved %s.', filesize.naturalsize(usage - new_usage))


def main(argv: Sequence[str]):
    """Main."""
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


def entry_point():
    """Entry point."""
    sys.exit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
