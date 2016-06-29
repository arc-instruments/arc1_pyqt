from PyQt4 import QtGui, QtCore
import sys
import os

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

tag="SS2"
g.tagDict.update({tag+'_e':"SwitchSeeker2"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(float, float, float, str)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal()
    disableInterface=QtCore.pyqtSignal(bool)

    def __init(self):
        super(getData,self).__init__()

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

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
                self.sendData.emit(valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                self.displayData.emit()
                tag_=tag+'_i'
            else:
                tag_=tag+'_e'
                self.sendData.emit(valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                self.displayData.emit()
                endCommand=1

        self.disableInterface.emit(False)
        self.updateTree.emit()
        self.finished.emit()


class Skeleton(QtGui.QWidget):
    
    def __init__(self):
        super(Skeleton, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        vbox1=QtGui.QVBoxLayout()

        titleLabel = QtGui.QLabel('Skeleton')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('Skeleton file.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Pulse amplitude (V)', \
                    'Pulse width (us', \
                    'Cycles', \
                    'Interpulse', \
                    'Hello', \
                    'What.s up', \
                    'Notin Much']
        self.leftEdits=[]

        rightLabels=['Interpulse', \
                    'Hello', \
                    'What.s up', \
                    'Notin Much', \
                    'What.s up', \
                    'Notin Much', \
                    'Interpulse', \
                    'Hello', \
                    'What.s up', \
                    'Notin Much']
        self.rightEdits=[]

        gridLayout=QtGui.QGridLayout()

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)


        for i in range(len(leftLabels)):
            lineLabel=QtGui.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        for i in range(len(rightLabels)):
            lineLabel=QtGui.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,3)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,4)

        self.vW=QtGui.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtGui.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        scrlArea.installEventFilter(self)
        
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,2)
        gridLayout.setColumnStretch(2,2)
        gridLayout.setColumnStretch(3,3)
        gridLayout.setColumnStretch(4,2)

        vbox1.addWidget(scrlArea)
        vbox1.addStretch()


        self.hboxProg=QtGui.QHBoxLayout()

        push_single=QtGui.QPushButton('Program One')
        push_range=QtGui.QPushButton('Program Range')
        push_all=QtGui.QPushButton('Program All')

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

    def resizeWidget(self,event):
        pass



    def programOne(self):
        job="19"
        g.ser.write(job+"\n")   # sends the job
        
        g.ser.write(str(float(self.amplitude.text()))+"\n")
        g.ser.write(str(float(self.pw.text())/1000000)+"\n")
        g.ser.write(str(float(self.interpulse.text()))+"\n")
        g.ser.write(str(float(self.cycles.text()))+"\n")
        g.ser.write("1\n")
        g.ser.write(str(g.w)+"\n")
        g.ser.write(str(g.b)+"\n")

        self.thread=QtCore.QThread()
        self.getData=getData()
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory_short)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree_short.emit)
        self.getData.disableInterface.connect(f.disableInterface.disable.emit)
        #self.getData.disableInterface.connect(self.disableProgPanel)
        self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


    def programRange(self):
        pass

    def programAll(self):
        pass
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Skeleton()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 