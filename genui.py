#!/usr/bin/python

import glob
import os
import os.path
import sys

from PyQt5.uic import compileUi


def doCompile(src, dst):
    """
    Compile UI file `src` into the python file `dst`. This is similar to
    what the pyuic script is doing but with some predefined values.
    """

    # First check python version
    if sys.hexversion >= 0x03000000:
        # Check if we are writing to stdout ("-") instead of a file
        if dst == '-':
            from io import TextIOWrapper
            out = TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        else:
            # just open the file
            out = open(dst, 'wt', encoding='utf-8')
    else:
        # Check if we are writing to stdout ("-") instead of a file
        if dst == '-':
            out = sys.stdout
        else:
            # just open the file
            out = open(dst, 'wt')

    # see the docstring of PyQt5.uic.compileUi for more!
    compileUi(src, out, execute=False, indent=4)


def main():

    # Find the current working directory (ie. the folder this script resides
    # in). Then find out where the UI files are stored and setup the output
    # directory.
    cwd = os.path.dirname(os.path.realpath(__file__))
    uidir = os.path.join(cwd, 'uis')
    outdir = os.path.join(cwd, 'GeneratedUiElements')

    # Check if outdir exists but is not a directory; in that case
    # bail out!
    if not os.path.isdir(outdir) and os.path.exists(outdir):
        print("%s exists but is not a directory; aborting" % outdir)
        sys.exit(1)

    # Load up all UI files from `uidir`...
    uis = glob.glob(os.path.join(uidir, "*.ui"))

    # ... and convert them into python classes in `outdir`.
    for ui in uis:
        # target filename is the same as source with the .py suffix instead
        # of .ui.
        fname = os.path.splitext(os.path.basename(ui))[0]
        target = os.path.join(outdir, "%s.py" % fname)

        print("[UIC] Generating %s " % os.path.basename(target), \
            file=sys.stderr)

        doCompile(ui, target)

if __name__ == "__main__":
    main()

