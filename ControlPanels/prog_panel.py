####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
import importlib
from PyQt4 import QtGui
from PyQt4 import QtCore

import GlobalStyles as s

sys.path.append(os.path.abspath(os.getcwd()+'/ProgPanels/'))


class prog_panel(QtGui.QWidget):
    
    def __init__(self):
        super(prog_panel, self).__init__()
        self.initUI()
        
    def initUI(self):   
        mainLayout=QtGui.QVBoxLayout()

        hbox_1=QtGui.QHBoxLayout()

        label_panels = QtGui.QLabel('Panels:')
        label_panels.setMaximumWidth(40)

        self.prog_panelList = QtGui.QComboBox()
        self.prog_panelList.setStyleSheet(s.comboStyle)
        self.prog_panelList.setMinimumWidth(150)

        files = [f for f in os.listdir('ProgPanels') if f.endswith(".py")]  # populate prog panel dropbox
        for f in files:
            self.prog_panelList.addItem(f[:-3])

        boldFont=QtGui.QFont("FontFamily")
        boldFont.setBold(True)
        self.prog_panelList.setItemData(self.prog_panelList.findText("SuperMode"), boldFont, QtCore.Qt.FontRole)

        self.push_add=QtGui.QPushButton('Add')
        self.push_add.setStyleSheet(s.btnStyle2)
        self.push_add.clicked.connect(self.addPanel)

        self.push_remove=QtGui.QPushButton('Remove')
        self.push_remove.setStyleSheet(s.btnStyle2)
        self.push_remove.clicked.connect(self.removePanel)

        self.tabFrame=QtGui.QTabWidget()

        hbox_1.addWidget(label_panels)
        hbox_1.addWidget(self.prog_panelList)
        hbox_1.addWidget(self.push_add)
        hbox_1.addWidget(self.push_remove)
        
        mainLayout.addLayout(hbox_1)
        mainLayout.addWidget(self.tabFrame)

        mainLayout.setContentsMargins(10,10,10,0)   # no margin on the bottom

        self.setContentsMargins(0,0,0,0)

        #self.mainPanel = QtGui.QGroupBox('')
        #self.mainPanel.setStyleSheet(s.groupStyleProg)
        #self.mainPanel.setLayout(mainLayout)

        #container=QtGui.QVBoxLayout()
        #container.addWidget(self.mainPanel)   
        #container.setContentsMargins(0,0,0,0)    

        self.setLayout(mainLayout)

        #self.setLayout(mainLayout)

        #self.show()

    def addPanel(self):

        moduleName=str(self.prog_panelList.currentText())   # format module name from drop down
        thisPanel = importlib.import_module(moduleName)     # import the module
        panel_class = getattr(thisPanel, moduleName)        # get it's main class    
        widg=panel_class()                    
        self.tabFrame.addTab(widg,moduleName) # instantiate it and add to tabWidget

        self.tabFrame.setCurrentWidget(widg)

    def removePanel(self):
        self.tabFrame.removeTab(self.tabFrame.currentIndex())

    def populatePanels(self):
        pass
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = prog_panel()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()  