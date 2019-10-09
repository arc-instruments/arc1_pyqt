####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtWidgets
from . import cell as c

import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f


class configHardware(QtWidgets.QWidget):
    
    def __init__(self):
        super(configHardware, self).__init__()
        self.initUI()

    def initUI(self):      
        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        # Setup mCAT settings
        self.hwSettings = QtWidgets.QGroupBox('Hardware Settings')
        self.hwSettings.setStyleSheet(s.groupStyleNewSesh)
        self.hwSettings.setFont(fonts.font2)

        hwSetLayout=QtWidgets.QGridLayout()
        hwSetLayout.setContentsMargins(10,20,10,10)

        readCyclesLabel=QtWidgets.QLabel(self)
        readCyclesLabel.setText("Reading Cycles:")
        readCyclesLabel.setFont(fonts.font3)

        sneakLabel=QtWidgets.QLabel(self)
        sneakLabel.setText("Sneak Path Limiting:")
        sneakLabel.setFont(fonts.font3)

        self.readCyclesEntry=QtWidgets.QLineEdit()
        self.readCyclesEntry.setFixedWidth(320)
        self.readCyclesEntry.setText(str(g.readCycles))
        self.readCyclesEntry.setFont(fonts.font3)

        self.sneakCombo=QtWidgets.QComboBox(self)
        self.sneakCombo.setMaximumWidth(320)
        self.sneakCombo.addItem("Write: V/3")
        self.sneakCombo.addItem("Write: V/2")
        self.sneakCombo.setFont(fonts.font3)
        self.sneakCombo.setCurrentIndex(g.sneakPathOption)

        hwSetLayout.addWidget(readCyclesLabel,0,0)
        hwSetLayout.addWidget(sneakLabel,1,0)
        hwSetLayout.addWidget(self.readCyclesEntry,0,1)
        hwSetLayout.addWidget(self.sneakCombo,1,1)

        self.hwSettings.setLayout(hwSetLayout)
        mainLayout.addWidget(self.hwSettings)

        # Apply/Cancel buttons Layout
        startLay_group=QtWidgets.QGroupBox()
        startLay_group.setStyleSheet(s.groupStyle)
        startLay=QtWidgets.QHBoxLayout()

        start_btn=QtWidgets.QPushButton('Apply')
        start_btn.setStyleSheet(s.btnStyle2)
        start_btn.setMinimumWidth(100)
        start_btn.clicked.connect(self.updateHW)

        cancel_btn=QtWidgets.QPushButton('Cancel')
        cancel_btn.setStyleSheet(s.btnStyle2)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.cancelUpdateHW)

        startLay.addStretch()
        startLay.addWidget(cancel_btn)
        startLay.addWidget(start_btn)
        startLay.setContentsMargins(5,5,5,5)
        startLay.setSpacing(2)

        line=QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Plain)
        line.setStyleSheet(s.lineStyle)
        line.setLineWidth(1)

        mainLayout.addWidget(line)

        mainLayout.addLayout(startLay)

        self.setContentsMargins(0,0,0,0)
        self.setLayout(mainLayout)

    def updateHW(self):

        g.readCycles=int(self.readCyclesEntry.text())
        g.sneakPathOption=self.sneakCombo.currentIndex()

        f.interfaceAntenna.updateHW.emit()

        self.close()

    def cancelUpdateHW(self):
        self.close()

