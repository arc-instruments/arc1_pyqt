####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys

import time


import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="Read"
g.tagDict.update({tag:"Read"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)

    def __init__(self, Vread, readType):
        super(getData,self).__init__()
        self.Vread=Vread
        self.readType=readType

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

        needsUpdate=False
        if self.Vread!=g.Vread or self.readType!=g.readOption:
            needsUpdate=True
            # Update Read
            job='01'
            g.ser.write(job+"\n")
            g.ser.write(str(self.readType)+"\n")
            g.ser.write(str(self.Vread)+"\n")       

        job="1"
        g.ser.write(job+"\n")
        g.ser.write(str(g.w)+"\n")
        g.ser.write(str(g.b)+"\n")

        # try:
        #     currentline='%.10f' % float(g.ser.readline().rstrip())     # currentline contains the new Mnow value followed by 2 \n characters
        # except ValueError:
        #     currentline='%.10f' % 0.0

        Mnow=f.getFloats(1)

        tag='S R'+str(self.readType)+' V='+str(self.Vread)
        self.sendData.emit(g.w,g.b,Mnow,float(self.Vread),0,tag)

        self.displayData.emit()
        self.updateTree.emit(g.w,g.b)


        if needsUpdate==True:
            # Update Read
            job='01'
            g.ser.write(job+"\n")
            g.ser.write(str(g.readOption)+"\n")
            g.ser.write(str(g.Vread)+"\n") 

        self.disableInterface.emit(False)
        
        self.finished.emit()


class READ(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(READ, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      
        self.Vread=g.Vread
        self.readOption=g.readOption

        vbox1=QtGui.QVBoxLayout()
        hbox1=QtGui.QHBoxLayout()

        titleLabel = QtGui.QLabel('READ')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Apply a READ operation.')
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
        self.combo_readType=QtGui.QComboBox()
        self.combo_readType.setStyleSheet(s.comboStyle)
        self.combo_readType.insertItems(1,g.readOptions)
        self.combo_readType.currentIndexChanged.connect(self.updateReadType)
        self.combo_readType.setCurrentIndex(2)
        #g.readOption=combo_readType.currentIndex()

        self.read_voltage=QtGui.QDoubleSpinBox()
        #read_voltage.setHeight(25)
        self.read_voltage.setStyleSheet(s.spinStyle)
        self.read_voltage.setMinimum(-12)
        self.read_voltage.setMaximum(12)
        self.read_voltage.setSingleStep(0.05)
        self.read_voltage.setValue(0.5)
        self.read_voltage.setSuffix(' V')
        self.read_voltage.valueChanged.connect(self.setVread)     

        #hbox1.addWidget(self.combo_readType)
        #hbox1.addWidget(self.read_voltage)   

        gridLayout.addWidget(self.combo_readType,0,0)
        gridLayout.addWidget(self.read_voltage,0,1)
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
            if isinstance(item, QtGui.QDoubleSpinBox):
                layoutWidgets.append([i,'QDoubleSpinBox', item.value()])

        
        #self.setPanelParameters(layoutWidgets)
        return layoutWidgets

    def setPanelParameters(self, layoutWidgets):
        for i,w_type,value in layoutWidgets:
            if w_type=='QLineEdit':
                print i, w_type, value
                self.gridLayout.itemAt(i).widget().setText(value)
            if w_type=='QComboBox':
                print i, w_type, value
                self.gridLayout.itemAt(i).widget().setCurrentIndex(value)
            if w_type=='QCheckBox':
                print i, w_type, value
                self.gridLayout.itemAt(i).widget().setChecked(value)
            if w_type=='QDoubleSpinBox':
                self.gridLayout.itemAt(i).widget().setValue(value)

    def setVread(self, value):
        self.Vread=value

    def updateReadType(self, value):
        self.readOption=value

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False


    def programOne(self):

        self.thread=QtCore.QThread()
        self.getData=getData(self.Vread, self.readOption)
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
        self.thread.finished.connect(f.interfaceAntenna.wakeUp)

        self.thread.start()

    def updateRead(self):
        job='01'
        g.ser.write(job+"\n")
        g.ser.write(str(g.readOption)+"\n")
        
        g.ser.write(str(g.Vread)+"\n")


        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = READ()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 