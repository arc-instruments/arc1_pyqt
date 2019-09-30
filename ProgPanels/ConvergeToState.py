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
ConvergeToState attempts to attain a specific resistance for the select device
(or devices). This corresponds to job 21 in the uC firmware.

In a sense ConvergeToState is similar to FormFinder but it is not limited to a
specific low resistance. Instead it will try to "guess" the correct polarity by
observing the current resistance evolution trend. If source and target
resistance diverge the polarity will switch. This works well for bistable
devices but there is a chance to fall into a never-ending loop with unipolar
devices. To counter this problem the firmware counts the number of polarity
reversals which are registered as "failures". The algorithm will stop if a
number of failures is reached. Currently this is hardcoded to 5 but it will
probably change in the future.

User parameters
---------------
* Target R: Desired target resistance.
* Rt tolerance: Tolerance band for the target resistance, ie within what % the
state is considered "attained".
* Initial polarity: Desired polarity of the first pulse train. This serves as a
"hint" to the algorithm as otherwise the response of the device to certain bias
polarities is uknown. In conjuction with other modules (eg. SwitchSeeker) the
user can determine how the device responds to a given stimulus.
* Ro tolerance: This defines a tolerance band around the initial resistance.
While the device is within the region it will be considered as being in Ro.
Please note that Ro is defined again after each failure.
* PW min, step, max: As their FormFinder counterparts.
* Voltage min, step, max: As their FormFinder counterparts.
* Interpulse: Delay between two consecutive pulses
* Pulses: Number of pulses at each (V, PW) step.
"""

from __future__ import print_function
from PyQt5 import QtGui, QtCore, QtWidgets
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

from GeneratedUiElements.convergeToState import Ui_CTSParent


tag="CTS"
g.tagDict.update({tag:"Converge to State"})


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
        """ Write to stderr if CTSDBG is set"""

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

        self.log("Initiating ConvergeToState (job 21)")
        g.ser.write_b(str(21) + "\n") # job number, converge to state

        p = self.params # shorthand; `self.params` is too long!

        self.log("Sending ConvergeToState params")
        g.ser.write_b("%.3e\n" % p["vmin"])
        g.ser.write_b("%.3e\n" % p["vstep"])
        g.ser.write_b("%.3e\n" % p["vmax"])
        g.ser.write_b("%.3e\n" % p["pwmin"])
        g.ser.write_b("%.3e\n" % p["pwstep"])
        g.ser.write_b("%.3e\n" % p["pwmax"])
        g.ser.write_b("%.3e\n" % p["interpulse"])
        g.ser.write_b("%.3e\n" % p["res_target"])
        g.ser.write_b("%.3e\n" % p["res_target_tolerance"])
        g.ser.write_b("%.3e\n" % p["res_initial_tolerance"])

        g.ser.write_b("%d\n" % p["pulses"])
        g.ser.write_b("%d\n" % p["init_pol"])
        g.ser.write_b(str(len(self.deviceList)) + "\n")

    def run(self):

        self.DBG = bool(os.environ.get('CTSDBG', False))

        self.disableInterface.emit(True)

        self.sendParams()

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)
            self.convergeToState(w, b)
            self.updateTree.emit(w, b)

        self.disableInterface.emit(False)

        self.finished.emit()
        self.log("ConvergeToState finished")

    def convergeToState(self, w, b):

        self.log("Running ConvergeToState on (W=%d, B=%d)" % (w, b))
        g.ser.write_b("%d\n" % int(w)) # word line
        g.ser.write_b("%d\n" % int(b)) # bit line

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
                self.log("ConvergeToState on (W=%d, B=%d) finishing..." % (w, b))
                end = True
                aTag = tag + "_e"

            self.sendData.emit(w, b, buf[0], buf[1], buf[2], aTag)
            self.displayData.emit()
            aTag = tag + "_i"

            buf[0] = curValues[0]
            buf[1] = curValues[1]
            buf[2] = curValues[2]

        self.log("ConvergeToState on (W=%d, B=%d) finished..." % (w, b))


class ConvergeToState(Ui_CTSParent, QtWidgets.QWidget):

    PROGRAM_ONE = 0x1;
    PROGRAM_RANGE = 0x2;
    PROGRAM_ALL = 0x3;

    def __init__(self, short=False):
        super(ConvergeToState, self).__init__()
        self.short = short
        self.thread = None
        self.threadWrapper = None

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(s.btnStyle)
        self.applyOneButton.setStyleSheet(s.btnStyle)
        self.applyRangeButton.setStyleSheet(s.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        # initial polarity combo
        for (k, v) in [("Positive", 1), ("Negative", -1)]:
            self.polarityCombo.addItem(k, v)

        self.applyValidators()

        self.applyOneButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ONE))
        self.applyAllButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ALL))
        self.applyRangeButton.clicked.connect(partial(self.programDevs, self.PROGRAM_RANGE))

    def applyValidators(self):
        floatValidator = QtGui.QDoubleValidator()
        intValidator = QtGui.QIntValidator()

        self.pulsesEdit.setValidator(intValidator)
        self.resTargetEdit.setValidator(floatValidator)
        self.targetToleranceEdit.setValidator(floatValidator)
        self.pwMinEdit.setValidator(floatValidator)
        self.pwStepEdit.setValidator(floatValidator)
        self.pwMaxEdit.setValidator(floatValidator)
        self.voltMinEdit.setValidator(floatValidator)
        self.voltStepEdit.setValidator(floatValidator)
        self.voltMaxEdit.setValidator(floatValidator)
        self.interpulseEdit.setValidator(floatValidator)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width() - object.verticalScrollBar().width())
        return False

    def gatherData(self):
        result = {}

        result["res_target"] = float(self.resTargetEdit.text())
        result["res_target_tolerance"] = float(self.targetToleranceEdit.text())
        result["res_initial_tolerance"] = float(self.initialToleranceEdit.text())
        result["interpulse"] = float(self.interpulseEdit.text())/1000.0
        result["pulses"] = int(self.pulsesEdit.text())
        result["vmin"] = float(self.voltMinEdit.text())
        result["vstep"] = float(self.voltStepEdit.text())
        result["vmax"] = float(self.voltMaxEdit.text())
        result["pwmin"] = float(self.pwMinEdit.text())/1000.0
        result["pwstep"] = float(self.pwStepEdit.text())
        result["pwmax"] = float(self.pwMaxEdit.text())/1000.0

        idx = self.polarityCombo.currentIndex()
        result["init_pol"] = int(self.polarityCombo.itemData(idx))

        return result

    def programDevs(self, programType):

        if programType == self.PROGRAM_ONE:
            devs = [[g.w, g.b]]
        else:
            if programType == self.PROGRAM_RANGE:
                devs = self.makeDeviceList(True)
            else:
                devs = self.makeDeviceList(False)

        allData = self.gatherData()

        self.thread = QtCore.QThread()
        self.threadWrapper = ThreadWrapper(devs, allData)

        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapperFinished)
        self.thread.finished.connect(self.threadFinished)
        self.threadWrapper.sendData.connect(f.updateHistory)
        self.threadWrapper.highlight.connect(f.cbAntenna.cast)
        self.threadWrapper.displayData.connect(f.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.cast)
        self.thread.finished.connect(f.interfaceAntenna.wakeUp)

        self.thread.start()

    def threadFinished(self):
        self.thread.wait()
        self.thread = None

    def threadWrapperFinished(self):
        self.threadWrapper = None

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

