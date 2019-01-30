#!/bin/bash

#Run this script after activating (workon) the virtual env.
PYVER=3.7

if [ -z "$VIRTUAL_ENV" ] ; then
    echo "You must activate your virtualenv: set '$VIRTUAL_ENV'"
    exit 1
fi

# Modify PYTHON_ROOT to point to your globally installed version of Python
PYTHON_ROOT="/usr/local/Cellar/python/3.7.2_1/Frameworks/Python.framework/Versions/$PYVER"
PYTHON_BINARY="bin/python$PYVER"
FRAMEWORK_PYTHON="$PYTHON_ROOT/$PYTHON_BINARY"

# Use the Framework Python to run the app
export PYTHONHOME=$VIRTUAL_ENV

echo "Using Python framework:" $FRAMEWORK_PYTHON
#echo "Using virtual environment:" $$VIRTUAL_ENV

exec "$FRAMEWORK_PYTHON" "./$1" $*