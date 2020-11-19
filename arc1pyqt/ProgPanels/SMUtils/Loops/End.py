####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
from arc1pyqt.Globals import fonts


class End(QtWidgets.QWidget):

    def __init__(self, short=False):
        super().__init__()
        self.initUI()

    def initUI(self):

        vbox = QtWidgets.QVBoxLayout()

        titleLabel = QtWidgets.QLabel('End loop')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtWidgets.QLabel('End of loop indicator.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        vbox.addWidget(titleLabel)
        vbox.addWidget(descriptionLabel)

        vbox.addStretch()

        self.setLayout(vbox)

    def extractPanelParameters(self):
        return []

    def setPanelParameters(self, layoutWidgets):
        pass
