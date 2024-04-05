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

# SHELL ensures more consistent behavior between macOS and Linux.
SHELL=/bin/bash

test_reports := build/test_reports/py

.PHONY: *


clean:
	rm -rf build .mypy_cache .coverage *.egg-info dist

build:
	python3 -m build

# Install the script locally.
install:
	pip install .


# Install the script and the development dependencies.
dev-install:
	pip install '.[dev]'


uninstall:
	pip uninstall azure_sdk_trim

# Run the unittests.
test:
	rm -rf $(test_reports) .coverage; \
    mkdir -p $(test_reports); \
    python3 -m green --run-coverage --junit-report=$(test_reports)/azure_sdk_trim-pytests.xml azure_sdk_trim; \
    python3 -m coverage xml -o $(test_reports)/azure_sdk_trim-pycoverage.xml; \
    python3 -m coverage html -d $(test_reports)/azure_sdk_trim-pycoverage-html
	@echo "HTML code coverage report was generated in $(test_reports)/azure_sdk_trim-pycoverage-html"
	@echo "Open it with:"
	@echo "  open $(test_reports)/azure_sdk_trim-pycoverage-html/index.html"


# Run pylint to help check that our code is sane.
pylint:
	python3 -m pylint azure_sdk_trim


# Run mypy to check that our type annotation is correct.
mypy:
	python3 -m mypy azure_sdk_trim


checks: pylint mypy test
