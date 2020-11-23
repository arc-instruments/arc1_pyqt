####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
from arc1pyqt.Globals import fonts
from arc1pyqt.modutils import BaseProgPanel


class End(BaseProgPanel):

    def __init__(self, short=False):
        super().__init__(title='SuperMode End Loop', description='')
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
