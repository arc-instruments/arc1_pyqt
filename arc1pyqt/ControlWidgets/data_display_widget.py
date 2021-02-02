####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
import time
import numpy as np

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np

from .. import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from ..state import DisplayMode
from ..Globals import functions



class DataDisplayWidget(QtWidgets.QWidget):

    __valueFormatter = {
        DisplayMode.RESISTANCE: ('Ω', 'Resistance', lambda r, v: r),
        DisplayMode.CONDUCTANCE: ('S', 'Conductance', lambda r, v: 1.0/r),
        DisplayMode.CURRENT: ('A', 'Current', lambda r, v: v/r),
        DisplayMode.ABS_CURRENT: ('A', 'Abs. Current', lambda r, v: np.abs(v/r))
    }

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        (unit, label, _) = self.__valueFormatter[APP.displayMode]

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # pen to draw the resistance curves
        penM = pg.mkPen('r', width=1)

        # pen to draw the amplitude curves
        penP = pg.mkPen('b', width=1)

        # pen to draw the pulse width curves
        penPW = pg.mkPen(color=QtGui.QColor(QtCore.Qt.darkGreen), width=1)

        brushP=QtGui.QBrush()
        brushP.setColor(QtCore.Qt.blue)

        brushPW=QtGui.QBrush()
        brushPW.setColor(QtCore.Qt.darkGreen)

        self.readSymbol=QtGui.QPainterPath()
        self.readSymbol.moveTo(-3,0)
        self.readSymbol.lineTo(3,0)

        view=pg.GraphicsLayoutWidget()

        self.plot_mem=view.addPlot()
        self.plot_mem.setMouseEnabled(True,False)
        self.curveM=self.plot_mem.plot(pen=penM, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
        labelM_style = {'color': '#000000', 'font-size': '10pt'}
        self.plot_mem.getAxis('left').setLabel(label+'\n', units=unit, **labelM_style)
        self.plot_mem.getAxis('left').setGrid(50)
        self.plot_mem.getAxis('left').setWidth(60)
        self.plot_mem.showAxis('right')
        self.plot_mem.getAxis('right').setWidth(60)
        self.plot_mem.getAxis('bottom').setGrid(50)

        self.plot_mem.getAxis('right').setStyle(showValues=False)

        view.nextRow()

        self.plot_pls=view.addPlot()
        self.plot_pls.setMouseEnabled(True,False)
        self.curveP=self.plot_pls.plot(pen=penP)
        self.curvePMarkers=self.plot_pls.plot(pen=None, symbolPen=None,
                symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)

        self.curveReadMarkers=self.plot_pls.plot(pen=None, symbolPen=(0,0,255),
                symbolBrush=None, symbol=self.readSymbol, symbolSize=6,
                pxMode=True)

        self.plot_pls.setFixedHeight(150)
        labelV_style = {'color': '#000000', 'font-size': '10pt'}
        labelPn_style = {'color': '#000000', 'font-size': '10pt'}
        self.plot_pls.getAxis('left').setLabel('Amplitude (V)', **labelV_style)
        self.plot_pls.getAxis('bottom').setLabel('Pulse Number', **labelPn_style)
        self.plot_pls.getAxis('left').setGrid(50)
        self.plot_pls.getAxis('bottom').setGrid(50)

        self.plot_width=pg.ViewBox()
        self.plot_pls.scene().addItem(self.plot_width)
        self.plot_pls.showAxis('right')
        self.plot_pls.getAxis('right').setLabel('Pulse width', units='s', **labelPn_style)
        self.plot_pls.getAxis('right').setPen(penPW)
        self.plot_width.setXLink(self.plot_pls)
        self.plot_pls.getAxis('right').linkToView(self.plot_width)

        self.plot_width.enableAutoRange(self.plot_width.YAxis,True)

        self.plot_pls.getAxis('left').setWidth(60)
        self.plot_pls.getAxis('right').setWidth(60)

        self.curvePW=pg.ScatterPlotItem(symbol='+')
        self.curvePW.setBrush(brushPW)
        self.curvePW.setPen(penPW)
        self.plot_width.addItem(self.curvePW)

        # link x axes
        self.plot_pls.getViewBox().setXLink(self.plot_mem.getViewBox())

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(view)
        mainLayout.setContentsMargins(0,0,3,3)

        self.log=0

        self.setLayout(mainLayout)

        functions.displayUpdate.updateSignal.connect(self.updateDisplay)
        functions.displayUpdate.updateSignal_short.connect(self.updateDisplay_short)
        functions.displayUpdate.updateLog.connect(self.updateLogScale)
        functions.interfaceAntenna.lastDisplaySignal.connect(self.last_updateDisplay_short)

        self.plot_pls.getViewBox().sigResized.connect(self.updateViews)
        self.plot_width.enableAutoRange(self.plot_width.YAxis,True)
        self.plot_pls.enableAutoRange()

        self.last_display_time=time.time()
        # 20 fps max
        self.frame_time=0.05
        self.min_frame_time=0.05

        self.updateViews()

    def updateLogScale(self,event):
        self.log=event
        self.plot_mem.setLogMode(False, event)
        self.plot_mem.getAxis('left').enableAutoSIPrefix(not(event > 0))


    def wheelEventOverride(self, event):
        pass

    def updateViews2(self):
        self.plot_pls.getViewBox().setGeometry(self.plot_mem.getViewBox().x(),
                self.plot_pls.getViewBox().y(),
                self.plot_pls.getViewBox().width(),
                self.plot_pls.getViewBox().height())

    def updateViews(self):

        self.plot_width.setGeometry(self.plot_pls.getViewBox().sceneBoundingRect())
        self.plot_width.linkedViewChanged(self.plot_pls.getViewBox(),self.plot_width.XAxis)

    def last_updateDisplay_short(self):
        self.bulk_updateDisplay(CB.word, CB.bit, 2, APP.displayPoints, 99)

    def updateDisplay_short(self):
        self.updateDisplay(CB.word, CB.bit, 2, APP.displayPoints, 99)

    def updateDisplay(self, w, b, type, points, slider):

        # type = 1: display all data
        # type = 2: display a nr of points
        firstPoint=0
        lastPoint=1

        timenow=time.time()
        if timenow-self.last_display_time>self.frame_time:
            self.last_display_time=time.time()
            self.bulk_updateDisplay(w,b,type,points,slider)
            stopDisplayTime=time.time()
            last_frame_time=stopDisplayTime-self.last_display_time
            if last_frame_time<self.min_frame_time:
                self.frame_time=self.min_frame_time
            else:
                self.frame_time=last_frame_time

    def bulk_updateDisplay(self,w,b,type,points,slider):

        (unit, label, func) = self.__valueFormatter[APP.displayMode]

        self.plot_mem.getAxis('left').setLabel(label + '\n', units=unit)

        lastPoint2 = len(CB.history[CB.word][CB.bit])
        lastPoint = lastPoint2
        firstPoint = lastPoint-points+1
        if firstPoint < 0:
            firstPoint = 0
        if lastPoint < 1:
            lastPoint = 1

        if lastPoint2:
            if type == 1:
                firstPoint = 0
                lastPoint = lastPoint2
                self.plot_mem.setXRange(0, lastPoint-1)
                self.plot_pls.setXRange(0, lastPoint-1)
            else:
                self.plot_mem.setXRange(max(lastPoint-points,0),lastPoint-1)
                self.plot_pls.setXRange(max(lastPoint-points,0),lastPoint-1)

            Mlist=[]
            PList=[]
            PWList=[]
            PMarkerList=[]
            ReadMarkerList=[]

            for item in CB.history[CB.word][CB.bit][firstPoint:lastPoint]:
                if self.log > 0:
                    Mlist.append(np.abs(func(item[0], item[1])))
                else:
                    Mlist.append(func(item[0], item[1]))
                PList.append(0)
                PList.append(item[1])
                PList.append(0)
                if (item[2]==0):
                    PMarkerList.append(np.nan)
                    PWList.append(np.nan)
                else:
                    PMarkerList.append(item[1])
                    PWList.append(item[2])

                ReadMarkerList.append(item[5])

            self.plot_pls.enableAutoRange()

            pNrList=np.asarray(range(firstPoint,lastPoint))

            self.curveM.setData(pNrList,np.asarray(Mlist))
            self.curveP.setData(np.repeat(pNrList,3),np.asarray(PList))
            self.curvePW.setData(pNrList,np.asarray(PWList))
            self.curvePMarkers.setData(pNrList,np.asarray(PMarkerList))
            self.curveReadMarkers.setData(pNrList, np.asarray(ReadMarkerList))

            if self.log==0:
                # If any infinite numbers arise, deal appropriately.
                self.plot_mem.setYRange(min(Mlist)/1.2,self.max_without_inf(Mlist)*1.2)
            else:
                self.plot_mem.setYRange(np.log10(min(Mlist)/1.2),np.log10(self.max_without_inf(Mlist)*1.2))

        else:
            self.curveM.setData([],[])
            self.curveP.setData([],[])
            self.curvePW.setData([],[])
            self.curvePMarkers.setData([],[])
            self.plot_mem.setYRange(10000,20000)
            self.plot_mem.setXRange(0,1)
            self.plot_pls.setXRange(0,1)

        self.update()

    def max_without_inf(self, lst):
        maxim=0
        for value in lst:
            if value>maxim and value!=np.inf:
                maxim=value

        return maxim

