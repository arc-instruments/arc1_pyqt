from PyQt4 import QtGui, QtCore
import sys
import os

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

tag="EN"
g.tagDict.update({tag:"Endurance"})

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

            valuesNew=[]
            valuesNew.append(float(g.ser.readline().rstrip()))
            valuesNew.append(float(g.ser.readline().rstrip()))
            valuesNew.append(float(g.ser.readline().rstrip()))

            if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                tag_=tag+'_s'
            else:
                endCommand=1;

            while(endCommand==0):
                valuesOld=valuesNew

                valuesNew=[]
                valuesNew.append(float(g.ser.readline().rstrip()))
                valuesNew.append(float(g.ser.readline().rstrip()))
                valuesNew.append(float(g.ser.readline().rstrip()))

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


class Endurance(QtGui.QWidget):
    
    def __init__(self):
        super(Endurance, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('Endurance')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Cycle the resistive state of a bistable device using alternative polarity voltage pulses, for any number of cycles.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Positive pulse amplitude (V)', \
                    'Negative pulse amplitude (V)', \
                    'Pulse width (us)', \
                    'Cycles', \
                    'Interpulse (ms)']
        leftInit=  ['1',\
                    '1', \
                    '100',\
                    '10',\
                    '1']

        self.leftEdits=[]
        rightLabels=[]
        self.rightEdits=[]

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
        #lineRight=QtGui.QFrame()
        #lineRight.setFrameShape(QtGui.QFrame.VLine); 
        #lineRight.setFrameShadow(QtGui.QFrame.Raised);
        #lineRight.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 4, 1)
        #gridLayout.addWidget(lineRight, 0, 6, 5, 1)

        #label1=QtGui.QLabel('Pulse Amplitude (V)')
        #label1.setFixedWidth(150)
        #label2=QtGui.QLabel('Pulse width (us)')
        #label2.setFixedWidth(150)
        #label3=QtGui.QLabel('Cycles')
        #label3.setFixedWidth(150)
        #label4=QtGui.QLabel('Interpulse (ms)')
        #label4.setFixedWidth(150)

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

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def sendParams(self):
        g.ser.write(str(float(self.leftEdits[0].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[1].text())*-1)+"\n")
        g.ser.write(str(float(self.leftEdits[2].text())/1000000)+"\n")
        g.ser.write(str(int(self.leftEdits[4].text()))+"\n")
        g.ser.write(str(int(self.leftEdits[3].text()))+"\n")


    def programOne(self):
        job="19"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData([[g.w,g.b]])
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

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


    def programRange(self):

        rangeDev=self.makeDeviceList(True)


        job="19"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev)
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
        rangeDev=self.makeDeviceList(False)

        job="19"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev)
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
    ex = Endurance()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 