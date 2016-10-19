####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys
import os

import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f


class aboutSection(QtGui.QWidget):
    
    def __init__(self):
        super(aboutSection, self).__init__()
        
        self.initUI()
        
    def initUI(self):

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)      



        mainLayout=QtGui.QVBoxLayout()  # Set main vertical layout
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        logoTop=QtGui.QLabel()
        logoTop.setPixmap(QtGui.QPixmap(os.getcwd()+"/Graphics/"+'aboutSection.png'))
        mainLayout.addWidget(logoTop)

        botHLay=QtGui.QHBoxLayout()
        botHLay.setContentsMargins(0,0,0,0)

        spacerWidget=QtGui.QWidget()
        spacerWidget.setFixedWidth(172)
        spacerWidget.setFixedHeight(120)

        p = spacerWidget.palette()
        p.setColor(spacerWidget.backgroundRole(), QtCore.Qt.white)
        spacerWidget.setPalette(p)  

        botHLay.addWidget(spacerWidget)
        botHLay.setSpacing(0)

        infoLay=QtGui.QVBoxLayout()
        infoLay.setContentsMargins(0,0,0,0)
        infoLay.setSpacing(0)

        line1=QtGui.QLabel()
        line2=QtGui.QLabel()
        line3=QtGui.QLabel()
        line4=QtGui.QLabel()
        line5=QtGui.QLabel()
        line6=QtGui.QLabel()
        line7=QtGui.QLabel()

        line1.setText('75 Sirocco, 33 Channel Way')
        line2.setText('Ocean Village')
        line3.setText('Southampton, UK')
        line4.setText('SO14 3JF')
        line5.setText('www.arc-instruments.co.uk')
        line6.setText('office@arc-instruments.co.uk')
        line7.setText('+44 777 235 0889')
        
        infoLay.addWidget(line1)
        infoLay.addWidget(line2)
        infoLay.addWidget(line3)
        infoLay.addWidget(line4)
        infoLay.addStretch()
        infoLay.addWidget(line5)
        infoLay.addWidget(line6)
        infoLay.addWidget(line7)

        botHLay.addLayout(infoLay)
        
        mainLayout.addStretch()
        mainLayout.addLayout(botHLay)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = aboutSection()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 