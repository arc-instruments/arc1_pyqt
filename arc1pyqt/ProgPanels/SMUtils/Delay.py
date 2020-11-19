####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import time

from arc1pyqt.Globals import fonts, functions, styles


class ThreadWrapper(QtCore.QObject):

    finished = QtCore.pyqtSignal()
    disableInterface = QtCore.pyqtSignal(bool)

    def __init__(self, delay):
        super().__init__()
        self.delay = delay

    def run(self):

        self.disableInterface.emit(True)

        time.sleep(self.delay)

        self.disableInterface.emit(False)

        self.finished.emit()


class Delay(QtWidgets.QWidget):

    def __init__(self, short=False):
        super().__init__()
        self.initUI()

    def initUI(self):

        vbox=QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('Delay')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('A time delay.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        gridLayout = QtWidgets.QGridLayout()

        # ========== ComboBox ===========

        self.delay_mag = QtWidgets.QLineEdit()
        self.delay_mag.setValidator(QtGui.QDoubleValidator())
        self.delay_mag.setText("1")
        self.delay_mag.setStyleSheet(styles.entryStyle)
        self.delay_mag.setMaximumWidth(100)
        self.delay_mult = QtWidgets.QComboBox()
        self.delay_mult.setStyleSheet(styles.comboStylePulse)

        self.unitsFull=[['s',1], ['ms',0.001]]
        self.units=[e[0] for e in self.unitsFull]
        self.multiply=[e[1] for e in self.unitsFull]

        self.delay_mult.insertItems(1, self.units)
        self.delay_mult.setCurrentIndex(2)
        self.delay_mult.setMaximumWidth(75)

        gridLayout.addWidget(self.delay_mag, 0, 0)
        gridLayout.addWidget(self.delay_mult, 0, 1)
        gridLayout.addItem(QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding), 0, 2)

        vbox.addWidget(titleLabel)
        vbox.addWidget(descriptionLabel)

        self.vW = QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        scrlArea=QtWidgets.QScrollArea()
        scrlArea.setWidget(self.vW)
        scrlArea.setContentsMargins(0,0,0,0)
        scrlArea.setWidgetResizable(False)
        scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrlArea.installEventFilter(self)

        vbox.addWidget(scrlArea)
        vbox.addStretch()

        self.extractParams()

        self.setLayout(vbox)
        self.gridLayout=gridLayout

    def extractPanelParameters(self):
        layoutItems=[[i,self.gridLayout.itemAt(i).widget()] \
            for i in range(self.gridLayout.count())]

        layoutWidgets = []

        for i,item in layoutItems:
            if isinstance(item, QtWidgets.QLineEdit):
                layoutWidgets.append([i,'QLineEdit', item.text()])
            if isinstance(item, QtWidgets.QComboBox):
                layoutWidgets.append([i,'QComboBox', item.currentIndex()])
            if isinstance(item, QtWidgets.QCheckBox):
                layoutWidgets.append([i,'QCheckBox', item.checkState()])

        return layoutWidgets

    def setPanelParameters(self, layoutWidgets):
        for i,type,value in layoutWidgets:
            if type=='QLineEdit':
                self.gridLayout.itemAt(i).widget().setText(value)
            if type=='QComboBox':
                self.gridLayout.itemAt(i).widget().setCurrentIndex(value)
            if type=='QCheckBox':
                self.gridLayout.itemAt(i).widget().setChecked(value)

    def eventFilter(self, object, event):
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        return False

    def programOne(self):
        self.extractParams()
        self.thread=QtCore.QThread()
        self.threadWrapper=ThreadWrapper(self.delay)
        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
        self.thread.finished.connect(functions.interfaceAntenna.wakeUp)

        self.thread.start()

    def extractParams(self):
        duration=float(self.delay_mag.text())
        unit=float(self.multiply[self.delay_mult.currentIndex()])
        self.delay=duration*unit

        if self.delay < 0.01:
            self.delay_mag.setText(str(10))
            self.delay_mult.setCurrentIndex(1)
            self.delay = 0.01
        if self.delay > 10:
            self.delay_mag.setText(str(10))
            self.delay_mult.setCurrentIndex(0)
            self.delay = 10

