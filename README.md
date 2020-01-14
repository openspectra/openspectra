## OpenSpectra 

An open source tool for viewing hyperspectral image data.

### Version 1.0 released 1/13/2020
#### _Important_ _Note_
If you've setup a previous version of the application from this git repository you may need to re-run
````
pip install -r requirements.txt
````
as some requirements were updated with the release of 1.0.  See the [Feature Notes](https://github.com/openspectra/openspectra/wiki/Feature-Notes) section of the wiki for a brief summary of what has changed.

### Setup notes
At this point the application is available only via this Github repo.  We plan to create an installer in the future for easier setup.

You'll need Python 3.7 or later installed.  Here is a good guide for setting up Python and your project on multiple platforms, https://docs.python-guide.org.  Using virutalenvwrapper is reccomended but not required.  Setup may be easier if you don't mind installing the dependencies globablly.

If you're using a virtual environment set up your project directory first then see the [Clone](https://github.com/openspectra/openspectra/wiki/Git-Tips#clone) section of git tips for how to get the code added to your project.  If not using a virtual environment you can jump straight to the clone instructions.

Once you have the code in your project you'll see a "requirements.txt" file in the top level project directory.  From that directory using the command line execute the follow "pip" command to download the project's dependencies.

````
pip install -r requirements.txt
````

Once the libraries have all downloaded you're ready to run the application.  Simply run,

````
python main.py
````

from the top level project directory.

On Mac if your are using a virtual environment you'll need to update and use the provided "run.sh" script.  It contains a workaround for a permission issue when running from within a virtual environment.  You'll need to update the value of PYTHON_ROOT in run.sh to point to your installation of Python 3.7.  And in this case to start the application use,

````
./run.sh main.py
````

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
*  [Home page](https://github.com/openspectra/openspectra/wiki)
*  [Git Tips](https://github.com/openspectra/openspectra/wiki/Git-Tips)