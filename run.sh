#!/bin/bash

#Run this script after activating (workon) the virtual env.
#Install wxPython in the virtual env using pip install wxPython.

#WXPYTHON_APP="helloWorld.py"
PYVER=3.6

if [ -z "$VIRTUAL_ENV" ] ; then
    echo "You must activate your virtualenv: set '$VIRTUAL_ENV'"
    exit 1
fi

PYSUBVER=3.6.5

BREW_PYTHON_ROOT="/usr/local/Cellar/python/3.6.5/Frameworks/Python.framework/Versions/$PYVER"

PYTHON_BINARY="bin/python$PYVER"

FRAMEWORK_PYTHON="$BREW_PYTHON_ROOT/$PYTHON_BINARY"

# Use the Framework Python to run the app
export PYTHONHOME=$VIRTUAL_ENV

echo $FRAMEWORK_PYTHON

#exec "$FRAMEWORK_PYTHON" "./$WXPYTHON_APP" $*
exec "$FRAMEWORK_PYTHON" "./$1" $*