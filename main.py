
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
import importlib
import csv
import time
import requests
import subprocess
import gzip
import types
from functools import partial
from PyQt5 import QtGui, QtCore, QtWidgets
from virtualArC import virtualarc
import ctypes
myappid = 'ArC ONE Control' # arbitrary string

# Platform dependent configuration
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    serialFormat = 'COM%d'
elif sys.platform in ["linux", "linux2"]:
    serialFormat = '/dev/ttyACM%d'
elif sys.platform in ["darwin"]:
    serialFormat = '/dev/tty.usbmodem%d'
else:
    serialFormat = '%d'

import Globals

import Globals.GlobalVars as g
import Globals.GlobalFunctions as f
import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts

import ControlPanels


def write_b(ser, what):
    ser.write(what.encode())


class Arcontrol(QtWidgets.QMainWindow):

    operationProgress = QtCore.pyqtSignal(int)
    operationFinished = QtCore.pyqtSignal()

    def __init__(self):
        super(Arcontrol, self).__init__()

        self.initUI()

    def initUI(self):


        ##########################
        # SPLASH SCREEN #
        pixmap = QtGui.QPixmap(os.getcwd()+"/Graphics/"+'splash2.png')
        splashScreen=QtWidgets.QSplashScreen(pixmap)
        splashScreen.show()
        ##########################

        splashScreen.showMessage("Starting up...", alignment=QtCore.Qt.AlignBottom, color=QtCore.Qt.white)


        ##########################
        # Setup menubar
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu('File')			# File menu
        settingsMenu = menuBar.addMenu('Settings')	# Setting menu
        helpMenu = menuBar.addMenu('Help')			# help menu

        # Define the actions of each menu item before adding them to the menu
        # 1) File Menu
        self.newAction = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'new.png'),'New Session', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('Start a new session')
        self.newAction.triggered.connect(self.newSession)


        self.openAction = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'open.png'),'Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open a previous session')
        self.openAction.triggered.connect(self.openSession)

        self.clearAction = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'clear.png'), 'Clear', self)
        self.clearAction.setShortcut('Ctrl+D')
        self.clearAction.setStatusTip('Clear all data')
        self.clearAction.triggered.connect(self.clearSession)

        self.saveAction = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'save.png'),'Save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save session')
        self.saveAction.triggered.connect(partial(self.saveSession, new=False))

        self.saveAsAction = QtWidgets.QAction('Save as...', self)
        self.saveAsAction.setShortcut('Ctrl+S')
        self.saveAsAction.setStatusTip('Save session as...')
        self.saveAsAction.triggered.connect(partial(self.saveSession, new=True))

        #exportEPSAction = QtWidgets.QAction('As EPS', self)
        #exportEPSAction.setStatusTip('Save current figure as EPS')
        #exportEPSAction.triggered.connect(self.exportSession)

        #exportPNGAction = QtWidgets.QAction('As PNG', self)
        #exportPNGAction.setStatusTip('Save current figure as PNG')
        #exportPNGAction.triggered.connect(self.exportSession)

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
        #exportMenu = fileMenu.addMenu('Export figure')
        #exportMenu.setStatusTip('Export figure...')
        #exportMenu.addAction(exportEPSAction)
        #exportMenu.addAction(exportPNGAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        # 2) Settings Menu
        self.updateAction = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'platform_manager.png'),'Update available', self)
        self.updateAction.setStatusTip('Update available')
        self.updateAction.triggered.connect(self.launch_manager)

        self.updateAction_menu = QtWidgets.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'platform_manager.png'),'Check for updates', self)
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


        #splashScreen.showMessage("Building menus...", alignment=QtCore.Qt.AlignBottom, color=QtCore.Qt.white)
        # Setup status bar
        self.statusBar()
        ##########################

        ##########################
        # Setup toolbar
        self.toolbar = self.addToolBar('Toolbar')

        # Define custom actions/widgets for connecting to ArC
        # maybe here all need to be widgets to avoid icon issues
        #connectAction = QtWidgets.QAction('Connect', self)

        self.connectBtn=QtWidgets.QPushButton('Connect')
        self.connectBtn.clicked.connect(self.connectArC)
        self.connectBtn.setStatusTip('Connect to ArC One')
        self.connectBtn.setStyleSheet(s.toolBtn)

        #connectAction.setStyleSheet(s.btnStyle2)
        #connectAction.setStatusTip('Connect to ArC One')
        #connectAction.triggered.connect(self.connectArC)

        #resetAction = QtWidgets.QAction('Reset', self)
        #resetAction.setStatusTip('Reset ArC One')
        #resetAction.triggered.connect(self.resetArC)

        #discAction = QtWidgets.QAction('Disconnect', self)
        #discAction.setStatusTip('Disconnect ArC One')
        #discAction.triggered.connect(self.discArC)

        self.discBtn=QtWidgets.QPushButton('Disconnect')
        self.discBtn.clicked.connect(self.discArC)
        self.discBtn.setStatusTip('Disconnect from ArC One')
        self.discBtn.setStyleSheet(s.toolBtn)

        self.comPorts = QtWidgets.QComboBox()
        self.comPorts.setStyleSheet(s.toolCombo)
        self.comPorts.insertItems(1,self.scanSerials())
        self.comPorts.currentIndexChanged.connect(self.updateComPort)
        #self.comPorts.view().clicked.connect(self.updateCOMList)
        #self.comPorts.installEventFilter(self)
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
        self.arcStatusLabel.setMinimumWidth(200*g.scaling_factor)
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

        from ControlPanels import crossbar_panel
        from ControlPanels import dataDisplay_panel
        from ControlPanels import history_panel
        from ControlPanels import manualOperations_panel
        from ControlPanels import prog_panel

        ##########################
        # Import control panels as separate widgets
        hp = history_panel.history_panel()
        self.mo = manualOperations_panel.manualOperations_panel()
        self.pp = prog_panel.prog_panel()
        dd = dataDisplay_panel.dataDisplay_panel()

        self.cp = crossbar_panel.crossbar_panel()

        # Divide the working space and populate
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal) # toplevel divider
        splitter.setHandleWidth(5)

        frameRight = QtWidgets.QWidget(self)	# define it as a widget; works also if it's defined as a frame

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
        #splitter.setContentsMargins(0,0,0,0)
        hp.setMinimumWidth(150*g.scaling_factor)
        hp.setMaximumWidth(300*g.scaling_factor)
        hp.setMinimumHeight(700*g.scaling_factor)

        self.mo.setFixedWidth(300*g.scaling_factor)
        dd.setMinimumWidth(650*g.scaling_factor)

        layoutRight.setStretchFactor(layoutTop, 5)	# define how scaling the window scales the two sections
        layoutRight.setStretchFactor(self.layoutBot, 6)

        self.layoutBot.setStretchFactor(self.pp, 6)			# define how scaling the window scales the two sections
        self.layoutBot.setStretchFactor(self.cp, 6)

        self.pp.setMinimumWidth(700*g.scaling_factor)
        self.cp.setMinimumWidth(600*g.scaling_factor)

        layoutTop.setSpacing(0)
        self.layoutBot.setSpacing(0)
        layoutRight.setSpacing(0)
        layoutRight.setContentsMargins(0,0,0,0)

        self.mo.setContentsMargins(0,0,0,0)

        self.setCentralWidget(splitter) 	# make the central widget the splitter
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
        self.setGeometry(100, 100, g.scaling_factor*1500, g.scaling_factor*800)
        self.setWindowTitle('ArC One - Control Panel')
        self.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))

        self.show()

        splashScreen.finish(self)

        self.updateAction.setEnabled(False)
        self.check_for_updates()

        self.newSessionStart()

    def check_for_updates(self):
        # Version comparison
        # If `target` is newer than `orig` -> 1
        # If `target` is older than `orig` -> -1
        # If `target` is same version as `orig` -> 0
        def vercmp(orig, target):
            old = [int(x) for x in orig.split(".")]
            # if version has less than 3 parts, pad with zeros
            if len(old) < 3:
                old.extend([0] * (3 - len(old)))

            new = [int(x) for x in target.split(".")]
            # if version has less than 3 parts, pad with zeros
            if len(new) < 3:
                new.extend([0] * (3 - len(new)))

            for i in range(3):
                if new[i] > old[i]:
                    return 1
                if new[i] < old[i]:
                    return -1
            return 0

        # check local version:
        with open(os.path.join("source","version.txt"), "r") as f:
            g.local_version=str(f.read().split("\n")[1])

        connection=False
        # check remote version:
        version_url="http://arc-instruments.com/files/release/version.txt"
        try:
            response = requests.get(version_url, stream=True, timeout=2)
            g.remote_version=str(response.text.split("\n")[1])
            connection=True
        except:
            pass

        if connection: # if there is an internet connection and the remote version has been retrieved
            status = vercmp(g.local_version, g.remote_version)
            if status > 0:
                self.updateAction.setEnabled(True)

    def launch_manager(self):
        self.check_for_updates()
        reply = QtWidgets.QMessageBox.question(self, "Launch ArC Platform Manager",
                "This will delete all saved data and proceed with a platform update.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        if reply==QtWidgets.QMessageBox.Yes:
            directory=os.path.join(os.getcwd(),os.pardir,"ArC Platform Manager")
            os.chdir(directory)
            launcher_path=os.path.join(directory,"ArC Platform Manager.exe")# + g.local_version)
            subprocess.Popen([launcher_path, g.local_version])
            QtCore.QCoreApplication.instance().quit()

        # get current version

    def showConfig(self):
        from ControlPanels import configHardware
        self.cfgHW=configHardware.configHardware()
        self.cfgHW.setFixedWidth(500)
        self.cfgHW.setFixedHeight(150)

        frameGm = self.cfgHW.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.cfgHW.move(frameGm.topLeft())

        self.cfgHW.setWindowTitle("Modify Hardware Settings")
        self.cfgHW.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))
        self.cfgHW.show()

    def updateHW(self):
        if g.ser.port != None:  # only connect if it's disconnected
            job="011"
            g.ser.write_b(job+"\n")                       # Send initial parameters
            g.ser.write_b(str(int(g.readCycles))+"\n")         # readcycles and array size
            g.ser.write_b(str(int(g.sneakPathOption))+"\n")           # send total nr of wordlines

    def showAbout(self):
        from ControlPanels import aboutSection
        self.aboutSesh=aboutSection.aboutSection()
        self.aboutSesh.setFixedWidth(600)
        self.aboutSesh.setFixedHeight(300)


        frameGm = self.aboutSesh.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.aboutSesh.move(frameGm.topLeft())

        self.aboutSesh.setWindowTitle("About ArC Instruments Ltd.")
        self.aboutSesh.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))

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
        from ControlPanels import crossbar_panel
        self.cp=crossbar_panel.crossbar_panel()

        self.layoutBot.addWidget(self.cp)

        self.layoutBot.setStretchFactor(self.cp, 6)
        #self.show()

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

                #print "Yes"
                #clear mhistory
                self.newSessionStart()

                #clear data display
                #clear crossbar
            elif reply == QtWidgets.QMessageBox.No:
                pass
            else:
                pass
            pass
        else:
            self.newSessionStart()

    def newSessionStart(self):
        self.deleteAllData()
        from ControlPanels import new_Session
        self.newSesh=new_Session.new_Session()
        self.newSesh.setFixedWidth(500)
        self.newSesh.setMaximumHeight(850*g.scaling_factor)


        frameGm = self.newSesh.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.newSesh.move(frameGm.topLeft())

        self.newSesh.setWindowTitle("New Session")
        self.newSesh.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))
        g.ser.close()
        g.ser.port=None
        #f.interfaceAntenna.changeArcStatus.emit('Disc')

        self.newSesh.show()


    def reformatInterface(self):
        f.interfaceAntenna.disable.emit(False)
        if g.sessionMode==0:        # if mode is Live: Local (Normal operation)
            self.redrawCrossbar()
            f.historyTreeAntenna.changeSessionName.emit()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Live: Local')

        elif g.sessionMode==1:      # mode is Live: External BNC
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

        elif g.sessionMode==2:      # mode is Live: BNC to local
            f.historyTreeAntenna.changeSessionName.emit()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Live: BNC to Local')

            self.setModeBNCtoLocal()
            self.redrawCrossbar()
            pass
            # restrict outputs on the mBED level
            # disables the whole interface except for CB
            # click on cb selects the device

        elif g.sessionMode==3:     # mode is offline
            g.wline=32
            g.bline=32
            self.setModeOffline()
            self.findAndLoadFile()
            self.redrawCrossbar()
            f.interfaceAntenna.changeArcStatus.emit('Disc')
            f.interfaceAntenna.changeSessionMode.emit('Offline')

            pass
            # cannot connect to mBED
            # open file works

        #f.interfaceAntenna.reformat.emit()

        pass

    def openSession(self):

        reply = QtWidgets.QMessageBox.question(self, "Open a previous session",
                "Opening a previous session will erase all recorded data. Do you want to proceed?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.Yes:
            self.deleteAllData()
            self.findAndLoadFile()
            f.interfaceAntenna.changeSessionMode.emit('Offline')
        elif reply == QtWidgets.QMessageBox.No:
            pass
        else:
            pass


    def _loadCSV(self, csvfile, filesize):

        bytecount = lambda x: len(x.encode())

        bytesLoaded = 0
        rdr = csv.reader(csvfile)
        delimiter_size = len(rdr.dialect.lineterminator.encode())

        error = 0

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

                        if 'S R' in tag or tag[-1]=='e' or tag[0]=='P': # ignore read all points
                            f.historyTreeAntenna.updateTree.emit(w, b)
                    except ValueError:
                        error = 1

            # find the byte size of the values + the byte size of the delimiter + the commas
            bytesLoaded += sum(map(bytecount, values)) + delimiter_size + len(values) - 1
            progress = int((bytesLoaded/filesize)*100)
            self.operationProgress.emit(progress)
            print("Loading file %d%%\r" % progress, end='')

        print()
        self.operationFinished.emit()
        return error

    def findAndLoadFile(self):

        # Import all programming panels in order to get all tags
        files = [fls for fls in os.listdir('ProgPanels') if fls.endswith(".py")]
        for fls in files:
            try:
                importlib.import_module(fls[:-3])     # import the module
            except:
                print("WARNING - Could not load libraries related to module:", fls[:-3])

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
            error = self._loadCSV(csvfile, filesize)

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

            print("File loaded successfully")
            f.interfaceAntenna.changeArcStatus.emit('Disc')

            return True

    def deleteAllData(self):
        g.Mhistory=[[[] for bit in range(33)] for word in range(33)]  # Main data container
            #Clear History tree
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
            #clear data display
            #clear crossbar
        else:
            pass

    def saveSession(self, new=False):
        if g.workingDirectory:
            if (not new) and g.saveFileName:
                path=g.workingDirectory
            else:
                path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                    'Save File', g.workingDirectory, g.SAVE_FI_PATTERN))
                path=path_.filePath()
                g.saveFileName=path_.fileName()
                g.workingDirectory=path_.filePath()
        else:
            path_ = QtCore.QFileInfo(QtWidgets.QFileDialog.getSaveFileName(self, \
                'Save File', '', g.SAVE_FI_PATTERN))
            path=path_.filePath()
            g.saveFileName=path_.fileName()
            g.workingDirectory=path_.filePath()

        if not path.isEmpty():
            if str(path).endswith('csv.gz'):
                opener = gzip.open
            else:
                opener = open

            with opener(str(path), 'wb') as stream:
                writer = csv.writer(stream)
                ######################
                writer.writerow([g.sessionName])
                writer.writerow([time.strftime("%c")])
                ########################

                writer.writerow(['Wordline', 'Bitline', 'Resistance', 'Amplitude (V)', 'Pulse width (s)', 'Tag', 'ReadTag','ReadVoltage'])
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

        doc = os.getcwd()+'/Documentation/'+'ArC_ONE.pdf'
        os.system('"' + doc + '"')

    def connectArC(self):
        #g.ser=virtualarc.virtualArC([])
        if g.COM=="VirtualArC":
            g.ser=virtualarc.virtualArC([])
        elif g.ser.port == None:  # only connect if it's disconnected
            job="0"
            try:
                #g.ser=virtualarc.virtualArC([])
                g.ser=serial.Serial(port=str(g.COM), baudrate=g.baudrate, timeout=7, parity=serial.PARITY_EVEN, \
                                stopbits=serial.STOPBITS_ONE) # connect to the serial port
                g.ser.write_b = types.MethodType(write_b, g.ser)

                g.ser.write_b("00\n") # initial reset of the mBED

                time.sleep(1)

                g.ser.write_b(job+"\n")                       # Send initial parameters
                g.ser.write_b(str(float(g.readCycles))+"\n")         # readcycles and array size
                g.ser.write_b(str(float(g.wline_nr))+"\n")           # send total nr of wordlines
                g.ser.write_b(str(float(g.bline_nr))+"\n")           # send total nr of bitlines

                g.ser.write_b(str(float(g.readOption))+"\n")
                g.ser.write_b(str(float(g.sessionMode))+"\n")        # send session mode
                g.ser.write_b(str(float(g.sneakPathOption))+"\n")

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

    def scanSerials(self):  # scan for available ports. returns a list of tuples (num, name)
        available = []
        for i in range(256):
            try:
                s = serial.Serial(serialFormat % i)
                available.append(s.name)
                s.close()
            except serial.SerialException:
                pass
        available.append("VirtualArC")
        return available

    def updateComPort(self):
        g.COM=self.comPorts.currentText()

    def updateSaveButton(self):
        self.saveAction.setEnabled(True)


def main():

    app = QtWidgets.QApplication(sys.argv)

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
