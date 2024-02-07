# azure-sdk-trim

Simple Python script to purge mostly useless Azure SDK API versions.

The Azure SDK for python is 1.2GB and growing. The main reason for the
size and growth is that each release gets added internally and all prior
release are kept. This is a troublesome design which does not seem to be
addressed in the near future. This deleted most but not all API versions as
multiple versions are required for importing the models. This keep a high
compatibility level while trimming half of the space used.

The latest version has been tested with Python 3.12.1, but the unittests pass with 3.8.
For the Azure versions the latest version has been tested with azure-cli 2.53.0 to 2.57.0.

So Long & Thanks For All The Fish.


## Installation

Due to the highly specilized nature of this script it is not published on pypi.org so you can either download the script as a standalone script or
pip install it from github directly:

```shell
wget https://raw.githubusercontent.com/clumio-code/azure-sdk-trim/main/azure_sdk_trim/azure_sdk_trim.py
```

```shell
pip install git+https://github.com/clumio-code/azure-sdk-trim@v0.2.0#egg=azure-sdk-trim
```

The script has been developed and tested with Python 3.12.1, but compatibility
with older releases of Python 3 should be possible.


## Caveats

While most third party packages that use the Azure SDK do not point to older
APIs explicitly,  some do which can lead to issues. The script does not support
keeping a list of directories that  should be preserved. In practice, we found
out that simply adding a symlink so that the old version points to the latest
version is a good enough workaround but this could lead to unsuspected behavior,
so we do not intend to add symlinks automatically. We recommend filing bugs
against the upstream maintainers so that they stop pointing to obsolete APIs.

We use newer Python syntax so py3.12 is recommended, but the code can be modified for
backward compatibility with 3.8 if needed. We will not accept any PR to add
support for unsupported versions of Python (anything older than 3.8).


## Style Guide

We follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
with a few distinctions. We use 100 character width and prefer single quotes
over double quotes for regular string declarations. Triple quoting is always
done with double quotes: `"""A docstring.""""`

For most of the formatting we rely on [Gray](https://github.com/dizballanze/gray)
and [Black](https://github.com/psf/black) to ensure conformance.

Please run `gray .` before submitting any Pull Request.


## Links

* https://github.com/Azure/azure-sdk-for-python/issues/11149
* https://github.com/Azure/azure-sdk-for-python/issues/17801
* https://github.com/kapicorp/kapitan/issues/761
