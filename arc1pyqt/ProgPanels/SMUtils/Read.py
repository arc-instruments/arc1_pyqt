####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
from copy import copy
import time

from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import fonts, functions, styles
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel


class ThreadWrapper(BaseThreadWrapper):

    def __init__(self, Vread, readType):
        super().__init__()
        self.Vread=Vread
        self.readType=readType

    @BaseThreadWrapper.runner
    def run(self):

        global tag

        needsUpdate = False

        if self.Vread != HW.conf.Vread or self.readType != HW.conf.readmode:
            # if current read configuration is different than the global one
            # make sure you set it back once we're done so set `needsUpdate` to
            # True.
            needsUpdate = True
            # Update Read
            conf = copy(HW.conf)
            conf.readmode = self.readType
            conf.Vread = self.Vread
            HW.ArC.update_read(conf)

        Mnow = HW.ArC.read_one(CB.word, CB.bit)

        tag='S R'+str(self.readType)+' V='+str(self.Vread)
        self.sendData.emit(CB.word, CB.bit, Mnow, float(self.Vread), 0, tag)

        self.displayData.emit()
        self.updateTree.emit(CB.word, CB.bit)

        # set read configuration back to its original state
        if needsUpdate == True:
            HW.ArC.update_read(HW.conf)


class Read(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title='SuperMode Read', description='')
        self.short=short
        self.initUI()

    def initUI(self):
        self.Vread = HW.conf.Vread
        self.readOption = HW.conf.readmode

        vbox1=QtWidgets.QVBoxLayout()
        hbox1=QtWidgets.QHBoxLayout()

        titleLabel = QtWidgets.QLabel('Read')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Apply a Read operation.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        gridLayout=QtWidgets.QGridLayout()
        gridLayout.setColumnStretch(0,3)
        gridLayout.setColumnStretch(1,1)
        gridLayout.setColumnStretch(2,1)
        gridLayout.setColumnStretch(3,1)
        gridLayout.setColumnStretch(4,3)
        gridLayout.setColumnStretch(5,1)
        gridLayout.setColumnStretch(6,1)
        if self.short==False:
            gridLayout.setColumnStretch(7,2)

        #setup a line separator
        lineLeft=QtWidgets.QFrame()
        lineLeft.setFrameShape(QtWidgets.QFrame.VLine)
        lineLeft.setFrameShadow(QtWidgets.QFrame.Raised)
        lineLeft.setLineWidth(1)

        gridLayout.addWidget(lineLeft, 0, 2, 2, 1)

        # ========== ComboBox ===========
        self.combo_readType=QtWidgets.QComboBox()
        self.combo_readType.setStyleSheet(styles.comboStyle)
        self.combo_readType.insertItems(1, ['Classic', 'TIA', 'TIA4P'])
        self.combo_readType.currentIndexChanged.connect(self.updateReadType)
        self.combo_readType.setCurrentIndex(2)

        self.read_voltage=QtWidgets.QDoubleSpinBox()
        self.read_voltage.setStyleSheet(styles.spinStyle)
        self.read_voltage.setMinimum(-12)
        self.read_voltage.setMaximum(12)
        self.read_voltage.setSingleStep(0.05)
        self.read_voltage.setValue(0.5)
        self.read_voltage.setSuffix(' V')
        self.read_voltage.valueChanged.connect(self.setVread)

        gridLayout.addWidget(self.combo_readType,0,0)
        gridLayout.addWidget(self.read_voltage,0,1)
        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scrlArea.installEventFilter(self)

        vbox1.addWidget(scrlArea)
        vbox1.addStretch()

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

        self.registerPropertyWidget(self.combo_readType, 'readtype')
        self.registerPropertyWidget(self.read_voltage, 'vread')

    def setVread(self, value):
        self.Vread=value

    def updateReadType(self, value):
        self.readOption=value

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def programOne(self):

        self.thread=QtCore.QThread()
        self.threadWrapper=ThreadWrapper(self.Vread, self.readOption)
        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.sendData.connect(functions.updateHistory)
        self.threadWrapper.highlight.connect(functions.cbAntenna.cast)
        self.threadWrapper.displayData.connect(functions.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(functions.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
        self.thread.finished.connect(functions.interfaceAntenna.wakeUp)


        self.thread.start()

