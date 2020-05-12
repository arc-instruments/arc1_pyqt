####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag = "EN"


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

            HW.ArC.write_b(str(int(w))+"\n")
            HW.ArC.write_b(str(int(b))+"\n")

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


class Endurance(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title="Endurance",\
                description="Cycle the resistive state of a bistable device "
                "using alternating polarity voltage pulses", short=short)
        self.short=short
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

        leftLabels=['Positive pulse amplitude (V)',\
                    'Positive pulse width (us)', \
                    'Positive current cut-off (uA)', \
                    'No. of positive pulses',\
                    'Cycles',\
                    'Interpulse time (ms)']

        rightLabels=['Negative pulse amplitude (V)',\
                    'Negative pulse width (us)', \
                    'Negative current cut-off (uA)', \
                    'No. of negative pulses']

        leftInit=  ['1',\
                    '100', \
                    '0',\
                    '1',\
                    '10',\
                    '0']

        rightInit=  ['1',\
                    '100',\
                    '0',\
                    '1']

        self.leftEdits=[]
        self.rightEdits=[]

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

        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 6, 1)

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
            lineEdit.setText(rightInit[i])
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

        self.leftEdits[2].editingFinished.connect(self.imposeLimitsOnCS_p)
        self.rightEdits[2].editingFinished.connect(self.imposeLimitsOnCS_n)
        self.leftEdits[1].editingFinished.connect(self.imposeLimitsOnPW_p)
        self.rightEdits[1].editingFinished.connect(self.imposeLimitsOnPW_n)

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

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

    # if pw is set to below 30us and current cut-off is activated, increase
    # pulse width to 30us
    def imposeLimitsOnPW_p(self):
        if float(self.leftEdits[2].text())!=0 and float(self.leftEdits[1].text())<30:
            self.leftEdits[1].setText("30")

    # if pw is set to below 30us and current cut-off is activated, increase
    # pulse width to 30us
    def imposeLimitsOnPW_n(self):
        if float(self.rightEdits[2].text())!=0 and float(self.rightEdits[1].text())<30:
            self.rightEdits[1].setText("30")

    # if current cut-off is set, make sure values are between 10 and 1000 uA.
    # Also, increase pw to a minimum of 30 us.
    def imposeLimitsOnCS_p(self):
        currentText=float(self.leftEdits[2].text())
        if currentText!=0:
            if currentText<10:
                self.leftEdits[2].setText("10")
            if currentText>1000:
                self.leftEdits[2].setText("1000")
            if float(self.leftEdits[1].text())<30:
                self.leftEdits[1].setText("30")

    # if current cut-off is set, make sure values are between 10 and 1000 uA.
    # Also, increase pw to a minimum of 30 us.
    def imposeLimitsOnCS_n(self,):
        currentText=float(self.rightEdits[2].text())
        if currentText!=0:
            if currentText<10:
                self.rightEdits[2].setText("10")
            if currentText>1000:
                self.rightEdits[2].setText("1000")
            if float(self.leftEdits[1].text())<30:
                self.rightEdits[1].setText("30")

    def extractPanelParameters(self):

        layoutItems=[[i,self.gridLayout.itemAt(i).widget()] for i in range(self.gridLayout.count())]
        layoutWidgets=[]

        for i,item in layoutItems:
            if isinstance(item, QtWidgets.QLineEdit):
                layoutWidgets.append([i,'QLineEdit', item.text()])
            if isinstance(item, QtWidgets.QComboBox):
                layoutWidgets.append([i,'QComboBox', item.currentIndex()])
            if isinstance(item, QtWidgets.QCheckBox):
                layoutWidgets.append([i,'QCheckBox', item.checkState()])

        return layoutWidgets

    def setPanelParameters(self, layoutWidgets):
        for i,type,value in layoutWidgets:
            if type=='QLineEdit':
                self.gridLayout.itemAt(i).widget().setText(value)
            if type=='QComboBox':
                self.gridLayout.itemAt(i).widget().setCurrentIndex(value)
            if type=='QCheckBox':
                self.gridLayout.itemAt(i).widget().setChecked(value)

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def sendParams(self):
        # positive amplitude
        HW.ArC.write_b(str(float(self.leftEdits[0].text()))+"\n")
        # positive pw
        HW.ArC.write_b(str(float(self.leftEdits[1].text())/1000000)+"\n")
        # positive cut-off
        HW.ArC.write_b(str(float(self.leftEdits[2].text())/1000000)+"\n")
        # negative amplitude
        HW.ArC.write_b(str(float(self.rightEdits[0].text())*-1)+"\n")
        # negative pw
        HW.ArC.write_b(str(float(self.rightEdits[1].text())/1000000)+"\n")
        # negative cut-off
        HW.ArC.write_b(str(float(self.rightEdits[2].text())/1000000)+"\n")
        # interpulse
        HW.ArC.write_b(str(float(self.leftEdits[5].text()))+"\n")

        # positive number of pulses
        HW.ArC.write_b(str(int(self.leftEdits[3].text()))+"\n")
        # negative number of pulses
        HW.ArC.write_b(str(int(self.rightEdits[3].text()))+"\n")
        # cycles
        HW.ArC.write_b(str(int(self.leftEdits[4].text()))+"\n")

    def programOne(self):
        self.programDevs([[CB.word, CB.bit]])

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def programDevs(self, devs):

        job="191"
        HW.ArC.write_b(job+"\n")
        self.sendParams()

        wrapper = ThreadWrapper(devs)
        self.execute(wrapper, wrapper.run)

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


tags = { 'top': ModTag(tag, "Endurance", None) }
