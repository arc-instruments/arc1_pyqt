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

tag="SS2"
g.tagDict.update({tag:"SwitchSeeker*"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)

    def __init__(self,deviceList):
        super(getData,self).__init__()
        self.deviceList=deviceList

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

        g.ser.write(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write(str(int(w))+"\n")
            g.ser.write(str(int(b))+"\n")

            firstPoint=1
            endCommand=0

            valuesNew=f.getFloats(3)
            #valuesNew.append(float(g.ser.readline().rstrip()))
            #valuesNew.append(float(g.ser.readline().rstrip()))
            #valuesNew.append(float(g.ser.readline().rstrip()))

            if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                tag_=tag+'_s'
            else:
                endCommand=1;

            while(endCommand==0):
                valuesOld=valuesNew

                valuesNew=f.getFloats(3)
                #valuesNew.append(float(g.ser.readline().rstrip()))
                #valuesNew.append(float(g.ser.readline().rstrip()))
                #valuesNew.append(float(g.ser.readline().rstrip()))

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

        self.disableInterface.emit(False)
        
        self.finished.emit()


class SwitchSeeker(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(SwitchSeeker, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('SwitchSeeker')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('State-of-art analogue resistive switching parameter finder.')
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

        gridLayout=QtGui.QGridLayout()
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
        lineLeft=QtGui.QFrame()
        lineLeft.setFrameShape(QtGui.QFrame.VLine); 
        lineLeft.setFrameShadow(QtGui.QFrame.Raised);
        lineLeft.setLineWidth(1)
        lineRight=QtGui.QFrame()
        lineRight.setFrameShape(QtGui.QFrame.VLine); 
        lineRight.setFrameShadow(QtGui.QFrame.Raised);
        lineRight.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 10, 1)
        if self.short==False:
            gridLayout.addWidget(lineRight, 0, 6, 10, 1)


        for i in range(len(leftLabels)):
            lineLabel=QtGui.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        for i in range(len(rightLabels)):
            lineLabel=QtGui.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,4)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

        self.checkRead=QtGui.QCheckBox(self)
        self.checkRead.setText("Read after pulse?")
        gridLayout.addWidget(self.checkRead,3,4)

        gridLayout.addWidget(QtGui.QLabel("Seeker algorithm"),0,4)
        self.modeSelectionCombo=QtGui.QComboBox()
        # SwitchSeeker_1 has id 15
        self.modeSelectionCombo.addItem("Fast",15)
        # SwitchSeeker_2 has id 152
        self.modeSelectionCombo.addItem("Slow",152)
        gridLayout.addWidget(self.modeSelectionCombo,0,5)

        gridLayout.addWidget(QtGui.QLabel("Stage II polarity"),1,4)
        self.polarityCombo=QtGui.QComboBox()
        self.polarityCombo.addItem("(+) Positive",1)
        self.polarityCombo.addItem("(-) Negative",-1)
        self.polarityCombo.setEnabled(False)
        gridLayout.addWidget(self.polarityCombo,1,5)

        self.skipICheckBox=QtGui.QCheckBox(self)
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

        self.gridLayout=gridLayout
        self.extractPanelParameters()
        self.setLayout(vbox1)

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

    def sendParams(self):
        g.ser.write(str(float(self.leftEdits[2].text())/1000)+"\n")
        g.ser.write(str(float(self.leftEdits[3].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[4].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[5].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[8].text())/1000)+"\n")
        g.ser.write(str(float(self.leftEdits[9].text()))+"\n")
        time.sleep(0.01)
        g.ser.write(str(int(self.leftEdits[0].text()))+"\n")
        g.ser.write(str(int(self.leftEdits[1].text()))+"\n")
        g.ser.write(str(int(self.leftEdits[6].text()))+"\n")
        g.ser.write(str(int(self.leftEdits[7].text()))+"\n")
        g.ser.write(str(int(self.checkRead.isChecked()))+"\n")

        # Check if Stage I should be skipped
        if self.skipICheckBox.isChecked():
            # -1 or 1 are the QVariants available from the combobox
            # -1 -> negative polarity for Stage II
            #  1 -> positive polarity for Stage II
            polarityIndex = self.polarityCombo.currentIndex()
            skipStageI = str(self.polarityCombo.itemData(polarityIndex).toInt()[0])
        else:
            # if 0 then Stage I will not be skipped
            skipStageI = str(0)

        g.ser.write(skipStageI+"\n")

    def programOne(self):
        if g.ser.port != None:
            job="%d"%self.getJobCode()
            g.ser.write(job+"\n")   # sends the job
            print self.getJobCode()

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData([[g.w,g.b]])
            self.finalise_thread_initialisation()

            self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def programRange(self):
        if g.ser.port != None:

            rangeDev=self.makeDeviceList(True)

            job="%d"%self.getJobCode()
            g.ser.write(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev)
            self.finalise_thread_initialisation()

            self.thread.start()  

    def programAll(self):
        if g.ser.port != None:
            rangeDev=self.makeDeviceList(False)

            job="%d"%self.getJobCode()
            g.ser.write(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev)
            self.finalise_thread_initialisation()

            self.thread.start()

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


    def makeDeviceList(self,isRange):
        #if g.checkSA=False:
        rangeDev=[] # initialise list which will contain the SA devices contained in the user selected range of devices
        #rangeMax=0;
        if isRange==False:
            minW=1
            maxW=g.wline_nr
            minB=1
            maxB=g.bline_nr
        else:
            minW=g.minW
            maxW=g.maxW
            minB=g.minB
            maxB=g.maxB            


        # Find how many SA devices are contained in the range
        if g.checkSA==False:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    rangeDev.append([w,b])
            #rangeMax=(wMax-wMin+1)*(bMax-bMin+1)
        else:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    for cell in g.customArray:
                        if (cell[0]==w and cell[1]==b):
                            rangeDev.append(cell)

        return rangeDev
        
    def getJobCode(self):
        job=self.modeSelectionCombo.itemData(self.modeSelectionCombo.currentIndex())
        return job

