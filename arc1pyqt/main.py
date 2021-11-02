####################################

# (c) Radu Berdan
# ArC Instruments Ltd.
# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

####################################
"""
Main module of ArC One Control Panel
"""
####################################

import sys
import os
import serial
import pkgutil
import csv
import time
import subprocess
import gzip
import types
import warnings
from functools import partial
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QStandardPaths
import ctypes

from . import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from .state import DisplayMode
from . import constants

from .ControlWidgets import CrossbarWidget
from .ControlWidgets import DataDisplayWidget
from .ControlWidgets import HistoryWidget
from .ControlWidgets import ManualOpsWidget
from .ControlWidgets import ProgPanelWidget
from .ControlWidgets import NewSessionDialog
from .ControlWidgets import AboutWidget
from .ControlWidgets import ModulePathWidget
from .Globals import fonts, styles, functions
from . import modutils
from .instrument import ArC1
from .version import VersionInfo, vercmp
from .VirtualArC import VirtualArC
from . import Graphics
from . import ProgPanels

try:
    from arc1docs import start_docs
except (ImportError, ModuleNotFoundError):
    start_docs = None


myappid = 'ArC ONE Control' # arbitrary string


# Filter pyqtgraph range warnings
warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered',
        module='pyqtgraph')
warnings.filterwarnings('ignore',
        r'invalid value encountered in (greater|less)',
        module='pyqtgraph')


# Platform dependent configuration
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class Arcontrol(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        # Splash Screen
        pixmap = Graphics.getPixmap('splash')
        splashScreen=QtWidgets.QSplashScreen(pixmap)
        splashScreen.show()

        splashScreen.showMessage("Starting up...", alignment=QtCore.Qt.AlignBottom, color=QtCore.Qt.white)


        # Setup menubar
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu('File')			# File menu
        settingsMenu = menuBar.addMenu('Settings')	# Settings menu
        helpMenu = menuBar.addMenu('Help')			# help menu

        # Define the actions of each menu item before adding them to the menu
        # 1) File Menu
        self.newAction = QtWidgets.QAction(Graphics.getIcon('new'), 'New Session', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('Start a new session')
        self.newAction.triggered.connect(self.newSession)

        self.openAction = QtWidgets.QAction(Graphics.getIcon('open'), 'Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open a previous session')
        self.openAction.triggered.connect(self.openSession)

        self.clearAction = QtWidgets.QAction(Graphics.getIcon('clear'), 'Clear', self)
        self.clearAction.setShortcut('Ctrl+D')
        self.clearAction.setStatusTip('Clear all data')
        self.clearAction.triggered.connect(self.clearSession)

        self.saveAction = QtWidgets.QAction(Graphics.getIcon('save'), 'Save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save session')
        self.saveAction.triggered.connect(partial(self.saveSession, new=False))

        self.saveAsAction = QtWidgets.QAction('Save as...', self)
        self.saveAsAction.setShortcut('Ctrl+S')
        self.saveAsAction.setStatusTip('Save session as...')
        self.saveAsAction.triggered.connect(partial(self.saveSession, new=True))

        exitAction = QtWidgets.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitApplication)

        # Populate the menu with the actions defined above
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.clearAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addSeparator()
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        # 2) Settings Menu
        self.updateAction = QtWidgets.QAction(Graphics.getIcon('platform-manager'), 'Update available', self)
        self.updateAction.setStatusTip('Update available')
        self.updateAction.triggered.connect(self.launch_manager)

        self.updateAction_menu = QtWidgets.QAction(Graphics.getIcon('platform-manager'), 'Check for updates', self)
        self.updateAction_menu.setStatusTip('Check for updates')
        self.updateAction_menu.triggered.connect(self.launch_manager)

        setCWDAction = QtWidgets.QAction('Set working directory', self)
        setCWDAction.setStatusTip('Set current working directory')
        setCWDAction.triggered.connect(self.setCWD)

        displayResistanceAction = QtWidgets.QAction(Graphics.getSvgIcon('display-res'),
            'Display Resistance')
        displayResistanceAction.setCheckable(True)
        displayResistanceAction.triggered.connect(partial(self.displayModeChanged,
            mode=DisplayMode.RESISTANCE))
        displayConductanceAction = QtWidgets.QAction(Graphics.getSvgIcon('display-cond'),
            'Display Conductance')
        displayConductanceAction.setCheckable(True)
        displayConductanceAction.triggered.connect(partial(self.displayModeChanged,
            mode=DisplayMode.CONDUCTANCE))
        displayCurrentAction = QtWidgets.QAction(Graphics.getSvgIcon('display-cur'),
            'Display Current')
        displayCurrentAction.setCheckable(True)
        displayCurrentAction.triggered.connect(partial(self.displayModeChanged,
            mode=DisplayMode.CURRENT))
        displayAbsCurrentAction = QtWidgets.QAction(Graphics.getSvgIcon('display-abs-cur'),
            'Display Absolute Current')
        displayAbsCurrentAction.setCheckable(True)
        displayAbsCurrentAction.triggered.connect(partial(self.displayModeChanged,
            mode=DisplayMode.ABS_CURRENT))

        self.displayModeGroup = QtWidgets.QActionGroup(self)
        self.displayModeGroup.setExclusive(True)
        self.displayModeGroup.addAction(displayResistanceAction)
        self.displayModeGroup.addAction(displayConductanceAction)
        self.displayModeGroup.addAction(displayCurrentAction)
        self.displayModeGroup.addAction(displayAbsCurrentAction)
        displayResistanceAction.setChecked(True)

        configAction = QtWidgets.QAction('Modify hardware settings', self)
        configAction.setStatusTip('Modify hardware settings')
        configAction.triggered.connect(self.showConfig)

        openModuleDirAction = QtWidgets.QAction('Module Directories', self)
        openModuleDirAction.triggered.connect(self.showModuleDir)

        # Populate settings menu
        settingsMenu.addAction(configAction)
        settingsMenu.addAction(setCWDAction)
        settingsMenu.addSeparator()
        #settingsMenu.addSeparator()
        settingsMenu.addAction(openModuleDirAction)
        settingsMenu.addSeparator()
        settingsMenu.addAction(self.updateAction_menu)

        # 3) Help menu
        if start_docs is not None:
            documentationAction = QtWidgets.QAction('Documentation', self)
            documentationAction.setStatusTip('Show ArC One documentation')
            documentationAction.triggered.connect(start_docs)
            helpMenu.addAction(documentationAction)
            helpMenu.addSeparator()

        aboutAction = QtWidgets.QAction('About ArC', self)
        aboutAction.setStatusTip('Information about ArC Instruments Ltd.')
        aboutAction.triggered.connect(self.showAbout)

        # Populate help menu
        helpMenu.addAction(aboutAction)


        # Setup status bar
        self.statusBar()
        ##########################

        ##########################
        # Setup toolbar
        self.toolbar = self.addToolBar('Toolbar')

        # Define custom actions/widgets for connecting to ArC
        # maybe here all need to be widgets to avoid icon issues
        self.connectBtn=QtWidgets.QPushButton('Connect')
        self.connectBtn.clicked.connect(self.connectArC)
        self.connectBtn.setStatusTip('Connect to ArC One')
        self.connectBtn.setStyleSheet(styles.toolBtn)

        self.discBtn=QtWidgets.QPushButton('Disconnect')
        self.discBtn.clicked.connect(self.discArC)
        self.discBtn.setStatusTip('Disconnect from ArC One')
        self.discBtn.setStyleSheet(styles.toolBtn)

        self.comPorts = QtWidgets.QComboBox()
        self.comPorts.setStyleSheet(styles.toolCombo)
        self.comPorts.insertItems(1,self.scanSerials())

        self.refresh=QtWidgets.QPushButton('Refresh')
        self.refresh.clicked.connect(self.updateCOMList)
        self.refresh.setStyleSheet(styles.toolBtn)
        self.refresh.setStatusTip('Refresh COM list')

        # Populate toolbar
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.updateAction)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.connectBtn)
        self.toolbar.addWidget(self.comPorts)
        self.toolbar.addWidget(self.refresh)
        self.toolbar.addWidget(self.discBtn)
        self.toolbar.addSeparator()

        self.toolbar.addAction(displayResistanceAction)
        self.toolbar.addAction(displayConductanceAction)
        self.toolbar.addAction(displayCurrentAction)
        self.toolbar.addAction(displayAbsCurrentAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.clearAction)

        spacer=QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        self.arcStatusLabel=QtWidgets.QLabel()
        self.arcStatusLabel.setMinimumWidth(int(200*APP.scalingFactor))
        self.arcStatusLabel.setStyleSheet(styles.arcStatus_disc)
        self.arcStatusLabel.setText('Disconnected')
        self.arcStatusLabel.setFont(fonts.font1)
        self.arcStatusLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.sessionModeLabel=QtWidgets.QLabel()
        self.sessionModeLabel.setFont(fonts.font1)
        self.sessionModeLabel.setText('Live: Local')

        self.toolbar.addWidget(self.sessionModeLabel)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.arcStatusLabel)

        ##########################

        splashScreen.showMessage("Loading Modules...", alignment=QtCore.Qt.AlignBottom, color=QtCore.Qt.white)

        ##########################
        # Import control panels as separate widgets
        hp = HistoryWidget()
        self.mo = ManualOpsWidget()
        self.pp = ProgPanelWidget()
        dd = DataDisplayWidget()

        self.cp = CrossbarWidget()

        # Divide the working space and populate
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal) # toplevel divider
        splitter.setHandleWidth(5)

        frameRight = QtWidgets.QWidget(self)

        layoutTop = QtWidgets.QHBoxLayout()
        layoutTop.addWidget(self.mo)
        layoutTop.addWidget(dd)

        self.layoutBot = QtWidgets.QHBoxLayout()
        self.layoutBot.addWidget(self.pp)
        self.layoutBot.addWidget(self.cp)

        layoutRight = QtWidgets.QVBoxLayout()
        layoutRight.addLayout(layoutTop)
        layoutRight.addLayout(self.layoutBot)

        frameRight.setLayout(layoutRight)

        splitter.addWidget(hp)
        splitter.addWidget(frameRight)
        splitter.setCollapsible(0,False)
        splitter.setCollapsible(1,False)

        # Setup size constraints for each compartment of the UI
        hp.setMinimumWidth(int(150*APP.scalingFactor))
        hp.setMaximumWidth(int(300*APP.scalingFactor))
        hp.setMinimumHeight(int(700*APP.scalingFactor))

        self.mo.setFixedWidth(int(300*APP.scalingFactor))
        dd.setMinimumWidth(int(650*APP.scalingFactor))

        # define how scaling the window scales the two sections
        layoutRight.setStretchFactor(layoutTop, 5)
        layoutRight.setStretchFactor(self.layoutBot, 6)

        # same
        self.layoutBot.setStretchFactor(self.pp, 6)
        self.layoutBot.setStretchFactor(self.cp, 6)

        self.pp.setMinimumWidth(int(700*APP.scalingFactor))
        self.cp.setMinimumWidth(int(600*APP.scalingFactor))

        layoutTop.setSpacing(0)
        self.layoutBot.setSpacing(0)
        layoutRight.setSpacing(0)
        layoutRight.setContentsMargins(0,0,0,0)

        self.mo.setContentsMargins(0,0,0,0)

        self.setCentralWidget(splitter)
        self.saveAction.setEnabled(False)
        # connect disable signal
        functions.interfaceAntenna.disable.connect(self.toggleEnable)
        functions.interfaceAntenna.disable.connect(self.changeStatus)
        functions.interfaceAntenna.reformat.connect(self.reformatInterface)
        functions.interfaceAntenna.changeArcStatus.connect(self.changeStatus)
        functions.interfaceAntenna.changeSessionMode.connect(self.setSessionModeLabel)
        functions.interfaceAntenna.updateHW.connect(self.updateHW)
        functions.cbAntenna.recolor.connect(self.updateSaveButton)

        # Setup main window geometry
        self.setGeometry(100, 100, int(APP.scalingFactor*1500),
                int(APP.scalingFactor*800))
        self.setWindowTitle('ArC One - Control Panel')
        self.setWindowIcon(Graphics.getIcon('appicon'))

        self.show()

        splashScreen.finish(self)

        self.updateAction.setEnabled(False)
        self.check_for_updates()

        self.newSessionStart()

    def showModuleDir(self):
        dlg = ModulePathWidget.modulePathDialog()
        dlg.exec_()

    def check_for_updates(self):

        vinfo = VersionInfo()

        try:
            if vinfo.update_available():
                self.updateAction.setEnabled(True)
        except Exception as exc:
            # versions could not be retrieved
            return

    def launch_manager(self):

        vinfo = VersionInfo()
        try:
            (local, remote) = (vinfo.local, vinfo.remote)
        except Exception:
            # versions could not be retrieved
            return

        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("ArC ONE Upgrade")
        if vercmp(local, remote) > 0:
            msg.setText(("""Your version is <b>%s</b>. There is a new """ +
                        """version available: <b>%s</b>. Please visit """ +
                        """<a href="https://github.com/arc-instruments/arc1_pyqt/releases">""" +
                        """https://github.com/arc-instruments/arc1_pyqt/releases</a> """ +
                        """to download a new version.""")
                        % (local, remote))
        else:
            msg.setText("Your ArC ONE installation is up to date!")
        msg.exec_()

    def displayModeChanged(self, _, mode):
        APP.displayMode = mode
        functions.displayUpdate.cast()

    def showConfig(self):
        from .ControlWidgets import ConfigHardwareWidget
        self.cfgHW = ConfigHardwareWidget()
        self.cfgHW.setFixedWidth(500)
        self.cfgHW.setFixedHeight(150)

        frameGm = self.cfgHW.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.cfgHW.move(frameGm.topLeft())

        self.cfgHW.setWindowTitle("Modify Hardware Settings")
        self.cfgHW.setWindowIcon(Graphics.getIcon('appicon'))
        self.cfgHW.show()

    def updateHW(self):
        # only connect if it's disconnected
        if HW.ArC is not None:
            job="011"
            # Initial parameters job
            HW.ArC.write_b(job+"\n")
            HW.ArC.write_b(str(int(HW.conf.cycles))+"\n")
            HW.ArC.write_b(str(int(HW.conf.sneakpath))+"\n")

    def showAbout(self):

        try:
            self.aboutWidget.show()
            return
        except AttributeError:
            pass

        self.aboutWidget = AboutWidget()
        self.aboutWidget.setFixedWidth(600)
        self.aboutWidget.setFixedHeight(320)

        frameGm = self.aboutWidget.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.aboutWidget.move(frameGm.topLeft())

        self.aboutWidget.setWindowTitle("About ArC ONE")
        self.aboutWidget.setWindowIcon(Graphics.getIcon('appicon'))

        self.aboutWidget.show()

    def updateCOMList(self):
        self.comPorts.clear()
        self.comPorts.insertItems(1,self.scanSerials())

    def setSessionModeLabel(self,mode):
        self.sessionModeLabel.setText(mode)

    def changeStatus(self,status):

        if (status=='Disc'):
            self.arcStatusLabel.setText('Disconnected')
            self.arcStatusLabel.setStyleSheet(styles.arcStatus_disc)

        if (status=='Ready'):
            self.arcStatusLabel.setText('Ready')
            self.arcStatusLabel.setStyleSheet(styles.arcStatus_ready)

        if (status=='Busy'):
            self.arcStatusLabel.setText('Busy')
            self.arcStatusLabel.setStyleSheet(styles.arcStatus_busy)

        if (status==True):
            self.arcStatusLabel.setText('Busy')
            self.arcStatusLabel.setStyleSheet(styles.arcStatus_busy)

        if (status==False):
            self.arcStatusLabel.setText('Ready')
            self.arcStatusLabel.setStyleSheet(styles.arcStatus_ready)

        self.arcStatusLabel.update()

    def redrawCrossbar(self):
        self.cp.setParent(None)
        del self.cp
        self.cp = CrossbarWidget()

        self.layoutBot.addWidget(self.cp)

        self.layoutBot.setStretchFactor(self.cp, 6)

    def setModeOffline(self):
        self.mo.readPanel.setEnabled(False)
        self.mo.pulsePanel.setEnabled(False)
        self.pp.setEnabled(False)
        self.update()

    def setModeBNCtoLocal(self):
        self.mo.readPanel.setEnabled(False)
        self.mo.pulsePanel.setEnabled(False)
        self.pp.setEnabled(False)
        self.update()

    def toggleEnable(self,state):
        if (state==True):
            self.mo.readPanel.setEnabled(False)
            self.mo.pulsePanel.setEnabled(False)
            self.pp.setEnabled(False)
            self.cp.setEnabled(False)
            #self.saveAction.setEnabled(False)
            self.openAction.setEnabled(False)
            self.clearAction.setEnabled(False)
            self.newAction.setEnabled(False)
            self.refresh.setEnabled(False)

            self.connectBtn.setEnabled(False)
            self.discBtn.setEnabled(False)
            self.update()
        else:
            self.mo.readPanel.setEnabled(True)
            self.mo.pulsePanel.setEnabled(True)
            self.pp.setEnabled(True)
            self.cp.setEnabled(True)
            self.refresh.setEnabled(True)
            self.openAction.setEnabled(True)
            self.clearAction.setEnabled(True)
            self.newAction.setEnabled(True)
            self.connectBtn.setEnabled(True)
            self.discBtn.setEnabled(True)
            self.update()


    def newSession(self):
        if self.saveAction.isEnabled():
            reply = QtWidgets.QMessageBox.question(self, "Start a new session",
                    "Starting a new session will erase all recorded data. Do you want to proceed?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

            if reply == QtWidgets.QMessageBox.Yes:
                self.newSessionStart()

            elif reply == QtWidgets.QMessageBox.No:
                pass
            else:
                pass
            pass
        else:
            self.newSessionStart()

    def newSessionStart(self):
        self.deleteAllData()
        newSession = NewSessionDialog()
        newSession.setFixedWidth(500)

        frameGm = newSession.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        newSession.move(frameGm.topLeft())

        newSession.setWindowTitle("New Session")
        newSession.setWindowIcon(Graphics.getIcon('appicon'))
        if HW.ArC is not None:
            HW.ArC.close()
            HW.ArC = None

        newSession.exec_()

    def reformatInterface(self):
        functions.interfaceAntenna.disable.emit(False)

        session = HW.conf.sessionmode

        if session == 0:  # mode is Live: Local (Normal operation)
            self.redrawCrossbar()
            functions.historyTreeAntenna.changeSessionName.emit()
            functions.interfaceAntenna.changeArcStatus.emit('Disc')
            functions.interfaceAntenna.changeSessionMode.emit('Live: Local')

        elif session == 1:  # mode is Live: External BNC
            functions.historyTreeAntenna.changeSessionName.emit()
            functions.interfaceAntenna.changeArcStatus.emit('Disc')
            functions.interfaceAntenna.changeSessionMode.emit('Live: External BNC')
            # restrict to 1,1
            HW.conf.words = 1
            HW.conf.bits = 1
            CB.word = 1
            CB.bit = 1
            self.redrawCrossbar()

        elif session == 2:  # mode is Live: BNC to local
            functions.historyTreeAntenna.changeSessionName.emit()
            functions.interfaceAntenna.changeArcStatus.emit('Disc')
            functions.interfaceAntenna.changeSessionMode.emit('Live: BNC to Local')

            self.setModeBNCtoLocal()
            self.redrawCrossbar()

        elif session == 3:  # mode is offline
            HW.conf.words = 32
            HW.conf.bits = 32
            self.setModeOffline()
            self.redrawCrossbar()
            self.findAndLoadFile()
            functions.interfaceAntenna.changeArcStatus.emit('Disc')
            functions.interfaceAntenna.changeSessionMode.emit('Offline')

    def openSession(self):

        reply = QtWidgets.QMessageBox.question(self, "Open a previous session",
                "Opening a previous session will erase all recorded data. Do you want to proceed?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.deleteAllData()
            self.findAndLoadFile()
            functions.interfaceAntenna.changeSessionMode.emit('Offline')
        else:
            pass


    def _loadCSV(self, csvfile, filesize, filename):

        bytecount = lambda x: len(x.encode())

        bytesLoaded = 0
        rdr = csv.reader(csvfile)
        delimiter_size = len(rdr.dialect.lineterminator.encode())

        error = 0

        dialog = QtWidgets.QProgressDialog("Loading file <b>%s</b>…" % filename,
                "Cancel", 0, 100, parent=self)
        bar = QtWidgets.QProgressBar()
        bar.setStyleSheet(styles.progressBarStyle)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle("Loading file")
        dialog.setWindowIcon(Graphics.getIcon('appicon'))
        dialog.setBar(bar)
        dialog.setCancelButton(None)

        for (counter, values) in enumerate(rdr):
            if (counter == 0):
                APP.sessionName=str(values[0])
                functions.historyTreeAntenna.changeSessionName.emit()
            else:
                if counter > 2:
                    try:
                        w = int(values[0])
                        b = int(values[1])
                        m = float(values[2])
                        a = float(values[3])
                        pw = float(values[4])
                        tag = str(values[5])
                        readTag = str(values[6])
                        readVoltage = float(values[7])
                        CB.append(w, b, m, a, pw, str(tag), readTag, readVoltage)

                        # ignore Read All points
                        if 'S R' in tag or tag[-1]=='e' or tag == 'P':
                            functions.historyTreeAntenna.updateTree.emit(w, b)
                    except ValueError:
                        error = 1

            # find the byte size of the values + the byte size of the delimiter + the commas
            bytesLoaded += sum(map(bytecount, values)) + delimiter_size + len(values) - 1
            progress = int((bytesLoaded/filesize)*100)
            dialog.setValue(progress)

        dialog.setValue(100)
        return error

    def findAndLoadFile(self):

        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',
            filter=constants.OPEN_FI_PATTERN)[0]

        if not os.path.isfile(path):
            return

        if path.endswith('.gz'):
            opener = gzip.open
            filesize = functions.gzipFileSize(path)
        else:
            opener = open
            filesize = os.stat(path).st_size

        with opener(path, 'rt') as csvfile:
            error = self._loadCSV(csvfile, filesize, os.path.basename(path))

        # check if positions read are correct
        if (error):
            errMessage = QtWidgets.QMessageBox()
            errMessage.setText("Selected file is incompatible!")
            errMessage.setIcon(QtWidgets.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

            return False
        else:
            for w in range(1,33):
                for b in range(1,33):
                    if CB.history[w][b]:
                        functions.cbAntenna.recolor.emit(CB.history[w][b][-1][0],w,b)

            functions.interfaceAntenna.changeArcStatus.emit('Disc')

            return True

    def deleteAllData(self):
        CB.history=[[[] for bit in range(33)] for word in range(33)]

        if CB.customArray:
            for w in range(1,HW.conf.words+1):
                for b in range(1,HW.conf.bits+1):
                    functions.SAantenna.disable.emit(w,b)
            for device in CB.customArray:
                functions.SAantenna.enable.emit(device[0],device[1])
        else:
            for w in range(1,HW.conf.words+1):
                for b in range(1,HW.conf.bits+1):
                    functions.SAantenna.enable.emit(w,b)

        functions.historyTreeAntenna.clearTree.emit()
        functions.displayUpdate.updateSignal_short.emit()
        self.saveAction.setEnabled(False)

    def clearSession(self):
        reply = QtWidgets.QMessageBox.question(self, "Clear data",
                "Are you sure you want to clear all data?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.deleteAllData()
            APP.saveFileName=[]
        else:
            pass

    def saveSession(self, new=False):
        if APP.workingDirectory:
            if (not new) and APP.saveFileName:
                path = APP.workingDirectory
            else:
                path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                    'Save File', APP.workingDirectory, constants.SAVE_FI_PATTERN)[0])
                path = path_.filePath()
                APP.saveFileName = path_.fileName()
                APP.workingDirectory = path_.filePath()
        else:
            path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                'Save File', '', constants.SAVE_FI_PATTERN)[0])
            path = path_.filePath()
            APP.saveFileName=path_.fileName()
            APP.workingDirectory=path_.filePath()

        if len(path) > 0:
            if str(path).endswith('csv.gz'):
                opener = gzip.open
            else:
                opener = open

            with opener(str(path), 'w', newline='') as stream:
                writer = csv.writer(stream)

                # Header
                writer.writerow([APP.sessionName])
                writer.writerow([time.strftime("%c")])
                writer.writerow(['Wordline', 'Bitline', 'Resistance', 'Amplitude (V)',
                    'Pulse width (s)', 'Tag', 'ReadTag', 'ReadVoltage'])

                # Actual data
                for w in range(1,HW.conf.words+1):
                    for b in range(1,HW.conf.bits+1):
                        for row in range(len(CB.history[w][b])):
                            rowdata = [w, b]
                            # drop the start index, it's ephemeral
                            # and it's only needed for runtime
                            for item in CB.history[w][b][row][:-1]:
                                if item is not None:
                                    rowdata.append(item)
                                else:
                                    rowdata.append('')
                            writer.writerow(rowdata)
            self.saveAction.setEnabled(False)

    def closeEvent(self, evt):
        reply = QtWidgets.QMessageBox.question(self, "Exit Application",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            evt.accept()
        else:
            evt.ignore()

    def exitApplication(self):
        reply = QtWidgets.QMessageBox.question(self, "Exit Application",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            QtCore.QCoreApplication.instance().quit()
        else:
            pass

    def setCWD(self):
        if APP.workingDirectory:
            wdirectory = str(QtWidgets.QFileDialog.getExistingDirectory(self, \
                    "Select Directory", APP.workingDirectory,))
        else:
            wdirectory = str(QtWidgets.QFileDialog.getExistingDirectory(self, \
                    "Select Directory"))
        APP.workingDirectory = wdirectory

    def connectArC(self):

        port = self.comPorts.currentText()
        if port == "VirtualArC":
            HW.ArC = VirtualArC()
            return

        try:
            HW.ArC = ArC1(port)
            HW.ArC.initialise(HW.conf)
            functions.interfaceAntenna.changeArcStatus.emit('Ready')

            # if mode is bnc-to-local update interface accordingly
            if HW.conf.sessionmode == 2:
                self.setModeBNCtoLocal()

        except Exception as exc:
            print("Error while initialising ArC1:", exc)
            reply = QtWidgets.QMessageBox.question(self, "Connect to ArC One",
                "Connection failed. Please check if ArC One is connected via the "
                "USB cable, and try another COM port. If the problem persists, "
                "restart this program with ArC One connected.",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            HW.ArC = None


    def discArC(self):
        if HW.ArC is None:
            return

        HW.ArC.close()
        #ArC.port=None
        functions.interfaceAntenna.changeArcStatus.emit('Disc')
        HW.ArC = None

    def resetArC(self):
        HW.ArC.reset()

    # Scan for available ports. returns a list of tuples (num, name)
    def scanSerials(self):
        from serial.tools.list_ports import comports

        available = []

        for serial in comports():
            available.append(serial.device)

        available.append("VirtualArC")

        return available

    def updateSaveButton(self):
        self.saveAction.setEnabled(True)


def main():
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("arc1pyqt")
    Graphics.initialise()

    # Add standard readout and pulse. These are never top-level modules and
    # have no callbacks
    APP.modules['S R'] = modutils.ModDescriptor(None, 'Read', 'Read', False, None)
    APP.modules['P'] = modutils.ModDescriptor(None, 'Pulse', 'Pulse', False, None)

    # Get all possible locations for data files as long as it includes
    # a "ProgPanels" directory under it.
    paths = QStandardPaths.locateAll(QStandardPaths.AppDataLocation, \
            'ProgPanels', \
            QStandardPaths.LocateDirectory)

    # QStandardPaths.locateAll follows the following priority (high to low)
    # $HOME/.local/share/<app>, /usr/local/share/<app>, /usr/share/<app>
    #       idx = 0                   idx = 1              idx = 2
    # In order to make sure that the most local module will always overwrite
    # a less local we need to make sure that the most local modules are always
    # loaded LAST and hence we reverse the list reported by `locateAll`.
    paths.reverse()

    # built-in modules first (under `ProgPanels`)
    modutils.discoverModules(ProgPanels.__path__, 'arc1pyqt.ProgPanels')
    # and all user-supplied modules (under a non-physical module `ExtPanels`)
    # external packages MUST be forced into `sys.modules` otherwise internal
    # package resolution will fail
    modutils.discoverModules(paths, 'arc1pyqt.ExtPanels', True)

    # Determine the scaling factor
    if sys.platform == "win32":
        from win32api import GetSystemMetrics
        monitor_width = GetSystemMetrics(0)
        monitor_height = GetSystemMetrics(1)
    else:
        monitor = app.desktop().screenGeometry()
        monitor_width = monitor.width()
        monitor_height = monitor.height()

    APP.scalingFactor=float(monitor_height)/1200

    ex = Arcontrol()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
