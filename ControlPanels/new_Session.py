####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
from . import cell as c

import Graphics

import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f


class new_Session(QtWidgets.QWidget):
    
    def __init__(self):
        super(new_Session, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        mainLayout=QtWidgets.QVBoxLayout()  # Set main vertical layout
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        # Setup top logo
        # ============================
        logoTop=QtWidgets.QLabel()
        logoTop.setPixmap(Graphics.getPixmap('NewSeshLogoDrawing2'))
        mainLayout.addWidget(logoTop)
        # ============================

        if sys.version_info.major == 2:
            self.pythonWarningGroupBox = QtGui.QGroupBox('Python migration')
            self.pythonWarningGroupBox.setStyleSheet(s.groupStyleNewSesh)
            self.pythonWarningGroupBox.setFont(fonts.font2)
            warningLabelText = "ArC ONE is migrating to Python 3.x. Python 2.x "+ \
                    "will not be supported past August 31, 2019." + \
                    "This <b>will not affect you</b> if you are running the built-in "+ \
                    "modules, but <b>if you have custom modules</b> you should "+ \
                    "prepare to migrate them to Python 3.6+. The ArC Instruments "+ \
                    "team can help you during the transition. If you need any "+ \
                    "help send us an e-mail at <b>py3migrate@arc-instruments.co.uk</b>."
            warningLabel = QtGui.QLabel(self)
            warningLabel.setText(warningLabelText)
            warningLabel.setFont(fonts.font3)
            warningLabel.setStyleSheet(" color: #CC0000; ")
            warningLabel.setWordWrap(True)
            warningLayout = QtGui.QGridLayout()
            warningLayout.setContentsMargins(10, 10, 10, 5)
            warningLayout.addWidget(warningLabel, 0, 0)
            self.pythonWarningGroupBox.setLayout(warningLayout)
            mainLayout.addWidget(self.pythonWarningGroupBox)

        # Setup general settings
        # ============================
        self.generalSettings = QtWidgets.QGroupBox('General Settings')
        self.generalSettings.setStyleSheet(s.groupStyleNewSesh)
        self.generalSettings.setFont(fonts.font2)
        genSetLayout=QtWidgets.QGridLayout()
        genSetLayout.setContentsMargins(10,20,10,20)

        wModeLabel=QtWidgets.QLabel(self)
        wModeLabel.setText("Session Mode:")
        wModeLabel.setFont(fonts.font3)

        wDirLabel=QtWidgets.QLabel(self)
        wDirLabel.setText("Working Directory:")
        wDirLabel.setFont(fonts.font3)

        push_browse = QtWidgets.QPushButton('...')
        push_browse.clicked.connect(self.selectWDir)    # open custom array defive position file
        push_browse.setFixedWidth(20)

        self.dirName=QtWidgets.QLineEdit()
        self.dirName.setReadOnly(True)
        self.dirName.setMaximumWidth(294)
        self.dirName.setStyleSheet(s.entryStyle2)

        dirLayout=QtWidgets.QHBoxLayout()
        dirLayout.addWidget(self.dirName)
        dirLayout.addWidget(push_browse)

        wNameLabel=QtWidgets.QLabel(self)
        wNameLabel.setText("Session Name:")
        wNameLabel.setFont(fonts.font3)

        self.wModeCombo=QtWidgets.QComboBox(self)
        self.wModeCombo.addItem("Live: Local")
        self.wModeCombo.addItem("Live: External BNC")
        self.wModeCombo.addItem("Live: BNC to Local")    
        self.wModeCombo.addItem("Offline")
        self.wModeCombo.setFont(fonts.font3)

        self.wNameEntry=QtWidgets.QLineEdit()
        self.wNameEntry.setMaximumWidth(320)
        self.wNameEntry.setText('Package1')
        self.wNameEntry.setFont(fonts.font3)

        genSetLayout.addWidget(wModeLabel,0,0)
        genSetLayout.addWidget(wDirLabel,1,0)
        genSetLayout.addWidget(wNameLabel,2,0)
        genSetLayout.addWidget(self.wModeCombo,0,1)
        genSetLayout.addLayout(dirLayout,1,1)
        genSetLayout.addWidget(self.wNameEntry,2,1)

        self.generalSettings.setLayout(genSetLayout)
        mainLayout.addWidget(self.generalSettings)
        #mainLayout.addWidget(self.generalSettings)

        # ============================

        # Setup mCAT settings
        # ============================

        #hwTitle=QtWidgets.QLabel(self)
        #hwTitle.setText('Hardware Settings')
        #hwTitle.setFont(fonts.font3)
        self.hwSettings = QtWidgets.QGroupBox('Hardware Settings')
        self.hwSettings.setStyleSheet(s.groupStyleNewSesh)
        #palette=QtGui.QPalette()
        self.hwSettings.setFont(fonts.font2)


        hwSetLayout=QtWidgets.QGridLayout()
        hwSetLayout.setContentsMargins(10,20,10,10)

        readCyclesLabel=QtWidgets.QLabel(self)
        readCyclesLabel.setText("Reading Cycles:")
        readCyclesLabel.setFont(fonts.font3)

        sneakLabel=QtWidgets.QLabel(self)
        sneakLabel.setText("Sneak Path Limiting:")
        sneakLabel.setFont(fonts.font3)

        arShapeLabel=QtWidgets.QLabel(self)
        arShapeLabel.setText("Array Shape:")
        arShapeLabel.setFont(fonts.font3)

        self.readCyclesEntry=QtWidgets.QLineEdit()
        self.readCyclesEntry.setFixedWidth(320)
        self.readCyclesEntry.setText("50")
        self.readCyclesEntry.setFont(fonts.font3)

        self.sneakCombo=QtWidgets.QComboBox(self)
        self.sneakCombo.setMaximumWidth(320)
        self.sneakCombo.addItem("Write: V/3")
        self.sneakCombo.addItem("Write: V/2")
        self.sneakCombo.setFont(fonts.font3)
        self.sneakCombo.setCurrentIndex(g.sneakPathOption)

        cbHBox=QtWidgets.QHBoxLayout(self)
        self.cb_w=QtWidgets.QSpinBox(self)
        self.cb_w.setMinimum(1)
        self.cb_w.setMaximum(32)
        self.cb_w.setSingleStep(1)
        self.cb_w.setValue(32)
        self.cb_w.setFont(fonts.font3)
        self.cb_w.valueChanged.connect(self.redrawCB)

        self.cb_b=QtWidgets.QSpinBox(self)
        self.cb_b.setMinimum(1)
        self.cb_b.setMaximum(32)
        self.cb_b.setSingleStep(1)
        self.cb_b.setValue(32)
        self.cb_b.valueChanged.connect(self.redrawCB)
        self.cb_b.setFont(fonts.font3)

        cb_w_label=QtWidgets.QLabel(self)
        cb_w_label.setText("W:")
        cb_w_label.setFont(fonts.font3)

        cb_b_label=QtWidgets.QLabel(self)
        cb_b_label.setText("B:")
        cb_b_label.setFont(fonts.font3)

        cbHBox.setContentsMargins(0,0,0,0)
        cbHBox.addStretch()
        cbHBox.addWidget(cb_w_label)
        cbHBox.addWidget(self.cb_w)
        cbHBox.addStretch()
        cbHBox.addWidget(cb_b_label)
        cbHBox.addWidget(self.cb_b)
        cbHBox.addStretch()

        aux=QtWidgets.QWidget()
        aux.setLayout(cbHBox)

        hwSetLayout.addWidget(readCyclesLabel,0,0)
        hwSetLayout.addWidget(sneakLabel,1,0)
        hwSetLayout.addWidget(arShapeLabel,2,0)
        hwSetLayout.addWidget(self.readCyclesEntry,0,2)
        hwSetLayout.addWidget(self.sneakCombo,1,2)
        hwSetLayout.addWidget(aux,2,2)
        hwSetLayout.setColumnStretch(1,2)

        self.hwSettings.setLayout(hwSetLayout)
        mainLayout.addWidget(self.hwSettings)

        line2=QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setFrameShadow(QtWidgets.QFrame.Plain)
        line2.setStyleSheet(s.lineStyle)
        line2.setLineWidth(1)

        mainLayout.addWidget(line2)

        cbWidget=QtWidgets.QWidget()
        self.cbWindow=QtWidgets.QStackedLayout()
        cbWidget.setLayout(self.cbWindow)

        mainLayout.addWidget(cbWidget)

        # Apply/Cancel buttons Layout
        startLay_group=QtWidgets.QGroupBox()
        startLay_group.setStyleSheet(s.groupStyle)
        startLay=QtWidgets.QHBoxLayout()

        start_btn=QtWidgets.QPushButton('Start')
        start_btn.setStyleSheet(s.btnStyle2)
        start_btn.setMinimumWidth(100)
        start_btn.clicked.connect(self.startSession)

        cancel_btn=QtWidgets.QPushButton('Cancel')
        cancel_btn.setStyleSheet(s.btnStyle2)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.cancelNewSession)

        startLay.addStretch()
        startLay.addWidget(cancel_btn)
        startLay.addWidget(start_btn)
        startLay.setContentsMargins(5,5,5,5)
        startLay.setSpacing(2)

        #startLay_group.setLayout(startLay)

        line=QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Plain)
        line.setStyleSheet(s.lineStyle)
        line.setLineWidth(1)

        #QFrame *line = new QFrame(this);
        #line->setFrameShape(QFrame::HLine); // Horizontal line
        #line->setFrameShadow(QFrame::Sunken);
        #line->setLineWidth(1);

        mainLayout.addWidget(line)

        mainLayout.addLayout(startLay)

        #spacer=QtWidgets.QSpacerItem(1,1)
        #mainLayout.addWidget(spacer)
        #mainLayout.addSpacing(1)

        self.setContentsMargins(0,0,0,0)    # spacing of the full Layout to accomodate line numbers and colorbar on the right  
        self.setLayout(mainLayout)
        #self.setGeometry()
        self.redrawCB()

    def selectWDir(self):
        folderDialog=QtWidgets.QFileDialog()
        #folderDialog.setFileMode(QtWidgets.QFileDialog.Directory)

        directory = folderDialog.getExistingDirectory(self, 'Choose Directory', os.path.curdir)

        self.dirName.setText(directory)

        pass

    def redrawCB(self):
        #layout=QtWidgets.QGridLayout()
        #self.
        #self.cbWidget.setLayout(layout)

        wordline=QtWidgets.QLabel()
        wordline.setText("W\no\nr\nd\nl\ni\nn\ne")
        bitline=QtWidgets.QLabel()
        bitline.setText("Bitline")

        bitH=QtWidgets.QHBoxLayout()
        bitH.addStretch()
        bitH.addWidget(bitline)
        bitH.addStretch()

        w1=QtWidgets.QWidget()
        lay1=QtWidgets.QVBoxLayout()
        lay2=QtWidgets.QVBoxLayout()

        lay2=QtWidgets.QHBoxLayout()
        layout=QtWidgets.QGridLayout()
        layout.setSpacing(0)
        w1.setLayout(lay1)

        layout2=QtWidgets.QVBoxLayout()
        layout2.addStretch()
        layout2.addLayout(layout)
        #layout2.addLayout(bitH)
        layout2.addStretch()

        lay1.addStretch()
        lay1.setAlignment(QtCore.Qt.AlignCenter)
        lay1.addLayout(lay2)
        lay1.addLayout(bitH)
        lay1.addStretch()

        lay2.addStretch()
        lay2.addWidget(wordline)
        lay2.addLayout(layout2)
        lay2.addStretch()

        wmax=self.cb_w.value()
        bmax=self.cb_b.value()

        for w in range(1,wmax+1):
            for b in range(1,bmax+1):
                aCell=c.cell()
                aCell.setMinimumWidth(15)
                aCell.setMaximumHeight(20*g.scaling_factor)
                layout.addWidget(aCell,w,b)
        aCell=[]

        for w in range(1,wmax+1):
            aux=QtWidgets.QLabel()
            aux.setText(str(w))
            aux.setFont(fonts.font4)
            layout.addWidget(aux,w,0)

        for b in range(1,bmax+1):
            aux=QtWidgets.QLabel()
            aux.setText(str(b))
            aux.setFont(fonts.font4)
            layout.addWidget(aux,33,b)


        self.cbWindow.addWidget(w1)
        self.cbWindow.setCurrentIndex(self.cbWindow.count()-1)


    def startSession(self):
        g.wline_nr=self.cb_w.value()
        g.bline_nr=self.cb_b.value()

        if not len(self.dirName.text()) == 0:
            g.workingDirectory=self.dirName.text()

        g.readCycles=int(self.readCyclesEntry.text())
        g.sneakPathOption=self.sneakCombo.currentIndex()
        g.sessionMode=self.wModeCombo.currentIndex()
        g.sessionName=self.wNameEntry.text()

        f.interfaceAntenna.reformat.emit()

        self.close()

        pass

    def cancelNewSession(self):
        self.close()
        pass

