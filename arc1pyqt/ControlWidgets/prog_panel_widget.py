####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
import importlib
import json
from PyQt5 import QtGui, QtCore, QtWidgets

from .. import ProgPanels
from ..Globals import styles

from .. import state
HW = state.hardware
CB = state.crossbar
APP = state.app


class ProgPanelWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        mainLayout=QtWidgets.QVBoxLayout()

        hbox_1=QtWidgets.QHBoxLayout()

        self.prog_panelList = QtWidgets.QComboBox()
        self.prog_panelList.setStyleSheet(styles.comboStyle)
        self.prog_panelList.setMinimumWidth(150*APP.scalingFactor)

        for (tag, mod) in APP.modules.items():
            if mod.module is None or tag == "CTLive":
                continue

            if mod.toplevel is not None:
                self.prog_panelList.addItem(mod.name, mod)

        boldFont=QtGui.QFont()
        boldFont.setBold(True)
        self.prog_panelList.setItemData(self.prog_panelList.findText("SuperMode"),
            boldFont, QtCore.Qt.FontRole)

        self.push_add=QtWidgets.QPushButton('Add')
        self.push_add.setStyleSheet(styles.btnStyle2)
        self.push_add.setToolTip('Add a new panel from list')
        self.push_add.clicked.connect(self.addPanel)

        self.push_remove=QtWidgets.QPushButton('Remove')
        self.push_remove.setStyleSheet(styles.btnStyle2)
        self.push_remove.setToolTip('Remove current panel')
        self.push_remove.clicked.connect(self.removePanel)

        self.push_save=QtWidgets.QPushButton('Save')
        self.push_save.setStyleSheet(styles.btnStyle2)
        self.push_save.clicked.connect(self.savePanel)
        self.push_save.setToolTip('Save active panel parameters')
        sp = self.push_save.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.push_save.setSizePolicy(sp)

        self.push_load=QtWidgets.QPushButton('Load')
        self.push_load.setStyleSheet(styles.btnStyle2)
        self.push_load.setToolTip('Load a panel from file')
        self.push_load.clicked.connect(self.loadPanel)

        self.tabFrame = QtWidgets.QTabWidget()
        self.tabFrame.currentChanged.connect(self.tabChanged)

        hbox_1.addWidget(self.prog_panelList, 2)
        hbox_1.addWidget(self.push_add, 1)
        hbox_1.addWidget(self.push_remove, 1)
        hbox_1.addWidget(self.push_save, 1)
        hbox_1.addWidget(self.push_load, 1)

        mainLayout.addLayout(hbox_1)
        mainLayout.addWidget(self.tabFrame)
        # no margin on the bottom
        mainLayout.setContentsMargins(10,10,10,0)

        self.setContentsMargins(0,0,0,0)

        self.setLayout(mainLayout)

    def addPanel(self):

        mod = self.prog_panelList.currentData()
        topKlass = mod.toplevel
        widget = topKlass()
        self.tabFrame.addTab(widget, mod.name)
        self.tabFrame.setCurrentWidget(widget)

    def tabChanged(self, *args):
        wdg = self.tabFrame.currentWidget()

        # SuperMode provides separate facilty for saving data
        self.push_save.setVisible(not
            wdg.__class__.__module__.startswith(
            'arc1pyqt.ProgPanels.SuperMode'))

    def savePanel(self):
        filters = ['Panel data (*.json)', 'All files (*.*)']
        wdg = self.tabFrame.currentWidget()

        (saveFileName, fltr) = QtWidgets.QFileDialog.getSaveFileName(self,
            'Save panel parameters', '', ';;'.join(filters))

        if (not saveFileName) or (len(saveFileName) == 0):
            return

        if hasattr(wdg, 'extractPanelData'):
            fullmodname = ".".join([
                wdg.__class__.__module__,
                wdg.__class__.__name__])

            if (fltr == filters[0]) and (not saveFileName.lower().endswith('.json')):
                finalSaveFileName = saveFileName + ".json"
            else:
                finalSaveFileName = saveFileName

            if os.path.exists(finalSaveFileName):
                res = QtWidgets.QMessageBox.question(self, '',
                    "File %s exists. Overwrite?" % finalSaveFileName,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if res == QtWidgets.QMessageBox.No:
                    return
            with open(finalSaveFileName, 'w') as f:
                json.dump([fullmodname, wdg.extractPanelData()], f)

    def loadPanel(self):

        filters = ['Panel data (*.json)', 'All files (*.*)']

        try:
            panelDataFileNames = QtWidgets.QFileDialog.getOpenFileNames(self,
                'Open panel from file(s)...', '', ';;'.join(filters))[0]
        except IndexError:
            return

        errors = []

        if panelDataFileNames:
            for panelDataFileName in panelDataFileNames:
                with open(panelDataFileName, 'rb') as inputFile:
                    (modpath, data) = json.load(inputFile)

                if (not modpath) or (not data):
                    errors.append(panelDataFileName)
                    continue

                (modname, classname) = modpath.rsplit('.', 1)
                try:
                    panelMod = importlib.import_module(modname)
                    klass = getattr(panelMod, classname)
                    tag = getattr(panelMod, 'tags')
                    panel = klass()
                    panel.setPanelData(data)

                    self.tabFrame.addTab(panel, tag['top'].name)
                    self.tabFrame.setCurrentWidget(panel)
                except:
                    errors.append(panelDataFileName)

            if len(errors) > 0:
                QtWidgets.QMessageBox.warning(self, "Invalid module data",
                    "Could not load modules from [%s]" % ', '.join(errors),
                    QtWidgets.QMessageBox.Ok)

    def setEnabled(self, state):
        for child in range(self.tabFrame.count()):
            self.tabFrame.widget(child).setEnabled(state)

    def removePanel(self):
        self.tabFrame.removeTab(self.tabFrame.currentIndex())

