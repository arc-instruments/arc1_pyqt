####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
from . import device as d
from . import colorBarSlice as cBS

import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s

from . import cbContainer
from . import hoverPanel as hP


class crossbar_panel(QtWidgets.QWidget):
    
    def __init__(self):
        super(crossbar_panel, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        #mainLayout=QtGui.QGridLayout()  # Set grid layout
        #self.setLayout(mainLayout)
        #mainLayout.setSpacing(0)

        f.hoverAntenna.displayHoverPanel.connect(self.displayHover)
        f.hoverAntenna.hideHoverPanel.connect(self.hideHover)

        mainLayout=QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)


        wordline=QtWidgets.QLabel()
        wordline.setText("W\no\nr\nd\nl\ni\nn\ne")
        bitline=QtWidgets.QLabel()
        bitline.setText("Bitline")

        bitH=QtWidgets.QHBoxLayout()
        bitH.addStretch()
        bitH.addWidget(bitline)
        bitH.addStretch()

        bitH.setSpacing(0)
        #bitH.setAlignment(QtCore.Qt.AlignCenter)

        lay1=QtWidgets.QVBoxLayout()
        lay1.setSpacing(0)

        lay2=QtWidgets.QHBoxLayout()
        #lay2.setAlignment(QtCore.Qt.AlignCenter)
        lay2.setSpacing(0)

        #cbContainer=QtWidgets.QWidget(self)
        self.cb=cbContainer.cbContainer()

        #lay1.setAlignment(QtCore.Qt.AlignCenter)

        #lay1.addStretch()
        #lay2.addStretch()

        #factor=2
        #lay2.insertStretch(0,factor)
        lay2.addStretch()
        lay2.addWidget(wordline)
        lay2.addWidget(self.cb)
        lay2.addStretch()
        #lay2.insertStretch(-1,factor)
        
        #lay2.setStretch(2,10)

        #factor=2
        #lay1.insertStretch(0,factor)
        lay1.addStretch()
        lay1.addLayout(lay2)
        lay1.addLayout(bitH)
        lay1.addStretch()
        
        #lay1.insertStretch(3,factor)
        #lay1.setStretch(1,15)
        #lay1.setStretch(0,1)


        #lay2.setStretch(1,1)
        #lay2.setAlignment(QtCore.Qt.AlignCenter)
        
        
        #lay2.addStretch()

        # Colorbar setup
        colorBarLay=QtWidgets.QHBoxLayout()
        colorBarLeft=QtWidgets.QVBoxLayout()
        for i in range(len(g.qColorList)):
            aux=cBS.colorBarSlice()
            aux.recolor(g.qColorList[255-i])
            aux.setMinimumWidth(20)
            aux.setMaximumWidth(20)
            colorBarLeft.addWidget(aux)

        # Create Tick labels
        resTicks=['100M','10M','1M','100k','10k','1k','100']
        resTicksLabels=[]
        for i in range(len(resTicks)):
            aux=QtWidgets.QLabel(self)
            aux.setText(resTicks[i])
            aux.setFont(fonts.font3)
            resTicksLabels.append(aux)
        colorBarLeft.setSpacing(0)


        # Add ticks
        colorBarRight=QtWidgets.QVBoxLayout()
        colorBarRight.addWidget(resTicksLabels[0])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[1])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[2])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[3])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[4])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[5])
        colorBarRight.addStretch()
        colorBarRight.addWidget(resTicksLabels[6])

        colorBarLay.addLayout(colorBarLeft)
        colorBarLay.addLayout(colorBarRight)
        colorBarLay.setContentsMargins(0,12,10,21)
        #lay2.addLayout(colorBarLay)

        mainLayout.addLayout(lay1)

        #self.hoverPanel=hP.hoverPanel()
        #self.hoverPanel.setFixedSize(100,50)

        # SETUP HOVER PANEL
        #######################
        hoverLayout=QtWidgets.QVBoxLayout()
        self.posLabel=QtWidgets.QLabel()
        self.posLabel.setText("W=10 | B=9 \n Mnow" )
        self.posLabel.setStyleSheet(s.labelStyle)
        self.mLabel=QtWidgets.QLabel()
        self.mLabel.setText("10000")
        self.mLabel.setFont(fonts.font3)
        self.mLabel.setStyleSheet(s.labelStyle)
        hoverLayout.addWidget(self.posLabel)
        hoverLayout.addWidget(self.mLabel)
        hoverLayout.setContentsMargins(2,2,2,2)

        hoverLayout.setSpacing(0)

        #container=QtWidgets.QVBoxLayout()
         # Changed Here
         # Container to create border around the CB
        #self.mainPanel = QtWidgets.QGroupBox('')
        #self.mainPanel.setStyleSheet(s.groupStyleCB)
        #self.mainPanel.setLayout(lay1)

        #container.addWidget(self.mainPanel)   
        #container.setContentsMargins(0,0,0,0)    

        #self.setLayout(lay1)
        mainLayout.addLayout(colorBarLay)
        self.setLayout(mainLayout)
        #=====================================

        self.setContentsMargins(0,0,0,0)    # spacing of the full Layout to accomodate line numbers and colorbar on the right  

        self.hoverPanel=QtWidgets.QWidget(self)

        self.hoverPanel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.hoverPanel.setFixedSize(100,50)
        self.hoverPanel.setStyleSheet("background-color: rgb(0,32,87)")
        self.hoverPanel.setLayout(hoverLayout)
        #self.hoverPanel.installEventFilter(self)
        self.hoverPanel.hide()


    def displayHover(self,r,c,x,y,w,h):
        self.posLabel.setText("W="+str(r)+" | B="+str(c))

        try:
            self.mLabel.setText(str(int(g.Mhistory[r][c][-1][0])))
        except IndexError:
            self.mLabel.setText("Not Read")
        except OverflowError:
            self.mLabel.setText("Inf")

        newX=self.cb.geometry().x()+x+w
        newY=y+self.cb.geometry().y()-50

        if (newY<0):
            newY=0

        self.hoverPanel.move(newX, newY)
        self.hoverPanel.show()


    def hideHover(self):
        self.hoverPanel.hide()

