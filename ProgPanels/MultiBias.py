####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys
import os
import time

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="MB"
g.tagDict.update({tag:"MultiBias"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    updateCurrentRead=QtCore.pyqtSignal(float)

    def __init__(self, wLines, bLine, RW, V, pw):
        super(getData,self).__init__()
        self.wLines=wLines
        self.bLine=bLine
        self.RW=RW
        self.V=V;
        self.pw=pw;

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

        if (self.RW==1): # READ operation
            valuesNew=f.getFloats(3)
            current=valuesNew[1]/valuesNew[0]
            self.updateCurrentRead.emit(current)

        if (self.RW==2):
            for device in range(1,g.wline_nr+1):
                valuesNew=f.getFloats(3)
                self.sendData.emit(device,self.bLine,valuesNew[0],valuesNew[1],valuesNew[2],"MB")

            for device in range(1,g.wline_nr+1):
                valuesNew=f.getFloats(3)
                if device in self.wLines:
                    self.sendData.emit(device,self.bLine,valuesNew[0],self.V,self.pw,"P")
                else:
                    self.sendData.emit(device,self.bLine,valuesNew[0],self.V/2,self.pw,"P")
                self.updateTree.emit(device,self.bLine)

        self.disableInterface.emit(False)
        self.finished.emit()


class MultiBias(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(MultiBias, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('MultiBias')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Apply WRITE or READ pulses to multiple active wordlines. Read from one bitline.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['WRITE amplitude (V)', \
                    'WRITE pulse width (us)',\
                    'READ voltage (V)']

        rightLabels=[]

        leftInit=  ['1',\
                    '100', \
                    '0.5']

        rightInit=  []

        self.leftEdits=[]
        self.rightEdits=[]

        gridLayout=QtGui.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,3)
        gridLayout.setColumnStretch(3,5)

        if self.short==False:
            gridLayout.setColumnStretch(7,2)
        #gridLayout.setSpacing(2)

        #setup a line separator
        lineLeft=QtGui.QFrame()
        lineLeft.setFrameShape(QtGui.QFrame.VLine); 
        lineLeft.setFrameShadow(QtGui.QFrame.Raised);
        lineLeft.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 6, 1)

        label_wlines=QtGui.QLabel("Active Wordlines")
        self.edit_wlines=QtGui.QLineEdit("1 2")

        label_blines=QtGui.QLabel("Active Bitline")
        self.edit_blines=QtGui.QSpinBox()
        self.edit_blines.setRange(1,32)
        self.edit_blines.setSingleStep(1)
        self.edit_blines.setValue(1)

        label_current=QtGui.QLabel("Current on Active Bitline:")
        label_suffix=QtGui.QLabel("uA")

        self.edit_current=QtGui.QLineEdit("0")
        self.edit_current.setReadOnly(True)

        gridLayout.addWidget(label_wlines,0,0)
        gridLayout.addWidget(self.edit_wlines,0,1)
        gridLayout.addWidget(label_blines,1,0)
        gridLayout.addWidget(self.edit_blines,1,1)

        gridLayout.addWidget(label_current,0,3)
        gridLayout.addWidget(self.edit_current,1,3)
        gridLayout.addWidget(label_suffix,1,4)


        for i in range(len(leftLabels)):
            lineLabel=QtGui.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i+2,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i+2,1)

        for i in range(len(rightLabels)):
            lineLabel=QtGui.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i+2,4)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(rightInit[i])
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i+2,5)

        # verticalLine.setFrameStyle(QFrame.VLine)
        # verticalLine.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Expanding)

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

            push_write=QtGui.QPushButton('WRITE')
            push_read=QtGui.QPushButton('READ')

            push_write.setStyleSheet(s.btnStyle)
            push_read.setStyleSheet(s.btnStyle)

            push_write.clicked.connect(self.apply_write)
            push_read.clicked.connect(self.apply_read)

            self.hboxProg.addWidget(push_write)
            self.hboxProg.addWidget(push_read)

            vbox1.addLayout(self.hboxProg)

        self.setLayout(vbox1)
        self.gridLayout=gridLayout


    def apply_multiBias(self, RW):
        wLines=self.extract_wordlines()
        if wLines==False:
            self.throwError()
        else:
            if g.ser.port != None:
                job="50"
                g.ser.write(job+"\n")   # sends the job

                self.sendParams()

                g.ser.write(str(len(wLines))+"\n")
                g.ser.write(str(self.edit_blines.value())+"\n")
                g.ser.write(str(RW)+"\n")

                for nr in wLines:
                    g.ser.write(str(nr)+"\n")


                self.thread=QtCore.QThread()
                self.getData=getData(wLines, int(self.edit_blines.value()), RW, float(self.leftEdits[0].text()), float(self.leftEdits[1].text())/1000000)
                self.finalise_thread_initialisation()

                self.thread.start()

    def sendParams(self):
        g.ser.write(str(float(self.leftEdits[0].text()))+"\n")              # send positive amplitude
        g.ser.write(str(float(self.leftEdits[1].text())/1000000)+"\n")      # send positive pw
        g.ser.write(str(float(self.leftEdits[2].text()))+"\n")              # send read Voltage


    def apply_write(self):
        self.apply_multiBias(2)

    def apply_read(self):
        self.apply_multiBias(1)

    def extract_wordlines(self):
        wlines=[]
        try:
            wlines_txt=list(self.edit_wlines.text().split(" "))
            for nr in wlines_txt:
                w=int(nr)
                if w<1 or w>32:
                    return False
                else:
                    wlines.append(w)
            return wlines
        except:
            return False

    def updateCurrentRead(self, value):
        self.edit_current.setText(str(value*1000000))



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

        #time.sleep(0.001)

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def finalise_thread_initialisation(self):
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
        self.getData.updateCurrentRead.connect(self.updateCurrentRead) 


    def throwError(self):
        reply = QtGui.QMessageBox.question(self, "Error",
            "Formatting of active worlines input box is wrong. Check for double spaces, trailing spaces, and addresses larger than 32 or smaller than 1.",
            QtGui.QMessageBox.Ok)
        event.ignore()

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = MultiBias()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 