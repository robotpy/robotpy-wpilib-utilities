#!/bin/bash

set -e
cd `dirname $0`

PYTHONPATH=.. python3 -m coverage run --source robotpy_ext -m pytest $@
python -m coverage report -m

