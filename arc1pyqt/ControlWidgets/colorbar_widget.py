####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtWidgets


class ColorbarWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # edge of the square
        self.pen=QtGui.QPen(QtGui.QColor(200,200,200))
        # fill of the square
        self.brush=QtGui.QBrush(QtGui.QColor(150,10,100))

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

    def recolor(self,qColor):
        self.pen.setColor(qColor)
        self.brush.setColor(qColor)
        self.update()
