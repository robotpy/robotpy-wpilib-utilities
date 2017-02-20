#!/bin/bash

set -e
cd `dirname $0`/..

ROBOTPY_DIR="../robotpy-wpilib"

source $ROBOTPY_DIR/devtools/_windows_env.sh

VERSION=`git describe --tags --long --dirty='-dirty'`

if [[ ! $VERSION =~ ^[0-9]+\.[0-9]\.[0-9]+$ ]]; then
    # Convert to PEP440
    IFS=- read VTAG VCOMMITS VLOCAL <<< "$VERSION"
    VERSION=`printf "%s.post0.dev%s" $VTAG $VCOMMITS`
fi

python3 setup.py sdist --formats=gztar

# Run the install now
python3 -m robotpy_installer install -U --force-reinstall --no-deps dist/robotpy-wpilib-utilities-$VERSION.tar.gz
