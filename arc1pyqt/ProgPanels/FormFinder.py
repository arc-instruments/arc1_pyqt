####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see License.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import pyqtgraph
import numpy as np
from functools import partial

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts, functions
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag="FF"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self,deviceList):
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


class FormFinder(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title="FormFinder", \
                description="Applies a pulsed voltage ramp. Can be used "
                "for electroforming", short=short)
        self.initUI()

    def initUI(self):

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel(self.title)
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel(self.description)
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Voltage min (V)', \
                    'Voltage step (V)', \
                    'Voltage max (V)', \
                    'Pulse width min (us)', \
                    'Pulse width step (%)', \
                    'Pulse width max (us)', \
                    'Interpulse time (ms)']
        self.leftLabels = []
        self.leftEdits=[]
        leftInit=  ['0.25',\
                    '0.25',\
                    '3',\
                    '100',\
                    '100',\
                    '1000',\
                    '10']

        rightLabels=['Nr of pulses', \
                    'Resistance threshold', \
                    'Resistance threshold (%)', \
                    'Series Resistance']
        self.rightEdits=[]
        rightInit=  ['1',\
                    '1000000',\
                    '10',\
                    '7']

        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)
        gridLayout.setColumnStretch(2,1)
        gridLayout.setColumnStretch(3,1)
        gridLayout.setColumnStretch(4,3)
        gridLayout.setColumnStretch(5,1)
        gridLayout.setColumnStretch(6,1)
        if self.short==False:
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

        gridLayout.addWidget(lineLeft, 0, 2, 7, 1)
        gridLayout.addWidget(lineRight, 0, 6, 7, 1)

        #gridLayout=QtWidgets.QGridLayout()

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)


        for i in range(len(leftLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            self.leftLabels.append(lineLabel)
            gridLayout.addWidget(lineEdit, i,1)

        for i in range(len(rightLabels)):
            lineLabel=QtWidgets.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,4)

            if i != 3:
                lineEdit = QtWidgets.QLineEdit()
                lineEdit.setText(rightInit[i])
                lineEdit.setValidator(isFloat)
                self.rightEdits.append(lineEdit)
                gridLayout.addWidget(lineEdit, i, 5)
            else:
                lineCombo = QtWidgets.QComboBox()
                lineCombo.addItem('None', 7)
                lineCombo.addItem('1 kΩ', 1)
                lineCombo.addItem('10 kΩ', 2)
                lineCombo.addItem('100 kΩ', 3)
                lineCombo.addItem('1 MΩ', 4)
                lineCombo.setCurrentIndex(0)
                self.rightEdits.append(lineCombo)
                gridLayout.addWidget(lineCombo, i, 5)

        gridLayout.addWidget(QtWidgets.QLabel("Pulse width progression"), 4, 4)
        self.pulsingModeCombo = QtWidgets.QComboBox()
        # you might wonder why we have different job numbers here. 14 is
        # the original formfinder which allowed only for geometric progression
        # of pulse widths. 141 is the newer version that also allows linear
        # pwsteps. Since FormFinder is a general use module the original
        # behaviour of the FormFinder module has been preserved in the
        # firmware. In order to maintain backwards compatibility with previous
        # firmwares (that only allow geometric pwsteps) the job number for this
        # option is set to the old one. Checks for 14 have also been made when
        # writing the experiment data to the uC. The core of the routine is
        # the same for both but for compatibility reasons we need to maintain
        # the old interface.
        self.pulsingModeCombo.addItem("Multiplicative", {"job": 14, "mode": 0})
        self.pulsingModeCombo.addItem("Linear", {"job": 141, "mode": 1})
        self.pulsingModeCombo.setCurrentIndex(0)
        self.pulsingModeCombo.currentIndexChanged.connect(self.pulsingModeComboIndexChanged)
        gridLayout.addWidget(self.pulsingModeCombo, 4, 5)

        self.checkNeg=QtWidgets.QCheckBox(self)
        self.checkNeg.setText("Negative amplitude?")
        gridLayout.addWidget(self.checkNeg,5,4)

        self.checkRthr=QtWidgets.QCheckBox(self)
        self.checkRthr.setText("Use Rthr (%)")
        gridLayout.addWidget(self.checkRthr,6,4)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

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

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

        self.registerPropertyWidget(self.leftEdits[0], "vmin")
        self.registerPropertyWidget(self.leftEdits[1], "vstep")
        self.registerPropertyWidget(self.leftEdits[2], "vmax")
        self.registerPropertyWidget(self.leftEdits[3], "pwmin")
        self.registerPropertyWidget(self.leftEdits[4], "pwstep")
        self.registerPropertyWidget(self.leftEdits[5], "pwmax")
        self.registerPropertyWidget(self.leftEdits[6], "interpulse")
        self.registerPropertyWidget(self.rightEdits[0], "numpulses")
        self.registerPropertyWidget(self.rightEdits[1], "threshold")
        self.registerPropertyWidget(self.rightEdits[2], "threshold_pc")
        self.registerPropertyWidget(self.rightEdits[3], "psr")
        self.registerPropertyWidget(self.pulsingModeCombo, "pulsemode")
        self.registerPropertyWidget(self.checkNeg, "negative")
        self.registerPropertyWidget(self.checkRthr, "useRthr")

    def pulsingModeComboIndexChanged(self, idx):
        data = self.pulsingModeCombo.itemData(idx)
        mode = data["mode"]

        if int(mode) == 1:
            self.leftLabels[4].setText("Pulse width step (us)")
        else:
            self.leftLabels[4].setText("Pulse width step (%)")

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def resizeWidget(self,event):
        pass

    def sendParams(self, job):
        polarity=1
        if (self.checkNeg.isChecked()):
            polarity=-1

        HW.ArC.write_b(job+"\n")   # sends the job

        pmodeIdx = self.pulsingModeCombo.currentIndex()
        pmode = self.pulsingModeCombo.itemData(pmodeIdx)["mode"]

        HW.ArC.write_b(str(float(self.leftEdits[0].text())*polarity)+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[1].text())*polarity)+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[2].text())*polarity)+"\n")

        time.sleep(0.05)

        HW.ArC.write_b(str(float(self.leftEdits[3].text())/1000000)+"\n")

        # Determine the step
        if job != "14": # modal formfinder
            if pmode == 1:
                # if step is time make it into seconds
                HW.ArC.write_b(str(float(self.leftEdits[4].text())/1000000)+"\n")
            else:
                # else it is percentage, leave it as is
                HW.ArC.write_b(str(float(self.leftEdits[4].text()))+"\n")
        else: # legacy behaviour
            HW.ArC.write_b(str(float(self.leftEdits[4].text()))+"\n")

        HW.ArC.write_b(str(float(self.leftEdits[5].text())/1000000)+"\n")

        HW.ArC.write_b(str(float(self.leftEdits[6].text())/1000)+"\n")
        time.sleep(0.05)

        HW.ArC.write_b(str(float(self.rightEdits[1].text()))+"\n")
        #HW.ArC.write_b(str(float(self.rightEdits[2].text()))+"\n")
        time.sleep(0.05)
        if self.checkRthr.isChecked():
            HW.ArC.write_b(str(float(self.rightEdits[2].text()))+"\n")
        else:
            HW.ArC.write_b(str(float(0))+"\n")
        time.sleep(0.05)

        if job != "14": # newer version of formfinder
            HW.ArC.write_b(str(int(pmode))+"\n")

        pSR = self.rightEdits[3].currentData()
        HW.ArC.write_b(str(int(pSR))+"\n")
        HW.ArC.write_b(str(int(self.rightEdits[0].text()))+"\n")
        time.sleep(0.05)

    def programDevs(self, devs):

        idx = self.pulsingModeCombo.currentIndex()
        job = self.pulsingModeCombo.itemData(idx)["job"]
        self.sendParams(str(job))

        wrapper = ThreadWrapper(devs)
        self.execute(wrapper, wrapper.run)

    def programOne(self):
        self.programDevs([[CB.word, CB.bit]])

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    @staticmethod
    def display(w, b, data, parent=None):

        siFormat = pyqtgraph.siFormat
        def _updateLinkedPlots(base, overlay):
            overlay.setGeometry(base.vb.sceneBoundingRect())
            overlay.linkedViewChanged(base.vb, overlay.XAxis)

        dialog = QtWidgets.QDialog(parent)

        containerLayout = QtWidgets.QVBoxLayout()
        dialog.setWindowTitle("FormFinder W=%d | B=%d" % (w, b))

        R = np.empty(len(data)-1)
        V = np.empty(len(data)-1)
        P = np.empty(len(data)-1)
        for (i, line) in enumerate(data[1:]):
            R[i] = line[0]
            V[i] = line[1]
            P[i] = line[2]

        Vidx = np.repeat(np.arange(0, len(R)), 2)

        gv = pyqtgraph.GraphicsLayoutWidget(show=False)
        Rplot = gv.addPlot(name="resistance")
        Rplot.plot(R, pen=pyqtgraph.mkPen('r', width=1), symbolPen=None,
            symbolBrush=(255,0,0), symbolSize=5, symbol='s')
        Rplot.showAxis('right')
        Rplot.getAxis('left').setLabel('Resistance', units='Ω')
        Rplot.getAxis('left').setStyle(tickTextWidth=40, autoExpandTextSpace=False)
        Rplot.getAxis('left').setGrid(50)
        Rplot.getAxis('bottom').setGrid(50)
        Rplot.getAxis('right').setWidth(40)
        Rplot.getAxis('right').setStyle(showValues=False)
        Rplot.getAxis('bottom').setLabel('Pulse')

        gv.nextRow()

        Vplot = gv.addPlot(name="voltage")
        Vplot.plot(V, pen=None, symbolPen=None, symbolBrush=(0,0,255),
            symbolSize=5, symbol='s', connect='pairs')
        Vplot.plot(Vidx, np.dstack((np.zeros(V.shape[0]), V)).flatten(),
            pen='b', symbolPen=None, symbolBrush=None, connect='pairs')
        Vplot.getAxis('left').setLabel('Voltage', units='V')
        Vplot.getAxis('left').setGrid(50)
        Vplot.getAxis('bottom').setGrid(50)
        Vplot.getAxis('left').setStyle(tickTextWidth=40, autoExpandTextSpace=False)
        Vplot.getAxis('bottom').setLabel('Pulse')
        Vplot.setXLink("resistance")

        Pview = pyqtgraph.ViewBox()
        Vplot.scene().addItem(Pview)
        Vplot.showAxis('right')
        Vplot.getAxis('right').setLabel('Pulse width', units='s')
        Pview.setXLink(Vplot)
        Vplot.getAxis('right').linkToView(Pview)
        Pview.enableAutoRange(Pview.XAxis, True)
        Pview.enableAutoRange(Pview.YAxis, True)

        _updateLinkedPlots(Vplot, Pview)
        Vplot.vb.sigResized.connect(partial(_updateLinkedPlots, base=Vplot, \
            overlay=Pview))

        Pplot = pyqtgraph.ScatterPlotItem(symbol='+')
        Pplot.setPen(pyqtgraph.mkPen(color=QtGui.QColor(QtCore.Qt.darkGreen), \
            width=1))
        Pplot.setBrush(pyqtgraph.mkBrush(color=QtGui.QColor(QtCore.Qt.darkGreen)))
        Pplot.setData(np.arange(0, len(data)-1), P)
        Pview.addItem(Pplot)

        containerLayout.addWidget(gv)

        saveButton = QtWidgets.QPushButton("Export data")
        saveCb = partial(functions.writeDelimitedData, np.column_stack((V, R, P)))
        saveButton.clicked.connect(partial(functions.saveFuncToFilename, saveCb,
            "Save data to...", parent))

        bottomLayout = QtWidgets.QHBoxLayout()
        labelText = 'Final resistance: %s recorded after a %s %s pulse' % \
            (siFormat(R[-1], suffix='Ω'), siFormat(V[-1], suffix='V'), \
                siFormat(P[-1], suffix='s'))
        bottomLayout.addWidget(QtWidgets.QLabel(labelText))
        bottomLayout.addItem(QtWidgets.QSpacerItem(40, 10,
            QtWidgets.QSizePolicy.Expanding))
        bottomLayout.addWidget(saveButton)

        containerLayout.addItem(bottomLayout)

        dialog.setLayout(containerLayout)

        return dialog


tags = { 'top': ModTag(tag, "FormFinder", FormFinder.display) }
