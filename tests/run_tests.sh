#!/bin/bash

set -e
cd `dirname $0`

PYTHONPATH=.. python3 -m coverage run --source robotpy_ext,magicbot -m pytest $@
python -m coverage report -m

