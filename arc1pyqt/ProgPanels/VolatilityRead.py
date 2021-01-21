from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import scipy.stats as stat
import numpy as np

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag = "VOL"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList, A, pw, B, stopTime, stopConf, stopTol, stopOpt):
        super().__init__()
        self.A=A
        self.pw=pw
        self.B=B
        self.stopTime=stopTime
        self.stopConf=stopConf
        self.deviceList=deviceList
        self.stopOpt = stopOpt
        self.stopTol = stopTol
        # No. of samples at the beginning and at the end of the batch to be
        # taken for t-test.
        self.ttestsamp = 25

    @BaseThreadWrapper.runner
    def run(self):

        self.disableInterface.emit(True)
        global tag

        HW.ArC.write_b(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            HW.ArC.queue_select(w, b)

            Mnow = HW.ArC.read_floats(1)
            self.sendData.emit(w,b,Mnow,self.A,self.pw,tag+'_s')

            start=time.time()
            stop=0

            while stop==0:
                # Prepare for batch processing.
                # Reset batch result array contents.
                values = np.empty(shape=self.B)

                # Obtain data for entire batch.
                for i in np.arange(self.B):
                    # Send data to log-file.
                    dataTime=int(HW.ArC.readline().rstrip())
                    Mnow=HW.ArC.read_floats(1)
                    self.sendData.emit(w,b,Mnow,HW.conf.Vread,0,\
                            tag+'_i_ '+ str(dataTime))

                    # Hold all or portion of incoming data in temporary array.
                    values[i] = Mnow

                timeNow=time.time()

                # FIX TIME option - end volatility test after fixed time.
                if self.stopOpt == 'FixTime':
                    # if more than stopTime has elapsed, do not request a new
                    # batch
                    if (timeNow-start)>=self.stopTime:
                        stop=1
                        HW.ArC.write_b(str(int(stop))+"\n")
                    else:
                        stop=0
                        HW.ArC.write_b(str(int(stop))+"\n")

                elif self.stopOpt == 'LinearFit':
                    # Check that there are at least 2 points in batch, or no
                    # linear fit possible.
                    if self.B > 1:
                        try:
                            fitres = np.polyfit(np.arange(self.B), values, 1)
                        except RuntimeError:
                            fitres = np.array([0, 0])
                            print('Error: Could not fit data to linear function.')

                        # Obtain slope of linear fit on volatile data in units of %/batch.
                        linslope = fitres[0]*self.B
                        # Convert linear fit slope (Ohms/batch) into relative slope (%/batch)
                        relslope = linslope/np.mean(values)
                        print('Fitted resistive state slope: %g %%/batch.' % (relslope*100))

                        # If the linear slope along the batch drops below certain magnitude,
                        # or time limit exceeded stop procedure.
                        if abs(relslope)<=self.stopTol or (timeNow-start)>=self.stopTime:
                            stop=1
                            HW.ArC.write_b(str(int(stop))+"\n")
                        else:
                            stop=0
                            HW.ArC.write_b(str(int(stop))+"\n")

                    # If the batch is not large enough just end it there.
                    else:
                        stop=1
                        HW.ArC.write_b(str(int(stop))+"\n")

                elif self.stopOpt == 'T-Test':
                    # Check that the batch is actually large enough to carry
                    # out a stat-test.
                    if self.B >= self.ttestsamp*2:
                        # Perform t-test on first & last N samples in batch,
                        # then get t-metric.
                        tmet = abs(stat.ttest_ind(values[:self.ttestsamp], values[-self.ttestsamp:], equal_var = False)[0])
                        print('T-metric: ' + str(tmet))

                        # If probability (loosely speaking) of null hypothesis
                        # being true is below our confidence tolerance...
                        if tmet < self.stopConf or (timeNow-start)>=self.stopTime:
                            # ... stop requestiong batches. Also have a max time-check.
                            stop=1
                            HW.ArC.write_b(str(int(stop))+"\n")
                        else:
                            stop=0
                            HW.ArC.write_b(str(int(stop))+"\n")

                    # If the batch is not large enough just end it there.
                    else:
                        stop=1
                        HW.ArC.write_b(str(int(stop))+"\n")
                        print('WARNING: Batch not long enough to support this '+
                              'operation. Minimum batch length required is ' +
                              str(2*self.ttestsamp) + '.')

                # DEFAULT case - something went wrong so just stop the text
                # after 1 batch.
                else:
                    stop=1
                    HW.ArC.write_b(str(int(stop))+"\n")

            Mnow = HW.ArC.read_floats(1)
            self.sendData.emit(w, b, Mnow, HW.conf.Vread, 0, tag+'_e')

            self.updateTree.emit(w,b)

        self.displayData.emit()


class VolatilityRead(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title="VolatilityRead", \
                description="Measurement protocol for volatile memristors.", \
                short=short)
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

        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)
        lineRight=QtWidgets.QFrame()
        lineRight.setFrameShape(QtWidgets.QFrame.VLine)
        lineRight.setFrameShadow(QtWidgets.QFrame.Raised)
        lineRight.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 5, 1)
        gridLayout.addWidget(lineRight, 0, 6, 5, 1)

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

        lineLabel=QtWidgets.QLabel()
        lineLabel.setText('Stop Option:')
        gridLayout.addWidget(lineLabel,3,4)

        gridLayout.addWidget(self.combo_stopOptions,3,5)

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
        self.vW.setFixedWidth(self.size().width())
        self.gridLayout=gridLayout

        self.registerPropertyWidget(self.leftEdits[0], "vpulse")
        self.registerPropertyWidget(self.leftEdits[1], "pwpulse")
        self.registerPropertyWidget(self.leftEdits[2], "batch")
        self.registerPropertyWidget(self.leftEdits[3], "cyclavg")
        self.registerPropertyWidget(self.rightEdits[0], "stoptime")
        self.registerPropertyWidget(self.rightEdits[1], "stoptmetric")
        self.registerPropertyWidget(self.rightEdits[2], "stoptolerance")

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
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def resizeWidget(self,event):
        pass

    def sendParams(self):
        HW.ArC.write_b(str(float(self.leftEdits[0].text()))+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[1].text())/1000000)+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[2].text()))+"\n")
        HW.ArC.write_b(str(float(self.leftEdits[3].text()))+"\n")

    def programOne(self):
        self.programDevs([[CB.word, CB.bit]])

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def programDevs(self, devs):

        B = int(self.leftEdits[2].text())
        stopTime = int(self.rightEdits[0].text())
        stopConf = float(self.rightEdits[1].text())
        stopTol = float(self.rightEdits[2].text())/100

        A = float(self.leftEdits[0].text())
        pw = float(self.leftEdits[1].text())/1000000

        job="33"
        HW.ArC.write_b(job+"\n")

        self.sendParams()

        wrapper = ThreadWrapper(devs, A, pw, B, stopTime, stopConf, \
                stopTol, self.combo_stopOptions.currentText())
        self.execute(wrapper, wrapper.run)

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


tags = { 'top': ModTag(tag, "Volatile Read", None) }
