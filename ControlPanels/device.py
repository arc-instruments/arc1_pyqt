####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
from PyQt5 import QtGui, QtWidgets
import numpy as np


import Globals
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g

class device(QtWidgets.QWidget):
    
    def __init__(self,r,c):
        super(device, self).__init__()
        self.r=r
        self.c=c
        self.initUI()
        
    def initUI(self):  
        #decomment here
        #f.cbAntenna.selectDeviceSignal.connect(self.deselect)   # receive the signal that another device has been selected
        #self.setContentsMargins(0,0,15,15)
        self.setStyleSheet("padding-right: 1px; padding-bottom: 1px")

        self.pen=QtGui.QPen(QtGui.QColor(200,200,200))      # Set the initial pen (which draws the edge of a square)
        self.brush=QtGui.QBrush(QtGui.QColor(255,255,255))   # Set the initial brush (which sets the fill of a square) 
        self.setMaximumWidth(200)
        self.setMaximumHeight(200)

    def paintEvent(self, e):    # this is called whenever the Widget is resized
        qp = QtGui.QPainter()   # initialise the Painter Object
        qp.begin(self)          # Begin the painting process
        self.drawRectangle(qp)  # Call the function
        qp.end()                # End the painting process
        
    def drawRectangle(self,qp): 
        size=self.size()        # get the size of this Widget (which by default fills the parent (Layout box))
        qp.setPen(self.pen)     # set the pen
        qp.setBrush(self.brush) # set the brush

        if size.width()/size.height()>2:
            self.setWidth(size.height())

        if size.height()/size.width()>2:
            self.setHeight(size.width())

        qp.drawRect(0,0,size.width(),size.height())     # Draw the new rectangle which fills the entire widget

    #def mouseReleaseEvent(self,event):
    #    #print str(self.r) + ' ' + str(self.c) + ' clicked!'
        # decomment here
    #    f.cbAntenna.selectDeviceSignal.emit(self.r, self.c)       # signal the crossbar antenna that this device has been selected
    #    f.displayUpdate.updateSignal_short.emit()
    #    self.pen.setWidth(4)                    # highlight this device
    #    self.pen.setColor(QtGui.QColor(0,0,0))  # Draw the rectangle with the new Pen and old Brush
    #    self.update()                           # update the display

    def highlight(self):
        self.pen.setColor(QtGui.QColor(0,0,0))
        self.pen.setWidth(4)
        self.update()        

    def dehighlight(self):
        self.pen.setColor(QtGui.QColor(200,200,200))
        self.pen.setWidth(1)
        self.update()

    def disableIt(self):
        self.pen.setWidth(0)
        self.pen.setColor(QtGui.QColor(255,255,255))
        self.brush.setColor(QtGui.QColor(255,255,255))
        self.update()

    def enableIt(self,w,b):
        self.pen.setWidth(1)
        self.pen.setColor(QtGui.QColor(200,200,200))
        #self.pen.setColor(QtGui.QColor(0,0,0))
        try:
            self.recolor(g.Mhistory[w][b][-1][0])
        except IndexError:
            self.colorWhite()
        self.update()

    def colorWhite(self):
        self.brush.setColor(QtGui.QColor(255,255,255))
        self.update()


    def recolor(self,M):

        if M>0:
            try:
                # get the log index out of 255 max values
                idx = int((np.log10(M)-g.minMlog)*255/(g.normMlog))
                color = g.qColorList[idx]
            except OverflowError:
                # Inf
                color = QtGui.QColor(125, 125, 125)
            except ValueError:
                # Inf
                color = QtGui.QColor(125, 125, 125)
            except IndexError:
                # Above 100M but still measurable
                color = g.qColorList[-1]

        self.brush.setColor(color)
        self.update()

    def enterEvent(self, event):
        #print self.geometry().x()
        f.hoverAntenna.displayHoverPanel.emit(self.r,self.c,self.geometry().x(),self.geometry().y(),self.geometry().width(),self.geometry().height())

        pass



class lineNr(QtWidgets.QLabel):

    def __init__(self,n):
        super(lineNr, self).__init__()
        self.setText(str(n))







