# -*- coding: utf-8 -*-
####################################
#
# (c) Spyros Stathopoulos
# ArC Instruments Ltd.
#
# This code is licensed under GNU v3 license (see LICENSE.txt for details)
#
####################################
"""
Brief description
-----------------
ChronoAmperometry monitors the resistance of the device under bias. The
resistance of the device is logged while it is under a specific bias.

User parameters
---------------
* Bias: The applied bias.
* Pulse width: The duration of the bias in ms.
* Number of reads: The number of read "checkpoints". The first read is *always*
at the start as the voltage is applied and the last just before bias is
cut off.
"""

from __future__ import print_function
from PyQt4 import QtGui, QtCore
from functools import partial
import sys
import os
import time
import numpy as np
import pyqtgraph

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

from GeneratedUiElements.chronoamperometry import Ui_ChronoAmpParent


tag="CRA"
g.tagDict.update({tag:"ChronoAmperometry"})


class ThreadWrapper(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    sendData = QtCore.pyqtSignal(int, int, float, float, float, str)
    sendDataCT = QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight = QtCore.pyqtSignal(int,int)
    displayData = QtCore.pyqtSignal()
    updateTree = QtCore.pyqtSignal(int, int)
    disableInterface = QtCore.pyqtSignal(bool)
    getDevices = QtCore.pyqtSignal(int)

    def __init__(self, deviceList, params = {}):
        super(ThreadWrapper, self).__init__()
        self.deviceList = deviceList
        self.params = params
        self.DBG = False

    def log(self, *args, **kwargs):
        """ Write to stderr if CRADBG is set"""

        if self.DBG:
            print(*args, file=sys.stderr, **kwargs)

    def isEndTag(self, val):
        """
        Check for three consecutives 0.0, which indicate that the process
        has finished
        """

        try:
            for v in val:
                # this works because there is no way we are having
                # < 1 Ohm resistance; at least one of the values will
                # be <> 0 unless it's a program termination signal
                if int(v) != 0:
                    self.log("end-tag-assess: Found a non-zero val: %f" % v)
                    return False
        except:
            return False

        return True

    def sendParams(self):
        """ Transfer the parameters to ArC ONE """

        self.log("Initiating ChronoAmperometry (job 220)")
        g.ser.write(str(220) + "\n")

        p = self.params # shorthand; `self.params` is too long!

        self.log("Sending ChronoAmperometry params:", p)
        g.ser.write("%.3e\n" % p["bias"])
        g.ser.write("%.3e\n" % p["pw"])
        g.ser.write("%d\n" % p["num_reads"])
        g.ser.write(str(len(self.deviceList)) + "\n")
        self.log("Parameters written")

    def run(self):

        self.DBG = bool(os.environ.get('CRADBG', False))

        self.disableInterface.emit(True)

        self.sendParams()

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)
            self.chronoamperometry(w, b)
            self.updateTree.emit(w, b)

        self.disableInterface.emit(False)

        self.finished.emit()
        self.log("ChronoAmperometry finished")

    def chronoamperometry(self, w, b):

        self.log("Running ChronoAmperometry on (W=%d, B=%d)" % (w, b))
        g.ser.write("%d\n" % int(w)) # word line
        g.ser.write("%d\n" % int(b)) # bit line

        # Read the first batch of values
        global tag
        end = False
        buf = np.zeros(3)
        curValues = list(f.getFloats(3))
        self.log(curValues)
        buf[0] = curValues[0]
        buf[1] = curValues[1]
        buf[2] = curValues[2]
        aTag = tag + "_s"

        # Repeat while an end tag is not encountered
        while(not end):
            curValues = list(f.getFloats(3))
            self.log(curValues)

            if (self.isEndTag(curValues)):
                self.log("ChronoAmperometry on (W=%d, B=%d) finishing..." % (w, b))
                end = True
                aTag = tag + "_e"

            self.sendData.emit(w, b, buf[0], buf[1], buf[2]/1e6, aTag)
            self.displayData.emit()
            aTag = tag + "_i"

            buf[0] = curValues[0]
            buf[1] = curValues[1]
            buf[2] = curValues[2]

        self.log("ChronoAmperometry on (W=%d, B=%d) finished..." % (w, b))


class ChronoAmperometry(Ui_ChronoAmpParent, QtGui.QWidget):

    PROGRAM_ONE = 0x1;
    PROGRAM_RANGE = 0x2;
    PROGRAM_ALL = 0x3;

    def __init__(self, short=False):
        super(ChronoAmperometry, self).__init__()
        self.short = short

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(s.btnStyle)
        self.applyOneButton.setStyleSheet(s.btnStyle)
        self.applyRangeButton.setStyleSheet(s.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        self.applyValidators()

        self.applyOneButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ONE))
        self.applyAllButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ALL))
        self.applyRangeButton.clicked.connect(partial(self.programDevs, self.PROGRAM_RANGE))

    def applyValidators(self):
        floatValidator = QtGui.QDoubleValidator()
        intValidator = QtGui.QIntValidator()

        self.biasEdit.setValidator(floatValidator)
        self.pwEdit.setValidator(floatValidator)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width() - object.verticalScrollBar().width())
        return False

    def gatherData(self):
        result = {}

        result["bias"] = float(self.biasEdit.text())
        result["pw"] = float(self.pwEdit.text())/1000.0
        result["num_reads"] = int(self.numReadsBox.value())

        return result

    def programDevs(self, programType):

        self.thread=QtCore.QThread()

        if programType == self.PROGRAM_ONE:
            devs = [[g.w, g.b]]
        else:
            if programType == self.PROGRAM_RANGE:
                devs = self.makeDeviceList(True)
            else:
                devs = self.makeDeviceList(False)

        allData = self.gatherData()

        self.threadWrapper = ThreadWrapper(devs, allData)

        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.sendData.connect(f.updateHistory)
        self.threadWrapper.sendDataCT.connect(f.updateHistory_CT)
        self.threadWrapper.highlight.connect(f.cbAntenna.cast)
        self.threadWrapper.displayData.connect(f.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

    def disableProgPanel(self, state):
        self.hboxProg.setEnabled(not state)

    def makeDeviceList(self,isRange):
        rangeDev = []
        if isRange == False:
            minW = 1
            maxW = g.wline_nr
            minB = 1
            maxB = g.bline_nr
        else:
            minW = g.minW
            maxW = g.maxW
            minB = g.minB
            maxB = g.maxB

        # Find how many SA devices are contained in the range
        if g.checkSA == False:
            for w in range(minW, maxW + 1):
                for b in range(minB, maxB + 1):
                    rangeDev.append([w, b])
        else:
            for w in range(minW, maxW + 1):
                for b in range(minB, maxB + 1):
                    for cell in g.customArray:
                        if (cell[0] == w and cell[1] == b):
                            rangeDev.append(cell)

        return rangeDev

