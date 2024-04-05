# azure-sdk-trim

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=bugs)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=clumio-code_azure-sdk-trim&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=clumio-code_azure-sdk-trim)

Simple Python script to purge mostly useless Azure SDK API versions.

The Azure SDK for python is 1.2GB and growing. The main reason for the
size and growth is that each release gets added internally and all prior
releases are kept. This is a troublesome design that does not seem to be fully
addressed in the near future. The logic deletes most but not all older API
versions as multiple API versions can import prior versions, and the azure cli
can point directly at older, preview, versions. This approach keeps a high
compatibility level while trimming half of the space used.

The 0.2.2 release has been tested with Python 3.12.2, azure-cli 2.59.0 where the
azure sdk is 1.2GB and the trimmed version is about 600MB.
We unittest against python versions 3.8 to 3.12 on macOS, Linux and Windows.

So Long & Thanks For All The Fish.


## Installation

This script is not published on pypi.org but you can either download the script
as a standalone script or pip install it from github directly:

```shell
wget https://raw.githubusercontent.com/clumio-code/azure-sdk-trim/main/azure_sdk_trim/azure_sdk_trim.py
```

```shell
pip install git+https://github.com/clumio-code/azure-sdk-trim@v0.2.0#egg=azure-sdk-trim
```


## Caveats

While most third party packages that use the Azure SDK do not point to older
APIs explicitly, some do which can lead to issues.

If you use a third party package that points to a specific version that got
deleted, then you will experience runtime failures. A temporary workaround can
be to create a symlink to point the old version folder to a newer version. This
usually works but could lead to unsuspected behavior.
As such, we do not intend to add symlinks automatically. We recommend filing
bugs against the upstream maintainers so that they stop pointing to obsolete
APIs versions.

We use newer Python syntax, so py3.12 is recommended, but the code can be
modified for backward compatibility with older python versions if needed.
We will not accept any PR to add support for unsupported versions of Python
(anything older than 3.8 as of this writing).


## Style Guide

We follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
with a few distinctions. We use 100 characters width and prefer single quotes
over double quotes for regular string declarations. Triple quoting is always
done with double quotes: `"""A docstring.""""`

For most of the formatting,
we rely on [Gray](https://github.com/dizballanze/gray)
configured to use [Black](https://github.com/psf/black).

Please run `gray .` and `make test mypy pylint`, before submitting any PR.


## Disclaimer

This project is not affiliated with Microsoft or the Azure SDK maintainers.


## Links

* https://github.com/Azure/azure-sdk-for-python/issues/11149
* https://github.com/Azure/azure-sdk-for-python/issues/17801
* https://github.com/kapicorp/kapitan/issues/761
