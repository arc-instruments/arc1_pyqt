####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see License.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="FF"
g.tagDict.update({tag:"FormFinder"})

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
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))

            if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                tag_=tag+'_s'
            else:
                endCommand=1;

            while(endCommand==0):
                valuesOld=valuesNew

                valuesNew=f.getFloats(3)
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))

                if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                    self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                    self.displayData.emit()
                    tag_=tag+'_i'
                else:
                    tag_=tag+'_e'
                    self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                    self.displayData.emit()
                    endCommand=1

                #print " "
                #print valuesNew
                #print "End command " + str(endCommand)
            self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        
        self.finished.emit()


class FormFinder(QtWidgets.QWidget):
    
    def __init__(self, short=False):
        super(FormFinder, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('FormFinder')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Applies a pulsed voltage ramp. Can be utilised when electroforming.')
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
                    'pSR 1-1k, 4-1M, 7-short']
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
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine);
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised);
        lineLeft.setLineWidth(1)
        lineRight=QtWidgets.QFrame()
        lineRight.setFrameShape(QtWidgets.QFrame.VLine);
        lineRight.setFrameShadow(QtWidgets.QFrame.Raised);
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

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(rightInit[i])
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

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

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

    def pulsingModeComboIndexChanged(self, idx):
        data = self.pulsingModeCombo.itemData(idx)
        mode = data["mode"]

        if int(mode) == 1:
            self.leftLabels[4].setText("Pulse width step (us)")
        else:
            self.leftLabels[4].setText("Pulse width step (%)")

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

    def resizeWidget(self,event):
        pass

    def sendParams(self, job):
        polarity=1
        if (self.checkNeg.isChecked()):
            polarity=-1

        g.ser.write(job+"\n")   # sends the job

        pmodeIdx = self.pulsingModeCombo.currentIndex()
        pmode = self.pulsingModeCombo.itemData(pmodeIdx)["mode"]

        g.ser.write(str(float(self.leftEdits[0].text())*polarity)+"\n")
        g.ser.write(str(float(self.leftEdits[1].text())*polarity)+"\n")
        g.ser.write(str(float(self.leftEdits[2].text())*polarity)+"\n")

        time.sleep(0.05)

        g.ser.write(str(float(self.leftEdits[3].text())/1000000)+"\n")

        # Determine the step
        if job != "14": # modal formfinder
            if pmode == 1:
                # if step is time make it into seconds
                g.ser.write(str(float(self.leftEdits[4].text())/1000000)+"\n")
            else:
                # else it is percentage, leave it as is
                g.ser.write(str(float(self.leftEdits[4].text()))+"\n")
        else: # legacy behaviour
            g.ser.write(str(float(self.leftEdits[4].text()))+"\n")

        g.ser.write(str(float(self.leftEdits[5].text())/1000000)+"\n")

        g.ser.write(str(float(self.leftEdits[6].text())/1000)+"\n")
        time.sleep(0.05)
        
        g.ser.write(str(float(self.rightEdits[1].text()))+"\n")
        #g.ser.write(str(float(self.rightEdits[2].text()))+"\n")
        time.sleep(0.05)
        if self.checkRthr.isChecked():
            g.ser.write(str(float(self.rightEdits[2].text()))+"\n")
        else:
            g.ser.write(str(float(0))+"\n")
        time.sleep(0.05)

        if job != "14": # newer version of formfinder
            g.ser.write(str(int(pmode))+"\n")

        g.ser.write(str(int(self.rightEdits[3].text()))+"\n")
        g.ser.write(str(int(self.rightEdits[0].text()))+"\n")
        time.sleep(0.05)

    def programOne(self):
        if g.ser.port != None:
            idx = self.pulsingModeCombo.currentIndex()
            job = self.pulsingModeCombo.itemData(idx)["job"]
            self.sendParams(str(job))

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

            idx = self.pulsingModeCombo.currentIndex()
            job = self.pulsingModeCombo.itemData(idx)["job"]
            self.sendParams(str(job))

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev)
            self.finalise_thread_initialisation()

            self.thread.start()

    def programAll(self):
        if g.ser.port != None:
            rangeDev=self.makeDeviceList(False)

            idx = self.pulsingModeCombo.currentIndex()
            job = self.pulsingModeCombo.itemData(idx)["job"]
            self.sendParams(str(job))

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

