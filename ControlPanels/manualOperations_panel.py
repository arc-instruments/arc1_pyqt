####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore

sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Graphics/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s
import GlobalFonts as fonts


class readAllWorker(QtCore.QObject):
    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    sendPosition=QtCore.pyqtSignal(int,int)
    disableInterface=QtCore.pyqtSignal(bool)

    Vread=g.Vread
    tag='F R'+str(g.readOption)+' V='+str(Vread)

    def __init__(self):
        super(readAllWorker,self).__init__()

    def readAll(self):
        self.disableInterface.emit(True)
        job="2"
        g.ser.write(job+"\n")   # sends the job
        if g.checkSA==False:
            g.ser.write(str(1)+"\n")    # send the type of read - currently read All devices
            g.ser.write(str(g.wline_nr)+"\n")
            g.ser.write(str(g.bline_nr)+"\n")
            for word in range(1,g.wline_nr+1):    # perform standard read All
                for bit in range(1,g.bline_nr+1):      
                    Mnow=float(g.ser.readline().rstrip())         # read the value

                    #g.Mhistory[word][bit].append([g.Mnow,0,0,0])    # store it

                    self.sendData.emit(word,bit,Mnow,self.Vread,0,self.tag)
                    self.sendPosition.emit(word,bit)

                    #f.cbAntenna.selectDeviceSignal.emit(word,bit)
            #self.updateHistoryTree.emit()
            self.disableInterface.emit(False)
            self.finished.emit()
        else:
            g.ser.write(str(2)+"\n")    # send the type of read - read stand alone custom array
            g.ser.write(str(g.wline_nr)+"\n")
            g.ser.write(str(g.bline_nr)+"\n")
            g.ser.write(str(len(g.customArray))+"\n")
            for cell in g.customArray:
                word,bit=cell
                g.ser.write(str(word)+"\n")  # send wordline
                g.ser.write(str(bit)+"\n")  # send bitline

                Mnow=float(g.ser.readline().rstrip())         # read the value

                #g.Mhistory[word][bit].append([g.Mnow,0,0,0])    # store it

                self.sendData.emit(word,bit,Mnow,self.Vread,0,self.tag)
                self.sendPosition.emit(word,bit)

                    #f.cbAntenna.selectDeviceSignal.emit(word,bit)
            #self.updateHistoryTree.emit()
            self.disableInterface.emit(False)
            self.finished.emit()



class manualOperations_panel(QtGui.QWidget):
    def __init__(self):
        super(manualOperations_panel, self).__init__()
        self.initUI()
        
    def initUI(self):
        #p = self.palette()
        #p.setColor(self.backgroundRole(), QtCore.Qt.white)
        #self.setPalette(p)
        #self.update()
        #self.butn=f.deviceAntenna()
        ######################################
        # Setup position and resistance labels
        self.position = QtGui.QLabel(self)
        self.position.setText(g.Mnow_position_str)
        self.position.setFont(fonts.font2)
        self.position.setStyleSheet(s.style1)

        self.resistance = QtGui.QLabel(self)
        self.resistance.setText(g.Mnow_str)
        self.resistance.setFont(fonts.font1)
        self.resistance.setStyleSheet(s.style1)

        # Setup slots for automatic Label updating
        f.cbAntenna.selectDeviceSignal.connect(self.setM)
        ######################################

        ######################################
        # Setup manual reading panel
        self.readPanel = QtGui.QGroupBox('Read Operations')
        self.readPanel.setStyleSheet(s.groupStyle)
        readPanelLayout = QtGui.QVBoxLayout()
        readPanelLayout.setContentsMargins(10,25,10,10)
        #readPanelLayout.setContentsMargins(0,0,0,0)

        push_read=QtGui.QPushButton('Read Single')
        push_read.setStyleSheet(s.btnStyle)
        push_read.clicked.connect(self.readSingle)

        push_readAll=QtGui.QPushButton('Read All')
        push_readAll.setStyleSheet(s.btnStyle)
        push_readAll.clicked.connect(self.readAll)

        hbox_1=QtGui.QHBoxLayout()
        #hbox_1.setContentsMargins(0,0,0,0)
        hbox_1.addWidget(push_read)
        hbox_1.addWidget(push_readAll)

        push_updateRead=QtGui.QPushButton('Update Read')
        push_updateRead.setStyleSheet(s.btnStyle2)
        push_updateRead.clicked.connect(self.updateRead)
        push_updateRead.setMinimumWidth(100)

        combo_readType=QtGui.QComboBox()
        combo_readType.setStyleSheet(s.comboStyle)
        #combo_readType.down-arrow.setPixMap(QtGui.QPixmap(os.getcwd()+"/Graphics/"+'newSeshLogo.png'))
        combo_readType.insertItems(1,g.readOptions)
        combo_readType.currentIndexChanged.connect(self.updateReadType)
        combo_readType.setCurrentIndex(2)
        g.readOption=combo_readType.currentIndex()

        read_voltage=QtGui.QDoubleSpinBox()
        #read_voltage.setHeight(25)
        read_voltage.setStyleSheet(s.spinStyle)
        read_voltage.setMinimum(-12)
        read_voltage.setMaximum(12)
        read_voltage.setSingleStep(0.05)
        read_voltage.setValue(0.5)
        read_voltage.setSuffix(' V')
        read_voltage.valueChanged.connect(self.setVread)

        hbox_2=QtGui.QHBoxLayout()
        hbox_2.addWidget(push_updateRead)
        hbox_2.addWidget(combo_readType)
        hbox_2.addWidget(read_voltage)

        self.customArrayCheckbox = QtGui.QCheckBox("Custom array")
        self.customArrayCheckbox.stateChanged.connect(self.toggleSA)

        self.customArrayFileName=QtGui.QLabel()
        self.customArrayFileName.setStyleSheet(s.style1)

        push_browse = QtGui.QPushButton('...')
        push_browse.clicked.connect(self.findSAfile)    # open custom array defive position file
        push_browse.setFixedWidth(20)

        hbox_3=QtGui.QHBoxLayout()
        hbox_3.addWidget(self.customArrayCheckbox)
        hbox_3.addWidget(self.customArrayFileName)
        hbox_3.addWidget(push_browse)

        readPanelLayout.addLayout(hbox_1)
        readPanelLayout.addLayout(hbox_2)
        readPanelLayout.addLayout(hbox_3)

        self.readPanel.setLayout(readPanelLayout)

        ######################################
        # Manual Pulse panel
        self.pulsePanel = QtGui.QGroupBox('Manual Pulsing')
        self.pulsePanel.setStyleSheet(s.groupStyle)
        
        pulsePanelLayout= QtGui.QGridLayout()
        pulsePanelLayout.setContentsMargins(10,25,10,10)

        self.pulse_V_pos = QtGui.QLineEdit()
        self.pulse_V_neg = QtGui.QLineEdit()
        self.pulse_pw_pos = QtGui.QLineEdit()
        self.pulse_pw_neg = QtGui.QLineEdit()

        self.pulse_V_pos.setStyleSheet(s.entryStyle)
        self.pulse_pw_pos.setStyleSheet(s.entryStyle)
        self.pulse_V_neg.setStyleSheet(s.entryStyle)
        self.pulse_pw_neg.setStyleSheet(s.entryStyle)

        # Initialise fields
        self.pulse_V_pos.setText('1')
        self.pulse_V_neg.setText('1')
        self.pulse_pw_pos.setText('100')
        self.pulse_pw_neg.setText('100')

        isFloat=QtGui.QDoubleValidator()

        # Apply an input mask to restrict the input to only numbers
        self.pulse_V_pos.setValidator(isFloat)
        self.pulse_V_neg.setValidator(isFloat)
        self.pulse_pw_pos.setValidator(isFloat)
        self.pulse_pw_neg.setValidator(isFloat)

        label_V = QtGui.QLabel('Voltage (V)')
        label_pw = QtGui.QLabel('Duration')

        push_pulsePos = QtGui.QPushButton('+Pulse')
        push_pulsePos.clicked.connect(self.extractParamsPlus)
        push_pulsePos.setStyleSheet(s.btnStyle)
        push_pulseNeg = QtGui.QPushButton('-Pulse')
        push_pulseNeg.clicked.connect(self.extractParamsNeg)
        push_pulseNeg.setStyleSheet(s.btnStyle)

        self.check_lock = QtGui.QCheckBox('Lock')
        self.check_lock.stateChanged.connect(self.lockPulses)

        pulsePanelLayout.addWidget(self.pulse_V_pos,0,0)
        pulsePanelLayout.addWidget(self.pulse_V_neg,0,2)

        # ========== ComboBox ===========
        pw_pos_lay=QtGui.QHBoxLayout()
        pw_neg_lay=QtGui.QHBoxLayout()

        self.pw_plusDropDown=QtGui.QComboBox()
        self.pw_plusDropDown.setStyleSheet(s.comboStylePulse)

        self.unitsFull=[['s',1],['ms',0.001],['us',0.000001],['ns',0.000000001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.pw_negDropDown=QtGui.QComboBox()
        self.pw_negDropDown.setStyleSheet(s.comboStylePulse)

        self.pw_plusDropDown.insertItems(1,self.units)
        self.pw_plusDropDown.setCurrentIndex(2)
        self.pw_negDropDown.insertItems(1,self.units)
        self.pw_negDropDown.setCurrentIndex(2)

        pw_pos_lay.addWidget(self.pulse_pw_pos)
        pw_pos_lay.addWidget(self.pw_plusDropDown)
        pw_neg_lay.addWidget(self.pulse_pw_neg)
        pw_neg_lay.addWidget(self.pw_negDropDown)

        #pulsePanelLayout.addWidget(self.pulse_pw_pos,1,0)
        #pulsePanelLayout.addWidget(self.pulse_pw_neg,1,2)

        pulsePanelLayout.addLayout(pw_pos_lay,1,0)
        pulsePanelLayout.addLayout(pw_neg_lay,1,2)

        pulsePanelLayout.addWidget(label_V,0,1)
        pulsePanelLayout.addWidget(label_pw,1,1)
        pulsePanelLayout.addWidget(push_pulsePos,2,0)
        pulsePanelLayout.addWidget(push_pulseNeg,2,2)
        pulsePanelLayout.addWidget(self.check_lock,2,1)

        pulsePanelLayout.setAlignment(label_V, QtCore.Qt.AlignHCenter)
        pulsePanelLayout.setAlignment(label_pw, QtCore.Qt.AlignHCenter)
        pulsePanelLayout.setAlignment(self.check_lock, QtCore.Qt.AlignHCenter)

        self.pulsePanel.setLayout(pulsePanelLayout)
        ######################################

        ######################################
        # Display Options Panel
        displayPanel = QtGui.QGroupBox('Display Options')
        displayPanel.setStyleSheet(s.groupStyle)
        displayPanelLayout = QtGui.QHBoxLayout()
        displayPanelLayout.setContentsMargins(10,25,10,10)

        push_displayAll = QtGui.QPushButton('Full')
        push_displayAll.setStyleSheet(s.btnStyle2)
        push_displayAll.clicked.connect(self.displayAll)
        push_displayRange = QtGui.QPushButton('Range')
        push_displayRange.setStyleSheet(s.btnStyle2)
        push_displayRange.clicked.connect(self.displayRange)

        points_spinbox = QtGui.QSpinBox()
        points_spinbox.setStyleSheet(s.spinStyle)
        points_spinbox.setMinimum(10)
        points_spinbox.setMaximum(10000)
        points_spinbox.setSingleStep(100)
        points_spinbox.setValue(g.dispPoints)
        points_spinbox.setSuffix(' p')
        points_spinbox.valueChanged.connect(self.updatePoints)

        check_log = QtGui.QCheckBox('log Y')
        check_log.stateChanged.connect(self.updateLogScale)

        displayPanelLayout.addWidget(push_displayAll)
        displayPanelLayout.addWidget(push_displayRange)
        displayPanelLayout.addWidget(points_spinbox)
        displayPanelLayout.addWidget(check_log)

        displayPanel.setLayout(displayPanelLayout)
        ######################################

        mainLayout = QtGui.QVBoxLayout()

        mainLayout.addWidget(self.position)
        mainLayout.addWidget(self.resistance)
        mainLayout.addWidget(self.readPanel)
        mainLayout.addWidget(self.pulsePanel)
        mainLayout.addWidget(displayPanel)
        mainLayout.addStretch()

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,3,0)

        self.setLayout(mainLayout)

        self.setContentsMargins(0,0,0,0)

        self.setM(1,1)

        #self.show()

    def lockPulses(self, state):
        print "capture"
        print state
        if state==2:
            self.pulse_V_neg.setEnabled(False)
            self.pw_negDropDown.setEnabled(False)
            self.pulse_pw_neg.setEnabled(False)
            self.update()
        else:
            self.pulse_V_neg.setEnabled(True)
            self.pw_negDropDown.setEnabled(True)
            self.pulse_pw_neg.setEnabled(True)
            self.update()


    def updateLogScale(self,event):
        f.displayUpdate.updateLog.emit(event)


    def toggleSA(self, event):
        print event
        if (event==0):
            g.checkSA=False
            for w in range(1,33):
                for b in range(1,33):
                    f.SAantenna.enable.emit(w,b)
        else:
            if (g.customArray):
                g.checkSA=True
                f.cbAntenna.selectDeviceSignal.emit(g.customArray[0][0], g.customArray[0][1])       # signal the crossbar antenna that this device has been selected
                f.displayUpdate.updateSignal_short.emit()
                for w in range(1,33):
                    for b in range(1,33):
                        f.SAantenna.disable.emit(w,b)

                for cell in g.customArray:
                    w,b=cell
                    f.SAantenna.enable.emit(w,b)
                print "Enabled"
            else:
                if self.findSAfile()==True:
                    g.checkSA=True
                    for w in range(1,33):
                        for b in range(1,33):
                            f.SAantenna.disable.emit(w,b)

                    for cell in g.customArray:
                        w,b=cell
                        f.SAantenna.enable.emit(w,b)
                    f.cbAntenna.selectDeviceSignal.emit(g.customArray[0][0], g.customArray[0][1])       # signal the crossbar antenna that this device has been selected
                    f.displayUpdate.updateSignal_short.emit()

                        # Disable all cells except the ones in g.customArray

                else:
                    g.checkSA=False
                    self.customArrayCheckbox.setCheckState(QtCore.Qt.Unchecked)


    def findSAfile(self):
        path = QtCore.QFileInfo(QtGui.QFileDialog().getOpenFileName(self, 'Open file', "*.txt"))
        #path=fname.getOpenFileName()

        customArray=[]
        name=path.fileName()

        file=QtCore.QFile(path.filePath())
        file.open(QtCore.QIODevice.ReadOnly)

        textStream=QtCore.QTextStream(file)
        error=0
        while not textStream.atEnd():
            line = textStream.readLine()
            try:
                w,b=line.split(", ")
                customArray.append([int(w),int(b)])
                if (int(w)<1 or int(w)>g.wline_nr or int(b)<1 or int(b)>g.bline_nr):
                    error=1
            except ValueError:
                error=1
        file.close()
        
        # check if positions read are correct
        if (error==1):
            #self.errorMessage=QtGui.QErrorMessage() 
            #self.errorMessage.showMessage("Custom array file is formatted incorrectly!")  
            errMessage = QtGui.QMessageBox()
            errMessage.setText("Custom array text file formatted incorrectly, or selected devices outside of array range!")
            errMessage.setIcon(QtGui.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()
            return False
        else:
            self.customArrayFileName.setText(name)
            g.customArray=customArray
            return True


    def setM(self,w,b):
        try:
            g.Mnow=g.Mhistory[w][b][-1][0]
            #self.resistance.setText(str(int(g.Mnow))+' Ohms')
			self.resistance.setText(str('%.0f' % g.Mnow)+' Ohms')
        except IndexError:
            self.resistance.setText('Not Read')
        self.position.setText('W='+str(w)+ ' | ' + 'B='+str(b))

        g.w=w
        g.b=b

    def readSingle(self):
        if g.ser.port != None:
            job="1"
            g.ser.write(job+"\n")
            g.ser.write(str(g.w)+"\n")
            g.ser.write(str(g.b)+"\n")

            try:
                currentline='%.10f' % float(g.ser.readline().rstrip())     # currentline contains the new Mnow value followed by 2 \n characters
            except ValueError:
                currentline='%.10f' % 0.0

            currentM=float(currentline)

            g.Mnow=currentM       # conver to float
            tag='S R'+str(g.readOption)+' V='+str(g.Vread)
            f.updateHistory(g.w,g.b,currentM,float(g.Vread),0,tag)
            self.setM(g.w,g.b)

            f.displayUpdate.updateSignal.emit(g.w,g.b,2,g.dispPoints,99)
            f.historyTreeAntenna.updateTree.emit(g.w,g.b)


    def readAll(self):
        #disableInterface.disable.emit()
        if g.ser.port != None:
            self.thread=QtCore.QThread()
            self.readAllWorker=readAllWorker()
            self.readAllWorker.moveToThread(self.thread)
            self.thread.started.connect(self.readAllWorker.readAll)
            self.readAllWorker.sendData.connect(f.updateHistory)
            self.readAllWorker.sendPosition.connect(f.cbAntenna.cast)
            #self.readAllWorker.updateHistoryTree.connect(f.deviceHistoryAntenna.cast)
            self.readAllWorker.finished.connect(self.thread.quit)
            self.readAllWorker.finished.connect(self.readAllWorker.deleteLater)
            self.thread.finished.connect(self.readAllWorker.deleteLater)
            self.readAllWorker.disableInterface.connect(f.interfaceAntenna.disable.emit)
            self.thread.start()

    #def storeReadAllData(self,w,b,Mnow):
    #    tag='F R'+str(g.readOption)+' V='+str(g.Vread)
    #    g.Mhistory[w][b].append([Mnow,float(g.Vread),0,tag])    # store it

    def updateRead(self):
        if g.ser.port != None:
            job='01'
            g.ser.write(job+"\n")
            g.ser.write(str(g.readOption)+"\n")
            
            g.ser.write(str(g.Vread)+"\n")

    def setVread(self,event):
        g.Vread=float(event)
        print g.Vread
        if g.ser.port != None:
            job='01'
            g.ser.write(job+"\n")
            g.ser.write(str(g.readOption)+"\n")
            
            g.ser.write(str(g.Vread)+"\n")


    def extractParamsPlus(self):
        self.amplitude=float(self.pulse_V_pos.text())
        duration=float(self.pulse_pw_pos.text())
        unit=float(self.multiply[self.pw_plusDropDown.currentIndex()])        
        self.pw=duration*unit

        if self.pw<0.00000009:
            self.pulse_pw_pos.setText(str(90))
            self.pw_plusDropDown.setCurrentIndex(3)
            self.pw=0.00000009
        if self.pw>10:
            self.pulse_pw_pos.setText(str(10))
            self.pw_plusDropDown.setCurrentIndex(0)
            self.pw=10

        self.update()
        self.pulse()

    def extractParamsNeg(self):
        if self.check_lock.isChecked():
            self.amplitude=-1*float(self.pulse_V_pos.text())
            duration=float(self.pulse_pw_pos.text())
            unit=float(self.multiply[self.pw_plusDropDown.currentIndex()])        
            self.pw=duration*unit
        else:
            self.amplitude=-1*float(self.pulse_V_neg.text())
            duration=float(self.pulse_pw_neg.text())
            unit=float(self.multiply[self.pw_negDropDown.currentIndex()])        
            self.pw=duration*unit

        if self.check_lock.isChecked():
            if self.pw<0.00000009:
                self.pulse_pw_pos.setText(str(90))
                self.pw_plusDropDown.setCurrentIndex(3)
                self.pw=0.00000009
            if self.pw>10:
                self.pulse_pw_pos.setText(str(10))
                self.pw_plusDropDown.setCurrentIndex(0)
                self.pw=10
        else:
            if self.pw<0.00000009:
                self.pulse_pw_neg.setText(str(90))
                self.pw_negDropDown.setCurrentIndex(3)
                self.pw=0.00000009
            if self.pw>10:
                self.pulse_pw_neg.setText(str(10))
                self.pw_negDropDown.setCurrentIndex(0)
                self.pw=10

        self.update()
        self.pulse()

    def pulse(self):
        if g.ser.port != None: 
            ser=g.ser                   # simplify the namespace
            job="3"                     # define job
            ser.write(job+"\n")            # Send job followed by cell position and pulsing parameters
            ser.write(str(g.w)+"\n")
            ser.write(str(g.b)+"\n")

            ser.write(str(float(self.amplitude))+"\n")
            ser.write(str(float(self.pw))+"\n")

            # Read the value of M after the pulse
            currentline='%.0f' % float(ser.readline().rstrip())     # currentline contains the new Mnow value followed by 2 \n characters
            g.Mnow=float(currentline)

            tag='P'
            f.updateHistory(g.w,g.b,g.Mnow,self.amplitude,self.pw,tag)
            self.setM(g.w,g.b)
            f.displayUpdate.updateSignal.emit(g.w, g.b, 2, g.dispPoints, 99)
            f.historyTreeAntenna.updateTree.emit(g.w,g.b)


    def displayAll(self):
        f.displayUpdate.updateSignal.emit(g.w,g.b,1,g.dispPoints,0)

    def displayRange(self):
        f.displayUpdate.updateSignal.emit(g.w,g.b,2,g.dispPoints,0)

    def updatePoints(self,event):
        g.dispPoints=event
        #print event

    def updateReadType(self,event):
        print event
        g.readOption=event
        if g.ser.port != None:
            job='01'
            g.ser.write(job+"\n")
            g.ser.write(str(g.readOption)+"\n")
            
            g.ser.write(str(g.Vread)+"\n")

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = manualOperations_panel()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()  