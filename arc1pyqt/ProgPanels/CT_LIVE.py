####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import pyqtgraph as pg
import numpy as np
import queue

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts, functions, styles
from arc1pyqt import Graphics
from arc1pyqt.modutils import BaseThreadWrapper


mutex = QtCore.QMutex()


class StartLiveThreadWrapper(QtCore.QObject):
    global mutex

    finished = QtCore.pyqtSignal()
    disableInterface = QtCore.pyqtSignal(bool)
    execute = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.stop=False

    def run(self):
        self.disableInterface.emit(True)
        while not self.stop:
            mutex.lock()
            self.execute.emit(1)
            APP.waitCondition.wait(mutex)
            mutex.unlock()

        self.disableInterface.emit(False)

        self.finished.emit()

    def stop_live(self):
        self.stop=True


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self,deviceList,totalCycles):
        super().__init__()
        self.deviceList=deviceList
        self.totalCycles=totalCycles
        self.stop=False

    # NOTE: We do not decorate this class with @BaseThreadWrapper.runner
    # because if we do the main interface will be enabled and disabled at
    # **every** I-V which is annoying. Instead interfacing locking is
    # governed by the `StartLiveThreadWrapper` thread instead.
    def run(self):

        tag = 'CT'

        readTag='R'+str(HW.conf.readmode)+' V='+str(HW.conf.Vread)

        HW.ArC.write_b(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:

            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            HW.ArC.queue_select(w, b)

            firstPoint=1
            for cycle in range(1,self.totalCycles+1):
                endCommand=0
                valuesNew=HW.ArC.read_floats(3)

                if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                    if (firstPoint==1):
                        tag_=tag+'_s'
                        firstPoint=0
                    else:
                        tag_=tag+'_i_'+str(cycle)

                else:
                    endCommand=1

                while(endCommand==0):
                    valuesOld=valuesNew
                    valuesNew=HW.ArC.read_floats(3)

                    if (float(valuesNew[0])!=0 or float(valuesNew[1])!=0 or float(valuesNew[2])!=0):
                        self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                        #self.displayData.emit()
                        tag_=tag+'_i_'+str(cycle)
                    else:
                        if (cycle==self.totalCycles):
                            tag_=tag+'_e'
                        else:
                            tag_=tag+'_i_'+str(cycle)
                        self.sendData.emit(w,b,valuesOld[0],valuesOld[1],valuesOld[2],tag_)
                        self.displayData.emit()
                        endCommand=1

        self.finished.emit()


class CT_LIVE(QtWidgets.QWidget):

    stop_signal=QtCore.pyqtSignal()

    def __init__(self, short=False, parent=None):
        super().__init__(parent=parent)

        self.short=short

        self.initUI()
        self.initialise_variables()

    def initUI(self):

        vbox1=QtWidgets.QVBoxLayout()

        self.view=pg.GraphicsLayoutWidget()
        label_style = {'color': '#000000', 'font-size': '10pt'}

        self.plot_IV=self.view.addPlot()
        self.plot_IV.getAxis('left').setLabel('Current', units='A', **label_style)
        self.plot_IV.getAxis('bottom').setLabel('Voltage', units='V', **label_style)
        self.plot_IV.getAxis('left').setGrid(50)
        self.plot_IV.getAxis('bottom').setGrid(50)

        vbox1.addWidget(self.view)

        titleLabel = QtWidgets.QLabel('CurveTracer')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Standard IV measurement module with current cut-off.')
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
                    'Interpulse (ms)',\
                    'Positive current cut-off (uA)',\
                    'Negative current cut-off (uA)']

        self.rightEdits=[]

        leftInit=  ['1', \
                    '1', \
                    '0.05', \
                    '0.05', \
                    '2']
        rightInit= ['1', \
                    '10',\
                    '0',\
                    '0']

        #               min, max, step, value
        spinbox_params=[[0.1,12,0.1,1],\
                        [0.1,12,0.1,1],\
                        [0.05,1,0.05,0.05],
                        [0.05,1,0.05,0.05],
                        [2,100,0.5,2]]
        spinbox_cutoff_params=[0, 1000, 10, 0]

        # Setup the two combo boxes
        IVtypes=['Staircase', 'Pulsed']
        IVoptions=['Start towards V+', 'Start towards V-', 'Only V+', 'Only V-']

        self.combo_IVtype=QtWidgets.QComboBox()
        self.combo_IVoption=QtWidgets.QComboBox()

        self.combo_IVtype.insertItems(1,IVtypes)
        self.combo_IVoption.insertItems(1,IVoptions)

        # Setup the two combo boxes
        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)
        gridLayout.setColumnStretch(2,1)
        gridLayout.setColumnStretch(3,1)
        gridLayout.setColumnStretch(4,3)

        if self.short==False:
            gridLayout.setColumnStretch(5,1)
            gridLayout.setColumnStretch(6,1)
            gridLayout.setColumnStretch(7,2)

        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)
        lineRight=QtWidgets.QFrame()
        lineRight.setFrameShape(QtWidgets.QFrame.VLine)
        lineRight.setFrameShadow(QtWidgets.QFrame.Raised)
        lineRight.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 7, 1)
        gridLayout.addWidget(lineRight, 0, 6, 7, 1)

        for i in range(len(leftLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            spinEdit=QtWidgets.QDoubleSpinBox()
            spinEdit.setMinimum(spinbox_params[i][0])
            spinEdit.setMaximum(spinbox_params[i][1])
            spinEdit.setSingleStep(spinbox_params[i][2])
            spinEdit.setValue(spinbox_params[i][3])
            gridLayout.addWidget(spinEdit, i,1)
            self.leftEdits.append(spinEdit)


        gridLayout.addWidget(QtWidgets.QLabel("Buffer size:"),6,0)
        edit_buffSize=QtWidgets.QDoubleSpinBox()
        edit_buffSize.setMinimum(10)
        edit_buffSize.setMaximum(100)
        edit_buffSize.setSingleStep(10)
        edit_buffSize.setValue(50)
        edit_buffSize.setDecimals(0)
        edit_buffSize.valueChanged.connect(self.update_bufSize)
        gridLayout.addWidget(edit_buffSize,6,1)


        for i in range(len(rightLabels)):
            lineLabel=QtWidgets.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,4)

            if i<2:
                lineEdit=QtWidgets.QLineEdit()
                lineEdit.setText(rightInit[i])
                lineEdit.setValidator(isFloat)
                self.rightEdits.append(lineEdit)
                gridLayout.addWidget(lineEdit, i,5)
            else:
                spinEdit=QtWidgets.QDoubleSpinBox()
                spinEdit.setMinimum(spinbox_cutoff_params[0])
                spinEdit.setMaximum(spinbox_cutoff_params[1])
                spinEdit.setSingleStep(spinbox_cutoff_params[2])
                spinEdit.setValue(spinbox_cutoff_params[3])
                spinEdit.setDecimals(0)
                gridLayout.addWidget(spinEdit, i,5)
                self.rightEdits.append(spinEdit)

        self.leftEdits[0].valueChanged.connect(self.update_v_pmax)
        self.leftEdits[1].valueChanged.connect(self.update_v_nmax)
        self.leftEdits[2].valueChanged.connect(self.update_v_step)
        self.leftEdits[3].valueChanged.connect(self.update_v_start)
        self.leftEdits[4].valueChanged.connect(self.update_pw)

        self.rightEdits[0].textChanged.connect(self.update_cycles)
        self.rightEdits[1].textChanged.connect(self.update_interpulse)
        self.rightEdits[2].valueChanged.connect(self.update_c_p)
        self.rightEdits[3].valueChanged.connect(self.update_c_n)

        returnCheckBox = QtWidgets.QCheckBox("Halt and return.")
        returnCheckBox.stateChanged.connect(self.toggleReturn)
        self.returnCheck=0
        gridLayout.addWidget(returnCheckBox, 4, 5)

        lineLabel=QtWidgets.QLabel()
        lineLabel.setText('Bias type:')
        gridLayout.addWidget(lineLabel,5,4)

        lineLabel=QtWidgets.QLabel()
        lineLabel.setText('IV span:')
        gridLayout.addWidget(lineLabel,6,4)

        gridLayout.addWidget(self.combo_IVtype,5,5)
        gridLayout.addWidget(self.combo_IVoption,6,5)

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
        self.scrlArea.setMaximumHeight(200)

        vbox1.addWidget(self.scrlArea)

        if self.short==False:

            self.hboxProg=QtWidgets.QHBoxLayout()

            push_single=QtWidgets.QPushButton('Apply to One')
            push_range=QtWidgets.QPushButton('Apply to Range')
            push_all=QtWidgets.QPushButton('Apply to All')

            push_single.setStyleSheet(styles.btnStyle)
            push_range.setStyleSheet(styles.btnStyle)
            push_all.setStyleSheet(styles.btnStyle)

            push_single.clicked.connect(self.programOne)
            push_range.clicked.connect(self.programRange)

            push_all.clicked.connect(self.programAll)

            self.hboxProg.addWidget(push_single)
            self.hboxProg.addWidget(push_range)
            self.hboxProg.addWidget(push_all)

            vbox1.addLayout(self.hboxProg)

            push_live=QtWidgets.QPushButton("LIVE")
            push_live.setStyleSheet("background-color: red")
            push_live.clicked.connect(self.goLive)
            gridLayout.addWidget(push_live,len(self.leftEdits),0)


        self.setLayout(vbox1)
        self.vW.setFixedWidth(self.size().width())
        self.gridLayout=gridLayout


        btn_widget=QtWidgets.QWidget()
        hbox=QtWidgets.QHBoxLayout(self)
        self.push_live=QtWidgets.QPushButton("GO LIVE!")
        self.push_live.clicked.connect(self.live)
        self.push_live.setStyleSheet(styles.btnStyle)
        self.push_one=QtWidgets.QPushButton("Apply to One")
        self.push_one.clicked.connect(self.start_programOne)
        self.push_one.setStyleSheet(styles.btnStyle)

        self.push_save=QtWidgets.QPushButton("Save Data")
        self.push_save.clicked.connect(self.saveQueue)
        self.push_save.setStyleSheet(styles.btnStyle2)

        hbox.addWidget(self.push_save)
        hbox.addWidget(self.push_live)
        hbox.addWidget(self.push_one)
        btn_widget.setLayout(hbox)

        vbox1.addWidget(btn_widget)

        self.setWindowTitle("CurveTracer: LIVE!")
        self.setWindowIcon(Graphics.getIcon('appicon'))

    def closeEvent(self, event):
        # What to do when the user closer the window and there's either
        # a live measurement run in progress or there is unsaved data
        if self.live_thread is not None:
            reply = QtWidgets.QMessageBox.question(self, "Error",
                "Live measurement in progress. Stop it and try again.",
                QtWidgets.QMessageBox.Ok)
            event.ignore()
        else:
            if self.data_queue.qsize()>0:
                reply = QtWidgets.QMessageBox.question(self, "Unsaved Data",
                    "You have about "+str(self.data_queue.qsize())+" unsaved I-V cycles. Do you want to save them?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if reply==QtWidgets.QMessageBox.Yes:
                    event.ignore()
                    self.saveQueue()

                else:
                    event.accept()

    def initialise_variables(self):
        self.voltage=[]
        self.current=[]
        self.data_queue=queue.Queue(maxsize=100)
        self.bufferSize=50

        self.pens=[]
        self.pens.append(pg.mkPen({'color':'F00', 'width':3}))
        self.pens.append(pg.mkPen({'color':'F55', 'width':3}))
        self.pens.append(pg.mkPen({'color':'F99', 'width':3}))
        self.pens.append(pg.mkPen({'color':'FCC', 'width':3}))
        self.pens.append(pg.mkPen({'color':'FEE', 'width':3}))

        #parameters
        self.v_pmax=float(self.leftEdits[0].value())
        self.v_nmax=float(self.leftEdits[1].value())
        self.v_step=float(self.leftEdits[2].value())
        self.v_start=float(self.leftEdits[3].value())
        self.pw=float(self.leftEdits[4].value())

        self.cycles=float(self.rightEdits[0].text())
        self.interpulse=float(self.rightEdits[1].text())

        self.c_p=float(self.rightEdits[2].value())
        self.c_n=float(self.rightEdits[3].value())

        # wrapper for live thread
        self.startLiveWrapper = None
        # wrapper for regular measurement thread
        self.threadWrapper = None
        # live measurement thread
        self.live_thread = None
        # regular measurement
        self.thread = None

    def start_programOne(self):
        self.programOne(int(self.rightEdits[0].text()))

    def live(self):

        if self.live_thread is None:
            self.push_live.setStyleSheet(styles.btnLive)
            self.push_live.setText("STOP!")
            self.push_one.setEnabled(False)
            self.push_save.setEnabled(False)

            self.live_thread = QtCore.QThread()

            self.startLiveWrapper=StartLiveThreadWrapper()
            self.startLiveWrapper.moveToThread(self.live_thread)
            self.live_thread.started.connect(self.startLiveWrapper.run)
            self.startLiveWrapper.finished.connect(self.live_thread.quit)
            self.startLiveWrapper.finished.connect(self.startLiveWrapper.deleteLater)
            self.live_thread.finished.connect(self.on_liveThread_finished)
            self.startLiveWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
            self.startLiveWrapper.execute.connect(self.programOne)

            self.stop_signal.connect(self.startLiveWrapper.stop_live)

            self.live_thread.start()

        else:
            self.startLiveWrapper.stop=True
            self.push_live.setStyleSheet(styles.btnStyle)
            self.push_live.setText("GO LIVE!")
            self.push_one.setEnabled(True)
            self.push_save.setEnabled(True)

    def on_liveThread_finished(self):
        self.live_thread.quit()
        self.live_thread.wait()
        self.live_thread.deleteLater()
        self.live_thread = None

    def update_bufSize(self,value):
        try:
            self.bufferSize=int(value)
        except:
            pass

    def toggleReturn(self, state):
        if state == 0:
            self.returnCheck=0
        else:
            self.returnCheck=1

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False
    def resizeWidget(self,event):
        pass

    def sendParams(self, totalCycles):
        HW.ArC.write_b(str(self.v_pmax)+"\n")
        HW.ArC.write_b(str(self.v_nmax)+"\n")
        HW.ArC.write_b(str(self.v_start)+"\n")
        HW.ArC.write_b(str(self.v_step)+"\n")
        HW.ArC.write_b(str((float(self.pw-2)/1000))+"\n")
        HW.ArC.write_b(str(float(self.interpulse/1000))+"\n")
        time.sleep(0.01)
        HW.ArC.write_b(str((self.c_p)/1000000)+"\n")
        HW.ArC.write_b(str((self.c_n)/-1000000)+"\n")

        HW.ArC.write_b(str(totalCycles)+"\n")
        HW.ArC.write_b(str(int(self.combo_IVtype.currentIndex()))+"\n")
        HW.ArC.write_b(str(int(self.combo_IVoption.currentIndex()))+"\n")
        HW.ArC.write_b(str(int(self.returnCheck))+"\n")

    def programOne(self, totalCycles):
        if (HW.ArC.port is not None) and (self.thread is None):
            self.wi = CB.word
            self.bi = CB.bit
            job="201"
            HW.ArC.write_b(job+"\n")

            self.sendParams(totalCycles)

            self.thread = QtCore.QThread()
            self.threadWrapper = ThreadWrapper([[CB.word,CB.bit]], totalCycles)
            self.threadWrapper.moveToThread(self.thread)
            self.thread.started.connect(self.threadWrapper.run)
            self.threadWrapper.finished.connect(self.thread.quit)
            self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
            self.thread.finished.connect(self.on_thread_finished)
            self.threadWrapper.sendData.connect(self.record_data)
            self.threadWrapper.highlight.connect(functions.cbAntenna.cast)
            self.threadWrapper.displayData.connect(self.display_data)
            self.threadWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
            self.thread.finished.connect(functions.interfaceAntenna.wakeUp)

            self.thread.start()

    def on_thread_finished(self):
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        self.thread = None

    def display_data(self):
        IV_curve=self.plot_IV.plot(pxMode=True)
        IV_curve.setData(np.asarray(self.voltage),np.asarray(self.current))

        if self.data_queue.qsize()<self.bufferSize:
            self.data_queue.put([self.voltage,self.current])
        else:
            self.data_queue.get()
            self.data_queue.put([self.voltage,self.current])

        self.voltage=[]
        self.current=[]

        curves=self.plot_IV.items

        for i,curve in enumerate(reversed(curves)):
            curve.setPen(self.pens[i])

        if len(curves)>4:
            self.plot_IV.removeItem(curves[0])

        self.update()

    def saveQueue(self):
        tag="CT_i"
        readTag="R2"
        cycle=0

        firstPoint=len(CB.history[self.wi][self.bi])

        while not self.data_queue.empty():
            cycle=cycle+1
            V,C=self.data_queue.get()
            (w, b) = (self.wi, self.bi)
            for i in range(len(V)):
                M=V[i]/C[i]
                CB.append(w, b, abs(V[i]/C[i]), V[i], 0, tag+"_"+str(cycle), readTag, V[i])

        if firstPoint > 0:
            CB.history[w][b][firstPoint-1][3]="CT_s"
        else:
            CB.history[w][b][0][3]="CT_s"

        CB.history[w][b][-1][3]="CT_e"

        # set the point where this starts
        CB.history[w][b][-1][-1]=firstPoint-1
        functions.historyTreeAntenna.updateTree.emit(self.wi, self.bi)

    def record_data(self, w,b, M, A, pw, tag):
        self.voltage.append(A)
        self.current.append(A/M)

    def update_v_pmax(self,value):
        try:
            self.v_pmax=float(value)
        except:
            pass

    def update_v_nmax(self,value):
        try:
            self.v_nmax=float(value)
        except:
            pass

    def update_v_step(self,value):
        try:
            self.v_step=float(value)
        except:
            pass

    def update_v_start(self,value):
        try:
            self.v_start=float(value)
        except:
            pass

    def update_pw(self,value):
        try:
            self.pw=float(value)
        except:
            pass

    def update_cycles(self,value):
        try:
            self.cycles=float(value)
        except:
            pass

    def update_interpulse(self,value):
        try:
            self.interpulse=float(value)
        except:
            pass

    def update_c_p(self,value):
        try:
            self.c_p=float(value)
        except:
            pass

    def update_c_n(self,value):
        try:
            self.c_n=float(value)
        except:
            pass

