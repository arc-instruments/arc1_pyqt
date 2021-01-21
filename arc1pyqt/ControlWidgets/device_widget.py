####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import numpy as np
from PyQt5 import QtGui, QtWidgets

from .. import Globals
from ..Globals import functions
from .common import resistanceColorGradient

from .. import state
CB = state.crossbar
from .. import constants


class DeviceWidget(QtWidgets.QWidget):

    def __init__(self, r, c, passive=False):
        super().__init__()
        self.r=r
        self.c=c
        self.passive = passive
        self.initUI()

    def initUI(self):

        self.setStyleSheet("padding-right: 1px; padding-bottom: 1px")

        self.pen=QtGui.QPen(QtGui.QColor(200,200,200))
        self.brush=QtGui.QBrush(QtGui.QColor(255,255,255))
        self.setMaximumWidth(200)
        self.setMaximumHeight(200)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRectangle(qp)
        qp.end()

    def drawRectangle(self,qp):
        size=self.size()
        qp.setPen(self.pen)
        qp.setBrush(self.brush)

        # Draw the new rectangle which fills the entire widget
        qp.drawRect(0,0,size.width(),size.height())

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
        try:
            self.recolor(CB.history[w][b][-1][0])
        except IndexError:
            self.colorWhite()
        self.update()

    def colorWhite(self):
        self.brush.setColor(QtGui.QColor(255,255,255))
        self.update()


    def recolor(self,M):

        minMlog=np.log10(constants.MIN_RES)
        normMlog=np.log10(constants.MAX_RES) - minMlog

        if M>0:
            try:
                # get the log index out of 255 max values
                idx = int((np.log10(M)-minMlog)*255/(normMlog))
                color = resistanceColorGradient[idx]
            except OverflowError:
                # Inf
                color = QtGui.QColor(125, 125, 125)
            except ValueError:
                # Inf
                color = QtGui.QColor(125, 125, 125)
            except IndexError:
                # Above 100M but still measurable
                color = resistanceColorGradient[-1]

        self.brush.setColor(color)
        self.update()

    def enterEvent(self, event):
        if not self.passive:
            functions.hoverAntenna.displayHoverPanel.emit(self.r, self.c,
                    self.geometry().x(), self.geometry().y(),
                    self.geometry().width(), self.geometry().height())

