## OpenSpectraDev 

...is a development project for OpenSpectra

You'll need Python 3.7 installed and can use,

````
pip install -r requirements.txt
````

from inside the OpenSpectra project directory.  Using virutalenvwrapper is highly reccomended.

Here is a good guide for setting up Python and your project on multiple platforms, https://docs.python-guide.org/

Note: On Mac you'll want to update and use the provided run.sh script.  It contains a workaround for a permissing problem when running from within a virtual environment.

### Samples

In the "samples" folder you'll find, you guessed it, samples!  These are intended to be small examples of how to use various features of OpenSpectra that don't rely on the UI of the main application.

To run a sample from the command line make sure you are in the top level project directory, the directory this README file is in.  Then for example to run the image sample use the following command,
````
python -m samples.image
````
Don't for the "samples." before the base file name.  

Also be sure to checkout the source code itself.  They'll be heavily commented to explain what is going on at each step in the code.

You should also be able to run them in your IDE with or without debugging.  In PyCharm for example simply right click the sample file you want to run and choose eithr "Run" or "Debug".

### Unit tests

To run unit tests from the command line make sure your project is active and you are in the project root directory.  Then run,
````
python -m unittest discover -t . -s test/unit_tests -p "*_test.py"
````

### Wiki links
*  [Home page](https://gitlab.com/openspectradev/openspectradev/wikis/OpenSpectraDev-Wiki-Home)
*  [Git Tips](https://gitlab.com/openspectradev/openspectradev/wikis/git/Git-Tips)