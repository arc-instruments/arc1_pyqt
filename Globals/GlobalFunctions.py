####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################


from . import GlobalVars as g
from ._antennae import CBAntenna, DisplayUpdateAntenna, HistoryTreeAntenna
from ._antennae import InterfaceAntenna, SAantenna, HoverAntenna, AddressAntenna
from PyQt5 import QtGui, QtWidgets, QtCore
import numpy as np
import collections
import struct
from VirtualArC import VirtualArC


# Signal emitters
cbAntenna = CBAntenna()
displayUpdate = DisplayUpdateAntenna()
historyTreeAntenna = HistoryTreeAntenna()
interfaceAntenna = InterfaceAntenna()
SAantenna = SAantenna()
hoverAntenna = HoverAntenna()
addressAntenna = AddressAntenna()


# Update history function
def updateHistory(w,b,m,a,pw,tag):
    readTag='R'+str(g.readOption)
    if g.sessionMode==1:
        g.Mnow=m/2
    else:
        g.Mnow=m
    g.Mhistory[w][b].append([g.Mnow,a,pw,tag,readTag,g.Vread])

    g.w=w
    g.b=b
    cbAntenna.recolor.emit(m,w,b)


def updateHistory_CT(w,b,m,a,pw,tag):
    readTag='R2'

    if g.sessionMode==1:
        g.Mnow=m/2
    else:
        g.Mnow=m

    g.Mhistory[w][b].append([g.Mnow,a,pw,tag,readTag,a])

    g.w=w
    g.b=b
    cbAntenna.recolor.emit(m,w,b)


def updateHistory_short(m,a,pw,tag):
    readTag='R'+str(g.readOption)
    if g.sessionMode==1:
        g.Mnow=m/2
    else:
        g.Mnow=m
    g.Mhistory[g.w][g.b].append([g.Mnow,a,pw,tag,readTag, g.Vread])
    cbAntenna.recolor.emit(m,g.w,g.b)


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


def getFloats(n):
    if not isinstance(g.ser, VirtualArC):
        while g.ser.inWaiting()<n*4:
            pass
        # read n * 4 bits of data (n floats) from the input serial
        values=g.ser.read(size=n*4)
        buf = memoryview(values)
        extracted=np.frombuffer(buf, dtype=np.float32)
    else:
        extracted = g.ser.read(n)
    # returns a list of these floats
    return extracted
