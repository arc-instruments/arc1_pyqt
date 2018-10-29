####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui
import cell as c


import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f


class configHardware(QtGui.QWidget):
    
    def __init__(self):
        super(configHardware, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        mainLayout=QtGui.QVBoxLayout()  # Set main vertical layout
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)
        # ============================

        # Setup mCAT settings
        # ============================

        self.hwSettings = QtGui.QGroupBox('Hardware Settings')
        self.hwSettings.setStyleSheet(s.groupStyleNewSesh)
        #palette=QtGui.QPalette()
        self.hwSettings.setFont(fonts.font2)


        hwSetLayout=QtGui.QGridLayout()
        hwSetLayout.setContentsMargins(10,20,10,10)

        readCyclesLabel=QtGui.QLabel(self)
        readCyclesLabel.setText("Reading Cycles:")
        readCyclesLabel.setFont(fonts.font3)

        sneakLabel=QtGui.QLabel(self)
        sneakLabel.setText("Sneak Path Limiting:")
        sneakLabel.setFont(fonts.font3)

        self.readCyclesEntry=QtGui.QLineEdit()
        self.readCyclesEntry.setFixedWidth(320)
        self.readCyclesEntry.setText(str(g.readCycles))
        self.readCyclesEntry.setFont(fonts.font3)

        self.sneakCombo=QtGui.QComboBox(self)
        self.sneakCombo.setMaximumWidth(320)
        self.sneakCombo.addItem("Write: V/3")
        self.sneakCombo.addItem("Write: V/2")
        self.sneakCombo.setFont(fonts.font3)
        self.sneakCombo.setCurrentIndex(g.sneakPathOption)

        hwSetLayout.addWidget(readCyclesLabel,0,0)
        hwSetLayout.addWidget(sneakLabel,1,0)
        hwSetLayout.addWidget(self.readCyclesEntry,0,1)
        hwSetLayout.addWidget(self.sneakCombo,1,1)

        self.hwSettings.setLayout(hwSetLayout)
        mainLayout.addWidget(self.hwSettings)


        # Apply/Cancel buttons Layout
        startLay_group=QtGui.QGroupBox()
        startLay_group.setStyleSheet(s.groupStyle)
        startLay=QtGui.QHBoxLayout()

        start_btn=QtGui.QPushButton('Apply')
        start_btn.setStyleSheet(s.btnStyle2)
        start_btn.setMinimumWidth(100)
        start_btn.clicked.connect(self.updateHW)

        cancel_btn=QtGui.QPushButton('Cancel')
        cancel_btn.setStyleSheet(s.btnStyle2)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.cancelUpdateHW)

        startLay.addStretch()
        startLay.addWidget(cancel_btn)
        startLay.addWidget(start_btn)
        startLay.setContentsMargins(5,5,5,5)
        startLay.setSpacing(2)

        #startLay_group.setLayout(startLay)

        line=QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Plain)
        line.setStyleSheet(s.lineStyle)
        line.setLineWidth(1)

        #QFrame *line = new QFrame(this);
        #line->setFrameShape(QFrame::HLine); // Horizontal line
        #line->setFrameShadow(QFrame::Sunken);
        #line->setLineWidth(1);

        mainLayout.addWidget(line)

        mainLayout.addLayout(startLay)

        #spacer=QtGui.QSpacerItem(1,1)
        #mainLayout.addWidget(spacer)
        #mainLayout.addSpacing(1)

        self.setContentsMargins(0,0,0,0)    # spacing of the full Layout to accomodate line numbers and colorbar on the right  
        self.setLayout(mainLayout)


    def updateHW(self):

        g.readCycles=int(self.readCyclesEntry.text())
        g.sneakPathOption=self.sneakCombo.currentIndex()

        # Browse label and browse button
        #wDirBrowse=QtGui.
        print g.readCycles
        print g.sneakPathOption

        f.interfaceAntenna.updateHW.emit()

        self.close()

        pass

    def cancelUpdateHW(self):
        self.close()
        pass

