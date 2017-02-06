####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtGui, QtCore
import sys
import os
import cell as c

import Globals.GlobalVars as g
import Globals.GlobalFonts as fonts
import Globals.GlobalStyles as s
import Globals.GlobalFunctions as f


class new_Session(QtGui.QWidget):
    
    def __init__(self):
        super(new_Session, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        mainLayout=QtGui.QVBoxLayout()  # Set main vertical layout
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        # Setup top logo
        # ============================
        logoTop=QtGui.QLabel()
        logoTop.setPixmap(QtGui.QPixmap(os.getcwd()+"/Graphics/"+'NewSeshLogoDrawing2.png'))
        mainLayout.addWidget(logoTop)
        # ============================

        # Setup general settings
        # ============================
        self.generalSettings = QtGui.QGroupBox('General Settings')
        self.generalSettings.setStyleSheet(s.groupStyleNewSesh)
        self.generalSettings.setFont(fonts.font2)
        genSetLayout=QtGui.QGridLayout()
        genSetLayout.setContentsMargins(10,20,10,20)

        wModeLabel=QtGui.QLabel(self)
        wModeLabel.setText("Session Mode:")
        wModeLabel.setFont(fonts.font3)

        wDirLabel=QtGui.QLabel(self)
        wDirLabel.setText("Working Directory:")
        wDirLabel.setFont(fonts.font3)

        push_browse = QtGui.QPushButton('...')
        push_browse.clicked.connect(self.selectWDir)    # open custom array defive position file
        push_browse.setFixedWidth(20)

        self.dirName=QtGui.QLineEdit()
        self.dirName.setReadOnly(True)
        self.dirName.setMaximumWidth(294)
        self.dirName.setStyleSheet(s.entryStyle2)

        dirLayout=QtGui.QHBoxLayout()
        dirLayout.addWidget(self.dirName)
        dirLayout.addWidget(push_browse)

        wNameLabel=QtGui.QLabel(self)
        wNameLabel.setText("Session Name:")
        wNameLabel.setFont(fonts.font3)

        self.wModeCombo=QtGui.QComboBox(self)
        self.wModeCombo.addItem("Live: Local")
        self.wModeCombo.addItem("Live: External BNC")
        self.wModeCombo.addItem("Live: BNC to Local")    
        self.wModeCombo.addItem("Offline")
        self.wModeCombo.setFont(fonts.font3)

        # Browse label and browse button
        #wDirBrowse=QtGui.

        self.wNameEntry=QtGui.QLineEdit()
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

        #hwTitle=QtGui.QLabel(self)
        #hwTitle.setText('Hardware Settings')
        #hwTitle.setFont(fonts.font3)
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

        arShapeLabel=QtGui.QLabel(self)
        arShapeLabel.setText("Array Shape:")
        arShapeLabel.setFont(fonts.font3)

        self.readCyclesEntry=QtGui.QLineEdit()
        self.readCyclesEntry.setFixedWidth(320)
        self.readCyclesEntry.setText("50")
        self.readCyclesEntry.setFont(fonts.font3)

        self.sneakCombo=QtGui.QComboBox(self)
        self.sneakCombo.setMaximumWidth(320)
        self.sneakCombo.addItem("Write: V/3")
        self.sneakCombo.addItem("Write: V/2")
        self.sneakCombo.setFont(fonts.font3)
        self.sneakCombo.setCurrentIndex(g.sneakPathOption)

        cbHBox=QtGui.QHBoxLayout(self)
        self.cb_w=QtGui.QSpinBox(self)
        self.cb_w.setMinimum(1)
        self.cb_w.setMaximum(32)
        self.cb_w.setSingleStep(1)
        self.cb_w.setValue(32)
        self.cb_w.setFont(fonts.font3)
        self.cb_w.valueChanged.connect(self.redrawCB)

        self.cb_b=QtGui.QSpinBox(self)
        self.cb_b.setMinimum(1)
        self.cb_b.setMaximum(32)
        self.cb_b.setSingleStep(1)
        self.cb_b.setValue(32)
        self.cb_b.valueChanged.connect(self.redrawCB)
        self.cb_b.setFont(fonts.font3)

        cb_w_label=QtGui.QLabel(self)
        cb_w_label.setText("W:")
        cb_w_label.setFont(fonts.font3)

        cb_b_label=QtGui.QLabel(self)
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

        aux=QtGui.QWidget()
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

        line2=QtGui.QFrame()
        line2.setFrameShape(QtGui.QFrame.HLine)
        line2.setFrameShadow(QtGui.QFrame.Plain)
        line2.setStyleSheet(s.lineStyle)
        line2.setLineWidth(1)

        mainLayout.addWidget(line2)

        cbWidget=QtGui.QWidget()
        self.cbWindow=QtGui.QStackedLayout()
        cbWidget.setLayout(self.cbWindow)

        mainLayout.addWidget(cbWidget)

        # Apply/Cancel buttons Layout
        startLay_group=QtGui.QGroupBox()
        startLay_group.setStyleSheet(s.groupStyle)
        startLay=QtGui.QHBoxLayout()

        start_btn=QtGui.QPushButton('Start')
        start_btn.setStyleSheet(s.btnStyle2)
        start_btn.setMinimumWidth(100)
        start_btn.clicked.connect(self.startSession)

        cancel_btn=QtGui.QPushButton('Cancel')
        cancel_btn.setStyleSheet(s.btnStyle2)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.cancelNewSession)

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
        #self.setGeometry()
        self.redrawCB()

    def selectWDir(self):
        folderDialog=QtGui.QFileDialog()
        #folderDialog.setFileMode(QtGui.QFileDialog.Directory)

        directory = folderDialog.getExistingDirectory(self, 'Choose Directory', os.path.curdir)

        self.dirName.setText(directory)
        print directory

        pass

    def redrawCB(self):
        #layout=QtGui.QGridLayout()
        #self.
        #self.cbWidget.setLayout(layout)

        wordline=QtGui.QLabel()
        wordline.setText("W\no\nr\nd\nl\ni\nn\ne")
        bitline=QtGui.QLabel()
        bitline.setText("Bitline")

        bitH=QtGui.QHBoxLayout()
        bitH.addStretch()
        bitH.addWidget(bitline)
        bitH.addStretch()

        w1=QtGui.QWidget()
        lay1=QtGui.QVBoxLayout()
        lay2=QtGui.QVBoxLayout()

        lay2=QtGui.QHBoxLayout()
        layout=QtGui.QGridLayout()
        layout.setSpacing(0)
        w1.setLayout(lay1)

        layout2=QtGui.QVBoxLayout()
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
            aux=QtGui.QLabel()
            aux.setText(str(w))
            aux.setFont(fonts.font4)
            layout.addWidget(aux,w,0)

        for b in range(1,bmax+1):
            aux=QtGui.QLabel()
            aux.setText(str(b))
            aux.setFont(fonts.font4)
            layout.addWidget(aux,33,b)


        self.cbWindow.addWidget(w1)
        self.cbWindow.setCurrentIndex(self.cbWindow.count()-1)


    def startSession(self):
        g.wline_nr=self.cb_w.value()
        g.bline_nr=self.cb_b.value()

        if not self.dirName.text().isEmpty():
            g.workingDirectory=self.dirName.text()

        g.readCycles=int(self.readCyclesEntry.text())
        g.sneakPathOption=self.sneakCombo.currentIndex()
        #print "Sneak option: ", g.sneakPathOption
        g.sessionMode=self.wModeCombo.currentIndex()
        g.sessionName=self.wNameEntry.text()

        # Browse label and browse button
        #wDirBrowse=QtGui.

        #print g.wline_nr
        #print g.bline_nr
        #print g.workingDirectory
        #print g.readCycles
        #print g.sneakPathOption
        #print g.sessionMode
        #print g.sessionName

        f.interfaceAntenna.reformat.emit()

        self.close()

        pass

    def cancelNewSession(self):
        self.close()
        pass
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = new_Session()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 