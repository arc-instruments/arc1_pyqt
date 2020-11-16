####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from ._antennae import CBAntenna, DisplayUpdateAntenna, HistoryTreeAntenna
from ._antennae import InterfaceAntenna, SAantenna, HoverAntenna, AddressAntenna
from PyQt5 import QtGui, QtWidgets, QtCore
import numpy as np
import collections
import struct
from ..VirtualArC import VirtualArC


# Signal emitters
cbAntenna = CBAntenna()
displayUpdate = DisplayUpdateAntenna()
historyTreeAntenna = HistoryTreeAntenna()
interfaceAntenna = InterfaceAntenna()
SAantenna = SAantenna()
hoverAntenna = HoverAntenna()
addressAntenna = AddressAntenna()


from .. import state
HW = state.hardware
CB = state.crossbar


# Update history function
def updateHistory(w, b, m, a, pw, tag, Vread=None):
    if Vread is None:
        Vread = HW.conf.Vread
    readTag = 'R'+str(HW.conf.readmode)
    if HW.conf.sessionmode == 1:
        res = m/2
    else:
        res = m

    CB.append(w, b, res, a, pw, tag, readTag, Vread)

    CB.word = w
    CB.bit = b
    cbAntenna.recolor.emit(m,w,b)


def writeDelimitedData(data, dest, delimiter="\t"):
    try:
        f = open(dest, 'w')
        for line in data:
            if isinstance(line, str) or (not isinstance(line, collections.Iterable)):
                line = [line]
            text = delimiter.join("{0:.5g}".format(x) for x in line)
            f.write(text+"\n")
        f.close()
    except Exception as exc:
        print("Error when writing delimited data:", exc)


def saveFuncToFilename(func, title="", parent=None):
    fname = QtWidgets.QFileDialog.getSaveFileName(parent, title)

    if fname:
        func(fname[0])


def gzipFileSize(fname):
    with open(fname, 'rb') as f:
        # gzip uncompressed file size is stored in the
        # last 4 bytes of the file. This will roll over
        # for files > 4 GB
        f.seek(-4,2)
        return struct.unpack('I', f.read(4))[0]

