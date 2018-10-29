####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

#import Globals
import Globals.GlobalFunctions as f

class hoverPanel(QtWidgets.QWidget):
    
    def __init__(self):
        super(hoverPanel, self).__init__()
        self.initUI()
        
    def initUI(self): 
        self.setWindowFlags(Qt.Popup)

        self.pen=QtGui.QPen(QtGui.QColor(0,0,0))      # Set the initial pen (which draws the edge of a square)
        self.brush=QtGui.QBrush(QtGui.QColor(0,32,87))   # Set the initial brush (which sets the fill of a square)

    def reposition(self,x,y):
        self.move(x,y)
        self.show()

        pass 

    def paintEvent(self, e):    # this is called whenever the Widget is resized
        qp = QtGui.QPainter()   # initialise the Painter Object
        qp.begin(self)          # Begin the painting process
        self.drawRectangle(qp)  # Call the function
        qp.end()                # End the painting process
        
    def drawRectangle(self,qp): 
        size=self.size()        # get the size of this Widget (which by default fills the parent (Layout box))
        qp.setPen(self.pen)     # set the pen
        qp.setBrush(self.brush) # set the brush
        qp.drawRect(0,0,100,50)     # Draw the new

