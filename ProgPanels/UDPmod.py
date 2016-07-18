from PyQt4 import QtGui, QtCore
import sys
import os
import time

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

tag="UDP" #Tag this module as... System will know how to handle it then.
g.tagDict.update({tag:"UDPconn"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    changeArcStatus=QtCore.pyqtSignal(str)

    def __init__(self, deviceList, A, pw, B, stopTime, stopBatchSize):
        super(getData,self).__init__()
        self.A=A
        self.pw=pw
        self.B=B
        self.stopTime=stopTime
        self.stopBatchSize=stopBatchSize
        self.deviceList=deviceList

    def getIt(self):

        self.disableInterface.emit(True)
        self.changeArcStatus.emit('Busy')
        global tag

        g.ser.write(str(int(len(self.deviceList)))+"\n")

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
                for i in range(self.B):
                    #values=[]
                    #values.append(float(g.ser.readline().rstrip()))
                    #values.append(float(g.ser.readline().rstrip()))
                    dataTime=int(g.ser.readline().rstrip())
                    Mnow=float(g.ser.readline().rstrip())

                    self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_i_ '+ str(dataTime))
                    #self.displayData.emit()

                timeNow=time.time()
        
                if (timeNow-start)>=self.stopTime:       # if more than stopTime ahas elapsed, do not request a new batch
                    stop=1
                    g.ser.write(str(int(stop))+"\n")
                else:
                    stop=0
                    g.ser.write(str(int(stop))+"\n")

            Mnow=float(g.ser.readline().rstrip())   # get first read value
            self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_e')

            self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        self.changeArcStatus.emit('Ready')
        self.displayData.emit()
        
        self.finished.emit()


class UDPmod(QtGui.QWidget):
    
    def __init__(self):
        super(UDPmod, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        ### Define GUI elements ###
        #Define module as a QVBox.
        vbox1=QtGui.QVBoxLayout()

        #Configure module title and description and text formats.
        titleLabel = QtGui.QLabel('UDPmod')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('UDP connectivity for neuromorphic applications.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        topLabels=['Recipient partner IP', \
                    'Recipient partner port']

        self.topEdits=[]

        btmLabels=['Sender partner IP', \
                    'Sender partner port']

        self.btmEdits=[]

        leftInit=  ['10.9.166.168', \
                    '5005']
        rightInit= ['10.9.166.168', \
                    '5005']


        # Setup the column 'length' ratios.
        gridLayout=QtGui.QGridLayout()
        gridLayout.setColumnStretch(0,1)
        gridLayout.setColumnStretch(1,1)
        #gridLayout.setSpacing(2)

        #Setup the line separators
        lineLeft=QtGui.QFrame()
        lineLeft.setFrameShape(QtGui.QFrame.HLine);
        lineLeft.setFrameShadow(QtGui.QFrame.Raised);
        lineLeft.setLineWidth(1)
        lineRight=QtGui.QFrame()
        lineRight.setFrameShape(QtGui.QFrame.HLine);
        lineRight.setFrameShadow(QtGui.QFrame.Raised);
        lineRight.setLineWidth(1)


        ### Build GUI insides ###
        gridLayout.addWidget(lineLeft, 2, 0, 1, 2)
        gridLayout.addWidget(lineRight, 5, 0, 1, 2)


        for i in range(len(topLabels)):
            lineLabel=QtGui.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(topLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.topEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        offset = len(topLabels)+1 #offset parameter is simply the first row of the bottom panel/label section.

        for i in range(len(btmLabels)):
            lineLabel=QtGui.QLabel()
            lineLabel.setText(btmLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, offset+i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(rightInit[i])
            lineEdit.setValidator(isFloat)
            self.btmEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, offset+i,1)

        # ============================================== #

        ### Set-up overall module GUI ###
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

        #Create... ???
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
        g.ser.write(str(float(self.topEdits[0].text()))+"\n")
        g.ser.write(str(float(self.topEdits[1].text())/1000000)+"\n")
        g.ser.write(str(float(self.topEdits[2].text()))+"\n")
        g.ser.write(str(float(self.topEdits[3].text()))+"\n")

    def programOne(self):

        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

        job="33"
        g.ser.write(job+"\n")   # sends the job
        
        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData([[g.w,g.b]], A, pw, B, stopTime, stopBatchSize)
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

        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

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
        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

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
    ex = UDPmod()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 