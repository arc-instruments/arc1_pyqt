####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time

import pyqtgraph as pg
import numpy as np

from arc1pyqt import Graphics
from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag = "SS2"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList):
        super().__init__()
        self.deviceList=deviceList

    @BaseThreadWrapper.runner
    def run(self):

        global tag

        HW.ArC.write_b(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            HW.ArC.queue_select(w, b)

            firstPoint=1
            endCommand=0

            valuesNew=HW.ArC.read_floats(3)

            if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                tag_=tag+'_s'
            else:
                endCommand=1

            while(endCommand==0):
                valuesOld=valuesNew

                valuesNew=HW.ArC.read_floats(3)

                if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                    self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                    self.displayData.emit()
                    tag_=tag+'_i'
                else:
                    tag_=tag+'_e'
                    self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                    self.displayData.emit()
                    endCommand=1
            self.updateTree.emit(w,b)


class SwitchSeeker(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title="SwitchSeeker", \
                description="State-of-art analogue resistive switching "
                "parameter finder.", short=short)
        self.initUI()

    def initUI(self):

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel(self.title)
        titleLabel.setFont(fonts.font1)
        descriptionLabel = \
            QtWidgets.QLabel(self.description)
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Reads in trailer card', \
                    'Programming pulses', \
                    'Pulse duration (ms)', \
                    'Voltage min (V)', \
                    'Voltage step (V)', \
                    'Voltage max (V)', \
                    'Max switching cycles', \
                    'Tolerance band (%)', \
                    'Interpulse time (ms)', \
                    'Resistance Threshold']
        leftInit=  ['5',\
                    '10',\
                    '0.1',\
                    '0.5',\
                    '0.2',\
                    '3',\
                    '5',\
                    '10',\
                    '1',\
                    '1000000']
        self.leftEdits=[]

        rightLabels=[]
        self.rightEdits=[]

        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)
        gridLayout.setColumnStretch(2,1)
        gridLayout.setColumnStretch(3,1)
        gridLayout.setColumnStretch(4,3)

        if self.short==False:
            gridLayout.setColumnStretch(5,1)
            gridLayout.setColumnStretch(6,1)
            gridLayout.setColumnStretch(7,2)
        #gridLayout.setSpacing(2)

        #setup a line separator
        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)
        lineRight=QtWidgets.QFrame()
        lineRight.setFrameShape(QtWidgets.QFrame.VLine)
        lineRight.setFrameShadow(QtWidgets.QFrame.Raised)
        lineRight.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 10, 1)
        if self.short==False:
            gridLayout.addWidget(lineRight, 0, 6, 10, 1)

        for i in range(len(leftLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        for i in range(len(rightLabels)):
            lineLabel=QtWidgets.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,4)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

        self.checkRead=QtWidgets.QCheckBox(self)
        self.checkRead.setText("Read after pulse?")
        gridLayout.addWidget(self.checkRead,3,4)

        gridLayout.addWidget(QtWidgets.QLabel("Seeker algorithm"),0,4)
        self.modeSelectionCombo=QtWidgets.QComboBox()
        # SwitchSeeker_1 has id 15
        self.modeSelectionCombo.addItem("Fast",15)
        # SwitchSeeker_2 has id 152
        self.modeSelectionCombo.addItem("Slow",152)
        gridLayout.addWidget(self.modeSelectionCombo,0,5)

        gridLayout.addWidget(QtWidgets.QLabel("Stage II polarity"),1,4)
        self.polarityCombo=QtWidgets.QComboBox()
        self.polarityCombo.addItem("(+) Positive",1)
        self.polarityCombo.addItem("(-) Negative",-1)
        self.polarityCombo.setEnabled(False)
        gridLayout.addWidget(self.polarityCombo,1,5)

        self.skipICheckBox=QtWidgets.QCheckBox(self)
        self.skipICheckBox.setText("Skip Stage I")
        def skipIChecked(state):
            if state == QtCore.Qt.Checked:
                self.polarityCombo.setEnabled(True)
            else:
                self.polarityCombo.setEnabled(False)
        self.skipICheckBox.stateChanged.connect(skipIChecked)
        gridLayout.addWidget(self.skipICheckBox,2,4)

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scrlArea.installEventFilter(self)

        vbox1.addWidget(scrlArea)
        vbox1.addStretch()

        if self.short==False:
            self.hboxProg=QtWidgets.QHBoxLayout()

            push_single = self.makeControlButton('Apply to One', \
                    self.programOne)
            push_range = self.makeControlButton('Apply to Range', \
                    self.programRange)
            push_all = self.makeControlButton('Apply to All', \
                    self.programAll)

            self.hboxProg.addWidget(push_single)
            self.hboxProg.addWidget(push_range)
            self.hboxProg.addWidget(push_all)

            vbox1.addLayout(self.hboxProg)

        self.gridLayout=gridLayout
        self.setLayout(vbox1)

        self.registerPropertyWidget(self.leftEdits[0], "numreads")
        self.registerPropertyWidget(self.leftEdits[1], "numpulses")
        self.registerPropertyWidget(self.leftEdits[2], "pw")
        self.registerPropertyWidget(self.leftEdits[3], "vmin")
        self.registerPropertyWidget(self.leftEdits[4], "vstep")
        self.registerPropertyWidget(self.leftEdits[5], "vmax")
        self.registerPropertyWidget(self.leftEdits[6], "cycles")
        self.registerPropertyWidget(self.leftEdits[7], "tolerance")
        self.registerPropertyWidget(self.leftEdits[8], "interpulse")
        self.registerPropertyWidget(self.leftEdits[9], "threshold")
        self.registerPropertyWidget(self.checkRead, "pulseread")
        self.registerPropertyWidget(self.modeSelectionCombo, "mode")
        self.registerPropertyWidget(self.polarityCombo, "polarity")
        self.registerPropertyWidget(self.skipICheckBox, "skip_stageI")

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def sendParams(self):
        HW.ArC.write_b(str(float(self.leftEdits[2].text())/1000)+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[3].text()))+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[4].text()))+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[5].text()))+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[8].text())/1000)+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[9].text()))+"\n")
        time.sleep(0.01)
        HW.ArC.write_b(str(int(self.leftEdits[0].text()))+"\n")
        HW.ArC.write_b(str(int(self.leftEdits[1].text()))+"\n")
        HW.ArC.write_b(str(int(self.leftEdits[6].text()))+"\n")
        HW.ArC.write_b(str(int(self.leftEdits[7].text()))+"\n")
        HW.ArC.write_b(str(int(self.checkRead.isChecked()))+"\n")

        # Check if Stage I should be skipped
        if self.skipICheckBox.isChecked():
            # -1 or 1 are the QVariants available from the combobox
            # -1 -> negative polarity for Stage II
            #  1 -> positive polarity for Stage II
            polarityIndex = self.polarityCombo.currentIndex()
            skipStageI = str(self.polarityCombo.itemData(polarityIndex))
        else:
            # if 0 then Stage I will not be skipped
            skipStageI = str(0)

        HW.ArC.write_b(skipStageI+"\n")

    def programOne(self):
        self.programDevs([[CB.word, CB.bit]])

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def programDevs(self, devs):
        job="%d"%self.getJobCode()
        HW.ArC.write_b(job+"\n")   # sends the job

        self.sendParams()
        wrapper = ThreadWrapper(devs)
        self.execute(wrapper, wrapper.run)

    def getJobCode(self):
        job=self.modeSelectionCombo.itemData(self.modeSelectionCombo.currentIndex())
        return job

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    @staticmethod
    def display(w, b, raw, parent=None):

        # Initialisations
        pulseNr = 0
        deltaR = []
        initR = []
        ampl = []
        Rs = []

        # Holds under and overshoot voltages
        over = []
        under = []
        offshoots = [] # holds both in order

        # holds maximum normalised resistance offset during a train of reads
        max_dR = 0

        # Find the pulse amplitudes and the resistance (averaged over the read
        # sequence) after each pulse train
        index = 0

        while index < len(raw):

            # if this is the first read pulse of a read sequence:
            if index < len(raw) and raw[index][2] == 0:

                # record the start index
                start_index = index
                # initialise average resistance during a read run accumulator
                readAvgRun = 0
                # counts nr of reads
                idx = 0

                # If the line contains 0 amplitude and 0 width, then we're
                # entering a read run
                while index < len(raw) and raw[index][2] == 0:

                    # increment the counter
                    idx += 1
                    # add to accumulator
                    readAvgRun += raw[index][0]
                    # increment the global index as we're advancing through the
                    # pulse run
                    index += 1
                    # if the index exceeded the lenght of the run, exit
                    if index > len(raw) - 1:
                        break

                # When we exit the while loop we are at the end of the reading
                # run
                readAvgRun = readAvgRun/idx

                # append with this resistance
                Rs.append(readAvgRun)

                # find the maximum deviation from the average read during a
                # read sequence (helps future plotting of the confidence bar)
                for i in range(idx):

                    # maybe not the best way to do this but still
                    if abs(raw[start_index+i][0] - readAvgRun)/readAvgRun > max_dR:
                        max_dR = abs(raw[start_index+i][0] - readAvgRun)/readAvgRun

            # if both amplitude and pw are non-zero, we are in a pulsing run
            # if this is the first  pulse of a write sequence:
            if index<len(raw) and raw[index][1] != 0 and raw[index][2] != 0:
                while index<len(raw) and raw[index][1] != 0 and raw[index][2] != 0:

                    # increment the index
                    index += 1
                    # if the index exceeded the length of the run, exit
                    if index == len(raw) - 1:
                        break

                # record the pulse voltage at the end
                ampl.append(raw[index-1][1])


        # Record initial resistances and delta R.
        for i in range(len(ampl)):
            initR.append(Rs[i])
            deltaR.append((Rs[i+1] - Rs[i])/Rs[i])

        confX = [0, 0]
        confY = [-max_dR, max_dR]

        # setup display
        resultWindow = QtWidgets.QWidget()
        resultWindow.setGeometry(100, 100, 1000*APP.scalingFactor, 500)
        resultWindow.setWindowTitle("SwitchSeeker: W="+ str(w) + " | B=" + str(b))
        resultWindow.setWindowIcon(Graphics.getIcon('appicon'))
        resultWindow.show()

        view = pg.GraphicsLayoutWidget()

        labelStyle = {'color': '#000000', 'font-size': '10pt'}

        japanPlot = view.addPlot()
        japanCurve = japanPlot.plot(pen=None, symbolPen=None,
                symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
        japanPlot.getAxis('left').setLabel('dM/M0', **labelStyle)
        japanPlot.getAxis('bottom').setLabel('Voltage', units='V', **labelStyle)
        japanPlot.getAxis('left').setGrid(50)
        japanPlot.getAxis('bottom').setGrid(50)

        resLayout = QtWidgets.QHBoxLayout()
        resLayout.addWidget(view)
        resLayout.setContentsMargins(0, 0, 0, 0)

        resultWindow.setLayout(resLayout)

        japanCurve.setData(np.asarray(ampl), np.asarray(deltaR))
        resultWindow.update()

        return resultWindow


tags = { 'top': ModTag(tag, "SwitchSeeker", SwitchSeeker.display) }
