####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys
import os

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

tag="CT"
g.tagDict.update({tag:"CurveTracer*"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    changeArcStatus=QtCore.pyqtSignal(str)

    def __init__(self,deviceList,totalCycles):
        super(getData,self).__init__()
        self.deviceList=deviceList
        self.totalCycles=totalCycles

    def getIt(self):

        self.disableInterface.emit(True)
        #self.changeArcStatus.emit('Busy')
        global tag

        readTag='R'+str(g.readOption)+' V='+str(g.Vread)

        g.ser.write(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write(str(int(w))+"\n")
            g.ser.write(str(int(b))+"\n")

            firstPoint=1
            for cycle in range(1,self.totalCycles+1):
                
                endCommand=0

                #measurementResult=g.ser.readline().rstrip()
                #print measurementResult

                valuesNew=[]
                valuesNew.append(float(g.ser.readline().rstrip()))
                valuesNew.append(float(g.ser.readline().rstrip()))
                valuesNew.append(float(g.ser.readline().rstrip()))

                if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                    if (firstPoint==1):
                        tag_=tag+'_s'
                        firstPoint=0
                    else:
                        tag_=tag+'_i_'+str(cycle)
                else:
                    endCommand=1;

                while(endCommand==0):
                    valuesOld=valuesNew

                    #measurementResult=g.ser.readline().rstrip()
                    #print measurementResult

                    valuesNew=[]
                    valuesNew.append(float(g.ser.readline().rstrip()))
                    valuesNew.append(float(g.ser.readline().rstrip()))
                    valuesNew.append(float(g.ser.readline().rstrip()))

                    if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                        self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                        self.displayData.emit()
                        tag_=tag+'_i_'+str(cycle)
                    else:
                        if (cycle==self.totalCycles):
                            tag_=tag+'_e'
                        else:
                            tag_=tag+'_i_'+str(cycle)
                        self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                        self.displayData.emit()
                        endCommand=1
            self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        #self.changeArcStatus.emit('Ready')
        
        self.finished.emit()

class CurveTracer(QtGui.QWidget):
    
    def __init__(self, short=False):
        super(CurveTracer, self).__init__()

        self.short=short
        
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('CurveTracer')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Standard IV measurement module.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Positive voltage max (V)', \
                    'Negative voltage max (V)', \
                    'Voltage step (V)', \
                    'Start Voltage (V)', \
                    'Step width (ms)']
        self.leftEdits=[]

        rightLabels=['Cycles', \
                    'Interpulse (ms)']

        self.rightEdits=[]

        leftInit=  ['1', \
                    '1', \
                    '0.05', \
                    '0.05', \
                    '50']
        rightInit= ['1', \
                    '10']

        # Setup the two combo boxes
        IVtypes=['Staircase', 'Pulsed']
        IVoptions=['Start towards V+', 'Start towards V-', 'Only V+', 'Only V-']

        self.combo_IVtype=QtGui.QComboBox()
        self.combo_IVoption=QtGui.QComboBox()

        self.combo_IVtype.insertItems(1,IVtypes)
        self.combo_IVoption.insertItems(1,IVoptions)

        self.combo_IVtype.currentIndexChanged.connect(self.updateIVtype)
        self.combo_IVoption.currentIndexChanged.connect(self.updateIVoption)


        # Setup the two combo boxes
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
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,5)

        #Position the combo boxes and respective labels

        lineLabel=QtGui.QLabel()
        lineLabel.setText('Bias type:')
        gridLayout.addWidget(lineLabel,2,4)

        lineLabel=QtGui.QLabel()
        lineLabel.setText('IV span:')
        gridLayout.addWidget(lineLabel,3,4)

        gridLayout.addWidget(self.combo_IVtype,2,5)
        gridLayout.addWidget(self.combo_IVoption,3,5)

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

        #dummyEvent=QtGui.QResizeEvent()
        #size=QtCore.QSize(200,200)
        #self.scrlArea.resizeEvent(dummyEvent)

        vbox1.addWidget(self.scrlArea)
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
        #width=self.width()
        #self.setFixedWidth(width)
        self.vW.setFixedWidth(self.size().width())
        #print '-------'
        #print self.vW.size().width()
        #print self.scrlArea.size().width()
        #print '-------'
        #self.vW.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        #self.scrlArea.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        #self.vW.setFixedWidth(self.sizeHint().width())
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

    def updateIVtype(self, event):
        print event   

    def updateIVoption(self, event):
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
        g.ser.write(str(float(self.leftEdits[1].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[3].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[2].text()))+"\n")
        g.ser.write(str(float(self.leftEdits[4].text())/1000)+"\n")
        g.ser.write(str(float(self.rightEdits[1].text())/1000)+"\n")

        g.ser.write(str(int(self.rightEdits[0].text()))+"\n")
        g.ser.write(str(int(self.combo_IVtype.currentIndex()))+"\n")
        g.ser.write(str(int(self.combo_IVoption.currentIndex()))+"\n")

    def programOne(self):
        if g.ser.port != None:
            job="20"
            g.ser.write(job+"\n")   # sends the job

            totalCycles=int(self.rightEdits[0].text())
            
            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData([[g.w,g.b]],totalCycles)
            self.finalise_thread_initialisation()

            self.thread.start()



    def programRange(self):
        if g.ser.port != None:
            totalCycles=int(self.rightEdits[0].text())

            rangeDev=self.makeDeviceList(True)

            job="20"
            g.ser.write(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev,totalCycles)
            self.finalise_thread_initialisation()

            self.thread.start()
        

    def programAll(self):
        if g.ser.port != None:
            totalCycles=int(self.rightEdits[0].text())
            rangeDev=self.makeDeviceList(False)

            job="20"
            g.ser.write(job+"\n")   # sends the job

            self.sendParams()
            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev,totalCycles)
            self.finalise_thread_initialisation()

            self.thread.start()

    def finalise_thread_initialisation(self):
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory_CT)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.cast)
        self.getData.changeArcStatus.connect(f.interfaceAntenna.castArcStatus)        

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
    ex = CurveTracer()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 