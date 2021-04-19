####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from . import DeviceWidget
from . import MatrixWidget

from .. import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from ..Globals import functions


class CrossbarContainerWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout=QtWidgets.QGridLayout(self)
        self.setLayout(layout)
        layout.setSpacing(0)
        self.matrix = MatrixWidget(words=HW.conf.words, bits=HW.conf.bits)
        layout.addWidget(self.matrix)

        functions.cbAntenna.selectDeviceSignal.connect(self.changeDevice)
        functions.cbAntenna.deselectOld.connect(self.dummySlot)
        functions.cbAntenna.recolor.connect(self.recolor)
        functions.SAantenna.disable.connect(self.disableCell)
        functions.SAantenna.enable.connect(self.enableCell)

        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.setMouseTracking(True)

        self.rangeRect=QtCore.QRect()

        self.rectWidget=QtWidgets.QWidget(self)
        self.rectWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.installEventFilter(self)

        self.dragging=False

    def disableCell(self, w, b):
        self.matrix.cells[w][b].disableIt()

    def enableCell(self, w, b):
        self.matrix.cells[w][b].enableIt(w,b)

    def changeDevice(self, w, b):

        functions.cbAntenna.deselectOld.emit()
        self.matrix.cells[w][b].highlight()

        functions.cbAntenna.deselectOld.disconnect()
        functions.cbAntenna.deselectOld.connect(self.matrix.cells[w][b].dehighlight)

    def recolor(self, M, w, b):
        self.matrix.cells[w][b].recolor(M)

    def dummySlot(self):
        pass

    def mousePressEvent(self, event):
        #if event==QtCore.Qt.LeftButton:
        if event.button()==1:
            self.origin = event.pos()
            self.rubberband.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.rubberband.show()
            self.dragging=True

            a=self.childAt(self.origin)

            try:
                position=a.whatsThis().split(" ")
            except ValueError:
                # this is probably an invalid position
                return

            w,b = position
            if CB.checkSA==False:
                self.changeDevice(int(w),int(b))
                # signal the crossbar antenna that this device has been selected
                functions.cbAntenna.selectDeviceSignal.emit(int(w), int(b))
                functions.displayUpdate.updateSignal_short.emit()
            else:
                if (int(w),int(b)) in CB.customArray:
                    self.changeDevice(int(w),int(b))
                    # signal the crossbar antenna that this device has been selected
                    functions.cbAntenna.selectDeviceSignal.emit(int(w), int(b))
                    functions.displayUpdate.updateSignal_short.emit()


            if  HW.ArC is not None and HW.conf.sessionmode == 2:
                HW.ArC.write_b("02\n")
                HW.ArC.queue_select(w, b)

        else:
            if self.rectWidget.isVisible():
                self.rectWidget.hide()
            else:
                self.rectWidget.show()

    def mouseMoveEvent(self, event):
        if self.dragging==True:
            self.rubberband.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.rubberband.hide()
            selected = []
            rect = self.rubberband.geometry()
            wList=[]
            bList=[]

            for child in self.findChildren(QtWidgets.QWidget):
                if rect.intersects(child.geometry()):
                    position=child.whatsThis().split(" ")
                    try:
                        wList.append(int(position[0]))
                        bList.append(int(position[1]))
                    except ValueError:
                        pass

            if len(wList) == 0 or len(bList) == 0:
                return

            minW = min(wList)
            maxW = max(wList)
            minB = min(bList)
            maxB = max(bList)

            CB.limits['words'] = (minW, maxW)
            CB.limits['bits'] = (minB, maxB)

            self.devTopLeft=self.matrix.cells[minW][minB]
            self.devBotRight=self.matrix.cells[maxW][maxB]

            x1=self.devTopLeft.x()
            y1=self.devTopLeft.y()

            x2=self.devBotRight.x()+self.devBotRight.width()
            y2=self.devBotRight.y()+self.devBotRight.height()

            self.rangeRect.setCoords(x1+5,y1+5,x2+8,y2+8)

            self.rectWidget.setGeometry(self.rangeRect)
            self.rectWidget.setStyleSheet("border: 3px solid red")
            self.rectWidget.show()

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            try:
                x1=self.devTopLeft.x()
                y1=self.devTopLeft.y()

                x2=self.devBotRight.x()+self.devBotRight.width()
                y2=self.devBotRight.y()+self.devBotRight.height()

                self.rangeRect.setCoords(x1+5,y1+5,x2+8,y2+8)
                self.rectWidget.setGeometry(self.rangeRect)

            except AttributeError:
                pass
        return False

    def mouseReleaseEvent(self, event):
        self.dragging=False

    def leaveEvent(self, event):
        functions.hoverAntenna.hideHoverPanel.emit()

