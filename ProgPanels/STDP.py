####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import pyqtgraph as pg
import time

import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalStyles as s

tag="stdp"
g.tagDict.update({tag:"STDP*"})


class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)

    def __init__(self, deviceList, values, timeSteps):
        super(getData,self).__init__()
        self.deviceList=deviceList
        self.gain=values[0]
        self.warp=values[1]
        self.max_spike_time=values[2]
        self.pre_time=values[3]
        self.pre_voltage=values[4]
        self.post_time=values[5]
        self.post_voltage=values[6]
        self.timeSteps=timeSteps

    def getIt(self):

        self.disableInterface.emit(True)
        global tag

        g.ser.write_b(str(int(len(self.deviceList)))+"\n") #Tell mBED how many devices to be operated on.

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write_b(str(int(w))+"\n")
            g.ser.write_b(str(int(b))+"\n")

            #store a first read
            valuesNew=f.getFloats(3)
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))
            tag_=tag+"_s"
            self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
            self.displayData.emit()

            g.ser.write_b(str(int(len(self.timeSteps)))+"\n")

            for dt in self.timeSteps:
                #dt/=self.warp # bug fix
                total_time, total_voltage=self.make_time_series(dt/self.warp, self.gain, self.warp, self.max_spike_time, self.pre_time, \
                             self.pre_voltage, self.post_time, self.post_voltage)

                g.ser.write_b(str(int(len(total_time)))+"\n")

                for i in range(len(total_time)):
                    g.ser.write_b(str(float(total_time[i]))+"\n")
                    g.ser.write_b(str(float(total_voltage[i]))+"\n")
                    time.sleep(0.001)

                valuesNew=f.getFloats(3)
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))
                tag_=tag+" dt="+str("%.6f" % dt)+" before"
                self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
                self.displayData.emit()

                valuesNew=f.getFloats(3)
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))
                # valuesNew.append(float(g.ser.readline().rstrip()))

                tag_=tag+" dt="+str("%.6f" % dt)+" after"

                if max(total_voltage)>=abs(min(total_voltage)):
                    max_ampl=max(total_voltage)
                else:
                    max_ampl=min(total_voltage)


                self.sendData.emit(w,b,valuesNew[0],max_ampl,max(total_time),tag_)
                self.displayData.emit()

            valuesNew=f.getFloats(3)
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))
            # valuesNew.append(float(g.ser.readline().rstrip()))

            tag_=tag+"_e"

            self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
            self.displayData.emit()

        self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        self.finished.emit()

    def make_time_series(self, dt, gain, warp, self_max_spike_time, self_pre_time, \
                         self_pre_voltage, self_post_time, self_post_voltage):
        if dt>0:
            pre_time=[x+dt for x in self_pre_time]
            pre_time.insert(0,0)

            pre_voltage=[0]+self_pre_voltage

            post_time=self_post_time+[self_max_spike_time+dt]
            post_voltage=self_post_voltage+[0]

        elif dt<0:
            post_time=[x+abs(dt) for x in self_post_time]
            post_time.insert(0,0)

            post_voltage=[0]+self_post_voltage

            pre_time=self_pre_time+[self_max_spike_time+abs(dt)]
            pre_voltage=self_pre_voltage+[0]

        else:
            pre_time=self_pre_time
            pre_voltage=self_pre_voltage

            post_time=self_post_time
            post_voltage=self_post_voltage

        total_time=[0]
        total_voltage=[0]   
        index_pre=1
        index_post=1

        # print "pre_voltage", pre_voltage
        # print "pre_time", pre_time
        # print "post_voltage", post_voltage
        # print "post_time", post_time

        pre_voltage=[x*gain for x in pre_voltage]
        post_voltage=[x*gain for x in post_voltage]

        pre_time=[x*warp for x in pre_time]
        post_time=[x*warp for x in post_time]

        while index_pre<len(pre_time) and index_post<len(post_time):
            if pre_time[index_pre]<post_time[index_post]:

                total_time.append(pre_time[index_pre])
                v1=post_voltage[index_post]
                v0=post_voltage[index_post-1]
                t1=post_time[index_post]
                t0=post_time[index_post-1]
                tx=pre_time[index_pre]

                vpost=v1-(v1-v0)*(t1-tx)/(t1-t0)

                total_voltage.append(pre_voltage[index_pre]-vpost)
                index_pre+=1

            elif pre_time[index_pre]>post_time[index_post]:

                total_time.append(post_time[index_post])
                v1=pre_voltage[index_pre]
                v0=pre_voltage[index_pre-1]
                t1=pre_time[index_pre]
                t0=pre_time[index_pre-1]
                tx=post_time[index_post]

                vpre=v1-(v1-v0)*(t1-tx)/(t1-t0)

                total_voltage.append(vpre-post_voltage[index_post])
                index_post+=1
            else:
                total_time.append(post_time[index_post])
                total_voltage.append(pre_voltage[index_pre]-post_voltage[index_post])
                index_pre+=1
                index_post+=1

        total_voltage.append(0)
        total_time.append(max([pre_time[-1],post_time[-1]]))

        # print "Total votlage"
        # print total_voltage
        # print "Total time"
        # print total_time
        
        return total_time, total_voltage


class STDP(QtWidgets.QWidget):
    
    def __init__(self, short=False):
        super(STDP, self).__init__()
        self.short=short
        self.initUI()
        
    def initUI(self):      

        vbox1=QtWidgets.QVBoxLayout()

        #titleLabel = QtWidgets.QLabel('STDP')
        #titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Spike-Timing Dependent Plasticity protocol.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        leftLabels=['Scale voltage', \
                    'Scale time', \
                    'Time step (ms)']
        leftInit=  ['1',\
                    '1', \
                    '1']

        self.leftEdits=[]
        rightLabels=[]
        self.rightEdits=[]

        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)

        if self.short==False:
            gridLayout.setColumnStretch(7,2)

        #setup a line separator
        # lineLeft=QtWidgets.QFrame()
        # lineLeft.setFrameShape(QtWidgets.QFrame.VLine);
        # lineLeft.setFrameShadow(QtWidgets.QFrame.Raised);
        # lineLeft.setLineWidth(1)

        # gridLayout.addWidget(lineLeft, 0, 2, 6, 1)

        self.push_load_pre=QtWidgets.QPushButton("Load Pre Spike")
        self.push_load_pre.clicked.connect(self.load_pre)

        self.check_identical=QtWidgets.QCheckBox("Identical Spikes")
        self.check_identical.setChecked(True)
        self.check_identical.stateChanged.connect(self.handleCheckIdentical)

        self.push_load_post=QtWidgets.QPushButton("Load Post Spike")
        self.push_load_post.setEnabled(False)
        self.push_load_post.clicked.connect(self.load_post)

        self.pre_filename=QtWidgets.QLabel("Filename")
        self.post_filename=QtWidgets.QLabel("Filename")

        gridLayout.addWidget(self.push_load_pre,0,0)
        gridLayout.addWidget(self.pre_filename,0,1)
        gridLayout.addWidget(self.check_identical,1,0)
        gridLayout.addWidget(self.post_filename,2,1)
        gridLayout.addWidget(self.push_load_post,2,0)

        for i in range(len(leftLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i+3,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i+3,1)

        self.leftEdits[0].textChanged.connect(self.scale_voltage)
        self.leftEdits[1].textChanged.connect(self.warp_time)

        #self.check_return=QtWidgets.QCheckBox("Return to G0")
        #gridLayout.addWidget(self.check_return,7,0)

        self.check_single=QtWidgets.QCheckBox("Only single event ->")
        gridLayout.addWidget(self.check_single, 8,0)


        self.gain=1
        self.warp=1

        #vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        hbox=QtWidgets.QHBoxLayout()

        vbox_left=QtWidgets.QVBoxLayout()
        vbox_left.addLayout(gridLayout)
        vbox_left.addStretch()

        hbox.addLayout(vbox_left)

        vbox_spikes=QtWidgets.QVBoxLayout()

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        view=pg.GraphicsLayoutWidget()

        pen_blue=QtGui.QPen()               # pen to draw the amplitude curves
        pen_blue.setColor(QtCore.Qt.blue)   
        pen_green=QtGui.QPen()               # pen to draw the amplitude curves
        pen_green.setColor(QtCore.Qt.green)   
        pen_red=QtGui.QPen()               # pen to draw the amplitude curves
        pen_red.setColor(QtCore.Qt.red)   
        labeltotal_style = {'color': '#000000', 'font-size': '10pt'}

        plot_height=80*g.scaling_factor
        plot_width=300*g.scaling_factor
        ################################################################### PLOT TOTAL ####
        self.plot_total=view.addPlot()
        self.plot_total.setMouseEnabled(False,False)
        self.curve_total=self.plot_total.plot(pen=pg.mkPen(color="00F", width=2)) 
        self.plot_total.getAxis('left').setLabel('Pre-Post', units='V', **labeltotal_style)
        #self.plot_total.setFixedHeight(plot_height)
        self.plot_total.getAxis('left').setGrid(50)
        self.plot_total.getAxis('left').setWidth(60)
        self.plot_total.getAxis('bottom').setGrid(50)
       # self.plot_total.setMinimumWidth(plot_width)


        ################################################################### PLOT PRE ######
        view.nextRow()  # go to next row and add the next plot

        self.plot_p=view.addPlot()
        self.plot_p.setMouseEnabled(False,False)
        self.curve_pre=self.plot_p.plot(pen=pg.mkPen(color="F00", width=2))
        self.curve_post=self.plot_p.plot(pen=pg.mkPen(color="0F0", width=2))
        #self.plot_pre.setFixedHeight(plot_height)
        self.plot_p.getAxis('left').setLabel('Pre and Post', units='V', **labeltotal_style)
        self.plot_p.getAxis('left').setGrid(50)
        self.plot_p.getAxis('bottom').setGrid(50)
        self.plot_p.getAxis('left').setWidth(60)
       #self.plot_p.setMinimumWidth(plot_width)


        vbox_spikes.addWidget(view)

        spike_desc_lay=QtWidgets.QHBoxLayout()
        self.spikes_dt_text=QtWidgets.QLabel("dt=10ms | ")
        self.spikes_order_text=QtWidgets.QLabel("before")
        self.pre_text=QtWidgets.QLabel("Pre")
        self.pre_text.setStyleSheet("color: red")
        self.post_text=QtWidgets.QLabel("Post")
        self.post_text.setStyleSheet("color: green")
        spike_desc_lay.addStretch()
        spike_desc_lay.addWidget(self.spikes_dt_text)
        spike_desc_lay.addWidget(self.pre_text)
        spike_desc_lay.addWidget(self.spikes_order_text)
        spike_desc_lay.addWidget(self.post_text)
        spike_desc_lay.addStretch()

        vbox_spikes.addLayout(spike_desc_lay)

        self.slider=QtWidgets.QSlider(QtCore.Qt.Horizontal, parent=self)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.updateSpikes)
        #self.slider.valueChanged.connect(self.updateDescription)

        vbox_spikes.addWidget(self.slider)

        hbox.addLayout(vbox_spikes)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(hbox)
        self.vW.setContentsMargins(0,0,0,0)
        self.vW.setMaximumHeight(320)
        #self.vW.setMinimumWidth(700)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #scrlArea.setMinimumHeight(330)

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

        self.pre_voltage=[]
        self.pre_time=[]
        self.post_voltage=[]
        self.post_time=[]

        self.dt=0

    def updateDescription(self,value):
        self.spikes_description.setText(str(value))


    def handleCheckIdentical(self, value):
        if value:
            self.push_load_post.setEnabled(False)
        else:
            self.push_load_post.setEnabled(True)

    def load_post(self):
        pass
        print("Loading spike...")

        path = QtCore.QFileInfo(QtWidgets.QFileDialog().getOpenFileName(self, 'Open spike file', "*.txt"))
        #path=fname.getOpenFileName()

        voltage=[]
        time=[]
        name=path.fileName()

        file=QtCore.QFile(path.filePath())
        file.open(QtCore.QIODevice.ReadOnly)

        textStream=QtCore.QTextStream(file)
        error=False
        while not textStream.atEnd():
            line = textStream.readLine()
            try:
                v,t=line.split(", ")
                voltage.append(float(v))
                time.append(float(t))
            except ValueError:
                error=True
        file.close()

        if not error:
            self.post_voltage=voltage
            self.post_time=time
            if self.pre_voltage and self.pre_time:
                self.max_spike_time=max([self.pre_time[-1],self.post_time[-1]])
                self.slider.setValue(50)
                self.fix_spike_timescales()
                self.updateSpikes(50.0)
            else:
                pass
            self.post_filename.setText(path.fileName()) 

        else:
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Invalid spike file! Possible problem with voltage-time series syntax.")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

        print("done")

    def load_pre(self):
        pass
        print("Loading spike...")

        path = QtCore.QFileInfo(QtWidgets.QFileDialog().getOpenFileName(self, 'Open spike file', "*.txt"))
        #path=fname.getOpenFileName()

        voltage=[]
        time=[]
        name=path.fileName()

        file=QtCore.QFile(path.filePath())
        file.open(QtCore.QIODevice.ReadOnly)

        textStream=QtCore.QTextStream(file)
        error=False
        while not textStream.atEnd():
            line = textStream.readLine()
            try:
                v,t=line.split(", ")
                voltage.append(float(v))
                time.append(float(t))
            except ValueError:
                error=True
        file.close()

        if not error:
            self.pre_voltage=voltage
            self.pre_time=time
            if self.check_identical.isChecked():
                self.post_voltage=voltage
                self.post_time=time
                self.max_spike_time=max([self.pre_time[-1],self.post_time[-1]])
                self.slider.setValue(50)
                self.fix_spike_timescales()
                self.updateSpikes(50.0)
            elif self.post_voltage and self.post_time:
                self.max_spike_time=max([self.pre_time[-1],self.post_time[-1]])
                self.fix_spike_timescales()
                self.slider.setValue(50)
                self.updateSpikes(50.0)     
            
            self.pre_filename.setText(path.fileName())           


        else:
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Invalid spike file! Possible problem with voltage-time series syntax.")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

        print("done")

    def scale_voltage(self, value):
        self.gain=float(value)
        self.updateSpikes(self.slider.value())

    def warp_time(self, value):
        self.warp=float(value)
        self.updateSpikes(self.slider.value())

    def fix_spike_timescales(self):
        if self.pre_time[-1]>self.post_time[-1]:
            self.post_time.append(self.pre_time[-1])
            self.post_voltage.append(0)
        elif self.pre_time[-1]<self.post_time[-1]:
            self.pre_time.append(self.post_time[-1])
            self.pre_voltage.append(self.pre_time[-1])

    def updateSpikes(self, sliderValue):
        # Updates the spike figure when the slider is moved.

        self.dt=self.max_spike_time*(self.slider.value()-50)/50.0*self.warp
        if self.dt<0:
            self.spikes_order_text.setText("before")
        else:
            self.spikes_order_text.setText("after")

        msg2="dt=" + str(self.dt) + " s  |  "

        self.spikes_dt_text.setText(msg2)

        if sliderValue>50:
            dt=self.max_spike_time*(sliderValue-50)/50.0
            pre_time=[x+dt for x in self.pre_time]
            pre_time.insert(0,0)

            pre_voltage=[0]+self.pre_voltage

            post_time=self.post_time+[self.max_spike_time+dt]
            post_voltage=self.post_voltage+[0]

        elif sliderValue<50:
            dt=self.max_spike_time*(50-sliderValue)/50.0
            post_time=[x+dt for x in self.post_time]
            post_time.insert(0,0)

            post_voltage=[0]+self.post_voltage

            pre_time=self.pre_time+[self.max_spike_time+dt]
            pre_voltage=self.pre_voltage+[0]

        else:
            pre_time=self.pre_time
            pre_voltage=self.pre_voltage

            post_time=self.post_time
            post_voltage=self.post_voltage

        # Creates the pre and post voltage waveforms

        total_time=[0]
        total_voltage=[0]   
        index_pre=1
        index_post=1

        pre_voltage=[x*self.gain for x in pre_voltage]
        post_voltage=[x*self.gain for x in post_voltage]

        pre_time=[x*self.warp for x in pre_time]
        post_time=[x*self.warp for x in post_time]

        while index_pre<len(pre_time) and index_post<len(post_time):
            if pre_time[index_pre]<post_time[index_post]:

                total_time.append(pre_time[index_pre])
                v1=post_voltage[index_post]
                v0=post_voltage[index_post-1]
                t1=post_time[index_post]
                t0=post_time[index_post-1]
                tx=pre_time[index_pre]

                vpost=v1-(v1-v0)*(t1-tx)/(t1-t0)

                total_voltage.append(pre_voltage[index_pre]-vpost)
                index_pre+=1

            elif pre_time[index_pre]>post_time[index_post]:

                total_time.append(post_time[index_post])
                v1=pre_voltage[index_pre]
                v0=pre_voltage[index_pre-1]
                t1=pre_time[index_pre]
                t0=pre_time[index_pre-1]
                tx=post_time[index_post]

                vpre=v1-(v1-v0)*(t1-tx)/(t1-t0)

                total_voltage.append(vpre-post_voltage[index_post])
                index_post+=1
            else:
                total_time.append(post_time[index_post])
                total_voltage.append(pre_voltage[index_pre]-post_voltage[index_post])
                index_pre+=1
                index_post+=1

        total_voltage.append(0)
        #total_time.append(pre_time[-1])
        total_time.append(max([pre_time[-1],post_time[-1]]))
        
        self.curve_pre.setData(pre_time,pre_voltage)
        self.curve_post.setData(post_time,post_voltage)
        self.curve_total.setData(total_time, total_voltage)


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

    def sendParams(self):
        pass

    def prepare_time_steps(self):
        timeSteps=[]
        if self.check_single.isChecked():
            timeSteps.append(self.dt)
        else:
            timeSteps.append(0)
            timeStep=float(self.leftEdits[2].text())/1000.0
            #timeSteps.append(timeStep)

            max_time=max([self.pre_time[-1],self.post_time[-1]])*self.warp

            i=1
            # Prepares the timesteps (dt's) for STDP measurement run.
            while i*timeStep<=max_time:
                timeSteps.append(i*timeStep)
                timeSteps.append(i*timeStep*-1)
                i+=1
            #print " =========> Timesteps", timeSteps
        return timeSteps

    def programOne(self):
        timeSteps=self.prepare_time_steps()

        if g.ser.port != None:
            job="40"
            g.ser.write_b(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData([[g.w,g.b]],[self.gain, self.warp, self.max_spike_time, \
                self.pre_time, self.pre_voltage, self.post_time, self.post_voltage], \
                timeSteps)
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


            job="40"
            g.ser.write_b(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev,[self.gain, self.warp, self.max_spike_time, \
                self.pre_time, self.pre_voltage, self.post_time, self.post_voltage], \
                timeSteps)
            self.finalise_thread_initialisation()

            self.thread.start()
        

    def programAll(self):
        if g.ser.port != None:
            rangeDev=self.makeDeviceList(True)


            job="40"
            g.ser.write_b(job+"\n")   # sends the job

            self.sendParams()

            self.thread=QtCore.QThread()
            self.getData=getData(rangeDev,[self.gain, self.warp, self.max_spike_time, \
                self.pre_time, self.pre_voltage, self.post_time, self.post_voltage], \
                timeSteps)
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

