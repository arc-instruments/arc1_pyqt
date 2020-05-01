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
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="DEL"
g.tagDict.update({tag:"Delay"})


class ThreadWrapper(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    disableInterface=QtCore.pyqtSignal(bool)

    def __init__(self,delay):
        super().__init__()
        self.delay=delay

    def run(self):

        self.disableInterface.emit(True)

        time.sleep(self.delay)

        self.disableInterface.emit(False)

        self.finished.emit()


class Delay(QtWidgets.QWidget):
    
    def __init__(self, short=False):
        super().__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('Delay')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('A time delay.')
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


        # ========== ComboBox ===========
        
        self.delay_mag=QtWidgets.QLineEdit()
        self.delay_mag.setValidator(isFloat)
        self.delay_mag.setText("1")
        self.delay_DropDown=QtWidgets.QComboBox()
        self.delay_DropDown.setStyleSheet(s.comboStylePulse)

        self.unitsFull=[['s',1],['ms',0.001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.delay_DropDown.insertItems(1,self.units)
        self.delay_DropDown.setCurrentIndex(2)


        gridLayout.addWidget(self.delay_mag,0,0)
        gridLayout.addWidget(self.delay_DropDown,0,1)

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
        self.extractParams()
        self.thread=QtCore.QThread()
        self.threadWrapper=ThreadWrapper(self.delay)
        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.disableInterface.connect(f.interfaceAntenna.cast)
        self.thread.finished.connect(f.interfaceAntenna.wakeUp)

        self.thread.start()


    def extractParams(self):
        duration=float(self.delay_mag.text())
        unit=float(self.multiply[self.delay_DropDown.currentIndex()])        
        self.delay=duration*unit

        if self.delay<0.01:
            self.delay_mag.setText(str(10))
            self.delay_DropDown.setCurrentIndex(1)
            self.delay=0.01
        if self.delay>10:
            self.delay_mag.setText(str(10))
            self.delay_DropDown.setCurrentIndex(0)
            self.delay=10

