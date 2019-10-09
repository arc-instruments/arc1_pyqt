####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import platform

import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f
import Graphics


class aboutSection(QtWidgets.QWidget):
    
    def __init__(self):
        super(aboutSection, self).__init__()
        
        self.initUI()
        
    def initUI(self):

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)      

        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        logoTop=QtWidgets.QLabel()
        logoTop.setPixmap(Graphics.getPixmap('about-banner'))
        mainLayout.addWidget(logoTop)

        botHLay=QtWidgets.QHBoxLayout()
        botHLay.setContentsMargins(0,0,0,0)

        spacerWidget=QtWidgets.QWidget()
        spacerWidget.setFixedWidth(172)
        spacerWidget.setFixedHeight(120)

        p = spacerWidget.palette()
        p.setColor(spacerWidget.backgroundRole(), QtCore.Qt.white)
        spacerWidget.setPalette(p)  

        botHLay.addWidget(spacerWidget)
        botHLay.setSpacing(0)

        infoLay=QtWidgets.QVBoxLayout()
        infoLay.setContentsMargins(0,10,0,10)
        infoLay.setSpacing(0)

        line0=QtWidgets.QLabel()
        line1=QtWidgets.QLabel()
        line2=QtWidgets.QLabel()
        line3=QtWidgets.QLabel()
        line4=QtWidgets.QLabel()
        line5=QtWidgets.QLabel()
        line6=QtWidgets.QLabel()
        line7=QtWidgets.QLabel()

        system = "%s %s" % (platform.system(), platform.architecture()[0])
        pyver = "%d.%d" % (sys.version_info.major, sys.version_info.minor)

        line0.setText("ArC ONE: <b>%s</b> System: <b>%s</b> "
                "Python: <b>%s</b> Qt: <b>%s</b>  " %
                (g.local_version, system, pyver, QtCore.QT_VERSION_STR))
        line1.setText('75 Sirocco, 33 Channel Way')
        line2.setText('Ocean Village')
        line3.setText('Southampton, UK')
        line4.setText('SO14 3JF\n')
        line5.setText('www.arc-instruments.co.uk')
        line6.setText('office@arc-instruments.co.uk')
        line7.setText('+44 777 235 0889\n')

        infoLay.addWidget(line1)
        infoLay.addWidget(line2)
        infoLay.addWidget(line3)
        infoLay.addWidget(line4)
        infoLay.addStretch()
        infoLay.addWidget(line5)
        infoLay.addWidget(line6)
        infoLay.addWidget(line7)
        infoLay.addStretch()
        infoLay.addWidget(line0)

        botHLay.addLayout(infoLay)

        mainLayout.addStretch()
        mainLayout.addLayout(botHLay)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

