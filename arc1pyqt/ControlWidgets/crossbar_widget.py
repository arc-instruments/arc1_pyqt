####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from . import DeviceWidget
from . import ColorbarWidget
from .. import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from ..Globals import functions, fonts, styles
from . import CrossbarContainerWidget
from .common import resistanceColorGradient


class CrossbarWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        functions.hoverAntenna.displayHoverPanel.connect(self.displayHover)
        functions.hoverAntenna.hideHoverPanel.connect(self.hideHover)

        mainLayout=QtWidgets.QHBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)


        wordline=QtWidgets.QLabel()
        wordline.setText("W\no\nr\nd\nl\ni\nn\ne")
        wordline.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        bitline=QtWidgets.QLabel()
        bitline.setText("Bitline")

        bitH=QtWidgets.QHBoxLayout()
        bitH.addStretch()
        bitH.addWidget(bitline)
        bitH.addStretch()

        bitH.setSpacing(0)

        lay1=QtWidgets.QVBoxLayout()
        lay1.setSpacing(0)

        lay2=QtWidgets.QHBoxLayout()
        lay2.setSpacing(0)

        self.cb = CrossbarContainerWidget()

        lay2.addStretch()
        lay2.addWidget(wordline)
        lay2.addWidget(self.cb)
        lay2.addStretch()

        lay1.addStretch()
        lay1.addLayout(lay2)
        lay1.addLayout(bitH)
        lay1.addStretch()

        # Colorbar setup
        colorBarLay = QtWidgets.QHBoxLayout()
        colorBarLeft = QtWidgets.QVBoxLayout()
        for color in reversed(resistanceColorGradient):
            aux = ColorbarWidget()
            #print(resistanceColorGradient[255-i])
            aux.recolor(color)
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

        mainLayout.addLayout(lay1)

        # Setup hover panel
        hoverLayout=QtWidgets.QVBoxLayout()
        self.posLabel=QtWidgets.QLabel()
        self.posLabel.setText("W=10 | B=9 \n Mnow" )
        self.posLabel.setStyleSheet(styles.labelStyle)
        self.mLabel=QtWidgets.QLabel()
        self.mLabel.setText("10000")
        self.mLabel.setFont(fonts.font3)
        self.mLabel.setStyleSheet(styles.labelStyle)
        hoverLayout.addWidget(self.posLabel)
        hoverLayout.addWidget(self.mLabel)
        hoverLayout.setContentsMargins(2,2,2,2)

        hoverLayout.setSpacing(0)

        mainLayout.addLayout(colorBarLay)
        self.setLayout(mainLayout)

        self.setContentsMargins(0,0,0,0)

        self.hoverPanel=QtWidgets.QWidget(self)

        self.hoverPanel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.hoverPanel.setFixedSize(100,50)
        self.hoverPanel.setStyleSheet("background-color: rgb(0,32,87)")
        self.hoverPanel.setLayout(hoverLayout)
        self.hoverPanel.hide()


    def displayHover(self,r,c,x,y,w,h):
        self.posLabel.setText("W="+str(r)+" | B="+str(c))

        try:
            self.mLabel.setText(str(int(CB.history[r][c][-1][0])))
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

