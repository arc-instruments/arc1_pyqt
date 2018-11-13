from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import scipy.optimize as opt
import scipy.stats as stat
import numpy as np

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="VOL"
g.tagDict.update({tag:"VolatilityMeas"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    changeArcStatus=QtCore.pyqtSignal(str)

    def __init__(self, deviceList, A, pw, B, stopTime, stopConf, stopTol, stopOpt):
        super(getData,self).__init__()
        self.A=A
        self.pw=pw
        self.B=B
        self.stopTime=stopTime
        self.stopConf=stopConf
        self.deviceList=deviceList
        self.stopOpt = stopOpt
        self.stopTol = stopTol
        self.ttestsamp = 25 #No. of samples at the beginning and at the end of the batch to be taken for t-test.

    def getIt(self):

        self.disableInterface.emit(True)
        self.changeArcStatus.emit('Busy')
        global tag

        g.ser.write_b(str(int(len(self.deviceList)))+"\n")

        #Stop condition preparation area.
        linfit = lambda x, a, b: a * x + b #Define linear fitter.
        xline = range(self.B) #Define x-axis values.
        initguess = [0.0, 0.0]

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write_b(str(int(w))+"\n")
            g.ser.write_b(str(int(b))+"\n")

            Mnow=float(g.ser.readline().rstrip())   # get first read value
            self.sendData.emit(w,b,Mnow,self.A,self.pw,tag+'_s')

            start=time.time()
            stop=0

            while stop==0:
                #Prepare for batch processing.
                values = [] #Reset batch result array contents.

                for i in range(self.B): #Obtain data for entire batch.
                    #Send data to log-file.
                    dataTime=int(g.ser.readline().rstrip())
                    Mnow=float(g.ser.readline().rstrip())
                    self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_i_ '+ str(dataTime))

                    #Hold all or portion of incoming data in temporary array.
                    values.append(Mnow)

                    #Update display.
                    #self.displayData.emit()

                timeNow=time.time()

                # FIX TIME option - end volatility test after fixed time.
                if self.stopOpt == 'FixTime':
                    if (timeNow-start)>=self.stopTime:       # if more than stopTime has elapsed, do not request a new batch
                        stop=1
                        g.ser.write_b(str(int(stop))+"\n")
                    else:
                        stop=0
                        g.ser.write_b(str(int(stop))+"\n")

                elif self.stopOpt == 'LinearFit':
                    if self.B > 1: #Check that there are at least 2 points in batch, or no linear fit possible.
                        try: #Try computing linear fit.
                            fitres = opt.curve_fit(linfit, xline, values, initguess) #Compute linear fit.
                        except RuntimeError: #If that proves impossible...
                            fitres = [[0]] #...assign dummy value.
                            print('Error: Could not fit data to linear function within no. of iteration limits.')

                        linslope = fitres[0][0]*self.B #Obtain slope of linear fit on volatile data in units of %/batch.
                        relslope = linslope/np.mean(values) #Convert linear fit slope (Ohms/batch) into relative slope (%/batch)
                        print('Fitted resistive state slope: ' + str(relslope*100) + ' %/batch.')

                        if abs(relslope)<=self.stopTol or (timeNow-start)>=self.stopTime: # If the linear slope along the batch drops below certain magnitude, or time limit exceeded stop procedure.
                            stop=1
                            g.ser.write_b(str(int(stop))+"\n")
                        else:
                            stop=0
                            g.ser.write_b(str(int(stop))+"\n")

                    else: #If the batch is not large enough just end it there.
                        stop=1
                        g.ser.write_b(str(int(stop))+"\n")


                elif self.stopOpt == 'T-Test':
                    if self.B >= self.ttestsamp*2: #Check that the batch is actually large enough to carry out a stat-test.
                        tmet = abs(stat.ttest_ind(values[:self.ttestsamp], values[-self.ttestsamp:], equal_var = False)[0]) #Perform t-test on first & last N samples in batch, then get t-metric.
                        print('T-metric: ' + str(tmet))

                        if tmet < self.stopConf or (timeNow-start)>=self.stopTime: #If probability (loosely speaking) of null hypothesis being true is below our confidence tolerance...
                            #... stop requestiong batches. Also have a max time-check.
                            stop=1
                            g.ser.write_b(str(int(stop))+"\n")
                        else:
                            stop=0
                            g.ser.write_b(str(int(stop))+"\n")

                    else: #If the batch is not large enough just end it there.
                        stop=1
                        g.ser.write_b(str(int(stop))+"\n")
                        print('WARNING: Batch not long enough to support this oepration. Minimum batch length required is '+str(2*self.ttestsamp)+'.')

                #DEFAULT case - something went wrong so just stop the text after 1 batch.
                else:
                    stop=1
                    g.ser.write_b(str(int(stop))+"\n")

            Mnow=float(g.ser.readline().rstrip())   # get first read value
            self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_e')

            self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        self.changeArcStatus.emit('Ready')
        self.displayData.emit()
        
        self.finished.emit()


class VolatilityRead(QtWidgets.QWidget):
    
    def __init__(self, short=False):
        super(VolatilityRead, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('VolatilityRead')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Measurement protocol for volatile memristors.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Pulse Amplitude (V)', \
                    'Pulse Width (us)', \
                    'Read Batch Size (B)', \
                    'Average cycles/point M']

        self.leftEdits=[]

        rightLabels=['Stop time (s)', \
                    'Stop t-metric', \
                    'Stop Tol. (%/batch)']

        self.rightEdits=[]

        leftInit=  ['2', \
                    '100', \
                    '1000', \
                    '100']
        rightInit= ['10', \
                    '10', \
                    '10']

        # Setup the two combo boxes
        stopOptions=['LinearFit', 'T-Test', 'FixTime']
                    #     0     ,     1   ,     2

        self.combo_stopOptions=QtWidgets.QComboBox()
        self.combo_stopOptions.insertItems(1,stopOptions)
        self.combo_stopOptions.currentIndexChanged.connect(self.updateStopOptions)


        # Setup the two combo boxes
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

        gridLayout.addWidget(lineLeft, 0, 2, 5, 1)
        gridLayout.addWidget(lineRight, 0, 6, 5, 1)
        #gridLayout.addWidget(line,1,2)
        #gridLayout.addWidget(line,2,2)
        #gridLayout.addWidget(line,3,2)
        #gridLayout.addWidget(line,4,2)


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

        #Position the combo boxes and respective labels

        lineLabel=QtWidgets.QLabel()
        lineLabel.setText('Stop Option:')
        gridLayout.addWidget(lineLabel,3,4)

        gridLayout.addWidget(self.combo_stopOptions,3,5)

        # ==============================================

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        self.scrlArea=QtWidgets.QScrollArea()
        self.scrlArea.setWidget(self.vW)
        self.scrlArea.setContentsMargins(0,0,0,0)
        self.scrlArea.setWidgetResizable(False)
        self.scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.scrlArea.installEventFilter(self)

        vbox1.addWidget(self.scrlArea)
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
        self.vW.setFixedWidth(self.size().width())
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

    def updateStopOptions(self, event):
        if self.combo_stopOptions.currentText() == 'FixTime':
            self.rightEdits[0].setStyleSheet("border: 1px solid red;")
            self.rightEdits[1].setStyleSheet("border: 1px solid grey;")
            self.rightEdits[2].setStyleSheet("border: 1px solid grey;")
        elif self.combo_stopOptions.currentText() == 'LinearFit':
            self.rightEdits[0].setStyleSheet("border: 1px solid red;")
            self.rightEdits[1].setStyleSheet("border: 1px solid grey;")
            self.rightEdits[2].setStyleSheet("border: 1px solid red;")
        elif self.combo_stopOptions.currentText() == 'T-Test':
            self.rightEdits[0].setStyleSheet("border: 1px solid red;")
            self.rightEdits[1].setStyleSheet("border: 1px solid red;")
            self.rightEdits[2].setStyleSheet("border: 1px solid grey;")

    def eventFilter(self, object, event):
        #print(object)
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #if event.type()==QtCore.QEvent.Paint:
        #    self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #print(self.vW.size().width())
        return False

    def resizeWidget(self,event):
        pass

    def sendParams(self):
        g.ser.write_b(str(float(self.leftEdits[0].text()))+"\n")
        g.ser.write_b(str(float(self.leftEdits[1].text())/1000000)+"\n")
        g.ser.write_b(str(float(self.leftEdits[2].text()))+"\n")
        g.ser.write_b(str(float(self.leftEdits[3].text()))+"\n")

    def programOne(self):
        if g.ser.port != None:
            B=int(self.leftEdits[2].text())
            stopTime=int(self.rightEdits[0].text())
            stopConf=float(self.rightEdits[1].text())
            stopTol = float(self.rightEdits[2].text())/100 #Convert % into normal.

            A=float(self.leftEdits[0].text())
            pw=float(self.leftEdits[1].text())/1000000

            job="33"
            g.ser.write_b(job+"\n")   # sends the job
            
            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData([[g.w,g.b]], A, pw, B, stopTime, stopConf, stopTol, self.combo_stopOptions.currentText())
            self.getData.moveToThread(self.thread)
            self.finalise_thread_initialisation()

            self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


    def programRange(self):
        if g.ser.port != None:
            B=int(self.leftEdits[2].text())
            stopTime=int(self.rightEdits[0].text())
            stopConf=float(self.rightEdits[1].text())
            stopTol = float(self.rightEdits[2].text())/100 #Convert % into normal.

            A=float(self.leftEdits[0].text())
            pw=float(self.leftEdits[1].text())/1000000

            rangeDev=self.makeDeviceList(True)

            job="33"
            g.ser.write_b(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev, A, pw, B, stopTime, stopConf, stopTol, self.combo_stopOptions.currentText())
            self.finalise_thread_initialisation()

            self.thread.start()

    def programAll(self):
        if g.ser.port != None:
            B=int(self.leftEdits[2].text())
            stopTime=int(self.rightEdits[0].text())
            stopConf=float(self.rightEdits[1].text())
            stopTol = float(self.rightEdits[2].text())/100 #Convert % into normal.

            A=float(self.leftEdits[0].text())
            pw=float(self.leftEdits[1].text())/1000000

            rangeDev=self.makeDeviceList(False)

            job="33"
            g.ser.write_b(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev, A, pw, B, stopTime, stopConf, stopTol, self.combo_stopOptions.currentText())
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

