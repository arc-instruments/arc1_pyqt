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

You need to have **Python ≥3.7** and **git** installed in your system. You can
install the latest snapshot using the command.

```
pip install git+https://github.com/arc-instruments/arc1_pyqt
```

Starting with v2.0.0-rc0 arc1_pyqt is also available from PyPI: `pip install
arc1_pyqt`.

## Use

You should now have everything you need to characterise devices with your ArC1
board. Follow [the user
documentation](http://files.arc-instruments.co.uk/documents/ArC_One.pdf) for a
complete guide on how to use the software for your experiments.

## Develop

If the built-in functionality is not enough for your testing procedure you can
create your own modules to better suit your needs. Custom modules must subclass
`arc1pyqt.modutils.BaseProgPanel` and be placed in one of the standard module
load directories which can be found under *Settings* → *Module directories*.
You can either create a single-file module such as those that are shipped with
`arc1_pyqt` and can be found under `arc1_pyqt/ProgPanels` or standard Python
packages for more elaborate ones. On the top-level of your package you should
have a python module with the same name as the module for `arc1_pyqt` to pick
it up at startup.

If you want to develop on `arc1_pyqt` itself clone this repository and install
its dependencies with `python -m pip install -r requirements.txt`.

## I found a bug!

If arc1_pyqt does not behave as you would expect please [open an
issue](https://github.com/arc-instruments/arc1_pyqt/issues/new) describing the
problem and how to reproduce it. Don't forget to mention the operating system
you are running on!

