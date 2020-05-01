####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
import importlib
import pkgutil
from PyQt5 import QtGui, QtCore, QtWidgets

import ProgPanels
import Globals.GlobalStyles as s
import Globals.GlobalVars as g


class ProgPanelWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        mainLayout=QtWidgets.QVBoxLayout()

        hbox_1=QtWidgets.QHBoxLayout()

        label_panels = QtWidgets.QLabel('Panels:')
        label_panels.setMaximumWidth(40)

        self.prog_panelList = QtWidgets.QComboBox()
        self.prog_panelList.setStyleSheet(s.comboStyle)
        self.prog_panelList.setMinimumWidth(150*g.scaling_factor)

        # List all non-package modules in `ProgPanels`
        for (_, modname, ispkg) in pkgutil.iter_modules(ProgPanels.__path__):
            if ispkg:
                continue
            name = modname.split(".")[-1]
            if name != "CT_LIVE":
                self.prog_panelList.addItem(name)

        boldFont=QtGui.QFont("FontFamily")
        boldFont.setBold(True)
        self.prog_panelList.setItemData(self.prog_panelList.findText("SuperMode"), boldFont, QtCore.Qt.FontRole)

        self.push_add=QtWidgets.QPushButton('Add')
        self.push_add.setStyleSheet(s.btnStyle2)
        self.push_add.clicked.connect(self.addPanel)

        self.push_remove=QtWidgets.QPushButton('Remove')
        self.push_remove.setStyleSheet(s.btnStyle2)
        self.push_remove.clicked.connect(self.removePanel)

        self.tabFrame=QtWidgets.QTabWidget()

        hbox_1.addWidget(label_panels)
        hbox_1.addWidget(self.prog_panelList)
        hbox_1.addWidget(self.push_add)
        hbox_1.addWidget(self.push_remove)

        mainLayout.addLayout(hbox_1)
        mainLayout.addWidget(self.tabFrame)
        # no margin on the bottom
        mainLayout.setContentsMargins(10,10,10,0)

        self.setContentsMargins(0,0,0,0)

        self.setLayout(mainLayout)

    def addPanel(self):

        baseModule = str(self.prog_panelList.currentText())
        moduleName = ".".join([ProgPanels.__name__, baseModule])
        thisPanel = importlib.import_module(moduleName)
        panel_class = getattr(thisPanel, baseModule)
        widg=panel_class()
        self.tabFrame.addTab(widg, baseModule)

        self.tabFrame.setCurrentWidget(widg)

    def setEnabled(self, state):
        for child in range(self.tabFrame.count()):
            self.tabFrame.widget(child).setEnabled(state)

    def removePanel(self):
        self.tabFrame.removeTab(self.tabFrame.currentIndex())

