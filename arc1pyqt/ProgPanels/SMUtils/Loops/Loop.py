####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
from arc1pyqt.Globals import fonts, styles
from arc1pyqt.modutils import BaseProgPanel


class Loop(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title='SuperMode Loop', description='')
        self.initUI()

    def initUI(self):

        vbox = QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('Start loop')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('Standard loop iterator.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        self.loopEdit = QtWidgets.QLineEdit()
        self.loopEdit.setProperty("key", "loops")
        self.loopEdit.setText('2')
        self.loopEdit.setStyleSheet(styles.entryStyle)
        self.loopEdit.setValidator(QtGui.QIntValidator())

        # Setup the two combo boxes
        gridLayout = QtWidgets.QGridLayout()

        gridLayout.addWidget(QtWidgets.QLabel('Loop ×'), 0, 0)
        gridLayout.addWidget(self.loopEdit, 0, 1)

        vbox.addWidget(titleLabel)
        vbox.addWidget(descriptionLabel)

        self.vW = QtWidgets.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        self.scrlArea = QtWidgets.QScrollArea()
        self.scrlArea.setWidget(self.vW)
        self.scrlArea.setContentsMargins(0,0,0,0)

        self.scrlArea.installEventFilter(self)

        vbox.addWidget(self.scrlArea)
        vbox.addStretch()

        self.setLayout(vbox)
        self.gridLayout=gridLayout

        self.registerPropertyWidget(self.loopEdit, 'loops')

    def loopTimes(self):
        return int(self.loopEdit.text())
