####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
import os.path
import itertools
from copy import copy
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets

import arc1pyqt

from .. import state
HW = state.hardware
CB = state.crossbar
APP = state.app

from ..Globals import functions, fonts, styles


class _ReadAllWorker(QtCore.QObject):
    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    sendPosition=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)

    Vread = HW.conf.Vread
    tag='F R'+str(HW.conf.readmode)+' V='+str(Vread)

    def __init__(self):
        super().__init__()

    def readAll(self):
        self.w_old = CB.word
        self.b_old = CB.bit
        self.disableInterface.emit(True)
        job="2"
        HW.ArC.write_b(job+"\n")

        all_devices = itertools.product(range(1, HW.conf.words+1),
            range(1, HW.conf.bits+1))

        # Check for standalone/custom array
        if CB.checkSA == False:
            # send the type of read - currently read All devices
            HW.ArC.write_b(str(1)+"\n")
            HW.ArC.write_b(str(HW.conf.words)+"\n")
            HW.ArC.write_b(str(HW.conf.bits)+"\n")

            devices = all_devices
            # perform standard read All
            for (word, bit) in devices:
                Mnow=float(HW.ArC.read_floats(1))

                self.sendData.emit(word,bit,Mnow,self.Vread,0,self.tag)
                self.sendPosition.emit(word,bit)
        else:
            # send the type of read - read stand alone custom array
            HW.ArC.write_b(str(2)+"\n")
            HW.ArC.write_b(str(HW.conf.words)+"\n")
            HW.ArC.write_b(str(HW.conf.bits)+"\n")
            HW.ArC.write_b(str(len(CB.customArray))+"\n")

            devices = [cell for cell in all_devices if cell in CB.customArray]

            for (word, bit) in devices:
                HW.ArC.write_b(str(word)+"\n")
                HW.ArC.write_b(str(bit)+"\n")

                Mnow = float(HW.ArC.read_floats(1))

                self.sendData.emit(word,bit,Mnow,self.Vread,0,self.tag)
                self.sendPosition.emit(word,bit)

        self.sendPosition.emit(self.w_old, self.b_old)
        self.disableInterface.emit(False)
        self.finished.emit()


class ManualOpsWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.standAlonePath = os.path.join(os.path.dirname(arc1pyqt.__file__), \
            'Helper')

    def initUI(self):

        # Setup position and resistance labels
        self.position = QtWidgets.QLabel(self)
        self.position.setText('')
        self.position.setFont(fonts.font2)
        self.position.setStyleSheet(styles.style1)

        self.resistance = QtWidgets.QLabel(self)
        self.resistance.setText("---")
        self.resistance.setFont(fonts.font1)
        self.resistance.setStyleSheet(styles.style1)

        # Setup slots for automatic Label updating
        functions.cbAntenna.selectDeviceSignal.connect(self.setM)

        # Setup manual reading panel
        self.readPanel = QtWidgets.QGroupBox('Read Operations')
        self.readPanel.setStyleSheet(styles.groupStyle)
        readPanelLayout = QtWidgets.QVBoxLayout()
        readPanelLayout.setContentsMargins(10,25,10,10)

        push_read=QtWidgets.QPushButton('Read Single')
        push_read.setStyleSheet(styles.btnStyle)
        push_read.clicked.connect(self.readSingle)

        push_readAll=QtWidgets.QPushButton('Read All')
        push_readAll.setStyleSheet(styles.btnStyle)
        push_readAll.clicked.connect(self.readAll)

        hbox_1=QtWidgets.QHBoxLayout()
        hbox_1.addWidget(push_read)
        hbox_1.addWidget(push_readAll)

        #'Update read' button.
        push_updateRead=QtWidgets.QPushButton('Update Read')
        push_updateRead.setStyleSheet(styles.btnStyle2)
        push_updateRead.clicked.connect(self.updateRead)
        push_updateRead.setMinimumWidth(100)

        # Read-out type options drop-down.
        combo_readType=QtWidgets.QComboBox()
        combo_readType.setStyleSheet(styles.comboStyle)
        combo_readType.insertItems(1, ['Classic', 'TIA', 'TIA4P'])
        combo_readType.currentIndexChanged.connect(self.updateReadType)
        combo_readType.setCurrentIndex(2)
        HW.conf.readmode = combo_readType.currentIndex()

        # Numerical 'spin box' to set read-out voltage.
        read_voltage=QtWidgets.QDoubleSpinBox()
        #read_voltage.setHeight(25)
        read_voltage.setStyleSheet(styles.spinStyle)
        read_voltage.setMinimum(-12)
        read_voltage.setMaximum(12)
        read_voltage.setSingleStep(0.05)
        read_voltage.setValue(0.5)
        read_voltage.setSuffix(' V')
        read_voltage.valueChanged.connect(self.setVread)

        # Instantiate GUI row including update read, read-out type and read-out
        # voltage spin-box.
        hbox_2=QtWidgets.QHBoxLayout()
        hbox_2.addWidget(push_updateRead)
        hbox_2.addWidget(combo_readType)
        hbox_2.addWidget(read_voltage)

        # Check-box for custom array.
        self.customArrayCheckbox = QtWidgets.QCheckBox("Custom array")
        self.customArrayCheckbox.stateChanged.connect(self.toggleSA)

        # Text field to show selected file containing SA locations for
        # particular application.
        self.customArrayFileName=QtWidgets.QLabel()
        self.customArrayFileName.setStyleSheet(styles.style1)

        # File browser. Push-button connecting to function opening file browser.
        push_browse = QtWidgets.QPushButton('...')
        # open custom array defive position file
        push_browse.clicked.connect(self.findSAfile)
        push_browse.setFixedWidth(20)

        hbox_3=QtWidgets.QHBoxLayout()
        hbox_3.addWidget(self.customArrayCheckbox)
        hbox_3.addWidget(self.customArrayFileName)
        hbox_3.addWidget(push_browse)

        readPanelLayout.addLayout(hbox_1)
        readPanelLayout.addLayout(hbox_2)
        readPanelLayout.addLayout(hbox_3)

        self.readPanel.setLayout(readPanelLayout)

        # Manual Pulse panel
        self.pulsePanel = QtWidgets.QGroupBox('Manual Pulsing')
        self.pulsePanel.setStyleSheet(styles.groupStyle)

        pulsePanelLayout= QtWidgets.QGridLayout()
        pulsePanelLayout.setContentsMargins(10,25,10,10)

        self.pulse_V_pos = QtWidgets.QLineEdit()
        self.pulse_V_neg = QtWidgets.QLineEdit()
        self.pulse_pw_pos = QtWidgets.QLineEdit()
        self.pulse_pw_neg = QtWidgets.QLineEdit()

        self.pulse_V_pos.setStyleSheet(styles.entryStyle)
        self.pulse_pw_pos.setStyleSheet(styles.entryStyle)
        self.pulse_V_neg.setStyleSheet(styles.entryStyle)
        self.pulse_pw_neg.setStyleSheet(styles.entryStyle)

        # Initialise fields
        self.pulse_V_pos.setText('1')
        self.pulse_V_neg.setText('1')
        self.pulse_pw_pos.setText('100')
        self.pulse_pw_neg.setText('100')

        isFloat=QtGui.QDoubleValidator()

        # Apply an input mask to restrict the input to only numbers
        self.pulse_V_pos.setValidator(isFloat)
        self.pulse_V_neg.setValidator(isFloat)
        self.pulse_pw_pos.setValidator(isFloat)
        self.pulse_pw_neg.setValidator(isFloat)

        label_V = QtWidgets.QLabel('Voltage (V)')
        label_pw = QtWidgets.QLabel('Duration')

        push_pulsePos = QtWidgets.QPushButton('+Pulse')
        push_pulsePos.clicked.connect(self.extractParamsPlus)
        push_pulsePos.setStyleSheet(styles.btnStyle)
        push_pulseNeg = QtWidgets.QPushButton('-Pulse')
        push_pulseNeg.clicked.connect(self.extractParamsNeg)
        push_pulseNeg.setStyleSheet(styles.btnStyle)

        self.check_lock = QtWidgets.QCheckBox('Lock')
        self.check_lock.stateChanged.connect(self.lockPulses)

        pulsePanelLayout.addWidget(self.pulse_V_pos,0,0)
        pulsePanelLayout.addWidget(self.pulse_V_neg,0,2)

        pw_pos_lay=QtWidgets.QHBoxLayout()
        pw_neg_lay=QtWidgets.QHBoxLayout()

        self.pw_plusDropDown=QtWidgets.QComboBox()
        self.pw_plusDropDown.setStyleSheet(styles.comboStylePulse)

        self.unitsFull=[['s',1],['ms',0.001],['us',0.000001],['ns',0.000000001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.pw_negDropDown=QtWidgets.QComboBox()
        self.pw_negDropDown.setStyleSheet(styles.comboStylePulse)

        self.pw_plusDropDown.insertItems(1,self.units)
        self.pw_plusDropDown.setCurrentIndex(2)
        self.pw_negDropDown.insertItems(1,self.units)
        self.pw_negDropDown.setCurrentIndex(2)

        pw_pos_lay.addWidget(self.pulse_pw_pos)
        pw_pos_lay.addWidget(self.pw_plusDropDown)
        pw_neg_lay.addWidget(self.pulse_pw_neg)
        pw_neg_lay.addWidget(self.pw_negDropDown)

        pulsePanelLayout.addLayout(pw_pos_lay,1,0)
        pulsePanelLayout.addLayout(pw_neg_lay,1,2)

        pulsePanelLayout.addWidget(label_V,0,1)
        pulsePanelLayout.addWidget(label_pw,1,1)
        pulsePanelLayout.addWidget(push_pulsePos,2,0)
        pulsePanelLayout.addWidget(push_pulseNeg,2,2)
        pulsePanelLayout.addWidget(self.check_lock,2,1)

        pulsePanelLayout.setAlignment(label_V, QtCore.Qt.AlignHCenter)
        pulsePanelLayout.setAlignment(label_pw, QtCore.Qt.AlignHCenter)
        pulsePanelLayout.setAlignment(self.check_lock, QtCore.Qt.AlignHCenter)

        self.pulsePanel.setLayout(pulsePanelLayout)

        # Display Options Panel
        displayPanel = QtWidgets.QGroupBox('Display Options')
        displayPanel.setStyleSheet(styles.groupStyle)
        displayPanelLayout = QtWidgets.QHBoxLayout()
        displayPanelLayout.setContentsMargins(10,25,10,10)

        push_displayAll = QtWidgets.QPushButton('Full')
        push_displayAll.setStyleSheet(styles.btnStyle2)
        push_displayAll.clicked.connect(self.displayAll)
        push_displayRange = QtWidgets.QPushButton('Range')
        push_displayRange.setStyleSheet(styles.btnStyle2)
        push_displayRange.clicked.connect(self.displayRange)

        points_spinbox = QtWidgets.QSpinBox()
        points_spinbox.setStyleSheet(styles.spinStyle)
        points_spinbox.setMinimum(10)
        points_spinbox.setMaximum(10000)
        points_spinbox.setSingleStep(100)
        points_spinbox.setValue(APP.displayPoints)
        points_spinbox.setSuffix(' p')
        points_spinbox.valueChanged.connect(self.updatePoints)

        check_log = QtWidgets.QCheckBox('log Y')
        check_log.stateChanged.connect(self.updateLogScale)

        displayPanelLayout.addWidget(push_displayAll)
        displayPanelLayout.addWidget(push_displayRange)
        displayPanelLayout.addWidget(points_spinbox)
        displayPanelLayout.addWidget(check_log)

        displayPanel.setLayout(displayPanelLayout)

        mainLayout = QtWidgets.QVBoxLayout()

        mainLayout.addWidget(self.position)
        mainLayout.addWidget(self.resistance)
        mainLayout.addWidget(self.readPanel)
        mainLayout.addWidget(self.pulsePanel)
        mainLayout.addWidget(displayPanel)
        mainLayout.addStretch()

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,3,0)

        self.setLayout(mainLayout)

        self.setContentsMargins(0,0,0,0)

        self.setM(1,1)

    def lockPulses(self, state):
        if state==2:
            self.pulse_V_neg.setEnabled(False)
            self.pw_negDropDown.setEnabled(False)
            self.pulse_pw_neg.setEnabled(False)
            self.update()
        else:
            self.pulse_V_neg.setEnabled(True)
            self.pw_negDropDown.setEnabled(True)
            self.pulse_pw_neg.setEnabled(True)
            self.update()

    def updateLogScale(self,event):
        functions.displayUpdate.updateLog.emit(event)

    def toggleSA(self, event):
        if (event == 0):
            CB.checkSA = False
            for w in range(1,33):
                for b in range(1,33):
                    functions.SAantenna.enable.emit(w,b)
        else:
            if (CB.customArray):
                CB.checkSA = True
                # signal the crossbar antenna that this device has been selected
                functions.cbAntenna.selectDeviceSignal.emit(CB.customArray[0][0], \
                        CB.customArray[0][1])
                functions.displayUpdate.updateSignal_short.emit()
                for w in range(1,33):
                    for b in range(1,33):
                        functions.SAantenna.disable.emit(w,b)

                for cell in CB.customArray:
                    w, b = cell
                    functions.SAantenna.enable.emit(w,b)
            else:
                if self.findSAfile() == True:
                    CB.checkSA = True
                    for w in range(1,33):
                        for b in range(1,33):
                            functions.SAantenna.disable.emit(w,b)

                    for cell in CB.customArray:
                        w, b = cell
                        functions.SAantenna.enable.emit(w,b)
                    functions.cbAntenna.selectDeviceSignal.emit(CB.customArray[0][0], \
                            CB.customArray[0][1])
                    functions.displayUpdate.updateSignal_short.emit()

                else:
                    CB.checkSA = False
                    self.customArrayCheckbox.setCheckState(QtCore.Qt.Unchecked)

    def findSAfile(self):
        try:
            path = QtCore.QFileInfo(QtWidgets.QFileDialog.\
                    getOpenFileName(self, 'Open file', self.standAlonePath,\
                    "Array files (*.txt)")[0])
            if (not path.exists()) or (not path.isFile()) or (not path.isReadable()):
                return False
        except IndexError: # nothing selected
            return False

        customArray = []

        try:
            arraydata = np.loadtxt(path.absoluteFilePath(), dtype=int,
                    delimiter=',', comments='#')

            for row in arraydata:
                (w, b) = row
                customArray.append((w, b))

                # check if w and b are within bounds
                if (int(w) < 1 or int(w) > HW.conf.words or
                        int(b) < 1 or
                        int(b) > HW.conf.bits):
                    raise ValueError("Device coordinates out of bounds")

        except ValueError as exc:
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Custom array text file formatted " +
                    "incorrectly, or selected devices outside of array range!")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()
            return False

        self.customArrayFileName.setText(path.baseName())
        CB.customArray = customArray
        self.standAlonePath = path.absoluteDir().absolutePath()
        return True

    def setM(self, w, b):
        try:
            res = CB.history[w][b][-1][0]
            self.resistance.setText(str('%.0f' % res)+' Ohms')
        except IndexError:
            self.resistance.setText('Not Read')
        self.position.setText('W='+str(w)+ ' | ' + 'B='+str(b))

        CB.word = w
        CB.bit = b

    def readSingle(self):
        if HW.ArC is not None:

            currentM = HW.ArC.read_one(CB.word, CB.bit)

            tag='S R'+str(HW.conf.readmode)+' V='+str(HW.conf.Vread)
            functions.updateHistory(CB.word, CB.bit, currentM, float(HW.conf.Vread), \
                    0, tag)
            self.setM(CB.word, CB.bit)

            functions.displayUpdate.updateSignal.emit(CB.word, CB.bit, 2, APP.displayPoints,99)
            functions.historyTreeAntenna.updateTree.emit(CB.word, CB.bit)

    def readAll(self):
        if HW.ArC is not None:
            self.thread=QtCore.QThread()
            self.readAllWorker = _ReadAllWorker()
            self.readAllWorker.moveToThread(self.thread)
            self.thread.started.connect(self.readAllWorker.readAll)
            self.readAllWorker.sendData.connect(functions.updateHistory)
            self.readAllWorker.sendPosition.connect(functions.cbAntenna.cast)
            #self.readAllWorker.updateHistoryTree.connect(f.deviceHistoryAntenna.cast)
            self.readAllWorker.finished.connect(self.thread.quit)
            self.readAllWorker.finished.connect(self.readAllWorker.deleteLater)
            self.thread.finished.connect(self.readAllWorker.deleteLater)
            self.readAllWorker.disableInterface.connect(functions.interfaceAntenna.disable.emit)
            self.thread.start()

    def updateRead(self):
        if HW.ArC is not None:
            HW.ArC.update_read(HW.conf)

    def setVread(self, event):
        if HW.ArC is None:
            return
        config = copy(HW.conf)
        config.Vread = float(event)
        try:
            HW.ArC.update_read(config)
            HW.conf = config
        except Exception as exc:
            print("Could not update Vread:", exc)

    def updateReadType(self, event):
        if HW.ArC is None:
            return
        config = copy(HW.conf)
        config.readmode = float(event)
        try:
            HW.ArC.update_read(config)
            HW.conf = config
        except Exception as exc:
            print("Could not update Vread:", exc)

    def extractParamsPlus(self):
        self.amplitude = float(self.pulse_V_pos.text())
        duration = float(self.pulse_pw_pos.text())
        unit = float(self.multiply[self.pw_plusDropDown.currentIndex()])
        self.pw = duration*unit

        if self.pw < 0.00000009:
            self.pulse_pw_pos.setText(str(90))
            self.pw_plusDropDown.setCurrentIndex(3)
            self.pw = 0.00000009
        if self.pw > 10:
            self.pulse_pw_pos.setText(str(10))
            self.pw_plusDropDown.setCurrentIndex(0)
            self.pw = 10

        self.update()
        self.pulse()

    def extractParamsNeg(self):
        if self.check_lock.isChecked():
            self.amplitude=-1*float(self.pulse_V_pos.text())
            duration=float(self.pulse_pw_pos.text())
            unit=float(self.multiply[self.pw_plusDropDown.currentIndex()])
            self.pw=duration*unit
        else:
            self.amplitude=-1*float(self.pulse_V_neg.text())
            duration=float(self.pulse_pw_neg.text())
            unit=float(self.multiply[self.pw_negDropDown.currentIndex()])
            self.pw=duration*unit

        if self.check_lock.isChecked():
            if self.pw<0.00000009:
                self.pulse_pw_pos.setText(str(90))
                self.pw_plusDropDown.setCurrentIndex(3)
                self.pw=0.00000009
            if self.pw>10:
                self.pulse_pw_pos.setText(str(10))
                self.pw_plusDropDown.setCurrentIndex(0)
                self.pw=10
        else:
            if self.pw<0.00000009:
                self.pulse_pw_neg.setText(str(90))
                self.pw_negDropDown.setCurrentIndex(3)
                self.pw=0.00000009
            if self.pw>10:
                self.pulse_pw_neg.setText(str(10))
                self.pw_negDropDown.setCurrentIndex(0)
                self.pw=10

        self.update()
        self.pulse()

    def pulse(self):
        if HW.ArC is not None:

            res = HW.ArC.pulseread_one(CB.word, CB.bit, self.amplitude, self.pw)

            tag='P'
            functions.updateHistory(CB.word, CB.bit, res, self.amplitude, self.pw, tag)
            self.setM(CB.word, CB.bit)
            functions.displayUpdate.updateSignal.emit(CB.word, CB.bit, 2,
                    APP.displayPoints, 99)
            functions.historyTreeAntenna.updateTree.emit(CB.word, CB.bit)

    def displayAll(self):
        functions.displayUpdate.updateSignal.emit(CB.word, CB.bit, 1,
                APP.displayPoints, 0)

    def displayRange(self):
        functions.displayUpdate.updateSignal.emit(CB.word, CB.bit, 2,
                APP.displayPoints, 0)

    def updatePoints(self, how_many):
        APP.displayPoints = how_many

