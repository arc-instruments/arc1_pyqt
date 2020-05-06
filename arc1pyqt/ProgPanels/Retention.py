####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import time
import numpy as np
import pyqtgraph as pg

from arc1pyqt import Graphics
import arc1pyqt.Globals.GlobalFonts as fonts
import arc1pyqt.Globals.GlobalFunctions as f
import arc1pyqt.Globals.GlobalVars as g
import arc1pyqt.Globals.GlobalStyles as s
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


tag = "RET"


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, deviceList, every, duration, Vread):
        super().__init__()
        self.deviceList=deviceList
        self.every=every
        self.duration=duration
        self.Vread=Vread

    @BaseThreadWrapper.runner
    def run(self):

        self.disableInterface.emit(True)
        global tag

        start=time.time()

        #Initial read
        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write_b("1\n")
            g.ser.write_b(str(int(w))+"\n")
            g.ser.write_b(str(int(b))+"\n")

            Mnow=f.getFloats(1)
            tag_=tag+"_s"
            self.sendData.emit(w,b,Mnow,self.Vread,0,tag_)
            self.displayData.emit()

        while True:
            start_op=time.time()

            for device in self.deviceList:
                w=device[0]
                b=device[1]
                self.highlight.emit(w,b)

                g.ser.write_b("1\n")
                g.ser.write_b(str(int(w))+"\n")
                g.ser.write_b(str(int(b))+"\n")

                Mnow=f.getFloats(1)
                tag_=tag+"_"+ str(time.time())
                self.sendData.emit(w,b,Mnow,self.Vread,0,tag_)
                self.displayData.emit()

            end=time.time()
            time.sleep(self.every-(end-start_op))
            end=time.time()

            if (end-start)>self.duration:
                break

        #Final read
        for device in self.deviceList:
            w=device[0]
            b=device[1]
            self.highlight.emit(w,b)

            g.ser.write_b("1\n")
            g.ser.write_b(str(int(w))+"\n")
            g.ser.write_b(str(int(b))+"\n")

            Mnow=f.getFloats(1)
            tag_=tag+"_e"
            self.sendData.emit(w,b,Mnow,self.Vread,0,tag_)
            self.displayData.emit()
            self.updateTree.emit(w,b)


class Retention(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(\
                title='Retention', \
                description='Measure resistive states for '
                            'extended periods of time.', \
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

        leftLabels=['Read every:', \
                    'Read for:']
        leftInit=  ['1',\
                    '1']

        self.leftEdits=[]
        rightLabels=[]
        self.rightEdits=[]

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

        gridLayout.addWidget(lineLeft, 0, 2, 2, 1)


        for i in range(len(leftLabels)):
            lineLabel=QtWidgets.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(leftLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setText(leftInit[i])
            lineEdit.setValidator(isFloat)
            self.leftEdits.append(lineEdit)

        for i in range(len(rightLabels)):
            lineLabel=QtWidgets.QLabel()
            lineLabel.setText(rightLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, i,4)

            lineEdit=QtWidgets.QLineEdit()
            lineEdit.setValidator(isFloat)
            self.rightEdits.append(lineEdit)


        # ========== ComboBox ===========
        every_lay=QtWidgets.QHBoxLayout()
        duration_lay=QtWidgets.QHBoxLayout()

        self.every_dropDown=QtWidgets.QComboBox()
        self.every_dropDown.setStyleSheet(s.comboStylePulse)

        self.unitsFull=[['s',1],['min',60],['hrs',3600]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.duration_dropDown=QtWidgets.QComboBox()
        self.duration_dropDown.setStyleSheet(s.comboStylePulse)

        self.every_dropDown.insertItems(1,self.units)
        self.every_dropDown.setCurrentIndex(0)
        self.duration_dropDown.insertItems(1,self.units)
        self.duration_dropDown.setCurrentIndex(1)

        gridLayout.addWidget(self.leftEdits[0],0,1)
        gridLayout.addWidget(self.every_dropDown,0,3)
        gridLayout.addWidget(self.leftEdits[1],1,1)
        gridLayout.addWidget(self.duration_dropDown,1,3)

        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

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

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)

    def programDevs(self, devs):
        time_mag=float(self.leftEdits[0].text())
        unit=float(self.multiply[self.every_dropDown.currentIndex()])
        every=time_mag*unit

        time_mag=float(self.leftEdits[1].text())
        unit=float(self.multiply[self.duration_dropDown.currentIndex()])
        duration=time_mag*unit

        wrapper = ThreadWrapper(devs, every, duration, g.Vread)
        self.execute(wrapper, wrapper.run)

    def programOne(self):
        self.programDevs([[g.w, g.b]])

    def programRange(self):
        rangeDev = makeDeviceList(True)
        self.programDevs(rangeDev)

    def programAll(self):
        rangeDev = makeDeviceList(False)
        self.programDevs(rangeDev)

    @staticmethod
    def display(w, b, data, parent=None):
        timePoints = []
        m = []

        for point in data:
            tag = str(point[3])
            tagCut = tag[4:]
            try:
                timePoint = float(tagCut)
                timePoints.append(timePoint)
                m.append(point[0])
            except ValueError:
                pass

        # subtract the first point from all timepoints
        firstPoint = timePoints[0]
        for i in range(len(timePoints)):
            timePoints[i] = timePoints[i] - firstPoint

        view = pg.GraphicsLayoutWidget()
        label_style = {'color': '#000000', 'font-size': '10pt'}

        retentionPlot = view.addPlot()
        retentionCurve = retentionPlot.plot(symbolPen=None,
                symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
        retentionPlot.getAxis('left').setLabel('Resistance', units='Ohms', **label_style)
        retentionPlot.getAxis('bottom').setLabel('Time', units='s', **label_style)
        retentionPlot.getAxis('left').setGrid(50)
        retentionPlot.getAxis('bottom').setGrid(50)

        resLayout = QtWidgets.QHBoxLayout()
        resLayout.addWidget(view)
        resLayout.setContentsMargins(0, 0, 0, 0)

        resultWindow = QtWidgets.QWidget()
        resultWindow.setGeometry(100,100,1000*g.scaling_factor, 400)
        resultWindow.setWindowTitle("Retention: W="+ str(w) + " | B=" + str(b))
        resultWindow.setWindowIcon(Graphics.getIcon('appicon'))
        resultWindow.show()
        resultWindow.setLayout(resLayout)

        retentionPlot.setYRange(min(m)/1.5, max(m)*1.5)
        retentionCurve.setData(np.asarray(timePoints),np.asarray(m))
        resultWindow.update()

        return resultWindow


tags = { 'top': ModTag(tag, "Retention", Retention.display) }
