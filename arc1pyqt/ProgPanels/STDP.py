####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import re
import numpy as np
import pyqtgraph as pg
import time

from arc1pyqt import Graphics
from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag="stdp"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList, values, timeSteps):
        super().__init__()
        self.deviceList=deviceList
        self.gain=values[0]
        self.warp=values[1]
        self.max_spike_time=values[2]
        self.pre_time=values[3]
        self.pre_voltage=values[4]
        self.post_time=values[5]
        self.post_voltage=values[6]
        self.timeSteps=timeSteps

    @BaseThreadWrapper.runner
    def run(self):

        global tag

        HW.ArC.write_b(str(int(len(self.deviceList)))+"\n")

        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            HW.ArC.queue_select(w, b)

            # store a first read
            valuesNew=HW.ArC.read_floats(3)
            tag_=tag+"_s"
            self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
            self.displayData.emit()

            HW.ArC.write_b(str(int(len(self.timeSteps)))+"\n")

            for dt in self.timeSteps:
                #dt/=self.warp # bug fix
                total_time, total_voltage=self.make_time_series(dt/self.warp, self.gain, self.warp, self.max_spike_time, self.pre_time, \
                             self.pre_voltage, self.post_time, self.post_voltage)

                HW.ArC.write_b(str(int(len(total_time)))+"\n")

                for i in range(len(total_time)):
                    HW.ArC.write_b(str(float(total_time[i]))+"\n")
                    HW.ArC.write_b(str(float(total_voltage[i]))+"\n")
                    time.sleep(0.001)

                valuesNew=HW.ArC.read_floats(3)
                tag_=tag+" dt="+str("%.6f" % dt)+" before"
                self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
                self.displayData.emit()

                valuesNew=HW.ArC.read_floats(3)

                tag_=tag+" dt="+str("%.6f" % dt)+" after"

                if max(total_voltage)>=abs(min(total_voltage)):
                    max_ampl=max(total_voltage)
                else:
                    max_ampl=min(total_voltage)


                self.sendData.emit(w,b,valuesNew[0],max_ampl,max(total_time),tag_)
                self.displayData.emit()

            valuesNew=HW.ArC.read_floats(3)

            tag_=tag+"_e"

            self.sendData.emit(w,b,valuesNew[0],valuesNew[1],valuesNew[2],tag_)
            self.displayData.emit()

            self.updateTree.emit(w,b)

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

        return total_time, total_voltage


class STDP(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title="STDP", \
                description="Spike-Timing Dependent Plasticity protocol.", \
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

        leftLabels=['Scale voltage', \
                    'Scale time', \
                    'Time step (ms)']
        leftInit=  ['1',\
                    '1', \
                    '1']

        self.leftEdits=[]

        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)

        if self.short==False:
            gridLayout.setColumnStretch(7,2)

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

        self.check_single=QtWidgets.QCheckBox("Only single event")
        gridLayout.addWidget(self.check_single, 8,0)

        self.gain=1
        self.warp=1

        vbox1.addWidget(titleLabel)
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

        # pen to draw the amplitude curves
        pen_blue=QtGui.QPen()
        pen_blue.setColor(QtCore.Qt.blue)

        # pen to draw the amplitude curves
        pen_green=QtGui.QPen()
        pen_green.setColor(QtCore.Qt.green)

        # pen to draw the amplitude curves
        pen_red=QtGui.QPen()
        pen_red.setColor(QtCore.Qt.red)

        labeltotal_style = {'color': '#000000', 'font-size': '10pt'}

        plot_height=80*APP.scalingFactor
        plot_width=300*APP.scalingFactor

        self.plot_total=view.addPlot()
        self.plot_total.setMouseEnabled(False,False)
        self.curve_total=self.plot_total.plot(pen=pg.mkPen(color="00F", width=2))
        self.plot_total.getAxis('left').setLabel('Pre-Post', units='V', **labeltotal_style)
        #self.plot_total.setFixedHeight(plot_height)
        self.plot_total.getAxis('left').setGrid(50)
        self.plot_total.getAxis('left').setWidth(60)
        self.plot_total.getAxis('bottom').setGrid(50)

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

        vbox_spikes.addWidget(self.slider)

        hbox.addLayout(vbox_spikes)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(hbox)
        self.vW.setContentsMargins(0,0,0,0)
        self.vW.setMaximumHeight(320)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scrlArea.installEventFilter(self)

        vbox1.addWidget(scrlArea)
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
        self.gridLayout=gridLayout

        self.pre_voltage = []
        self.pre_time = []
        self.post_voltage = []
        self.post_time = []
        self.pre_full_filename = None
        self.post_full_filename = None

        self.dt=0

        self.registerPropertyWidget(self.leftEdits[0], 'vscale')
        self.registerPropertyWidget(self.leftEdits[1], 'tscale')
        self.registerPropertyWidget(self.leftEdits[2], 'tstep')
        self.registerPropertyWidget(self.check_identical, 'identical_spikes')
        self.registerPropertyWidget(self.check_single, 'single_event')

    def updateDescription(self,value):
        self.spikes_description.setText(str(value))

    def handleCheckIdentical(self, value):
        if value:
            self.push_load_post.setEnabled(False)
        else:
            self.push_load_post.setEnabled(True)

    def load_post(self, filePath=None):

        # if no filename provided, ask for one
        if not filePath:
            openFileName = QtWidgets.QFileDialog().getOpenFileName(self,
                    'Open spike file', "*.txt")[0]
            path = QtCore.QFileInfo(openFileName)
        else:
            path = QtCore.QFileInfo(filePath)

        voltage = []
        time = []

        try:
            arraydata = np.loadtxt(path.absoluteFilePath(), dtype=float,
                    delimiter=',', comments='#')

            for row in arraydata:
                (v, t) = row
                voltage.append(v)
                time.append(t)

            self.post_voltage=voltage
            self.post_time=time
            if self.pre_voltage and self.pre_time:
                self.max_spike_time=max([self.pre_time[-1],self.post_time[-1]])
                self.slider.setValue(50)
                self.fix_spike_timescales()
                self.updateSpikes(50.0)

            self.post_full_filename = path.canonicalFilePath()
            self.post_filename.setText(path.baseName())

        except BaseException as exc:
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Invalid spike file! " +
                    "Possible problem with voltage-time series syntax.")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

    def load_pre(self, filePath=None):

        # if no filename provided, ask for one
        if not filePath:
            openFileName = QtWidgets.QFileDialog().getOpenFileName(self,
                    'Open spike file', "*.txt")[0]
            path = QtCore.QFileInfo(openFileName)
        else:
            path = QtCore.QFileInfo(filePath)

        voltage = []
        time = []

        try:
            arraydata = np.loadtxt(path.absoluteFilePath(), dtype=float,
                    delimiter=',', comments='#')

            for row in arraydata:
                (v, t) = row
                voltage.append(v)
                time.append(t)

            self.pre_voltage = voltage
            self.pre_time = time
            if self.check_identical.isChecked():
                self.post_voltage = voltage
                self.post_time = time
                self.max_spike_time = max([self.pre_time[-1],self.post_time[-1]])
                self.slider.setValue(50)
                self.fix_spike_timescales()
                self.updateSpikes(50.0)
            elif self.post_voltage and self.post_time:
                self.max_spike_time = max([self.pre_time[-1], self.post_time[-1]])
                self.fix_spike_timescales()
                self.slider.setValue(50)
                self.updateSpikes(50.0)

            self.pre_full_filename = path.canonicalFilePath()
            self.pre_filename.setText(path.baseName())

        except BaseException as exc:
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Invalid spike file! " +
                    "Possible problem with voltage-time series syntax.")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

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

    def extractPanelData(self):
        data = super().extractPanelData()

        data['pre_filename'] = self.pre_full_filename
        data['post_filename'] = self.post_full_filename
        data['slider'] = self.slider.value()

        return data

    def setPanelData(self, data):

        # prevent the text edit events from firing
        # because the panel data are not fully
        # initialised
        self.leftEdits[0].textChanged.disconnect()
        self.leftEdits[1].textChanged.disconnect()
        super().setPanelData(data)

        self.load_pre(data['pre_filename'])
        if data['post_filename']:
            self.load_post(data['post_filename'])

        self.slider.setValue(data['slider'])

        # reconnect the events above
        self.leftEdits[0].textChanged.connect(self.scale_voltage)
        self.leftEdits[1].textChanged.connect(self.warp_time)

        # and force them to fire to make sure everything is
        # up to date
        self.scale_voltage(self.leftEdits[0].text())
        self.warp_time(self.leftEdits[1].text())
        self.updateSpikes(self.slider.value())

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

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
        self.programDevs([[CB.word, CB.bit]])

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def programDevs(self, devs):
        job = "40"
        timeSteps = self.prepare_time_steps()

        HW.ArC.write_b(job+"\n")
        self.sendParams()

        wrapper = ThreadWrapper(devs, [self.gain, self.warp, self.max_spike_time, \
            self.pre_time, self.pre_voltage, self.post_time, self.post_voltage], \
            timeSteps)
        self.execute(wrapper, wrapper.run)

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    @staticmethod
    def display(w, b, raw, parent=None):

        reg = re.compile(r'-?[0-9\.]+')

        i = 0
        list_dt = []
        Mbefore = 0
        Mafter = 0
        dG = []
        dt = 0

        while i < len(raw):

            # find the STDP tag
            stdp_tag = str(raw[i][3])

            if "before" in stdp_tag:
                # register resistances before and after
                Mbefore = raw[i][0]
                Mafter = raw[i+1][0]

                # append delta Ts and delta Gs
                dt = float(re.findall(reg, stdp_tag)[0])
                list_dt.append(dt)
                dG.append((1/Mafter-1/Mbefore)/(1/Mbefore))
                i += 2
            else:
                i += 1

        resultWindow = QtWidgets.QWidget()
        resultWindow.setGeometry(100,100,500,500)
        resultWindow.setWindowTitle("STDP: W="+ str(w) + " | B=" + str(b))
        resultWindow.setWindowIcon(Graphics.getIcon('appicon'))
        resultWindow.show()

        view = pg.GraphicsLayoutWidget()
        label_style = {'color': '#000000', 'font-size': '10pt'}

        plot_stdp = view.addPlot()
        curve_stdp = plot_stdp.plot(pen=None, symbolPen=None, \
                symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
        plot_stdp.getAxis('left').setLabel('dG/G0', **label_style)
        plot_stdp.getAxis('bottom').setLabel('deltaT', units='s', **label_style)
        plot_stdp.getAxis('left').setGrid(50)
        plot_stdp.getAxis('bottom').setGrid(50)
        curve_stdp.setData(np.asarray(list_dt),np.asarray(dG))

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(view)
        layout.setContentsMargins(0,0,0,0)

        resultWindow.setLayout(layout)

        return resultWindow


tags = { 'top': ModTag(tag, "STDP", STDP.display) }
