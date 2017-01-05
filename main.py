
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
import FileDialog
import requests
import subprocess
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit
from PyQt4.QtWebKit import QWebView
from PyQt4.QtCore import QUrl
from virtualArC import virtualarc
import ctypes
myappid = 'ArC ONE Control' # arbitrary string

# Platform dependent configuration
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    serialFormat = 'COM%d'
elif sys.platform in ["linux", "linux2", "darwin"]:
    serialFormat = '/dev/ttyUSB%d'
else:
    serialFormat = '%d'

import ControlPanels
import Globals

import Globals.GlobalVars as g
import Globals.GlobalFunctions as f
import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts

class Arcontrol(QtGui.QMainWindow):
    
    def __init__(self):
        super(Arcontrol, self).__init__()
        
        self.initUI()
        
    def initUI(self): 
        ##########################
        # SPLASH SCREEN #
        pixmap = QtGui.QPixmap(os.getcwd()+"/Graphics/"+'splash2.png')
        splashScreen=QtGui.QSplashScreen(pixmap)
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
        self.newAction = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'new.png'),'New Session', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('Start a new session')
        self.newAction.triggered.connect(self.newSession)


        self.openAction = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'open.png'),'Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open a previous session')
        self.openAction.triggered.connect(self.openSession)

        self.clearAction = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'clear.png'), 'Clear', self)
        self.clearAction.setShortcut('Ctrl+D')
        self.clearAction.setStatusTip('Clear all data')
        self.clearAction.triggered.connect(self.clearSession)

        self.saveAction = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'save.png'),'Save', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save session')
        self.saveAction.triggered.connect(self.saveSession)

        self.saveAsAction = QtGui.QAction('Save as...', self)
        self.saveAsAction.setShortcut('Ctrl+S')
        self.saveAsAction.setStatusTip('Save session as...')
        self.saveAsAction.triggered.connect(self.saveAsSession)

        #exportEPSAction = QtGui.QAction('As EPS', self)
        #exportEPSAction.setStatusTip('Save current figure as EPS')
        #exportEPSAction.triggered.connect(self.exportSession)

        #exportPNGAction = QtGui.QAction('As PNG', self)
        #exportPNGAction.setStatusTip('Save current figure as PNG')
        #exportPNGAction.triggered.connect(self.exportSession)

        exitAction = QtGui.QAction('Exit', self)
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
        self.updateAction = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'platform_manager.png'),'Update available', self)
        self.updateAction.setStatusTip('Update available')
        self.updateAction.triggered.connect(self.launch_manager)

        self.updateAction_menu = QtGui.QAction(QtGui.QIcon(os.getcwd()+"/Graphics/"+'platform_manager.png'),'Check for updates', self)
        self.updateAction_menu.setStatusTip('Check for updates')
        self.updateAction_menu.triggered.connect(self.launch_manager)        

        setCWDAction = QtGui.QAction('Set working directory', self)
        setCWDAction.setStatusTip('Set current working directory')
        setCWDAction.triggered.connect(self.setCWD)

        configAction = QtGui.QAction('Modify hardware settings', self)
        configAction.setStatusTip('Modify hardware settings')
        configAction.triggered.connect(self.showConfig)

        # Populate settings menu
        settingsMenu.addAction(configAction)
        settingsMenu.addAction(setCWDAction)
        settingsMenu.addSeparator()
        settingsMenu.addAction(self.updateAction_menu)

        # 3) Help menu
        documentationAction = QtGui.QAction('Documentation', self)
        documentationAction.setStatusTip('Show ArC One documentation')
        documentationAction.triggered.connect(self.showDocumentation)

        aboutAction = QtGui.QAction('About ArC', self)
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
        #connectAction = QtGui.QAction('Connect', self)
        
        self.connectBtn=QtGui.QPushButton('Connect')
        self.connectBtn.clicked.connect(self.connectArC)
        self.connectBtn.setStatusTip('Connect to ArC One')
        self.connectBtn.setStyleSheet(s.toolBtn)

        #connectAction.setStyleSheet(s.btnStyle2)
        #connectAction.setStatusTip('Connect to ArC One')
        #connectAction.triggered.connect(self.connectArC)

        #resetAction = QtGui.QAction('Reset', self)
        #resetAction.setStatusTip('Reset ArC One')
        #resetAction.triggered.connect(self.resetArC)

        #discAction = QtGui.QAction('Disconnect', self)
        #discAction.setStatusTip('Disconnect ArC One')
        #discAction.triggered.connect(self.discArC)

        self.discBtn=QtGui.QPushButton('Disconnect')
        self.discBtn.clicked.connect(self.discArC)
        self.discBtn.setStatusTip('Disconnect from ArC One')
        self.discBtn.setStyleSheet(s.toolBtn)

        self.comPorts = QtGui.QComboBox()
        self.comPorts.setStyleSheet(s.toolCombo)
        self.comPorts.insertItems(1,self.scanSerials())
        self.comPorts.currentIndexChanged.connect(self.updateComPort)
        #self.comPorts.view().clicked.connect(self.updateCOMList)
        #self.comPorts.installEventFilter(self)
        g.COM=self.comPorts.currentText()

        self.refresh=QtGui.QPushButton('Refresh')
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

        spacer=QtGui.QWidget()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)

        self.arcStatusLabel=QtGui.QLabel()
        self.arcStatusLabel.setMinimumWidth(200)
        self.arcStatusLabel.setStyleSheet(s.arcStatus_disc)
        self.arcStatusLabel.setText('Disconnected')
        self.arcStatusLabel.setFont(fonts.font1)
        self.arcStatusLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.sessionModeLabel=QtGui.QLabel()
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
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal) # toplevel divider
        splitter.setHandleWidth(5)

        frameRight = QtGui.QWidget(self)	# define it as a widget; works also if it's defined as a frame

        layoutTop = QtGui.QHBoxLayout()
        layoutTop.addWidget(self.mo)
        layoutTop.addWidget(dd)

        self.layoutBot = QtGui.QHBoxLayout()
        self.layoutBot.addWidget(self.pp)
        self.layoutBot.addWidget(self.cp)

        layoutRight = QtGui.QVBoxLayout()
        layoutRight.addLayout(layoutTop)
        layoutRight.addLayout(self.layoutBot)

        frameRight.setLayout(layoutRight)

        splitter.addWidget(hp)
        splitter.addWidget(frameRight)
        splitter.setCollapsible(0,False)
        splitter.setCollapsible(1,False)

        # Setup size constraints for each compartment of the UI
        #splitter.setContentsMargins(0,0,0,0)
        hp.setMinimumWidth(150)
        hp.setMaximumWidth(300)
        hp.setMinimumHeight(700)

        self.mo.setFixedWidth(300)
        dd.setMinimumWidth(650)

        layoutRight.setStretchFactor(layoutTop, 5)	# define how scaling the window scales the two sections
        layoutRight.setStretchFactor(self.layoutBot, 6)

        self.layoutBot.setStretchFactor(self.pp, 6)			# define how scaling the window scales the two sections
        self.layoutBot.setStretchFactor(self.cp, 6)

        self.pp.setMinimumWidth(700)
        self.cp.setMinimumWidth(600)

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
    	self.setGeometry(100, 100, 1500, 800)
    	self.setWindowTitle('ArC One - Control Panel')  
    	self.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png')) 

        #self.redrawCrossbar()

    	self.show()

        splashScreen.finish(self)

        self.updateAction.setEnabled(False)
        self.check_for_updates()

        self.newSessionStart()

    def check_for_updates(self):
        # check local version:
        with open(os.path.join("source","version.txt"), "r") as f:
            g.local_version=f.read().split("\n")[1]

        connection=False
        # check remote version:
        version_url="http://arc-instruments.com/files/release/version.txt"
        try:
            response = requests.get(version_url, stream=True, timeout=2)
            g.remote_version=response.text.split("\n")[1]
            connection=True
        except:
            pass

        if connection: # if there is an internet connection and the remote version has been retrieved
            if g.local_version != g.remote_version:
                self.updateAction.setEnabled(True)
        

    def launch_manager(self):
        print "Launch platform manager"
        reply = QtGui.QMessageBox.question(self, "Launch ArC Platform Manager",
                "This will delete all saved data and proceed with a platform update.",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        if reply:
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
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.cfgHW.move(frameGm.topLeft())

        self.cfgHW.setWindowTitle("Modify Hardware Settings")
        self.cfgHW.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))
        self.cfgHW.show()



    def updateHW(self):
        if g.ser.port != None:  # only connect if it's disconnected
            job="011"
            g.ser.write(job+"\n")                       # Send initial parameters
            g.ser.write(str(int(g.readCycles))+"\n")         # readcycles and array size
            g.ser.write(str(int(g.sneakPathOption))+"\n")           # send total nr of wordlines





    def showAbout(self):
        from ControlPanels import aboutSection
        self.aboutSesh=aboutSection.aboutSection()
        self.aboutSesh.setFixedWidth(600)
        self.aboutSesh.setFixedHeight(300)


        frameGm = self.aboutSesh.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.aboutSesh.move(frameGm.topLeft())

        self.aboutSesh.setWindowTitle("About ArC Instruments Ltd.")
        self.aboutSesh.setWindowIcon(QtGui.QIcon(os.getcwd()+"/Graphics/"+'icon3.png'))

        self.aboutSesh.show()


    def updateCOMList(self):
        print "captured event"
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
            reply = QtGui.QMessageBox.question(self, "Start a new session",
                    "Starting a new session will erase all recorded data. Do you want to proceed?",
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
            if reply == QtGui.QMessageBox.Yes:

                #print "Yes"
                #clear mhistory
                self.newSessionStart()

                #clear data display
                #clear crossbar
            elif reply == QtGui.QMessageBox.No:
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
        self.newSesh.setFixedHeight(850)


        frameGm = self.newSesh.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
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

        reply = QtGui.QMessageBox.question(self, "Open a previous session",
                "Opening a previous session will erase all recorded data. Do you want to proceed?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.deleteAllData()
            self.findAndLoadFile()
            f.interfaceAntenna.changeSessionMode.emit('Offline')
        elif reply == QtGui.QMessageBox.No:
            pass
        else:
            pass


    def findAndLoadFile(self):

        # Import all programming panels in order to get all tags
        files = [fls for fls in os.listdir('ProgPanels') if fls.endswith(".py")]  # populate prog panel dropbox
        for fls in files:
            #prog_panelList.append(f[:-3])
            #moduleName=str(self.prog_panelList.currentText())   # format module name from drop down
            importlib.import_module(fls[:-3])     # import the module

        path = QtCore.QFileInfo(QtGui.QFileDialog().getOpenFileName(self, 'Open file', "*.csv"))

        customArray=[]
        name=path.fileName()

        file=QtCore.QFile(path.filePath())

        error=0

        with open(path.filePath(), 'rb') as csvfile:
            rdr = csv.reader(csvfile)
    
            counter=1
            for values in rdr:
                if (counter==1):
                    g.sessionName=str(values[0])
                    f.historyTreeAntenna.changeSessionName.emit()
                else:
                    if counter>3:
                        #print values
                        try:
                            w=int(values[0])
                            b=int(values[1])
                            m=float(values[2])
                            a=float(values[3])
                            pw=float(values[4])
                            tag=str(values[5])    
                            readTag=str(values[6])
                            readVoltage=float(values[7])
                            g.Mhistory[w][b].append([m,a,pw,str(tag),readTag,readVoltage])   

                            if 'S R' in tag or tag[-1]=='e' or tag[0]=='P': # ignore read all points
                                f.historyTreeAntenna.updateTree.emit(w,b) 
                            
                        except ValueError:
                            error=1

                counter=counter+1


                # check if positions read are correct
        if (error==1):
            #self.errorMessage=QtGui.QErrorMessage() 
            #self.errorMessage.showMessage("Custom array file is formatted incorrectly!")  
            errMessage = QtGui.QMessageBox()
            errMessage.setText("Selected file is incompatible!")
            errMessage.setIcon(QtGui.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()

            return False
        else:
            for w in range(1,33):
                for b in range(1,33):
                    if g.Mhistory[w][b]:
                        #for dataPoint in g.Mhistory[w][b]:                        
                        f.cbAntenna.recolor.emit(g.Mhistory[w][b][-1][0],w,b)

            print "Loaded successfully"
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
    	print "Clear Session pressed"
        reply = QtGui.QMessageBox.question(self, "Clear data",
                "Are you sure you want to clear all data?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            print "Yes"
            #clear mhistory
            self.deleteAllData()
            #clear data display
            #clear crossbar
        elif reply == QtGui.QMessageBox.No:
            print "No"
        else:
            print "Cancel"
    	pass

    def saveSession(self):
    	print "Save Session pressed"

        if g.workingDirectory:
            if g.saveFileName:
                path=g.workingDirectory
            else:
                path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', g.workingDirectory, 'CSV(*.csv)'))
                path=path_.filePath()
                g.saveFileName=path_.fileName()
                g.workingDirectory=path_.filePath()
        else:
            path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)'))
            path=path_.filePath()
            g.saveFileName=path_.fileName()
            g.workingDirectory=path_.filePath()
        

        if not path.isEmpty():
            with open(unicode(path), 'wb') as stream:
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
    	pass

    def saveAsSession(self):
    	print "Save as pressed"
        if g.workingDirectory:
            path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', g.workingDirectory, 'CSV(*.csv)'))
            path=path_.filePath()
            g.saveFileName=path_.fileName()
            g.workingDirectory=path_.filePath()
        else:
            path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv)'))
            path=path_.filePath()
            g.saveFileName=path_.fileName()
            g.workingDirectory=path_.filePath()

        if not path.isEmpty():
            with open(unicode(path), 'wb') as stream:
                writer = csv.writer(stream)
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
        pass

    #def exportSession(self):
   # 	print "New Session pressed"
    #	pass

    def exitApplication(self):
        reply = QtGui.QMessageBox.question(self, "Exit Application",
            "Are you sure you want to exit?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            #sys.exit(app.exec_())
            QtCore.QCoreApplication.instance().quit()
        else:
            pass

    def setCWD(self):
    	print "Set Working Directory"
        if g.workingDirectory:
            wdirectory = str(QtGui.QFileDialog.getExistingDirectory(self,  "Select Directory", g.workingDirectory,))
        else:
            wdirectory = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
        g.workingDirectory=wdirectory
    	pass

    def configCB(self):
    	print "New Session pressed"
    	pass

    def showDocumentation(self):

        doc = os.getcwd()+'/Documentation/'+'ArC_ONE.pdf' 

        os.system('"' + doc + '"')

    	print "Show Documentation"
    	pass

    def connectArC(self):
        #g.ser=virtualarc.virtualArC([])
        if g.COM=="VirtualArC":
            g.ser=virtualarc.virtualArC([])
        elif g.ser.port == None:  # only connect if it's disconnected
            job="0"
            try:
                #g.ser=virtualarc.virtualArC([])
                g.ser=serial.Serial(port=str(g.COM), baudrate=g.baudrate, timeout=3) # connect to the serial port
                g.ser.write(job+"\n")                       # Send initial parameters
                g.ser.write(str(g.readCycles)+"\n")         # readcycles and array size
                g.ser.write(str(g.wline_nr)+"\n")           # send total nr of wordlines
                g.ser.write(str(g.bline_nr)+"\n")           # send total nr of bitlines

                g.ser.write(str(int(g.readOption))+"\n")
                g.ser.write(str(int(g.sessionMode))+"\n")        # send session mode
                g.ser.write(str(int(g.sneakPathOption))+"\n")

                g.ser.write(str(float(g.Vread))+"\n")


                confirmation=[]
                try:
                    confirmation=int(g.ser.readline())
                    if (confirmation==1):
                        f.interfaceAntenna.disable.emit(False)

                        job='01'
                        g.ser.write(job+"\n")
                        g.ser.write(str(g.readOption)+"\n")
                        g.ser.write(str(g.Vread)+"\n")


                    else:
                        try:
                            g.ser.close()
                            g.ser.port=None
                        except SerialException:
                            pass
                        reply = QtGui.QMessageBox.question(self, "Connect to ArC One",
                            "Connection failed. Please check if ArC One is connected via the USB cable, and try another COM port. If the problem persists, restart this program with ArC One connected.",
                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                except ValueError:
                    reply = QtGui.QMessageBox.question(self, "Connect to ArC One",
                        "Connection failed. Please check if ArC One is connected via the USB cable, and try another COM port. If the problem persists, restart this program with ArC One connected.",
                        QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                    try:
                        g.ser.close()
                        g.ser.port=None
                    except serial.serialutil.SerialException:
                        pass

            except serial.serialutil.SerialException:
                reply = QtGui.QMessageBox.question(self, "Connect to ArC ONE",
                    "Connection failed due to non-existent COM port. Is Arc ONE connected?",
                    QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)


    def discArC(self):
        g.ser.close()
        g.ser.port=None
        f.interfaceAntenna.changeArcStatus.emit('Disc')

    def resetArC(self):
        job="00"
        g.ser.write(job+"\n")

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
    
    app = QtGui.QApplication(sys.argv)
    ex = Arcontrol()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()