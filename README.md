# Python + Qt5 interface to the ArC1 platform

This is the main repository of the ArC1 control panel, a tool to run tests on
the [ArC1 characterisation
platform](http://www.arc-instruments.co.uk/products/arc-one).  Versatile and
extensible it provides all you need to start characterising memory devices with
your ArC ONE board. Powered by the Qt framework it is available on all major
operating systems.

## Install

### On Windows

For Windows a ready-to-run executable is provided in the [releases
page](https://github.com/arc-instruments/arc1_pyqt/releases). Just unzip and
run `ArC ONE Control.exe`. Please note that depending on your Windows version
you might need to install the [ARM mbed serial port
driver](https://os.mbed.com/handbook/Windows-serial-configuration).

### On anything supported by Python + Qt5

You need to have Python ≥3.6 installed in your system. Then download and unzip
a release snapshot from the [releases
page](https://github.com/arc-instruments/arc1_pyqt/releases) or clone this
repository. Then using a command line navigate to the folder you have unzipped
arc1_pyqt and run

```
python -m pip install -r requirements.txt
```

to fetch all the required Python modules. On Linux you might want to use your
package manager instead or otherwise run the above command with the `user`
target:

```
python -m pip install --user -r requirements.txt
```

Then run `python genui.py` to generate necessary files. Everything should now
be up to date to run the program with `python main.py`.

## Use

You should now have everything you need to characterise devices with your ArC1
board. Follow [the user
documentation](http://files.arc-instruments.co.uk/documents/ArC_One.pdf) for a
complete guide on how to use the software for your experiments.

## Develop

If the built-in functionality is not enough for your testing procedure you can
create your own modules to better suit your needs. Existing modules under
[ProgPanels](https://github.com/arc-instruments/arc1_pyqt/tree/master/ProgPanels)
can serve as a scaffold for you to build your own characterisation routines.

## I found a bug!

If arc1_pyqt does not behave as you would expect please [open an
issue](https://github.com/arc-instruments/arc1_pyqt/issues/new) describing the
problem and how to reproduce it. Don't forget to mention the operating system
you are running on!

