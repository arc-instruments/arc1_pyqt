####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
from . import device as d


import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s


class cbContainer(QtWidgets.QWidget):
    
    def __init__(self):
        super(cbContainer, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        #mainLayout=QtWidgets.QGridLayout()  # Set grid layout
        #self.setLayout(mainLayout)
        #mainLayout.setSpacing(0)
        layout=QtWidgets.QGridLayout(self)
        self.setLayout(layout)
        layout.setSpacing(0)

        self.cells=[[[] for x in range(0,g.bline_nr+1)] for y in range(0,g.wline_nr+1)]

        #sizePolicy=QtWidgets.QSizePolicy()
        #sizePolicy.setWidthForHeight(True)

        for r in range(1,g.wline_nr+1):           # populate the grid with a "device" in each box
            for c in range(1,g.bline_nr+1):
                self.cells[r][c]=d.device(r,c)
                #self.cells[r][c].setSizePolicy(sizePolicy)
                self.cells[r][c].setMinimumWidth(22)
                self.cells[r][c].setMinimumHeight(14)
                self.cells[r][c].setMaximumWidth(50)
                self.cells[r][c].setMaximumHeight(50)
                self.cells[r][c].setWhatsThis(str(r)+" "+str(c))

                layout.addWidget(self.cells[r][c],r,c)

        for w in range(1,g.wline_nr+1):
            aux=QtWidgets.QLabel()
            aux.setText(str(w))
            aux.setFont(fonts.cbFont)
            layout.addWidget(aux,w,0)

        for b in range(1,g.bline_nr+1):
            aux=QtWidgets.QLabel()
            aux.setText(str(b))
            aux.setFont(fonts.cbFont)
            layout.addWidget(aux,33,b)

        f.cbAntenna.selectDeviceSignal.connect(self.changeDevice)
        f.cbAntenna.deselectOld.connect(self.dummySlot)
        f.cbAntenna.recolor.connect(self.recolor)
        f.SAantenna.disable.connect(self.disableCell)
        f.SAantenna.enable.connect(self.enableCell)

        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.setMouseTracking(True)

        self.rangeRect=QtCore.QRect()

        self.rectWidget=QtWidgets.QWidget(self)
        self.rectWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.installEventFilter(self)
        #self.highlightBox=QtWidgets.QWidget(self)
        #self.highlightBox.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.dragging=False
        #self.rectWidget.setStyleSheet("border: 3px solid red");


    def disableCell(self, w, b):
        self.cells[w][b].disableIt()

    def enableCell(self, w, b):
        self.cells[w][b].enableIt(w,b)

    
    def changeDevice(self, w, b):

        f.cbAntenna.deselectOld.emit()
        self.cells[w][b].highlight()


        f.cbAntenna.deselectOld.disconnect()
        f.cbAntenna.deselectOld.connect(self.cells[w][b].dehighlight)

    def recolor(self, M, w, b):
        self.cells[w][b].recolor(M)

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

            position=a.whatsThis().split(" ")

            w,b=position
            if g.checkSA==False:
                self.changeDevice(int(w),int(b))
                f.cbAntenna.selectDeviceSignal.emit(int(w), int(b))       # signal the crossbar antenna that this device has been selected
                f.displayUpdate.updateSignal_short.emit()
            else:
                if [int(w),int(b)] in g.customArray:
                    self.changeDevice(int(w),int(b))
                    f.cbAntenna.selectDeviceSignal.emit(int(w), int(b))       # signal the crossbar antenna that this device has been selected
                    f.displayUpdate.updateSignal_short.emit()

            if g.sessionMode==2 and g.ser.port != None:
                g.ser.write_b("02\n")
                g.ser.write_b(str(int(w))+"\n")
                g.ser.write_b(str(int(b))+"\n")

        else:
            if self.rectWidget.isVisible():
                self.rectWidget.hide()
            else:
                self.rectWidget.show()

    def mouseMoveEvent(self, event):
        #if self.rubberband.isVisible():
        if self.dragging==True:
            self.rubberband.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            self.rubberband.hide()
            selected = []
            rect = self.rubberband.geometry()
            wList=[]
            bList=[]

            for child in self.findChildren(QtWidgets.QWidget):
                if rect.intersects(child.geometry()):
                    #selected.append(child)
                    position=child.whatsThis().split(" ")
                    try:
                        wList.append(int(position[0]))
                        bList.append(int(position[1]))
                    except ValueError:
                        pass

            minW=min(wList)
            maxW=max(wList)
            minB=min(bList)
            maxB=max(bList)

            g.minW=minW
            g.minB=minB
            g.maxW=maxW
            g.maxB=maxB

            self.devTopLeft=self.cells[minW][minB]
            self.devBotRight=self.cells[maxW][maxB]

            x1=self.devTopLeft.x()-4
            y1=self.devTopLeft.y()-4

            x2=self.devBotRight.x()+self.devBotRight.width()+4
            y2=self.devBotRight.y()+self.devBotRight.height()+4

            self.rangeRect.setCoords(x1,y1,x2,y2)
            
            self.rectWidget.setGeometry(self.rangeRect)
            self.rectWidget.setStyleSheet("border: 3px solid red")
            self.rectWidget.show()

        #QtWidgets.QWidget.mouseMoveEvent(self, event)

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            try:
                x1=self.devTopLeft.x()-4
                y1=self.devTopLeft.y()-4

                x2=self.devBotRight.x()+self.devBotRight.width()+4
                y2=self.devBotRight.y()+self.devBotRight.height()+4

                self.rangeRect.setCoords(x1,y1,x2,y2)
                self.rectWidget.setGeometry(self.rangeRect)

            except AttributeError:
                pass
        return False


    def mouseReleaseEvent(self, event):
        self.dragging=False

    def leaveEvent(self, event):
        f.hoverAntenna.hideHoverPanel.emit()

