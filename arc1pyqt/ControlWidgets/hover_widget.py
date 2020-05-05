####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

import Globals.GlobalFunctions as f


class HoverWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.Popup)

        self.pen=QtGui.QPen(QtGui.QColor(0,0,0))
        self.brush=QtGui.QBrush(QtGui.QColor(0,32,87))

    def reposition(self,x,y):
        self.move(x,y)
        self.show()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRectangle(qp)
        qp.end()

    def drawRectangle(self,qp):
        size=self.size()
        qp.setPen(self.pen)
        qp.setBrush(self.brush)
        qp.drawRect(0,0,100,50)

