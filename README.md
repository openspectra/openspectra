##OpenSpectraDev 

...is a development project for OpenSpectra

You'll need Python 3.7 installed and can use,

````
pip install -r requirements.txt
````

from inside the OpenSpectra project directory.  Using virutalenvwrapper is highly reccomended.

Here is a good guide for setting up Python and your project on multiple platforms, https://docs.python-guide.org/

Note: On Mac you'll want to update and use the provided run.sh script.  It contains a workaround for a permissing problem when running from within a virtual environment.

###Unit tests

To run unit tests from the command line make sure your project is active and you are in the project root directory.  Then run,
````
python -m unittest discover -t . -s test/unit_tests -p "*_test.py"
````