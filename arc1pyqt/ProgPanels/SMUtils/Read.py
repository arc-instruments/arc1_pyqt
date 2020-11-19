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
from arc1pyqt.modutils import BaseThreadWrapper


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

        job="1"
        HW.ArC.write_b(job+"\n")
        HW.ArC.write_b(str(CB.word)+"\n")
        HW.ArC.write_b(str(CB.bit)+"\n")

        Mnow=HW.ArC.read_floats(1)

        tag='S R'+str(self.readType)+' V='+str(self.Vread)
        self.sendData.emit(CB.word, CB.bit, Mnow, float(self.Vread), 0, tag)

        self.displayData.emit()
        self.updateTree.emit(CB.word, CB.bit)


        # set read configuration back to its original state
        if needsUpdate == True:
            HW.ArC.update_read(HW.conf)


class Read(QtWidgets.QWidget):

    def __init__(self, short=False):
        super().__init__()
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

        if self.short==False:
            self.hboxProg=QtWidgets.QHBoxLayout()

            push_single=QtWidgets.QPushButton('Apply to One')
            push_range=QtWidgets.QPushButton('Apply to Range')
            push_all=QtWidgets.QPushButton('Apply to All')

            push_single.setStyleSheet(styles.btnStyle)
            push_range.setStyleSheet(styles.btnStyle)
            push_all.setStyleSheet(styles.btnStyle)

            push_single.clicked.connect(self.programOne)
            push_range.clicked.connect(self.programRange)
            push_all.clicked.connect(self.programAll)

            self.hboxProg.addWidget(push_single)
            self.hboxProg.addWidget(push_range)
            self.hboxProg.addWidget(push_all)

            vbox1.addLayout(self.hboxProg)

        self.setLayout(vbox1)
        self.gridLayout=gridLayout

    def extractPanelParameters(self):
        layoutItems=[[i,self.gridLayout.itemAt(i).widget()] for i in range(self.gridLayout.count())]
        
        layoutWidgets=[]

        for i,item in layoutItems:
            if isinstance(item, QtWidgets.QLineEdit):
                layoutWidgets.append([i,'QLineEdit', item.text()])
            if isinstance(item, QtWidgets.QComboBox):
                layoutWidgets.append([i,'QComboBox', item.currentIndex()])
            if isinstance(item, QtWidgets.QCheckBox):
                layoutWidgets.append([i,'QCheckBox', item.checkState()])
            if isinstance(item, QtWidgets.QDoubleSpinBox):
                layoutWidgets.append([i,'QDoubleSpinBox', item.value()])

        
        #self.setPanelParameters(layoutWidgets)
        return layoutWidgets

    def setPanelParameters(self, layoutWidgets):
        for i,w_type,value in layoutWidgets:
            if w_type=='QLineEdit':
                self.gridLayout.itemAt(i).widget().setText(value)
            if w_type=='QComboBox':
                self.gridLayout.itemAt(i).widget().setCurrentIndex(value)
            if w_type=='QCheckBox':
                self.gridLayout.itemAt(i).widget().setChecked(value)
            if w_type=='QDoubleSpinBox':
                self.gridLayout.itemAt(i).widget().setValue(value)

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

