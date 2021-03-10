####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets
from . import MatrixWidget
from . import LogoLabelWidget

from .. import state
HW = state.hardware
CB = state.crossbar
APP = state.app

from ..Globals import functions, styles, fonts
from .. import Graphics


class NewSessionDialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        mainLayout=QtWidgets.QVBoxLayout()  # Set main vertical layout
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        # Setup top logo
        logoTop = LogoLabelWidget()
        logoTop.setColor(255, 255, 255)
        logoTop.setPixmapResource('new-session-banner')
        mainLayout.addWidget(logoTop)

        # Setup general settings
        self.generalSettings = QtWidgets.QGroupBox('General Settings')
        self.generalSettings.setStyleSheet(styles.groupStyleNewSession)
        self.generalSettings.setFont(fonts.font2)
        genSetLayout=QtWidgets.QGridLayout()
        genSetLayout.setContentsMargins(10,20,10,20)

        wModeLabel=QtWidgets.QLabel(self)
        wModeLabel.setText("Session Mode:")
        wModeLabel.setFont(fonts.font3)

        wDirLabel=QtWidgets.QLabel(self)
        wDirLabel.setText("Working Directory:")
        wDirLabel.setFont(fonts.font3)

        push_browse = QtWidgets.QPushButton('...')
        push_browse.clicked.connect(self.selectWDir)
        push_browse.setFixedWidth(20)

        self.dirName=QtWidgets.QLineEdit()
        self.dirName.setReadOnly(True)
        self.dirName.setMaximumWidth(294)
        self.dirName.setStyleSheet(styles.entryStyle2)

        dirLayout=QtWidgets.QHBoxLayout()
        dirLayout.addWidget(self.dirName)
        dirLayout.addWidget(push_browse)

        wNameLabel=QtWidgets.QLabel(self)
        wNameLabel.setText("Session Name:")
        wNameLabel.setFont(fonts.font3)

        self.wModeCombo=QtWidgets.QComboBox(self)
        self.wModeCombo.addItem("Live: Local")
        self.wModeCombo.addItem("Live: External BNC")
        self.wModeCombo.addItem("Live: BNC to Local")
        self.wModeCombo.addItem("Offline")
        self.wModeCombo.setFont(fonts.font3)

        self.wNameEntry=QtWidgets.QLineEdit()
        self.wNameEntry.setMaximumWidth(320)
        self.wNameEntry.setText('Package1')
        self.wNameEntry.setFont(fonts.font3)

        genSetLayout.addWidget(wModeLabel,0,0)
        genSetLayout.addWidget(wDirLabel,1,0)
        genSetLayout.addWidget(wNameLabel,2,0)
        genSetLayout.addWidget(self.wModeCombo,0,1)
        genSetLayout.addLayout(dirLayout,1,1)
        genSetLayout.addWidget(self.wNameEntry,2,1)

        self.generalSettings.setLayout(genSetLayout)
        mainLayout.addWidget(self.generalSettings)
        #mainLayout.addWidget(self.generalSettings)

        # Setup mCAT settings
        self.hwSettings = QtWidgets.QGroupBox('Hardware Settings')
        self.hwSettings.setStyleSheet(styles.groupStyleNewSession)
        self.hwSettings.setFont(fonts.font2)

        hwSetLayout=QtWidgets.QGridLayout()
        hwSetLayout.setContentsMargins(10,20,10,10)

        readCyclesLabel=QtWidgets.QLabel(self)
        readCyclesLabel.setText("Reading Cycles:")
        readCyclesLabel.setFont(fonts.font3)

        sneakLabel=QtWidgets.QLabel(self)
        sneakLabel.setText("Sneak Path Limiting:")
        sneakLabel.setFont(fonts.font3)

        arShapeLabel=QtWidgets.QLabel(self)
        arShapeLabel.setText("Array Shape:")
        arShapeLabel.setFont(fonts.font3)

        self.readCyclesEntry=QtWidgets.QLineEdit()
        self.readCyclesEntry.setFixedWidth(320)
        self.readCyclesEntry.setText("50")
        self.readCyclesEntry.setFont(fonts.font3)

        self.sneakCombo=QtWidgets.QComboBox(self)
        self.sneakCombo.setMaximumWidth(320)
        self.sneakCombo.addItem("Write: V/3")
        self.sneakCombo.addItem("Write: V/2")
        self.sneakCombo.setFont(fonts.font3)
        self.sneakCombo.setCurrentIndex(HW.conf.sneakpath)

        cbHBox=QtWidgets.QHBoxLayout(self)
        self.cb_w=QtWidgets.QSpinBox(self)
        self.cb_w.setMinimum(1)
        self.cb_w.setMaximum(32)
        self.cb_w.setSingleStep(1)
        self.cb_w.setValue(32)
        self.cb_w.setFont(fonts.font3)
        self.cb_w.valueChanged.connect(self.matrixSizeChanged)

        self.cb_b=QtWidgets.QSpinBox(self)
        self.cb_b.setMinimum(1)
        self.cb_b.setMaximum(32)
        self.cb_b.setSingleStep(1)
        self.cb_b.setValue(32)
        self.cb_b.valueChanged.connect(self.matrixSizeChanged)
        self.cb_b.setFont(fonts.font3)

        cb_w_label=QtWidgets.QLabel(self)
        cb_w_label.setText("W:")
        cb_w_label.setFont(fonts.font3)

        cb_b_label=QtWidgets.QLabel(self)
        cb_b_label.setText("B:")
        cb_b_label.setFont(fonts.font3)

        cbHBox.setContentsMargins(0,0,0,0)
        cbHBox.addStretch()
        cbHBox.addWidget(cb_w_label)
        cbHBox.addWidget(self.cb_w)
        cbHBox.addStretch()
        cbHBox.addWidget(cb_b_label)
        cbHBox.addWidget(self.cb_b)
        cbHBox.addStretch()

        aux=QtWidgets.QWidget()
        aux.setLayout(cbHBox)

        hwSetLayout.addWidget(readCyclesLabel,0,0)
        hwSetLayout.addWidget(sneakLabel,1,0)
        hwSetLayout.addWidget(arShapeLabel,2,0)
        hwSetLayout.addWidget(self.readCyclesEntry,0,2)
        hwSetLayout.addWidget(self.sneakCombo,1,2)
        hwSetLayout.addWidget(aux,2,2)
        hwSetLayout.setColumnStretch(1,2)

        self.hwSettings.setLayout(hwSetLayout)
        mainLayout.addWidget(self.hwSettings)

        line2=QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setFrameShadow(QtWidgets.QFrame.Plain)
        line2.setStyleSheet(styles.lineStyle)
        line2.setLineWidth(1)

        mainLayout.addWidget(line2)

        cbWidget = QtWidgets.QWidget()
        self.cbWindow = QtWidgets.QStackedLayout()
        cbWidget.setLayout(self.cbWindow)

        mainLayout.addWidget(cbWidget)

        # Apply/Cancel buttons Layout
        startLay_group=QtWidgets.QGroupBox()
        startLay_group.setStyleSheet(styles.groupStyle)
        startLay=QtWidgets.QHBoxLayout()

        start_btn=QtWidgets.QPushButton('Start')
        start_btn.setStyleSheet(styles.btnStyle2)
        start_btn.setMinimumWidth(100)
        start_btn.clicked.connect(self.startSession)

        cancel_btn=QtWidgets.QPushButton('Cancel')
        cancel_btn.setStyleSheet(styles.btnStyle2)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.cancelNewSession)

        startLay.addStretch()
        startLay.addWidget(cancel_btn)
        startLay.addWidget(start_btn)
        startLay.setContentsMargins(5,5,5,5)
        startLay.setSpacing(2)

        #startLay_group.setLayout(startLay)

        line=QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Plain)
        line.setStyleSheet(styles.lineStyle)
        line.setLineWidth(1)

        mainLayout.addWidget(line)

        mainLayout.addLayout(startLay)

        self.setContentsMargins(0,0,0,0)
        self.updateCB()
        self.setLayout(mainLayout)
        # frame geometry won't be updated properly due to matrix
        # widget repaint
        self.show()
        self.hide()

    def selectWDir(self):
        folderDialog=QtWidgets.QFileDialog()
        directory = folderDialog.getExistingDirectory(self, 'Choose Directory', \
                os.path.curdir)
        self.dirName.setText(directory)

    def matrixSizeChanged(self, *args):
        w = self.cb_w.value()
        b = self.cb_b.value()
        self.updateCB(w, b)

    def updateCB(self, w=HW.conf.words, b=HW.conf.bits):

        wdg = QtWidgets.QWidget()
        mainLayout = QtWidgets.QHBoxLayout(wdg)
        gridLayout = QtWidgets.QGridLayout()

        wordline = QtWidgets.QLabel(wdg)
        wordline.setText("W\no\nr\nd\nl\ni\nn\ne")
        wordline.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        bitline = QtWidgets.QLabel(wdg)
        bitline.setText("Bitline")
        bitline.setAlignment(QtCore.Qt.AlignCenter)


        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, \
                QtWidgets.QSizePolicy.Maximum)
        matrix = MatrixWidget(words=w, bits=b, passive=True, width=(10, 12), \
                height=(12, 14*APP.scalingFactor))
        matrix.setSizePolicy(sizePolicy)

        gridLayout.addWidget(wordline, 0, 1, 1, 1)
        gridLayout.addWidget(matrix, 0, 2, 1, 1)
        gridLayout.addWidget(bitline, 1, 2, 1, 1)

        mainLayout.addLayout(gridLayout)

        self.cbWindow.addWidget(wdg)
        self.cbWindow.setCurrentIndex(self.cbWindow.count()-1)

    def startSession(self):
        HW.conf.words = self.cb_w.value()
        HW.conf.bits = self.cb_b.value()

        if not len(self.dirName.text()) == 0:
            APP.workingDirectory = self.dirName.text()

        HW.conf.cycles = int(self.readCyclesEntry.text())
        HW.conf.sneakpath = self.sneakCombo.currentIndex()
        HW.conf.sessionmode=self.wModeCombo.currentIndex()
        APP.sessionName=self.wNameEntry.text()

        functions.interfaceAntenna.reformat.emit()

        self.close()

    def cancelNewSession(self):
        self.close()

