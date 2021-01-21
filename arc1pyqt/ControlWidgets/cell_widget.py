####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtWidgets


class CellWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set the initial pen (which draws the edge of a square)
        self.pen=QtGui.QPen(QtGui.QColor(200,200,200))
        # Set the initial brush (which sets the fill of a square)
        self.brush=QtGui.QBrush(QtGui.QColor(255,255,255))

    # this is called whenever the Widget is resized
    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRectangle(qp)
        qp.end()

    def drawRectangle(self,qp):
        size=self.size()
        qp.setPen(self.pen)
        qp.setBrush(self.brush)
        qp.drawRect(0,0,size.width(),size.height())

