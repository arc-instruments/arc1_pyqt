import sys
import os
import numpy as np
from PyQt4 import QtGui
from PyQt4 import QtCore
import pyqtgraph as pg
import numpy as np

sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s


class dataDisplay_panel(QtGui.QWidget):
    
    def __init__(self):
        super(dataDisplay_panel, self).__init__()
        self.initUI()
        
    def initUI(self):

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        penM=QtGui.QPen()               # pen to draw the resistance curves
        penM.setColor(QtCore.Qt.red)

        penP=QtGui.QPen()               # pen to draw the amplitude curves
        penP.setColor(QtCore.Qt.blue)    

        penPW=QtGui.QPen()
        penPW.setColor(QtCore.Qt.darkGreen)

        brushP=QtGui.QBrush()
        brushP.setColor(QtCore.Qt.blue)

        brushPW=QtGui.QBrush()
        brushPW.setColor(QtCore.Qt.darkGreen)

        self.readSymbol=QtGui.QPainterPath()
        self.readSymbol.moveTo(-3,0)
        self.readSymbol.lineTo(3,0)
        #self.readSymbol.lineTo(5,1)
        #self.readSymbol.lineTo(-4,1)
        #self.readSymbol.closeSubpath()

        view=pg.GraphicsLayoutWidget()

        self.plot_mem=view.addPlot()
        #self.plot_mem.getViewBox().wheelEvent.connect
        self.plot_mem.setMouseEnabled(True,False)
        #self.plot_mem.getViewBox().sigYRangeChanged.connect(self.rangeChangedViaMouse)
        self.curveM=self.plot_mem.plot(pen=penM, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
        #self.plot_mem.enableAutoRange(self.plot_mem.getAxis('left'),True)
        labelM_style = {'color': '#000000', 'font-size': '10pt'}
        self.plot_mem.getAxis('left').setLabel('Resistance\n', units='Ohms', **labelM_style)
        self.plot_mem.getAxis('left').setGrid(50)
        self.plot_mem.getAxis('left').setWidth(60)
        self.plot_mem.showAxis('right')
        self.plot_mem.getAxis('right').setWidth(60)
        self.plot_mem.getAxis('bottom').setGrid(50)
        
        self.plot_mem.getAxis('right').setStyle(showValues=False)

        view.nextRow()  # go to next row and add the next plot

        self.plot_pls=view.addPlot()
        self.plot_pls.setMouseEnabled(True,False)
        self.curveP=self.plot_pls.plot(pen=penP)
        self.curvePMarkers=self.plot_pls.plot(pen=None, symbolPen=None, symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)

        self.curveReadMarkers=self.plot_pls.plot(pen=None, symbolPen=(0,0,255), symbolBrush=None, symbol=self.readSymbol, symbolSize=6, pxMode=True)


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
        #self.plot_pls.getAxis('right').setLogMode(True)
        self.plot_pls.getAxis('right').setPen(penPW)
        self.plot_width.setXLink(self.plot_pls)
        self.plot_pls.getAxis('right').linkToView(self.plot_width)

        #print self.plot_pls.getAxis('right')
        self.plot_width.enableAutoRange(self.plot_width.YAxis,True)
        
        self.plot_pls.getAxis('left').setWidth(60)
        self.plot_pls.getAxis('right').setWidth(60)

        self.curvePW=pg.ScatterPlotItem(symbol='+')
        self.curvePW.setBrush(brushPW)
        self.curvePW.setPen(penPW)
        self.plot_width.addItem(self.curvePW)

        #self.plot_pls.getAxis('right').setLogMode(True)

        self.plot_pls.getViewBox().setXLink(self.plot_mem.getViewBox()) # link x axes

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(view)
        mainLayout.setContentsMargins(0,0,3,3)

        self.log=0

        self.setLayout(mainLayout)

        f.displayUpdate.updateSignal.connect(self.updateDisplay)
        f.displayUpdate.updateSignal_short.connect(self.updateDisplay_short)
        f.displayUpdate.updateLog.connect(self.updateLogScale)

        # make the size of the viewboxes of PWplot and pusle plot the same
        self.plot_pls.getViewBox().sigResized.connect(self.updateViews)
        self.updateViews()

   # def rangeChangedViaMouse(self, event):
     #   print "-"
     #   print event
    def updateLogScale(self,event):
        self.log=event
        self.plot_mem.setLogMode(False,event)

    def wheelEventOverride(self, event):
        print event
        print "Wheel in motion"

    def updateViews2(self):
        self.plot_pls.getViewBox().setGeometry(self.plot_mem.getViewBox().x(), self.plot_pls.getViewBox().y(), self.plot_pls.getViewBox().width(), self.plot_pls.getViewBox().height())

    def updateViews(self):

        self.plot_width.setGeometry(self.plot_pls.getViewBox().sceneBoundingRect())
        self.plot_width.linkedViewChanged(self.plot_pls.getViewBox(),self.plot_width.XAxis)

    def updateDisplay_short(self):
        self.updateDisplay(g.w,g.b,2,g.dispPoints,99)

    def updateDisplay(self,w,b,type,points,slider):
        # type = 1: display all data
        # type = 2: display a nr of points
        firstPoint=0
        lastPoint=1
        #self.plot_mem.enableAutoRange()

        # Changed here
        """
        if type == 1:
            firstPoint=0
            lastPoint=len(g.Mhistory[w][b])-1
            pNrList=np.linspace(0,len(g.Mhistory[g.w][g.b])-1,len(g.Mhistory[g.w][g.b]))
        
        if type == 2:
            if points>=len(g.Mhistory[w][b]):
                firstPoint=0
                lastPoint=len(g.Mhistory[w][b])-1
                pNrList=np.asarray(range(lastPoint+1))
            else:
                firstPoint=int(len(g.Mhistory[w][b])-points)
                lastPoint=firstPoint+points
                pNrList=np.asarray(range(firstPoint,lastPoint+1))
        
        """

        lastPoint2=len(g.Mhistory[g.w][g.b])
        lastPoint=lastPoint2
        firstPoint=lastPoint-points+1
        if firstPoint<0:
            firstPoint=0
        if lastPoint<1:
            lastPoint=1

        if lastPoint2:
            if type==1:
                firstPoint=0
                lastPoint=lastPoint2
                self.plot_mem.setXRange(0,lastPoint-1)
                self.plot_pls.setXRange(0,lastPoint-1)
            else:
                self.plot_mem.setXRange(max(lastPoint-points,0),lastPoint-1)
                self.plot_pls.setXRange(max(lastPoint-points,0),lastPoint-1)
        
            Mlist=[]
            PList=[]
            PWList=[]
            PMarkerList=[]
            ReadMarkerList=[]

            for item in g.Mhistory[g.w][g.b][firstPoint:lastPoint]:
                Mlist.append(item[0])
                PList.append(0)
                PList.append(item[1])
                PList.append(0)
                if (item[2]==0):
                    PMarkerList.append(None)
                    PWList.append(None)
                else:
                    PMarkerList.append(item[1])
                    PWList.append(item[2])
                
                ReadMarkerList.append(item[5])

            pNrList=np.asarray(range(firstPoint,lastPoint))
            
            # Till  here
            #PList=[]
            #for item in g.Mhistory[g.w][g.b]:
            #   MList.append
            #    PList.append(0)
            #    PList.append(item[1])
            #    PList.append(0)

            #Mlist=np.asarray(g.Mhistory[g.w][g.b][firstPoint:lastPoint+1])
            #lastPoint=len(g.Mhistory[g.w][g.b])-1
            #pNrList=np.asarray(range(lastPoint+1))

            #Mlist=[el[0] for el in g.Mhistory[g.w][g.b]]
            #PWList=[el[2] for el in g.Mhistory[g.w][g.b]]
            #PMarkerList=[el[1] for el in g.Mhistory[g.w][g.b]]

            self.curveM.setData(pNrList,np.asarray(Mlist))
            self.curveP.setData(np.repeat(pNrList,3),np.asarray(PList))
            self.curvePW.setData(pNrList,np.asarray(PWList))
            self.curvePMarkers.setData(pNrList,np.asarray(PMarkerList))
            self.curveReadMarkers.setData(pNrList, np.asarray(ReadMarkerList))

            #self.curveM.setData(pNrList,g.MList[g.w][g.b])
            #self.curveP.setData(np.repeat(pNrList,3),g.PList[g.w][g.b])
            #self.curvePW.setData(pNrList,g.PWList[g.w][g.b])
            #self.curvePMarkers.setData(pNrList,g.PMarkerList[w][b])
            #print min(Mlist)/2
            #print max(Mlist)*2
            
            #self.plot_width.setYRange(np.log10(min(PWList)/2),np.log10(max(PWList)*1.5))
            #self.plot_pulses.setYRange(min(PList)-1,max(PList)+1)
            self.plot_width.enableAutoRange(self.plot_width.YAxis,True)
            #try:
            if self.log==0: 
                self.plot_mem.setYRange(min(Mlist)/1.2,max(Mlist)*1.2)
            else:
                self.plot_mem.setYRange(np.log10(min(Mlist)/1.2),np.log10(max(Mlist)*1.2))
        #except ValueError:
        else:
            self.curveM.setData([],[])
            self.curveP.setData([],[])
            self.curvePW.setData([],[])
            self.curvePMarkers.setData([],[])
            self.plot_mem.setYRange(10000,20000)
            self.plot_mem.setXRange(0,1)
            self.plot_pls.setXRange(0,1)

        self.update()
        
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = dataDisplay_panel()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()  