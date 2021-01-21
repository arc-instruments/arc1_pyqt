####################################

# (c) Spyros Stathopoulos
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial
import sys
import os
import time
import numpy
import scipy.stats as stat
import pyqtgraph

from arc1pyqt import Graphics
from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.GeneratedUiElements.mss import Ui_MSSParent
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag
from arc1pyqt.Globals import fonts, styles, functions


tag="MSS"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList, params = {}):
        super().__init__()
        self.deviceList = deviceList
        self.params = params

    def initialisePhase1(self, w, b):

        numDevices = int(len(self.deviceList))

        HW.ArC.write_b(str(161) + "\n")

        data = self.params

        HW.ArC.write_b(str(data["pulse_duration"])+"\n")
        HW.ArC.write_b(str(data["vmin"])+"\n")
        HW.ArC.write_b(str(data["vstep"])+"\n")
        HW.ArC.write_b(str(data["vmax"])+"\n")
        HW.ArC.write_b(str(data["interpulse"])+"\n")

        HW.ArC.write_b(str(data["trailer_reads"])+"\n")
        HW.ArC.write_b(str(data["prog_pulses"])+"\n")
        HW.ArC.write_b(str(data["tolerance_band"])+"\n")
        HW.ArC.write_b(str(data["read_write"])+"\n")

        HW.ArC.write_b(str(numDevices)+"\n")

        HW.ArC.queue_select(w, b)

    def phase1(self, w, b):

        self.initialisePhase1(w, b)

        global tag
        tag_ = "%s1"%(tag)

        values = []
        firstPoint = True

        while True:
            newValues = list(HW.ArC.read_floats(3))

            if not values:
                values = newValues
                if not values[2] < 0:
                    continue

            if(newValues[2] < 0):
                status = int(HW.ArC.readline().rstrip())
                self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_e")
                self.displayData.emit()

                # all OK, read the results, if any
                if status == 0:
                    ints = int(HW.ArC.readline().rstrip())   # expecting 1 int
                    floats = int(HW.ArC.readline().rstrip()) # expecting 0 floats
                    sign = int(HW.ArC.readline().rstrip())
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

        HW.ArC.write_b(str(162) + "\n")

        data = self.params
        stateMode = data["state_mode"]
        if data["single_phase_run"]: # always use the values supplied by user
            sign = 1
            stateMode = 1
        voltage = float(data["stability_voltage"] * sign * stateMode)

        HW.ArC.write_b(str(voltage) + "\n")
        HW.ArC.write_b(str(data["stability_pw"]) + "\n")

        HW.ArC.write_b(str(numDevices)+"\n")

        HW.ArC.write_b(str(w)+"\n")
        HW.ArC.write_b(str(b)+"\n")

    def phase2(self, w, b, sign = 1):

        self.initialisePhase2(w, b, sign)

        global tag
        tag_ = "%s2"%(tag)

        firstPoint = True
        lastPoint = False
        t0 = time.time()
        pulsedVoltage = float(self.params["stability_voltage"] * sign * self.params["state_mode"])
        pulsedPW = float(self.params["stability_pw"])
        test = self.params["stability_mode"]
        min_tan = numpy.tan((self.params["stability_slope"] / 100.0) * (numpy.pi/2.0))
        tmetric = self.params["stability_tmetric"]

        window = []

        result = False

        while True:
            #currentR = float(HW.ArC.readline().rstrip())
            currentR = float(HW.ArC.read_floats(1)[0])
            numPoints = len(window)

            # accumulate at least 50 points before starting to count
            if numPoints < 50:
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
                # print(slope)
                if slope <= min_tan:
                    lastPoint = True # done!
                    result = True
            elif test == "ttest" and numPoints > 50:
                tmet = abs(stat.ttest_ind(window[:int(numPoints/2)], window[-int(numPoints/2):], equal_var = False)[0])
                # print("%f vs %f" % (tmet, tmetric))
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

            self.sendData.emit(w, b, currentR, pulsedVoltage, pulsedPW, tag_ + suffix)
            self.displayData.emit()

            if lastPoint:
                HW.ArC.write_b(str(1) + "\n")
                break
            else:
                HW.ArC.write_b(str(0) + "\n")

        return result

    def initialisePhase3(self, w, b, sign = 1):
        numDevices = int(len(self.deviceList))

        data = self.params

        if str(data["assess_mode"]) == "voltage":
            HW.ArC.write_b(str(163) + "\n")

            HW.ArC.write_b(str(data["state_reads"]) + "\n")
            HW.ArC.write_b(str(data["state_prog_pulses"]) + "\n")
            HW.ArC.write_b(str(data["state_stdev"]) + "\n")
            HW.ArC.write_b(str(data["state_monotonic"]) + "\n")
            HW.ArC.write_b(str(data["state_counter_reset"]) + "\n")

            HW.ArC.write_b(str(data["state_pulse_duration"]) + "\n")
            HW.ArC.write_b(str(-sign * data["state_mode"] * data["state_vmin"]) + "\n")
            HW.ArC.write_b(str(-sign * data["state_mode"] * data["state_vstep"]) + "\n")
            HW.ArC.write_b(str(-sign * data["state_vmax"]) + "\n")
            HW.ArC.write_b(str(data["state_interpulse"]) + "\n")
            HW.ArC.write_b(str(data["state_retention"]) + "\n")
        elif str(data["assess_mode"]) == "pulse":
            HW.ArC.write_b(str(164) + "\n")

            HW.ArC.write_b(str(data["state_reads"]) + "\n")
            HW.ArC.write_b(str(data["state_prog_pulses"]) + "\n")
            HW.ArC.write_b(str(data["state_stdev"]) + "\n")
            HW.ArC.write_b(str(data["state_monotonic"]) + "\n")
            HW.ArC.write_b(str(data["state_counter_reset"]) + "\n")

            HW.ArC.write_b(str(data["state_pwmin"]) + "\n")
            HW.ArC.write_b(str(-sign * data["state_mode"] * data["state_voltage"]) + "\n")
            HW.ArC.write_b(str(data["state_pwstep"]) + "\n")
            HW.ArC.write_b(str(data["state_pwmax"]) + "\n")
            HW.ArC.write_b(str(data["state_interpulse"]) + "\n")
            HW.ArC.write_b(str(data["state_retention"]) + "\n")
        elif str(data["assess_mode"]) == "program":
            HW.ArC.write_b(str(165) + "\n")

            HW.ArC.write_b(str(data["state_reads"]) + "\n")
            HW.ArC.write_b(str(data["state_prog_pulses_min"]) + "\n")
            HW.ArC.write_b(str(data["state_prog_pulses_step"]) + "\n")
            HW.ArC.write_b(str(data["state_prog_pulses_max"]) + "\n")
            HW.ArC.write_b(str(data["state_stdev"]) + "\n")
            HW.ArC.write_b(str(data["state_monotonic"]) + "\n")
            HW.ArC.write_b(str(data["state_counter_reset"]) + "\n")

            HW.ArC.write_b(str(data["state_pulse_duration"]) + "\n")
            HW.ArC.write_b(str(-sign * data["state_mode"] * data["state_vmin"]) + "\n")
            HW.ArC.write_b(str(data["state_interpulse"]) + "\n")
            HW.ArC.write_b(str(data["state_retention"]) + "\n")
        else:
            raise Exception("Unknown state assessment mode")

        HW.ArC.write_b(str(numDevices)+"\n")

        HW.ArC.write_b(str(w)+"\n")
        HW.ArC.write_b(str(b)+"\n")

    def phase3(self, w, b, sign = 1):
        self.initialisePhase3(w, b, sign)

        global tag
        tag_ = "%s3"%(tag)

        values = []
        firstPoint = True
        states = []

        while True:
            # newValues = []
            # newValues.append(float(HW.ArC.readline().rstrip()))
            # newValues.append(float(HW.ArC.readline().rstrip()))
            # newValues.append(float(HW.ArC.readline().rstrip()))
            newValues = list(HW.ArC.read_floats(3))

            if not values:
                values = newValues
                if not values[2] < 0:
                    continue

            if(newValues[2] < 0):
                status = int(HW.ArC.readline().rstrip())
                self.sendData.emit(w, b, values[0], values[1], values[2], tag_+"_e")
                self.displayData.emit()

                # all OK, read the results, if any
                if status == 0:
                    HW.ArC.readline().rstrip() # expecting 0 int (discard them)
                    HW.ArC.readline().rstrip() # expecting 0 floats (discard them)
                    # nothing is returned
                else:
                    print("Phase 3 failed with exit code: %d", status)
                return states
            elif(newValues[0] < 0): # we have a state
                [state, lbound, ubound] = list(HW.ArC.read_floats(3))
                self.sendData.emit(w, b, values[0], values[1], 0, tag_ + "_STATE_%g_%g_%g"%(state, lbound, ubound))
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

    @BaseThreadWrapper.runner
    def run(self):

        DBG = bool(os.environ.get('MSSDBG', False))

        singlePhaseRun = self.params["single_phase_run"]
        singlePhase = self.params["single_phase_run_phase"]

        for device in self.deviceList:
            w = device[0]
            b = device[1]
            self.highlight.emit(w, b)

            if singlePhaseRun and singlePhase != 1:
                sign = 1 # use default sign if we are running a single phase

            if (not singlePhaseRun) or (singlePhase == 1):
                print("### Runnning MultiStateSeeker Phase I")
                sign = self.phase1(w, b)
                if sign == None: # failed, continue to next
                    print("Cannot infer polarity for %d x %d" % (int(w), int(b)))
                    if DBG:
                        print("...but continuing this run anyway...")
                        sign = -1
                    else:
                        self.updateTree.emit(w, b)
                        continue

            self.updateTree.emit(w, b)

            if (not singlePhaseRun) or (singlePhase == 2):
                print("### Runnning MultiStateSeeker Phase II")
                stable = self.phase2(w, b, sign)

                if (not stable) and (not DBG):
                    self.updateTree.emit(w, b)
                    continue

            self.updateTree.emit(w, b)

            if (not singlePhaseRun) or (singlePhase == 3):
                print("### Runnning MultiStateSeeker Phase III")
                resStates = self.phase3(w, b, sign)

                print("Resistive states:", resStates)

            self.updateTree.emit(w, b)

        print("### MultiStateSeeker finished!")


class MultiStateSeeker(Ui_MSSParent, BaseProgPanel):

    PROGRAM_ONE = 0x1
    PROGRAM_RANGE = 0x2
    PROGRAM_ALL = 0x3

    def __init__(self, short=False):
        Ui_MSSParent.__init__(self)
        BaseProgPanel.__init__(self, title="MultiStateSeeker", \
                description="Assess multiple bit storage capabilities", \
                short=short)

        self.setupUi(self)

        self.applyAllButton.setStyleSheet(styles.btnStyle)
        self.applyOneButton.setStyleSheet(styles.btnStyle)
        self.applyRangeButton.setStyleSheet(styles.btnStyle)
        self.titleLabel.setFont(fonts.font1)
        self.descriptionLabel.setFont(fonts.font3)

        self.applyValidators()

        self.stateModeCombo.addItem(u"As calculated", 1)
        self.stateModeCombo.addItem(u"Inverse polarity", -1)

        self.stabilityModeCombo.addItem("Linear fit", "linear")
        self.stabilityModeCombo.addItem("T-Test", "ttest")
        self.stabilityModeCombo.currentIndexChanged.connect(self.stabilityIndexChanged)

        self.assessModeCombo.addItem(u"Voltage sweep", "voltage")
        self.assessModeCombo.addItem(u"Pulse width sweep", "pulse")
        self.assessModeCombo.addItem(u"Programming sweep", "program")
        self.assessModeCombo.currentIndexChanged.connect(self.assessModeIndexChanged)

        self.singlePhaseRunComboBox.addItem("Phase I", 1)
        self.singlePhaseRunComboBox.addItem("Phase II", 2)
        self.singlePhaseRunComboBox.addItem("Phase III", 3)
        self.singlePhaseRunCheckBox.stateChanged.connect(self.singlePhaseRunChecked)
        self.singlePhaseRunComboBox.currentIndexChanged.connect(self.singlePhaseRunPhaseChanged)

        self.stateRetentionMultiplierComboBox.addItem("ms", 1)
        self.stateRetentionMultiplierComboBox.addItem("s", 1000)

        if not self.short:
            self.applyOneButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ONE))
            self.applyAllButton.clicked.connect(partial(self.programDevs, self.PROGRAM_ALL))
            self.applyRangeButton.clicked.connect(partial(self.programDevs, self.PROGRAM_RANGE))
        else:
            for wdg in [self.applyOneButton, self.applyAllButton, self.applyRangeButton]:
                wdg.hide()

        self.monotonicityComboBox.addItem(u"Ignore", 0)
        self.monotonicityComboBox.addItem(u"Stop on reversal", 1)
        self.monotonicityComboBox.addItem(u"Move to next step", 2)
        self.monotonicityComboBox.setCurrentIndex(1)

        self.updateInputWidgets()

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
        self.stateVoltageEdit.setValidator(floatValidator)
        self.statePWminEdit.setValidator(floatValidator)
        self.statePWstepEdit.setValidator(floatValidator)
        self.statePWmaxEdit.setValidator(floatValidator)
        self.statePulsesMinEdit.setValidator(intValidator)
        self.statePulsesStepEdit.setValidator(intValidator)
        self.statePulsesMaxEdit.setValidator(intValidator)

        self.registerPropertyWidget(self.readsEdit, "trailer_reads")
        self.registerPropertyWidget(self.pulsesEdit, "prog_pulses")
        self.registerPropertyWidget(self.pulseWidthEdit, "pulse_duration")
        self.registerPropertyWidget(self.vminEdit, "vmin")
        self.registerPropertyWidget(self.vstepEdit, "vstep")
        self.registerPropertyWidget(self.vmaxEdit, "vmax")
        self.registerPropertyWidget(self.tolbandEdit, "tolerance_band")
        self.registerPropertyWidget(self.interpulseEdit, "interpulse")
        self.registerPropertyWidget(self.stabilityVoltageEdit, "stability_voltage")
        self.registerPropertyWidget(self.readAfterPulseCheckBox, "read_write")
        self.registerPropertyWidget(self.volatilityReadPWEdit, "stability_pw")
        self.registerPropertyWidget(self.maxStabilityTimeEdit, "stability_tmax")
        self.registerPropertyWidget(self.stateModeCombo, "state_mode")
        self.registerPropertyWidget(self.stabilityModeCombo, "stability_mode")
        self.registerPropertyWidget(self.stabilitySlopeEdit, "stability_slope")
        self.registerPropertyWidget(self.tmetricEdit, "stability_tmetric")
        self.registerPropertyWidget(self.assessModeCombo, "assess_mode")
        self.registerPropertyWidget(self.stateReadsEdit, "state_reads")
        self.registerPropertyWidget(self.statePulsesEdit, "state_prog_pulses")
        self.registerPropertyWidget(self.stateVminEdit, "state_vmin")
        self.registerPropertyWidget(self.stateVmaxEdit, "state_vmax")
        self.registerPropertyWidget(self.stateVstepEdit, "state_vstep")
        self.registerPropertyWidget(self.stateVoltageEdit, "state_voltage")
        self.registerPropertyWidget(self.statePulseWidthEdit, "state_pulse_duration")
        self.registerPropertyWidget(self.stateInterpulseEdit, "state_interpulse")
        self.registerPropertyWidget(self.statePWminEdit, "state_pwmin")
        self.registerPropertyWidget(self.statePWmaxEdit, "state_pwmax")
        self.registerPropertyWidget(self.statePWstepEdit, "state_pwstep")
        self.registerPropertyWidget(self.statePulsesMinEdit, "state_prog_pulses_min")
        self.registerPropertyWidget(self.statePulsesStepEdit, "state_prog_pulses_step")
        self.registerPropertyWidget(self.statePulsesMaxEdit, "state_prog_pulses_max")
        self.registerPropertyWidget(self.stateRetentionEdit, "state_retention")
        self.registerPropertyWidget(self.stateStdevSpinBox, "state_stdev")
        self.registerPropertyWidget(self.monotonicityComboBox, "state_monotonic")
        self.registerPropertyWidget(self.resetCounterCheckBox, "state_counter_reset")
        self.registerPropertyWidget(self.singlePhaseRunCheckBox, "single_phase_run")
        self.registerPropertyWidget(self.singlePhaseRunComboBox, "single_phase_run_phase")


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
        result["state_mode"] = int(self.stateModeCombo.itemData(mode_index))
        result["stability_mode"] = str(self.stabilityModeCombo.itemData(stability_index))
        result["stability_slope"] = float(self.stabilitySlopeEdit.text())
        result["stability_tmetric"] = float(self.tmetricEdit.text())

        assess_index = self.assessModeCombo.currentIndex()
        result["assess_mode"] = str(self.assessModeCombo.itemData(assess_index))

        result["state_reads"] = int(self.stateReadsEdit.text())
        result["state_prog_pulses"] = int(self.statePulsesEdit.text())
        result["state_vmin"] = float(self.stateVminEdit.text())
        result["state_vmax"] = float(self.stateVmaxEdit.text())
        result["state_vstep"] = float(self.stateVstepEdit.text())
        result["state_voltage"] = float(self.stateVoltageEdit.text())
        result["state_pulse_duration"] = float(self.statePulseWidthEdit.text()) / 1000.0
        result["state_interpulse"] = float(self.stateInterpulseEdit.text()) / 1000.0
        result["state_pwmin"] = float(self.statePWminEdit.text()) / 1000.0
        result["state_pwstep"] = float(self.statePWstepEdit.text()) / 1000.0
        result["state_pwmax"] = float(self.statePWmaxEdit.text()) / 1000.0
        result["state_prog_pulses_min"] = int(self.statePulsesMinEdit.text())
        result["state_prog_pulses_step"] = int(self.statePulsesStepEdit.text())
        result["state_prog_pulses_max"] = int(self.statePulsesMaxEdit.text())

        multiplier_index = self.stateRetentionMultiplierComboBox.currentIndex()
        retention_mult = float(self.stateRetentionMultiplierComboBox.itemData(multiplier_index))

        result["state_retention"] = (float(self.stateRetentionEdit.text()) * retention_mult) / 1000.0
        result["state_stdev"] = int(self.stateStdevSpinBox.value())
        monotonicIndex = self.monotonicityComboBox.currentIndex()
        result["state_monotonic"] = int(self.monotonicityComboBox.itemData(monotonicIndex))
        result["state_counter_reset"] = int(self.resetCounterCheckBox.isChecked())

        result["single_phase_run"] = bool(self.singlePhaseRunCheckBox.isChecked())

        if result["single_phase_run"]:
            phaseIndex = self.singlePhaseRunComboBox.currentIndex()
            phase = self.singlePhaseRunComboBox.itemData(phaseIndex)
            result["single_phase_run_phase"] = phase
        else:
            result["single_phase_run_phase"] = None

        print(result)

        return result

    def sendParams(self):
        data = self.gatherData()

        HW.ArC.write_b(str(data["pulse_duration"])+"\n")
        HW.ArC.write_b(str(data["vmin"])+"\n")
        HW.ArC.write_b(str(data["vstep"])+"\n")
        HW.ArC.write_b(str(data["vmax"])+"\n")
        HW.ArC.write_b(str(data["interpulse"])+"\n")

        HW.ArC.write_b(str(data["trailer_reads"])+"\n")
        HW.ArC.write_b(str(data["prog_pulses"])+"\n")
        HW.ArC.write_b(str(data["tolerance_band"])+"\n")
        HW.ArC.write_b(str(data["read_write"])+"\n")

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

    def disableProgPanel(self,state):
        if state == True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def stabilityIndexChanged(self, index):
        self.stabilityCriterionStackedWidget.setCurrentIndex(index)
        self.stabilityCriterionLabelStackedWidget.setCurrentIndex(index)

    def assessModeIndexChanged(self, index):
        self.pwConst02LabelStackedWidget.setCurrentIndex(index)
        self.pwConst02EditStackedWidget.setCurrentIndex(index)
        self.pwConst03LabelStackedWidget.setCurrentIndex(index)
        self.pwConst03EditStackedWidget.setCurrentIndex(index)
        self.pwConst04LabelStackedWidget.setCurrentIndex(index)
        self.pwConst04EditStackedWidget.setCurrentIndex(index)

        state_mode = str(self.assessModeCombo.itemData(index))
        self.updateInputWidgets()

    def singlePhaseRunChecked(self, *args):
        checked = self.singlePhaseRunCheckBox.isChecked()
        self.singlePhaseRunComboBox.setEnabled(checked)

        if not checked:
            self.phase1GroupBox.setEnabled(True)
            self.phase2GroupBox.setEnabled(True)
            self.phase3GroupBox.setEnabled(True)
            self.stateModeCombo.setEnabled(True)
        else:
            phaseIndex = self.singlePhaseRunComboBox.currentIndex()
            self.singlePhaseRunPhaseChanged(phaseIndex)
            self.stateModeCombo.setEnabled(False)

    def singlePhaseRunPhaseChanged(self, phaseIndex):
        phase = self.singlePhaseRunComboBox.itemData(phaseIndex)

        if phase == 1:
            self.phase1GroupBox.setEnabled(True)
            self.phase2GroupBox.setEnabled(False)
            self.phase3GroupBox.setEnabled(False)
        elif phase == 2:
            self.phase1GroupBox.setEnabled(False)
            self.phase2GroupBox.setEnabled(True)
            self.phase3GroupBox.setEnabled(False)
        else:
            self.phase1GroupBox.setEnabled(False)
            self.phase2GroupBox.setEnabled(False)
            self.phase3GroupBox.setEnabled(True)

    def updateInputWidgets(self):
        index = self.assessModeCombo.currentIndex()
        sweep_mode = str(self.assessModeCombo.itemData(index))

        self.voltageBiasLabel.setEnabled(True)
        self.stateVoltageEdit.setEnabled(True)

        self.pulseWidthLabel.setEnabled(True)
        self.statePulseWidthEdit.setEnabled(True)

        self.progPulsesLabel.setEnabled(True)
        self.statePulsesEdit.setEnabled(True)

        if sweep_mode == "voltage":
            self.voltageBiasLabel.setEnabled(False)
            self.stateVoltageEdit.setEnabled(False)
        elif sweep_mode == "pulse":
            self.pulseWidthLabel.setEnabled(False)
            self.statePulseWidthEdit.setEnabled(False)
        elif sweep_mode == "program":
            self.progPulsesLabel.setEnabled(False)
            self.statePulsesEdit.setEnabled(False)

    @staticmethod
    def display(w, b, data, parent=None):
        dialog = QtWidgets.QDialog(parent)
        dialog.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        containerLayout = QtWidgets.QHBoxLayout()
        dialog.setLayout(containerLayout)
        tabs = QtWidgets.QTabWidget(dialog)
        containerLayout.addWidget(tabs)
        saveButton = QtWidgets.QPushButton("Export data")

        resStates = []

        tab1 = QtWidgets.QWidget()
        topLayout = QtWidgets.QVBoxLayout()
        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addItem(QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding))
        bottomLayout.addWidget(saveButton)
        topLayout.addWidget(QtWidgets.QLabel("Calculated resistive states for device %d x %d" % (w, b)))
        resultTable = QtWidgets.QTableWidget()
        resultTable.setColumnCount(3)
        resultTable.setHorizontalHeaderLabels(["Resistance", "Lower bound", "Upper bound"])
        resultTable.verticalHeader().setVisible(False)
        resultTable.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Stretch)
        resultTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        resultTable.setSelectionMode(QtWidgets.QTableWidget.NoSelection)
        topLayout.addWidget(resultTable)
        topLayout.addItem(bottomLayout)
        dialog.setGeometry(100,100,600,400)
        dialog.setWindowTitle("Multistate report for W=%d | B=%d" % (w, b))
        dialog.setWindowIcon(Graphics.getIcon('appicon'))
        tab1.setLayout(topLayout)
        tabs.addTab(tab1, "Data")

        for line in data:
            tag = line[3]
            if str(tag).startswith("MSS3_STATE"):
                elements = tag.split("_")
                resStates.append([float(elements[2]), float(elements[3]), float(elements[4])])
                position = resultTable.rowCount()
                resultTable.insertRow(position)
                resultTable.setItem(position, 0, QtWidgets.QTableWidgetItem(elements[2]))
                resultTable.setItem(position, 1, QtWidgets.QTableWidgetItem(elements[3]))
                resultTable.setItem(position, 2, QtWidgets.QTableWidgetItem(elements[4]))
        resultTable.resizeColumnsToContents()
        resultTable.resizeRowsToContents()

        saveCb = partial(functions.writeDelimitedData, resStates)
        saveButton.clicked.connect(partial(functions.saveFuncToFilename, saveCb,
            "Save data to...", parent))

        plot = pyqtgraph.PlotWidget()
        plot.getAxis('bottom').setLabel("State #")
        plot.getAxis('left').setLabel("Resistance", units=u"Ω")
        tab2 = QtWidgets.QWidget()
        plotLayout = QtWidgets.QVBoxLayout()
        plotLayout.addWidget(plot)
        tab2.setLayout(plotLayout)
        tabs.addTab(tab2, "Plot")

        indices = numpy.arange(1, len(resStates)+1)
        mainCurve = plot.plot(indices, [x[0] for x in resStates],
            pen = pyqtgraph.mkPen({'color': '000', 'width': 2}),
            symbolBrush = pyqtgraph.mkBrush('000'),
            symbol = 'o', symbolSize = 6, pxMode = True)
        lowBoundCurve = plot.plot(indices, [x[1] for x in resStates],
            pen = pyqtgraph.mkPen({'color': '00F', 'width': 1}),
            symbolPen = pyqtgraph.mkPen({'color': '00F', 'width': 1}),
            symbolBrush = pyqtgraph.mkBrush('00F'),
            symbol = '+', symbolSize = 6, pxMode = True)
        upperBoundCurve = plot.plot(indices, [x[2] for x in resStates],
            pen = pyqtgraph.mkPen({'color': 'F00', 'width': 1}),
            symbolPen = pyqtgraph.mkPen({'color': 'F00', 'width': 1}),
            symbolBrush = pyqtgraph.mkBrush('F00'),
            symbol = '+', symbolSize = 6, pxMode = True)

        filler = pyqtgraph.FillBetweenItem(lowBoundCurve, upperBoundCurve,
                brush=pyqtgraph.mkBrush('BBB'))

        plot.addItem(filler)

        return dialog


tags = {
    'top': ModTag(tag, "MultiStateSeeker", None),
    'subtags': [
        ModTag(tag+"1", "MultiState Polarity Inference", None),
        ModTag(tag+"2", "MultiState Retention", None),
        ModTag(tag+"3", "MultiState Calculation", MultiStateSeeker.display)
    ]
}
