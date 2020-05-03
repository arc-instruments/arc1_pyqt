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
import importlib
import csv
import time
import requests
import subprocess
import gzip
import types
import warnings
from functools import partial
from PyQt5 import QtGui, QtCore, QtWidgets
from VirtualArC import VirtualArC
import Graphics
import ProgPanels
import ctypes
import semver

from ControlWidgets import CrossbarWidget
from ControlWidgets import DataDisplayWidget
from ControlWidgets import HistoryWidget
from ControlWidgets import ManualOpsWidget
from ControlWidgets import ProgPanelWidget


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


import Globals
import Globals.GlobalVars as g
import Globals.GlobalFunctions as f
import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts


# Version comparison
# If `target` is newer than `orig` -> 1
# If `target` is older than `orig` -> -1
# If `target` is same version as `orig` -> 0
def vercmp(orig, target):
    return semver.compare(target, orig)


def write_b(ser, what):
    ser.write(what.encode())


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

        configAction = QtWidgets.QAction('Modify hardware settings', self)
        configAction.setStatusTip('Modify hardware settings')
        configAction.triggered.connect(self.showConfig)

        # Populate settings menu
        settingsMenu.addAction(configAction)
        settingsMenu.addAction(setCWDAction)
        settingsMenu.addSeparator()
        settingsMenu.addAction(self.updateAction_menu)

        # 3) Help menu
        documentationAction = QtWidgets.QAction('Documentation', self)
        documentationAction.setStatusTip('Show ArC One documentation')
        documentationAction.triggered.connect(self.showDocumentation)

        aboutAction = QtWidgets.QAction('About ArC', self)
        aboutAction.setStatusTip('Information about ArC Instruments Ltd.')
        aboutAction.triggered.connect(self.showAbout)

        # Populate help menu
        helpMenu.addAction(documentationAction)
        helpMenu.addSeparator()
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
        self.connectBtn.setStyleSheet(s.toolBtn)

        self.discBtn=QtWidgets.QPushButton('Disconnect')
        self.discBtn.clicked.connect(self.discArC)
        self.discBtn.setStatusTip('Disconnect from ArC One')
        self.discBtn.setStyleSheet(s.toolBtn)

        self.comPorts = QtWidgets.QComboBox()
        self.comPorts.setStyleSheet(s.toolCombo)
        self.comPorts.insertItems(1,self.scanSerials())
        self.comPorts.currentIndexChanged.connect(self.updateComPort)
        g.COM=self.comPorts.currentText()

        self.refresh=QtWidgets.QPushButton('Refresh')
        self.refresh.clicked.connect(self.updateCOMList)
        self.refresh.setStyleSheet(s.toolBtn)
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
        self.toolbar.addAction(self.clearAction)

        spacer=QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        self.arcStatusLabel=QtWidgets.QLabel()
        self.arcStatusLabel.setMinimumWidth(int(200*g.scaling_factor))
        self.arcStatusLabel.setStyleSheet(s.arcStatus_disc)
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
        hp.setMinimumWidth(int(150*g.scaling_factor))
        hp.setMaximumWidth(int(300*g.scaling_factor))
        hp.setMinimumHeight(int(700*g.scaling_factor))

        self.mo.setFixedWidth(int(300*g.scaling_factor))
        dd.setMinimumWidth(int(650*g.scaling_factor))

        # define how scaling the window scales the two sections
        layoutRight.setStretchFactor(layoutTop, 5)
        layoutRight.setStretchFactor(self.layoutBot, 6)

        # same
        self.layoutBot.setStretchFactor(self.pp, 6)
        self.layoutBot.setStretchFactor(self.cp, 6)

        self.pp.setMinimumWidth(int(700*g.scaling_factor))
        self.cp.setMinimumWidth(int(600*g.scaling_factor))

        layoutTop.setSpacing(0)
        self.layoutBot.setSpacing(0)
        layoutRight.setSpacing(0)
        layoutRight.setContentsMargins(0,0,0,0)

        self.mo.setContentsMargins(0,0,0,0)

        self.setCentralWidget(splitter)
        self.saveAction.setEnabled(False)
        # connect disable signal
        f.interfaceAntenna.disable.connect(self.toggleEnable)
        f.interfaceAntenna.disable.connect(self.changeStatus)
        f.interfaceAntenna.reformat.connect(self.reformatInterface)
        f.interfaceAntenna.changeArcStatus.connect(self.changeStatus)
        f.interfaceAntenna.changeSessionMode.connect(self.setSessionModeLabel)
        f.interfaceAntenna.updateHW.connect(self.updateHW)

        f.cbAntenna.recolor.connect(self.updateSaveButton)

        # Setup main window geometry
        self.setGeometry(100, 100, int(g.scaling_factor*1500),
                int(g.scaling_factor*800))
        self.setWindowTitle('ArC One - Control Panel')
        self.setWindowIcon(Graphics.getIcon('appicon'))

        self.show()

        splashScreen.finish(self)

        self.updateAction.setEnabled(False)
        self.check_for_updates()

        self.newSessionStart()

    def check_for_updates(self):
        # check local version:
        thisdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(thisdir, "source","version.txt"), "r") as f:
            g.local_version=str(f.read().split("\n")[1])

        connection=False
        # check remote version:
        version_url="http://files.arc-instruments.co.uk/release/version.txt"
        try:
            response = requests.get(version_url, stream=True, timeout=2)
            g.remote_version=str(response.text.split("\n")[1])
            if response.status_code < 400:
                connection=True
        except Exception as exc:
            pass

        # if there is an internet connection and the remote version has been retrieved
        if connection:
            status = vercmp(g.local_version, g.remote_version)
            if status > 0:
                self.updateAction.setEnabled(True)

    def launch_manager(self):
        self.check_for_updates()
        if vercmp(g.local_version, '1.4.2') >= 0:
            msg = QtGui.QMessageBox()
            msg.setWindowTitle("ArC ONE Upgrade")
            msg.setIcon(QtGui.QMessageBox.Warning)
            msg.setText("""Your version is <b>%s</b>. Upgrading from 1.4.2 """
                        """to any newer requires a <b>fresh installation</b>. Please """
                        """follow the details at """
                        """<a href="http://www.arc-instruments.co.uk/blog/upgrade-from-142/">"""
                        """http://www.arc-instruments.co.uk/blog/upgrade-from-142/</a> """
                        """for further information.""" % g.local_version)
            msg.exec_()
            return
        reply = QtGui.QMessageBox.question(self, "Launch ArC Platform Manager",
                "This will delete all saved data and proceed with a platform update.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        if reply==QtWidgets.QMessageBox.Yes:
            directory=os.path.abspath(os.path.join(os.path.dirname(__file__),
                os.pardir, "ArC Platform Manager"))
            os.chdir(directory)
            launcher_path=os.path.join(directory,"ArC Platform Manager.exe")
            subprocess.Popen([launcher_path, g.local_version])
            QtCore.QCoreApplication.instance().quit()

    def showConfig(self):
        from ControlWidgets import ConfigHardwareWidget
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
        if g.ser.port != None:
            job="011"
            # Initial parameters job
            g.ser.write_b(job+"\n")
            g.ser.write_b(str(int(g.readCycles))+"\n")
            g.ser.write_b(str(int(g.sneakPathOption))+"\n")

    def showAbout(self):
        from ControlWidgets import AboutWidget
        self.aboutSesh = AboutWidget()
        self.aboutSesh.setFixedWidth(600)
        self.aboutSesh.setFixedHeight(300)


        frameGm = self.aboutSesh.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.aboutSesh.move(frameGm.topLeft())

        self.aboutSesh.setWindowTitle("About ArC Instruments Ltd.")
        self.aboutSesh.setWindowIcon(Graphics.getIcon('appicon'))

        self.aboutSesh.show()

    def updateCOMList(self):
        self.comPorts.clear()
        self.comPorts.insertItems(1,self.scanSerials())

    def setSessionModeLabel(self,mode):
        self.sessionModeLabel.setText(mode)

    def changeStatus(self,status):

        if (status=='Disc'):
            self.arcStatusLabel.setText('Disconnected')
            self.arcStatusLabel.setStyleSheet(s.arcStatus_disc)

        if (status=='Ready'):
            self.arcStatusLabel.setText('Ready')
            self.arcStatusLabel.setStyleSheet(s.arcStatus_ready)

        if (status=='Busy'):
            self.arcStatusLabel.setText('Busy')
            self.arcStatusLabel.setStyleSheet(s.arcStatus_busy)

        if (status==True):
            self.arcStatusLabel.setText('Busy')
            self.arcStatusLabel.setStyleSheet(s.arcStatus_busy)

        if (status==False):
            self.arcStatusLabel.setText('Ready')
            self.arcStatusLabel.setStyleSheet(s.arcStatus_ready)

        self.arcStatusLabel.update()

    def replaceCBwithBNC(self):
        pass

    def redrawCrossbar(self):
        self.cp.deleteLater()
        self.cp = CrossbarWidget()

        self.layoutBot.addWidget(self.cp)

        self.layoutBot.setStretchFactor(self.cp, 6)

    def setModeOffline(self):
        self.mo.readPanel.setEnabled(False)
        self.mo.pulsePanel.setEnabled(False)
        self.pp.setEnabled(False)
        self.update()
        pass

    def setModeBNCtoLocal(self):
        self.mo.readPanel.setEnabled(False)
        self.mo.pulsePanel.setEnabled(False)
        self.pp.setEnabled(False)
        self.update()
        pass


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
        from ControlWidgets import NewSessionDialog
        newSession = NewSessionDialog()
        newSession.setFixedWidth(500)
        newSession.setMaximumHeight(int(850*g.scaling_factor))

        frameGm = newSession.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        newSession.move(frameGm.topLeft())

        newSession.setWindowTitle("New Session")
        newSession.setWindowIcon(Graphics.getIcon('appicon'))
        g.ser.close()
        g.ser.port=None

        newSession.exec_()

    def reformatInterface(self):
        f.interfaceAntenna.disable.emit(False)
        if g.sessionMode==0:  # mode is Live: Local (Normal operation)
            self.redrawCrossbar()
            f.historyTreeAntenna.changeSessionName.emit()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Live: Local')

        elif g.sessionMode==1:  # mode is Live: External BNC
            self.replaceCBwithBNC()
            f.historyTreeAntenna.changeSessionName.emit()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Live: External BNC')
            # restrict to 1,1
            g.wline_nr=1
            g.bline_nr=1
            g.w=1
            g.b=1
            self.redrawCrossbar()

        elif g.sessionMode==2:  # mode is Live: BNC to local
            f.historyTreeAntenna.changeSessionName.emit()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Live: BNC to Local')

            self.setModeBNCtoLocal()
            self.redrawCrossbar()

        elif g.sessionMode==3:  # mode is offline
            g.wline=32
            g.bline=32
            self.setModeOffline()
            self.findAndLoadFile()
            self.redrawCrossbar()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Offline')

    def openSession(self):

        reply = QtWidgets.QMessageBox.question(self, "Open a previous session",
                "Opening a previous session will erase all recorded data. Do you want to proceed?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.deleteAllData()
            self.findAndLoadFile()
            f.interfaceAntenna.changeSessionMode.emit('Offline')
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
        bar.setStyleSheet(s.progressBarStyle)
        dialog.setWindowModality(QtCore.Qt.WindowModal)
        dialog.setWindowTitle("Loading file")
        dialog.setWindowIcon(Graphics.getIcon('appicon'))
        dialog.setBar(bar)
        dialog.setCancelButton(None)

        for (counter, values) in enumerate(rdr):
            if (counter == 0):
                g.sessionName=str(values[0])
                f.historyTreeAntenna.changeSessionName.emit()
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
                        g.Mhistory[w][b].append([m, a, pw, str(tag), readTag, readVoltage])

                        # ignore Read All points
                        if 'S R' in tag or tag[-1]=='e' or tag[0]=='P':
                            f.historyTreeAntenna.updateTree.emit(w, b)
                    except ValueError:
                        error = 1

            # find the byte size of the values + the byte size of the delimiter + the commas
            bytesLoaded += sum(map(bytecount, values)) + delimiter_size + len(values) - 1
            progress = int((bytesLoaded/filesize)*100)
            dialog.setValue(progress)

        dialog.setValue(100)
        return error

    def findAndLoadFile(self):

        # Import all programming panels in order to get all tags
        for (_, modname, ispkg) in pkgutil.iter_modules(ProgPanels.__path__):
            if ispkg:
                continue
            try:
                importlib.import_module(".".join([ProgPanels.__name__, modname]))
            except ModuleNotFoundError as exc:
                print("Could not load module %s: %s" % (modname, exc))

        path = QtCore.QFileInfo(QtWidgets.QFileDialog().\
                getOpenFileName(self, 'Open file','', g.OPEN_FI_PATTERN)[0])

        if not os.path.isfile(path.filePath()):
            return

        if str(path.filePath()).endswith('.csv.gz'):
            opener = gzip.open
            filesize = f.gzipFileSize(path.filePath())
        else:
            opener = open
            filesize = os.stat(path.filePath()).st_size

        with opener(path.filePath(), 'rt') as csvfile:
            error = self._loadCSV(csvfile, filesize, path.fileName())

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
                    if g.Mhistory[w][b]:
                        #for dataPoint in g.Mhistory[w][b]:
                        f.cbAntenna.recolor.emit(g.Mhistory[w][b][-1][0],w,b)

            f.interfaceAntenna.changeArcStatus.emit('Disc')

            return True

    def deleteAllData(self):
        g.Mhistory=[[[] for bit in range(33)] for word in range(33)]

        if g.customArray:
            for w in range(1,g.wline_nr+1):
                for b in range(1,g.bline_nr+1):
                    f.SAantenna.disable.emit(w,b)
            for device in g.customArray:
                f.SAantenna.enable.emit(device[0],device[1])
        else:
            for w in range(1,g.wline_nr+1):
                for b in range(1,g.bline_nr+1):
                    f.SAantenna.enable.emit(w,b)

        f.historyTreeAntenna.clearTree.emit()
        f.displayUpdate.updateSignal_short.emit()
        self.saveAction.setEnabled(False)

    def clearSession(self):
        reply = QtWidgets.QMessageBox.question(self, "Clear data",
                "Are you sure you want to clear all data?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.deleteAllData()
            g.saveFileName=[]
        else:
            pass

    def saveSession(self, new=False):
        if g.workingDirectory:
            if (not new) and g.saveFileName:
                path=g.workingDirectory
            else:
                path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                    'Save File', g.workingDirectory, g.SAVE_FI_PATTERN)[0])
                path=path_.filePath()
                g.saveFileName=path_.fileName()
                g.workingDirectory=path_.filePath()
        else:
            path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                'Save File', '', g.SAVE_FI_PATTERN)[0])
            path=path_.filePath()
            g.saveFileName=path_.fileName()
            g.workingDirectory=path_.filePath()

        if len(path) > 0:
            if str(path).endswith('csv.gz'):
                opener = gzip.open
            else:
                opener = open

            with opener(str(path), 'w', newline='') as stream:
                writer = csv.writer(stream)

                # Header
                writer.writerow([g.sessionName])
                writer.writerow([time.strftime("%c")])
                writer.writerow(['Wordline', 'Bitline', 'Resistance', 'Amplitude (V)',
                    'Pulse width (s)', 'Tag', 'ReadTag', 'ReadVoltage'])

                # Actual data
                for w in range(1,g.wline_nr+1):
                    for b in range(1,g.bline_nr+1):
                        for row in range(len(g.Mhistory[w][b])):
                            rowdata = [w,b]
                            for item in g.Mhistory[w][b][row]:
                                if item is not None:
                                    rowdata.append(item)
                                else:
                                    rowdata.append('')
                            writer.writerow(rowdata)
            self.saveAction.setEnabled(False)

    def exitApplication(self):
        reply = QtWidgets.QMessageBox.question(self, "Exit Application",
            "Are you sure you want to exit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            QtCore.QCoreApplication.instance().quit()
        else:
            pass

    def setCWD(self):
        if g.workingDirectory:
            wdirectory = str(QtWidgets.QFileDialog.getExistingDirectory(self,  "Select Directory", g.workingDirectory,))
        else:
            wdirectory = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        g.workingDirectory=wdirectory

    def configCB(self):
        pass

    def showDocumentation(self):

        thisdir = os.path.dirname(os.path.abspath(__file__))
        doc = os.path.join(thisdir, 'Documentation', 'ArC_ONE.pdf')

        if sys.platform == "win32":
            os.startfile(os.path.normpath(doc))
        elif sys.platform == "darwin":
            subprocess.run(['open', doc], check=True)
        elif sys.platform in ["linux", "linux2"]:
            subprocess.run(['xdg-open', doc], check=True)

    def connectArC(self):
        if g.COM=="VirtualArC":
            g.ser = VirtualArC([])
        elif g.ser.port == None:  # only connect if disconnected
            job="0"
            try:
                g.ser=serial.Serial(port=str(g.COM), baudrate=g.baudrate, timeout=7, parity=serial.PARITY_EVEN, \
                                stopbits=serial.STOPBITS_ONE)
                g.ser.write_b = types.MethodType(write_b, g.ser)

                # Reset mbed
                g.ser.write_b("00\n")

                time.sleep(1)

                # Send initial parameters
                g.ser.write_b(job+"\n")
                # Read Cycles and array size
                g.ser.write_b(str(float(g.readCycles))+"\n")
                # Word lines
                g.ser.write_b(str(float(g.wline_nr))+"\n")
                # Bit lines
                g.ser.write_b(str(float(g.bline_nr))+"\n")

                # Read mode
                g.ser.write_b(str(float(g.readOption))+"\n")
                # Session type
                g.ser.write_b(str(float(g.sessionMode))+"\n")
                # Sneak path option
                g.ser.write_b(str(float(g.sneakPathOption))+"\n")
                # Read-out voltage
                g.ser.write_b(str(float(g.Vread))+"\n")


                confirmation=[]
                try:
                    confirmation=int(g.ser.readline())
                    if (confirmation==1):
                        f.interfaceAntenna.disable.emit(False)

                        job='01'
                        g.ser.write_b(job+"\n")
                        g.ser.write_b(str(g.readOption)+"\n")
                        g.ser.write_b(str(g.Vread)+"\n")

                        # disable interface on BNC-to-Local
                        if g.sessionMode == 2:
                            self.setModeBNCtoLocal()

                    else:
                        try:
                            g.ser.close()
                            g.ser.port=None
                        except SerialException:
                            pass
                        reply = QtWidgets.QMessageBox.question(self, "Connect to ArC One",
                            "Connection failed. Please check if ArC One is connected via the USB cable, and try another COM port. If the problem persists, restart this program with ArC One connected.",
                            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                except ValueError:
                    reply = QtWidgets.QMessageBox.question(self, "Connect to ArC One",
                        "Connection failed. Please check if ArC One is connected via the USB cable, and try another COM port. If the problem persists, restart this program with ArC One connected.",
                        QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                    try:
                        g.ser.close()
                        g.ser.port=None
                    except serial.serialutil.SerialException:
                        pass

            except serial.serialutil.SerialException:
                reply = QtWidgets.QMessageBox.question(self, "Connect to ArC ONE",
                    "Connection failed due to non-existent COM port. Is Arc ONE connected?",
                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)


    def discArC(self):
        g.ser.close()
        g.ser.port=None
        f.interfaceAntenna.changeArcStatus.emit('Disc')

    def resetArC(self):
        job="00"
        g.ser.write_b(job+"\n")

    # Scan for available ports. returns a list of tuples (num, name)
    def scanSerials(self):
        from serial.tools.list_ports import comports

        available = []

        for serial in comports():
            available.append(serial.device)

        available.append("VirtualArC")

        return available

    def updateComPort(self):
        g.COM=self.comPorts.currentText()

    def updateSaveButton(self):
        self.saveAction.setEnabled(True)


def main():

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("arc1pyqt")
    Graphics.initialise()

    # Determine the scaling factor
    if sys.platform == "win32":
        from win32api import GetSystemMetrics
        monitor_width = GetSystemMetrics(0)
        monitor_height = GetSystemMetrics(1)
    else:
        monitor = app.desktop().screenGeometry()
        monitor_width = monitor.width()
        monitor_height = monitor.height()

    g.scaling_factor=float(monitor_height)/1200

    ex = Arcontrol()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
