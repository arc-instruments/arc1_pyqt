####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys
import os
#import Queue

import time


import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="P"
g.tagDict.update({tag:"Pulse"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)

    def __init__(self,amplitude,pw):
        super(getData,self).__init__()
        self.amplitude=amplitude
        self.pw=pw

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

        ser=g.ser                   # simplify the namespace
        job="3"                     # define job
        ser.write(job+"\n")            # Send job followed by cell position and pulsing parameters
        ser.write(str(g.w)+"\n")
        ser.write(str(g.b)+"\n")

        ser.write(str(float(self.amplitude))+"\n")
        ser.write(str(float(self.pw))+"\n")

        # Read the value of M after the pulse
        currentline='%.0f' % float(ser.readline().rstrip())     # currentline contains the new Mnow value followed by 2 \n characters
        
        tag='P'
        self.sendData.emit(g.w,g.b,float(currentline),self.amplitude,self.pw,tag)

        #self.setM(g.w,g.b)

        self.displayData.emit()
        self.updateTree.emit(g.w,g.b)

        self.disableInterface.emit(False)
        
        self.finished.emit()

class Pulse(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(Pulse, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('Pulse')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Apply a voltage pulse.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()


        gridLayout=QtGui.QGridLayout()
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
        lineLeft=QtGui.QFrame()
        lineLeft.setFrameShape(QtGui.QFrame.VLine); 
        lineLeft.setFrameShadow(QtGui.QFrame.Raised);
        lineLeft.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 2, 1)

        self.pulse_V = QtGui.QLineEdit()
        self.pulse_pw = QtGui.QLineEdit()

        self.pulse_V.setStyleSheet(s.entryStyle)
        self.pulse_pw.setStyleSheet(s.entryStyle)

        # Initialise fields
        self.pulse_V.setText('1')
        self.pulse_pw.setText('100')

        # Apply an input mask to restrict the input to only numbers
        self.pulse_V.setValidator(isFloat)
        self.pulse_pw.setValidator(isFloat)

        self.pw_DropDown=QtGui.QComboBox()
        self.pw_DropDown.setStyleSheet(s.comboStylePulse)

        self.unitsFull=[['s',1],['ms',0.001],['us',0.000001],['ns',0.000000001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.pw_DropDown.insertItems(1,self.units)
        self.pw_DropDown.setCurrentIndex(2)


        VoltageLabel=QtGui.QLabel("V   @ ")

        gridLayout.addWidget(self.pulse_V,0,0)
        gridLayout.addWidget(VoltageLabel,0,1)
        gridLayout.addWidget(self.pulse_pw,0,3)
        gridLayout.addWidget(self.pw_DropDown,0,4)

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtGui.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtGui.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scrlArea.installEventFilter(self)

        vbox1.addWidget(scrlArea)
        vbox1.addStretch()

        if self.short==False:
            self.hboxProg=QtGui.QHBoxLayout()

            push_single=QtGui.QPushButton('Apply to One')
            push_range=QtGui.QPushButton('Apply to Range')
            push_all=QtGui.QPushButton('Apply to All')

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
            if isinstance(item, QtGui.QLineEdit):
                layoutWidgets.append([i,'QLineEdit', item.text()])
            if isinstance(item, QtGui.QComboBox):
                layoutWidgets.append([i,'QComboBox', item.currentIndex()])
            if isinstance(item, QtGui.QCheckBox):
                layoutWidgets.append([i,'QCheckBox', item.checkState()])

        
        #self.setPanelParameters(layoutWidgets)
        return layoutWidgets

    def setPanelParameters(self, layoutWidgets):
        for i,type,value in layoutWidgets:
            if type=='QLineEdit':
                print i, type, value
                self.gridLayout.itemAt(i).widget().setText(value)
            if type=='QComboBox':
                print i, type, value
                self.gridLayout.itemAt(i).widget().setCurrentIndex(value)
            if type=='QCheckBox':
                print i, type, value
                self.gridLayout.itemAt(i).widget().setChecked(value)


    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def programOne(self):

        #every=float(self.leftEdits[0].text())*60
        #duration=float(self.leftEdits[1].text())*60

        self.thread=QtCore.QThread()
        self.getData=getData(self.amplitude, self.pw)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.cast)

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

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Pulse()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 