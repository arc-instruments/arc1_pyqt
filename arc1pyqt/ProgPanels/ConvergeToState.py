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

from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial
import sys
import os
import time
import numpy as np
import pyqtgraph

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts, styles
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag

from arc1pyqt.GeneratedUiElements.convergeToState import Ui_CTSParent


tag = "CTS"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList, params = {}):
        super().__init__()
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
        HW.ArC.write_b(str(21) + "\n") # job number, converge to state

        p = self.params # shorthand; `self.params` is too long!

        self.log("Sending ConvergeToState params")
        HW.ArC.write_b("%.3e\n" % p["vmin"])
        HW.ArC.write_b("%.3e\n" % p["vstep"])
        HW.ArC.write_b("%.3e\n" % p["vmax"])
        HW.ArC.write_b("%.3e\n" % p["pwmin"])
        HW.ArC.write_b("%.3e\n" % p["pwstep"])
        HW.ArC.write_b("%.3e\n" % p["pwmax"])
        HW.ArC.write_b("%.3e\n" % p["interpulse"])
        HW.ArC.write_b("%.3e\n" % p["res_target"])
        HW.ArC.write_b("%.3e\n" % p["res_target_tolerance"])
        HW.ArC.write_b("%.3e\n" % p["res_initial_tolerance"])

        HW.ArC.write_b("%d\n" % p["pulses"])
        HW.ArC.write_b("%d\n" % p["init_pol"])
        HW.ArC.write_b(str(len(self.deviceList)) + "\n")

    @BaseThreadWrapper.runner
    def run(self):

        self.DBG = bool(os.environ.get('CTSDBG', False))

        self.sendParams()

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)
            self.convergeToState(w, b)
            self.updateTree.emit(w, b)

        self.log("ConvergeToState finished")

    def convergeToState(self, w, b):

        self.log("Running ConvergeToState on (W=%d, B=%d)" % (w, b))
        HW.ArC.queue_select(w, b)

        # Read the first batch of values
        global tag
        end = False
        buf = np.zeros(3)
        curValues = list(HW.ArC.read_floats(3))
        self.log(curValues)
        buf[0] = curValues[0]
        buf[1] = curValues[1]
        buf[2] = curValues[2]
        aTag = tag + "_s"

        # Repeat while an end tag is not encountered
        while(not end):
            curValues = list(HW.ArC.read_floats(3))
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


class ConvergeToState(Ui_CTSParent, BaseProgPanel):

    PROGRAM_ONE = 0x1
    PROGRAM_RANGE = 0x2
    PROGRAM_ALL = 0x3

    def __init__(self, short=False):
        Ui_CTSParent.__init__(self)
        BaseProgPanel.__init__(self, title="ConvergeToState",
                description="Applies alt. polarity voltage ramps to "
                "stabilise device into a specific resistive range",
                short=short)

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(styles.btnStyle)
        self.applyOneButton.setStyleSheet(styles.btnStyle)
        self.applyRangeButton.setStyleSheet(styles.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        # initial polarity combo
        for (k, v) in [("Positive", 1), ("Negative", -1)]:
            self.polarityCombo.addItem(k, v)

        self.applyValidators()

        if not self.short:
            self.applyOneButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_ONE))
            self.applyAllButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_ALL))
            self.applyRangeButton.clicked.connect(partial(self.programDevs, \
                    self.PROGRAM_RANGE))
        else:
            for wdg in [self.applyOneButton, self.applyAllButton, \
                    self.applyRangeButton]:
                wdg.hide()

        self.registerPropertyWidget(self.resTargetEdit, "res_target")
        self.registerPropertyWidget(self.targetToleranceEdit, "res_target_tolerance")
        self.registerPropertyWidget(self.initialToleranceEdit, "res_initial_tolerance")
        self.registerPropertyWidget(self.interpulseEdit, "interpulse")
        self.registerPropertyWidget(self.pulsesEdit, "pulses")
        self.registerPropertyWidget(self.voltMinEdit, "vmin")
        self.registerPropertyWidget(self.voltStepEdit, "vstep")
        self.registerPropertyWidget(self.voltMaxEdit, "vmax")
        self.registerPropertyWidget(self.pwMinEdit, "pwmin")
        self.registerPropertyWidget(self.pwStepEdit, "pwstep")
        self.registerPropertyWidget(self.pwMaxEdit, "pwmax")

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

    def programOne(self):
        self.programDevs(self.PROGRAM_ONE)

    def programRange(self):
        self.programDevs(self.PROGRAM_RANGE)

    def programAll(self):
        self.programDevs(self.PROGRAM_ALL)

    def programDevs(self, programType):

        if programType == self.PROGRAM_ONE:
            devs = [[CB.word, CB.bit]]
        else:
            if programType == self.PROGRAM_RANGE:
                devs = makeDeviceList(True)
            else:
                devs = makeDeviceList(False)

        allData = self.gatherData()

        wrapper = ThreadWrapper(devs, allData)
        self.execute(wrapper, wrapper.run)

    def disableProgPanel(self, state):
        self.hboxProg.setEnabled(not state)


tags = { 'top': ModTag(tag, "ConvergeToState", None) }
