# -*- coding: utf-8 -*-
####################################

# (c) Spyros Stathopoulos
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
from functools import partial
import sys
import os
import time
import numpy
import scipy.stats as stat

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/generated_/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

from mss import Ui_MSSParent

tag="MSS"
g.tagDict.update({tag:"MultiStateSeeker*"})

class ThreadWrapper(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    sendData = QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight = QtCore.pyqtSignal(int,int)
    displayData = QtCore.pyqtSignal()
    updateTree = QtCore.pyqtSignal(int, int)
    disableInterface = QtCore.pyqtSignal(bool)
    getDevices = QtCore.pyqtSignal(int)

    def __init__(self, deviceList, params = {}):
        super(ThreadWrapper, self).__init__()
        self.deviceList = deviceList
        self.params = params

    def initialisePhase1(self, w, b):

        numDevices = int(len(self.deviceList))

        g.ser.write(str(161) + "\n")

        data = self.params

        g.ser.write(str(data["pulse_duration"])+"\n")
        g.ser.write(str(data["vmin"])+"\n")
        g.ser.write(str(data["vstep"])+"\n")
        g.ser.write(str(data["vmax"])+"\n")
        g.ser.write(str(data["interpulse"])+"\n")

        g.ser.write(str(data["trailer_reads"])+"\n")
        g.ser.write(str(data["prog_pulses"])+"\n")
        g.ser.write(str(data["tolerance_band"])+"\n")
        g.ser.write(str(data["read_write"])+"\n")

        g.ser.write(str(numDevices)+"\n")

        g.ser.write(str(w)+"\n")
        g.ser.write(str(b)+"\n")

    def phase1(self, w, b):

        self.initialisePhase1(w, b)

        global tag
        tag_ = "%s1"%(tag)

        values = []
        firstPoint = True

        while True:
            newValues = []
            newValues.append(float(g.ser.readline().rstrip()))
            newValues.append(float(g.ser.readline().rstrip()))
            newValues.append(float(g.ser.readline().rstrip()))

            if not values:
                values = newValues
                if not values[2] < 0:
                    continue

            if(newValues[2] < 0):
                status = int(g.ser.readline().rstrip())
                self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_e")
                self.displayData.emit()
                if status == 0: # all OK, read the results, if any
                    ints = int(g.ser.readline().rstrip()) # expecting 1 int
                    floats = int(g.ser.readline().rstrip()) # expecting 0 floats
                    sign = int(g.ser.readline().rstrip())
                    return sign
                return None # failed!
            else:
                if firstPoint:
                    self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_s")
                    firstPoint = False
                else:
                    self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_i")
                self.displayData.emit()

            values = newValues

        return None

    def initialisePhase2(self, w, b, sign = 1):
        numDevices = int(len(self.deviceList))

        print(self.params)
        g.ser.write(str(162) + "\n")

        data = self.params
        stateMode = data["state_mode"]
        voltage = float(data["stability_voltage"] * sign * stateMode)

        g.ser.write(str(voltage) + "\n")
        g.ser.write(str(data["stability_pw"]) + "\n")
        
        g.ser.write(str(numDevices)+"\n")

        g.ser.write(str(w)+"\n")
        g.ser.write(str(b)+"\n")

    def phase2(self, w, b, sign = 1):

        self.initialisePhase2(w, b, sign)

        global tag
        tag_ = "%s2"%(tag)

        firstPoint = True
        lastPoint = False
        t0 = time.time()
        pulsedVoltage = float(self.params["stability_voltage"] * sign * self.params["state_mode"])
        test = self.params["stability_mode"]
        min_tan = numpy.tan((self.params["stability_slope"] / 100.0) * (numpy.pi/2.0))
        tmetric = self.params["stability_tmetric"]

        window = []

        result = False

        while True:
            currentR = float(g.ser.readline().rstrip())
            numPoints = len(window)

            if numPoints < 50: # accumulate at least 50 points before starting to count
                t0 = time.time()

            if (time.time() - t0 > self.params["stability_tmax"]):
                lastPoint = True

            # Roll the window if more than 100 points (these should be enough)
            if numPoints < 100:
                window.append(currentR)
            else:
                window = numpy.roll(window, -1)
                window[-1] = currentR

            if test == "linear" and numPoints > 25:
                slope = abs(numpy.polyfit(numpy.arange(len(window)), window, 1)[0])
                print(slope)
                if slope <= min_tan:
                    lastPoint = True # done!
                    result = True
            elif test == "ttest" and numPoints > 50:
                tmet = abs(stat.ttest_ind(window[:int(numPoints/2)], window[-int(numPoints/2):], equal_var = False)[0])
                print("%f vs %f" % (tmet, tmetric))
                if tmet <= tmetric:
                    lastPoint = True # done!
                    result = True

            if firstPoint:
                suffix = "_s"
                firstPoint = False
            elif lastPoint:
                suffix = "_e"
            else:
                suffix = "_i"

            self.sendData.emit(w, b, currentR, pulsedVoltage, 0, tag_ + suffix)
            self.displayData.emit()

            if lastPoint:
                g.ser.write(str(1) + "\n")
                break
            else:
                g.ser.write(str(0) + "\n")

        return result

    def initialisePhase3(self, w, b, sign = 1):
        numDevices = int(len(self.deviceList))

        data = self.params
        print(data)

        g.ser.write(str(163) + "\n")

        g.ser.write(str(data["state_reads"]) + "\n")
        g.ser.write(str(data["state_prog_pulses"]) + "\n")
        g.ser.write(str(data["state_stdev"]) + "\n")

        # WARNING!!! Need to account for sign and state direction
        g.ser.write(str(data["state_pulse_duration"]) + "\n")
        g.ser.write(str(-sign * data["state_vmin"]) + "\n")
        g.ser.write(str(-sign * data["state_vstep"]) + "\n")
        g.ser.write(str(-sign * data["state_vmax"]) + "\n")
        g.ser.write(str(data["state_interpulse"]) + "\n")
        g.ser.write(str(data["state_retention"]) + "\n")

        g.ser.write(str(numDevices)+"\n")

        g.ser.write(str(w)+"\n")
        g.ser.write(str(b)+"\n")

    def phase3(self, w, b, sign = 1):
        self.initialisePhase3(w, b, sign)

        global tag
        tag_ = "%s3"%(tag)

        values = []
        firstPoint = True
        states = []

        while True:
            newValues = []
            newValues.append(float(g.ser.readline().rstrip()))
            newValues.append(float(g.ser.readline().rstrip()))
            newValues.append(float(g.ser.readline().rstrip()))

            if not values:
                values = newValues
                if not values[2] < 0:
                    continue

            if(newValues[2] < 0):
                status = int(g.ser.readline().rstrip())
                self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_e")
                self.displayData.emit()
                if status == 0: # all OK, read the results, if any
                    g.ser.readline().rstrip() # expecting 0 int (discard them)
                    g.ser.readline().rstrip() # expecting 0 floats (discard them)
                    # nothing is returned
                else:
                    print("Phase 3 failed with exit code: %d", status)
                return
            elif(newValues[0] < 0): # we have a state
                state = float(g.ser.readline().rstrip())
                lbound = float(g.ser.readline().rstrip())
                ubound = float(g.ser.readline().rstrip())
                self.sendData.emit(w, b, state, lbound, ubound, tag_+"_STATE")
                self.displayData.emit()
                states.append([state, lbound, ubound])
            else:
                if firstPoint:
                    self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_s")
                    firstPoint = False
                else:
                    self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_i")
                self.displayData.emit()

            values = newValues

        return states

    def run(self):

        self.disableInterface.emit(True)

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)

            sign = self.phase1(w, b)
            if sign == None: # failed, continue to next
                print("Cannot infer polarity for %d x %d" % (int(w), int(b)))
                #continue

            # print("Polarity for %d x %d: %d" % (int(w), int(b), sign))
            # self.initialisePhase2(sign)
            # g.ser.write(str(int(len(self.deviceList)))+"\n")
            stable = self.phase2(w, b, sign)

            if not stable:
                continue

            resStates = self.phase3(w, b, sign)

            print(resStates)

        self.disableInterface.emit(False)
        
        self.finished.emit()

class MultiStateSeeker(Ui_MSSParent, QtGui.QWidget):

    PROGRAM_ONE = 0x1;
    PROGRAM_RANGE = 0x2;
    PROGRAM_ALL = 0x3;
    
    def __init__(self):
        super(MultiStateSeeker, self).__init__()
        
        self.setupUi(self)

        self.applyAllButton.setStyleSheet(s.btnStyle)
        self.applyOneButton.setStyleSheet(s.btnStyle)
        self.applyRangeButton.setStyleSheet(s.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        self.applyValidators()

        self.stateModeCombo.addItem(u"Low → High", 1)
        self.stateModeCombo.addItem(u"High → Low", -1)

        self.stabilityModeCombo.addItem("Linear fit", "linear")
        self.stabilityModeCombo.addItem("T-Test", "ttest")
        self.stabilityModeCombo.currentIndexChanged.connect(self.stabilityIndexChanged)

        self.stateRetentionMultiplierComboBox.addItem("ms", 1)
        self.stateRetentionMultiplierComboBox.addItem("s", 1000)

        self.applyOneButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ONE))
        self.applyAllButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ALL))
        self.applyRangeButton.clicked.connect(partial(self.programDevs, self.PROGRAM_RANGE))

    def applyValidators(self):
        floatValidator = QtGui.QDoubleValidator()
        intValidator = QtGui.QIntValidator()

        self.readsEdit.setValidator(intValidator)
        self.pulsesEdit.setValidator(intValidator)
        self.pulseWidthEdit.setValidator(floatValidator)
        self.vminEdit.setValidator(floatValidator)
        self.vstepEdit.setValidator(floatValidator)
        self.vmaxEdit.setValidator(floatValidator)
        self.tolbandEdit.setValidator(intValidator)
        self.interpulseEdit.setValidator(intValidator)

        self.stabilityVoltageEdit.setValidator(floatValidator)
        self.stabilitySlopeEdit.setValidator(floatValidator)
        self.tmetricEdit.setValidator(floatValidator)
        self.volatilityReadPWEdit.setValidator(floatValidator)
        self.maxStabilityTimeEdit.setValidator(floatValidator)

        self.stateReadsEdit.setValidator(intValidator)
        self.stateVminEdit.setValidator(floatValidator)
        self.stateVmaxEdit.setValidator(floatValidator)
        self.stateVstepEdit.setValidator(floatValidator)
        self.statePulseWidthEdit.setValidator(floatValidator)
        self.stateInterpulseEdit.setValidator(floatValidator)
        self.stateRetentionEdit.setValidator(floatValidator)
        self.statePulsesEdit.setValidator(intValidator)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width() - object.verticalScrollBar().width())
        return False

    def gatherData(self):
        result = {}

        result["trailer_reads"] = int(self.readsEdit.text())
        result["prog_pulses"] = int(self.pulsesEdit.text())
        result["pulse_duration"] = float(self.pulseWidthEdit.text()) / 1000.0
        result["vmin"] = float(self.vminEdit.text())
        result["vstep"] = float(self.vstepEdit.text())
        result["vmax"] = float(self.vmaxEdit.text())
        result["tolerance_band"] = int(self.tolbandEdit.text())
        result["interpulse"] = float(self.interpulseEdit.text()) / 1000.0
        result["stability_voltage"] = float(self.stabilityVoltageEdit.text())
        result["read_write"] = int(self.readAfterPulseCheckBox.isChecked())
        result["stability_pw"] = float(self.volatilityReadPWEdit.text()) / 1000.0
        result["stability_tmax"] = float(self.maxStabilityTimeEdit.text())
        mode_index = self.stateModeCombo.currentIndex()
        stability_index = self.stabilityModeCombo.currentIndex()
        result["state_mode"] = self.stateModeCombo.itemData(mode_index).toInt()[0]
        result["stability_mode"] = self.stabilityModeCombo.itemData(stability_index).toString()
        result["stability_slope"] = float(self.stabilitySlopeEdit.text())
        result["stability_tmetric"] = float(self.tmetricEdit.text())

        result["state_reads"] = int(self.stateReadsEdit.text())
        result["state_prog_pulses"] = int(self.statePulsesEdit.text())
        result["state_vmin"] = float(self.stateVminEdit.text())
        result["state_vmax"] = float(self.stateVmaxEdit.text())
        result["state_vstep"] = float(self.stateVstepEdit.text())
        result["state_pulse_duration"] = float(self.statePulseWidthEdit.text()) / 1000.0
        result["state_interpulse"] = float(self.stateInterpulseEdit.text()) / 1000.0

        multiplier_index = self.stateRetentionMultiplierComboBox.currentIndex()
        retention_mult = self.stateRetentionMultiplierComboBox.itemData(multiplier_index).toFloat()[0]

        result["state_retention"] = (float(self.stateRetentionEdit.text()) * retention_mult) / 1000.0
        result["state_stdev"] = int(self.stateStdevSpinBox.value())

        return result

    def sendParams(self):
        data = self.gatherData()

        g.ser.write(str(data["pulse_duration"])+"\n")
        g.ser.write(str(data["vmin"])+"\n")
        g.ser.write(str(data["vstep"])+"\n")
        g.ser.write(str(data["vmax"])+"\n")
        g.ser.write(str(data["interpulse"])+"\n")

        g.ser.write(str(data["trailer_reads"])+"\n")
        g.ser.write(str(data["prog_pulses"])+"\n")
        g.ser.write(str(data["tolerance_band"])+"\n")
        g.ser.write(str(data["read_write"])+"\n")

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
        self.threadWrapper.highlight.connect(f.cbAntenna.cast)
        self.threadWrapper.displayData.connect(f.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

    def disableProgPanel(self,state):
        if state == True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

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

    def stabilityIndexChanged(self, index):
        self.stabilityCriterionStackedWidget.setCurrentIndex(index)
        self.stabilityCriterionLabelStackedWidget.setCurrentIndex(index)

def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = SwitchSeeker()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 
