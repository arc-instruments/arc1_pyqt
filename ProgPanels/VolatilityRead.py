from PyQt4 import QtGui, QtCore
import sys
import os
import time
import scipy.optimize as opt
import numpy as np

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

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

    def __init__(self, deviceList, A, pw, B, stopTime, stopBatchSize, stopTol, stopOpt):
        super(getData,self).__init__()
        self.A=A
        self.pw=pw
        self.B=B
        self.stopTime=stopTime
        self.stopBatchSize=stopBatchSize
        self.deviceList=deviceList
        self.stopOpt = stopOpt
        self.stopTol = stopTol

    def getIt(self):

        self.disableInterface.emit(True)
        self.changeArcStatus.emit('Busy')
        global tag

        g.ser.write(str(int(len(self.deviceList)))+"\n")

        #Stop condition preparation area.
        linfit = lambda x, a, b: a * x + b #Define linear fitter.
        xline = range(self.B) #Define x-axis values.
        initguess = [0.0, 0.0]

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write(str(int(w))+"\n")
            g.ser.write(str(int(b))+"\n")

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
                        g.ser.write(str(int(stop))+"\n")
                    else:
                        stop=0
                        g.ser.write(str(int(stop))+"\n")

                elif self.stopOpt == 'LinearFit':
                    linslope = opt.curve_fit(linfit, xline, values, initguess)[0][0] #Obtain slope of linear fit on volatile data.
                    relslope = linslope/np.mean(values) #Convert linear fit slope (Ohms/batch) into relative slope (%/batch)

                    if abs(relslope)<=self.stopTol:       # If the linear slope along the batch drops below certain magnitude stop procedure.
                        stop=1
                        g.ser.write(str(int(stop))+"\n")
                    else:
                        stop=0
                        g.ser.write(str(int(stop))+"\n")

                #DEFAULT case - something went wrong so just stop the text after 1 batch.
                else:
                    stop=1
                    g.ser.write(str(int(stop))+"\n")

            Mnow=float(g.ser.readline().rstrip())   # get first read value
            self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_e')

            self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        self.changeArcStatus.emit('Ready')
        self.displayData.emit()
        
        self.finished.emit()


class VolatilityRead(QtGui.QWidget):
    
    def __init__(self):
        super(VolatilityRead, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('VolatilityRead')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Measurement protocol for volatile memristors.')
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
                    'Stop Batch Size', \
                    'Stop Tol. (%/batch)']

        self.rightEdits=[]

        leftInit=  ['2', \
                    '100', \
                    '1000', \
                    '100']
        rightInit= ['10', \
                    '100', \
                    '10']

        # Setup the two combo boxes
        stopOptions=['LinearFit', 'T-Test', 'FixTime']
                    #     0     ,     1   ,     2

        self.combo_stopOptions=QtGui.QComboBox()

        self.combo_stopOptions.insertItems(1,stopOptions)

        self.combo_stopOptions.currentIndexChanged.connect(self.updateStopOptions)


        # Setup the two combo boxes
        gridLayout=QtGui.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)
        gridLayout.setColumnStretch(2,1)
        gridLayout.setColumnStretch(3,1)
        gridLayout.setColumnStretch(4,3)
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

        gridLayout.addWidget(lineLeft, 0, 2, 5, 1)
        gridLayout.addWidget(lineRight, 0, 6, 5, 1)
        #gridLayout.addWidget(line,1,2)
        #gridLayout.addWidget(line,2,2)
        #gridLayout.addWidget(line,3,2)
        #gridLayout.addWidget(line,4,2)


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
            lineEdit.setText(rightInit[i])
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

        #Position the combo boxes and respective labels

        lineLabel=QtGui.QLabel()
        lineLabel.setText('Stop Option:')
        gridLayout.addWidget(lineLabel,3,4)

        gridLayout.addWidget(self.combo_stopOptions,3,5)

        # ==============================================

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtGui.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        self.scrlArea=QtGui.QScrollArea()
        self.scrlArea.setWidget(self.vW)
        self.scrlArea.setContentsMargins(0,0,0,0)
        self.scrlArea.setWidgetResizable(False)
        self.scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.scrlArea.installEventFilter(self)

        vbox1.addWidget(self.scrlArea)
        vbox1.addStretch()

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
        self.vW.setFixedWidth(self.size().width())
        #print '-------'
        #print self.vW.size().width()
        #print self.scrlArea.size().width()
        #print '-------'
        #self.vW.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        #self.scrlArea.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        #self.vW.setFixedWidth(self.sizeHint().width())

    def updateStopOptions(self, event):
        print event   

    def eventFilter(self, object, event):
        #print object
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #if event.type()==QtCore.QEvent.Paint:
        #    self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #print self.vW.size().width()
        return False
    def resizeWidget(self,event):
        pass

    def sendParams(self):
        g.ser.write(str(float(self.leftEdits[0].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[1].text())/1000000)+"\n")
        g.ser.write(str(float(self.leftEdits[2].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[3].text()))+"\n")

    def programOne(self):

        B=int(self.leftEdits[2].text())
        stopTime=int(self.rightEdits[0].text())
        stopBatchSize=int(self.rightEdits[1].text())
        stopTol = float(self.rightEdits[2].text()/100) #Convert % into normal.

        A=float(self.leftEdits[0].text())
        pw=float(self.leftEdits[1].text())/1000000

        job="33"
        g.ser.write(job+"\n")   # sends the job
        
        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData([[g.w,g.b]], A, pw, B, stopTime, stopBatchSize, stopTol, self.combo_stopOptions.currentText())
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)
        self.getData.changeArcStatus.connect(f.interfaceAntenna.changeArcStatus.emit)

        self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


    def programRange(self):

        stopTime=int(self.rightEdits[0].text())
        B=int(self.leftEdits[2].text())
        stopBatchSize=int(self.rightEdits[1].text())

        A=float(self.leftEdits[0].text())
        pw=float(self.leftEdits[1].text())/1000000

        rangeDev=self.makeDeviceList(True)

        job="33"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev, A, pw, B, stopTime, stopBatchSize)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()
        

    def programAll(self):
        stopTime=int(self.rightEdits[0].text())
        B=int(self.leftEdits[2].text())
        stopBatchSize=int(self.rightEdits[1].text())

        A=float(self.leftEdits[0].text())
        pw=float(self.leftEdits[1].text())/1000000

        rangeDev=self.makeDeviceList(False)

        job="33"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev, A, pw, B, stopTime, stopBatchSize)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

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
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = VolatilityRead()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 