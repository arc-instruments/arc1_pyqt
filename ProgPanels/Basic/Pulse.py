####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
#import Queue

import time

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
from Globals.modutils import BaseThreadWrapper
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="P"
g.tagDict.update({tag:"Pulse"})


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, amplitude, pw):
        super().__init__()
        self.amplitude=amplitude
        self.pw=pw

    @BaseThreadWrapper.runner
    def run(self):

        global tag

        ser=g.ser                   # simplify the namespace
        job="3"                     # define job
        ser.write_b(job+"\n")            # Send job followed by cell position and pulsing parameters
        ser.write_b(str(g.w)+"\n")
        ser.write_b(str(g.b)+"\n")

        ser.write_b(str(float(self.amplitude))+"\n")
        ser.write_b(str(float(self.pw))+"\n")

        # Read the value of M after the pulse
        Mnow=f.getFloats(1)
        tag='P'
        self.sendData.emit(g.w,g.b,Mnow,self.amplitude,self.pw,tag)

        #self.setM(g.w,g.b)

        self.displayData.emit()
        self.updateTree.emit(g.w,g.b)


class Pulse(QtWidgets.QWidget):
    
    def __init__(self, short=False):
        super().__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('Pulse')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Apply a voltage pulse.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()


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

        gridLayout.addWidget(lineLeft, 0, 2, 2, 1)

        self.pulse_V = QtWidgets.QLineEdit()
        self.pulse_pw = QtWidgets.QLineEdit()

        self.pulse_V.setStyleSheet(s.entryStyle)
        self.pulse_pw.setStyleSheet(s.entryStyle)

        # Initialise fields
        self.pulse_V.setText('1')
        self.pulse_pw.setText('100')

        # Apply an input mask to restrict the input to only numbers
        self.pulse_V.setValidator(isFloat)
        self.pulse_pw.setValidator(isFloat)

        self.pw_DropDown=QtWidgets.QComboBox()
        self.pw_DropDown.setStyleSheet(s.comboStylePulse)

        self.unitsFull=[['s',1],['ms',0.001],['us',0.000001],['ns',0.000000001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.pw_DropDown.insertItems(1,self.units)
        self.pw_DropDown.setCurrentIndex(2)


        VoltageLabel=QtWidgets.QLabel("V   @ ")

        gridLayout.addWidget(self.pulse_V,0,0)
        gridLayout.addWidget(VoltageLabel,0,1)
        gridLayout.addWidget(self.pulse_pw,0,3)
        gridLayout.addWidget(self.pw_DropDown,0,4)

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

            push_single=QtWidgets.QPushButton('Apply to One')
            push_range=QtWidgets.QPushButton('Apply to Range')
            push_all=QtWidgets.QPushButton('Apply to All')

            push_single.setStyleSheet(s.btnStyle)
            push_range.setStyleSheet(s.btnStyle)
            push_all.setStyleSheet(s.btnStyle)

            push_single.clicked.connect(self.programOne)
            push_range.clicked.connect(self.programRange)
            push_all.clicked.connect(self.programAll)

            self.hboxProg.addWidget(push_single)
            self.hboxProg.addWidget(push_range)
            self.hboxProg.addWidget(push_all)

            vbox1.addLayout(self.hboxProg)

        self.extractParams()

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

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

        
        #self.setPanelParameters(layoutWidgets)
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

    def programOne(self):

        #every=float(self.leftEdits[0].text())*60
        #duration=float(self.leftEdits[1].text())*60
        self.extractParams()
        self.thread=QtCore.QThread()
        self.threadWrapper=ThreadWrapper(self.amplitude, self.pw)
        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.sendData.connect(f.updateHistory)
        self.threadWrapper.highlight.connect(f.cbAntenna.cast)
        self.threadWrapper.displayData.connect(f.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.cast)
        self.thread.finished.connect(f.interfaceAntenna.wakeUp)

        self.thread.start()


    def extractParams(self):
        self.amplitude=float(self.pulse_V.text())
        duration=float(self.pulse_pw.text())
        unit=float(self.multiply[self.pw_DropDown.currentIndex()])        
        self.pw=duration*unit

        if self.pw<0.00000009:
            self.pulse_pw.setText(str(90))
            self.pw_DropDown.setCurrentIndex(3)
            self.pw=0.00000009
        if self.pw>10:
            self.pulse_pw.setText(str(10))
            self.pw_DropDown.setCurrentIndex(0)
            self.pw=10

