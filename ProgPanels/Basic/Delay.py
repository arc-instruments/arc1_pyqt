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

tag="DEL"
g.tagDict.update({tag:"Delay"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    disableInterface=QtCore.pyqtSignal(bool)

    def __init__(self,delay):
        super(getData,self).__init__()
        self.delay=delay

    def getIt(self):

        self.disableInterface.emit(True)

        time.sleep(self.delay)

        self.disableInterface.emit(False)
        
        self.finished.emit()

class Delay(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(Delay, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('Delay')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('A time delay.')
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


        # ========== ComboBox ===========
        
        self.delay_mag=QtGui.QLineEdit()
        self.delay_mag.setValidator(isFloat)
        self.delay_mag.setText("1")
        self.delay_DropDown=QtGui.QComboBox()
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
        self.extractParams()
        self.thread=QtCore.QThread()
        self.getData=getData(self.delay)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.disableInterface.connect(f.interfaceAntenna.cast)

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

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Delay()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 