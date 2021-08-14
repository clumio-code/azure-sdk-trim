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

"""Setup script for azure-sdk-trim."""

import sys

from setuptools import find_packages
from setuptools import setup

if sys.version_info[0] < 3:
    with open('README.md') as fh:
        long_description = fh.read()
else:
    with open('README.md', encoding='utf-8') as fh:
        long_description = fh.read()

setup(
    name='azure-sdk-trim',
    version='0.1.0',
    description='Python SDK for Clumio REST API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Clumio Inc.',
    author_email='support@clumio.com',
    url='https://clumio.com',
    classfiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    entry_points={'console_scripts': ['azure-sdk-trim=azure_sdk_trim.azure_sdk_trim:main']},
    install_requires=[
        'humanize>=3.11.0',
    ],
)
