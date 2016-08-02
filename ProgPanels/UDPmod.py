from PyQt4 import QtGui, QtCore
import sys
import os
import time
import socket       # Import socket module for Internet connections.
import select       # Import select module to allow 'listening' on ports.
import struct
import numpy as np
import csv


# Set up directory environment.
sys.path.append(os.path.abspath(os.getcwd()+'/ControlPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/Globals/'))

import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

tag="UDP" #Tag this module as... System will know how to handle it then.
g.tagDict.update({tag:"UDPconn"})

class getData(QtCore.QObject):

    #Define signals to be used throughout module.
    finished=QtCore.pyqtSignal()
    sendData=QtCore.pyqtSignal(int, int, float, float, float, str)
    highlight=QtCore.pyqtSignal(int,int)
    displayData=QtCore.pyqtSignal()
    updateTree=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    getDevices=QtCore.pyqtSignal(int)
    changeArcStatus=QtCore.pyqtSignal(str)

    def __init__(self, deviceList, sndip, sndport, rcvip, rcvport):
        super(getData,self).__init__()
        self.deviceList=deviceList
        self.sndip = sndip
        self.sndport = sndport
        self.rcvip = rcvip
        self.rcvport = rcvport

    def runUDP(self):
        ### Define connectivity motif ###
        #Operational parameters.
        maxtime = 15 #Maximum time allowed for UDP operation before returning control (s).

        #Define socket object, set-up local server to receive data coming from other computers and bind socket to local server.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create a socket object - for Internet (INET) and UDP (DGRAM).
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) #Configure socket.
        ip = ""
        port = 5005
        sock.bind((ip, port)) #Bind socket.

        #Prepare instrument for operation.
        self.disableInterface.emit(True)
        self.changeArcStatus.emit('Busy')
        global tag

        ### ESTABLISH CONNECTIONS WITH SENDER AND RECEIVER ###

        if self.rcvip: #If we have defined a receiver. -- UPDATE THESE SECTIONS TO HANDLE AN 'UPSTREAM' AND A 'DOWNSTREAM' PARTNER.
            sock.sendto("RDY", (self.rcvip, int(self.rcvport)))
            ready = select.select([sock], [], [], 5)
            tstart = time.clock() #Set starting point for operation. Helps for time-limiting UDP operation.

            #Create packer through use of 'struct' library.
            packer = struct.Struct('!I I') #'!' character tells the packer this data has to be sent to a network, so the byte order has to be correctly rendered.

            #print(g.ConnMat) ### TEST OUTPUT ###

            while (time.clock()-tstart) <= maxtime and ready[0]:
                data, addr = sock.recvfrom(1024)
                unpacked_data = packer.unpack(data)

                id_res_in = (unpacked_data[0]>>24)&0xff
                id_in = unpacked_data[0]&0xffffff
                tst_res_in = (unpacked_data[1]>>24)&0xff
                tst_in = unpacked_data[1]&0xffffff

                print "Received ", id_res_in, " ", id_in, " ", tst_res_in, " ", tst_in, " from ", addr

                #Decide which devices to bias depending on input.
                id_out = np.where(g.ConnMat[id_in, :, 0] == 1)[0]

                for elem in range(len(id_out)): #For every synapse that the incoming pre-synaptic spike affects...
                    if id_in <= len(g.ConnMat[:,0,0]-1):
                        #Determine physical device that corresponds to affected synapse.
                        w_tar = g.ConnMat[id_in, id_out[elem], 1] #Capture w-line & b-line.
                        b_tar = g.ConnMat[id_in, id_out[elem], 2]

                        #Display updates.
                        f.cbAntenna.selectDeviceSignal.emit(int(w_tar), int(b_tar))       # signal the crossbar antenna that this device has been selected
                        f.displayUpdate.updateSignal_short.emit()

                        #Interaction example with mBED.
                        g.ser.write("02\n") #Select device operation.
                        g.ser.write(str(int(w_tar))+"\n") #Send wordline address.
                        g.ser.write(str(int(b_tar))+"\n") #Send bitline address.
                        #print(str(int(w_tar)), " ", str(int(b_tar)))

                        g.ser.write("03\n") #Read operation.
                        g.ser.write("k\n") #Calibrated read operation.

                        try:
                            result='%.10f' % float(g.ser.readline().rstrip())     # currentline contains the new Mnow value followed by 2 \n characters
                        except ValueError:
                            result='%.10f' % 0.0

                        result = float(result)

                        #result = float(g.ser.readline().rstrip()) #Capture response and display it.
                        print(result)
                        #Prepare to send response via UDP.
                        id_res = 83 #Identify sender of this packet as SOTON (d83, ASCII 'S')
                        id = id_out[elem]
                        tst_res = int(np.round(np.clip((255.0/19000.0)*(result-1000.0), 0, 255))) #Clip & round - pretty self-explanatory.
                        tst = tst_in
                        print(tst_res)
                        #Preparation for packing.
                        id_int = (((id_res&0xff)<<24)|(id&(0x00fffff)))
                        tst_int =(((tst_res&0xff)<<24)|(tst&(0x00fffff)))

                        pack = (id_int, tst_int)
                        pack_data = packer.pack(*pack)

                        sock.sendto(pack_data, (self.rcvip, int(self.rcvport)))

                        ready = select.select([sock], [], [], 5)
                    else:
                        print("Index error. Trying to access input neuron that isn't regitered with connectivity matrix.")
                        ready = select.select([sock], [], [], 5)

        # for device in self.deviceList:
        #     w=device[0]
        #     b=device[1]
        #     self.highlight.emit(w,b) #Emit signal to highlight pertinent device. - Disable if running on multiple devices and slows things down.
        #
        #     g.ser.write(str(int(w))+"\n")
        #     g.ser.write(str(int(b))+"\n")
        #
        #     Mnow=float(g.ser.readline().rstrip())   # get first read value
        #     self.sendData.emit(w,b,Mnow,self.A,self.pw,tag+'_s')
        #
        #     start=time.time()
        #     stop=0
        #
        #     while stop==0:
        #         for i in range(self.B):
        #             #values=[]
        #             #values.append(float(g.ser.readline().rstrip()))
        #             #values.append(float(g.ser.readline().rstrip()))
        #             dataTime=int(g.ser.readline().rstrip())
        #             Mnow=float(g.ser.readline().rstrip())
        #
        #             self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_i_ '+ str(dataTime))
        #             #self.displayData.emit()
        #
        #         timeNow=time.time()
        #
        #         if (timeNow-start)>=self.stopTime:       # if more than stopTime ahas elapsed, do not request a new batch
        #             stop=1
        #             g.ser.write(str(int(stop))+"\n")
        #         else:
        #             stop=0
        #             g.ser.write(str(int(stop))+"\n")
        #
        #     Mnow=float(g.ser.readline().rstrip())   # get first read value
        #     self.sendData.emit(w,b,Mnow,g.Vread,0,tag+'_e')
        #
        #     self.updateTree.emit(w,b)

        self.disableInterface.emit(False)
        self.changeArcStatus.emit('Ready')
        #self.displayData.emit()
        
        self.finished.emit()


class UDPmod(QtGui.QWidget): #Define new module class inheriting from QtGui.QWidget.
    
    def __init__(self):
        super(UDPmod, self).__init__()
        
        self.initUI()
        
    def initUI(self):      

        ### Define GUI elements ###
        #Define module as a QVBox.
        vbox1=QtGui.QVBoxLayout()

        #Configure module title and description and text formats.
        titleLabel = QtGui.QLabel('UDPmod')
        titleLabel.setFont(fonts.font1)
        descriptionLabel = QtGui.QLabel('UDP connectivity for neuromorphic applications.')
        descriptionLabel.setFont(fonts.font3)
        descriptionLabel.setWordWrap(True)

        isInt=QtGui.QIntValidator()
        isFloat=QtGui.QDoubleValidator()

        topLabels=['Recipient partner IP', \
                    'Recipient partner port']

        self.topEdits=[]

        btmLabels=['Sender partner IP', \
                    'Sender partner port']

        self.btmEdits=[]

        leftInit=  ['10.9.166.168', \
                    '5005']
        rightInit= ['10.9.166.168', \
                    '5005']


        # Setup the column 'length' ratios.
        gridLayout=QtGui.QGridLayout()
        gridLayout.setColumnStretch(0,1)
        gridLayout.setColumnStretch(1,1)
        #gridLayout.setSpacing(2)

        #Setup the line separators
        lineLeft=QtGui.QFrame()
        lineLeft.setFrameShape(QtGui.QFrame.HLine);
        lineLeft.setFrameShadow(QtGui.QFrame.Raised);
        lineLeft.setLineWidth(1)
        lineRight=QtGui.QFrame()
        lineRight.setFrameShape(QtGui.QFrame.HLine);
        lineRight.setFrameShadow(QtGui.QFrame.Raised);
        lineRight.setLineWidth(1)


        ### Build GUI insides ###
        gridLayout.addWidget(lineLeft, 2, 0, 1, 2)
        gridLayout.addWidget(lineRight, 5, 0, 1, 2)


        for i in range(len(topLabels)):
            lineLabel=QtGui.QLabel()
            #lineLabel.setFixedHeight(50)
            lineLabel.setText(topLabels[i])
            gridLayout.addWidget(lineLabel, i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(leftInit[i])
            #lineEdit.setValidator(isFloat)
            self.topEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, i,1)

        offset = len(topLabels)+1 #offset parameter is simply the first row of the bottom panel/label section.

        for i in range(len(btmLabels)):
            lineLabel=QtGui.QLabel()
            lineLabel.setText(btmLabels[i])
            #lineLabel.setFixedHeight(50)
            gridLayout.addWidget(lineLabel, offset+i,0)

            lineEdit=QtGui.QLineEdit()
            lineEdit.setText(rightInit[i])
            #lineEdit.setValidator(isFloat)
            self.btmEdits.append(lineEdit)
            gridLayout.addWidget(lineEdit, offset+i,1)

        # ============================================== #

        #Label explaining connectivity matrix boot from file.
        CMLabel=QtGui.QLabel()
        #lineLabel.setFixedHeight(50)
        CMLabel.setText("Connectivity matrix file: ")

        #Text field to show selected file containing SA locations for particular application.
        self.UDPmapFName=QtGui.QLabel()
        self.UDPmapFName.setStyleSheet(s.style1)

        #File browser. Push-button connecting to function opening file browser.
        push_browse = QtGui.QPushButton('...')
        push_browse.clicked.connect(self.findUDPMAPfile)    # open custom array defive position file
        push_browse.setFixedWidth(20)

        gridLayout.addWidget(CMLabel, 6,0)
        gridLayout.addWidget(self.UDPmapFName, 6, 1)
        gridLayout.addWidget(push_browse, 6, 2)

        ### Set-up overall module GUI ###
        vbox1.addWidget(titleLabel)
        vbox1.addWidget(descriptionLabel)

        self.vW=QtGui.QWidget()
        self.vW.setLayout(gridLayout)
        self.vW.setContentsMargins(0,0,0,0)

        self.scrlArea=QtGui.QScrollArea()
        self.scrlArea.setWidget(self.vW)
        self.scrlArea.setContentsMargins(0,0,0,0)
        self.scrlArea.setWidgetResizable(False)
        self.scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.scrlArea.installEventFilter(self) #Allow object to 'listen' for events.

        vbox1.addWidget(self.scrlArea)
        vbox1.addStretch()

        #Create graphics area that holds buttons to activate module.
        self.hboxProg=QtGui.QHBoxLayout()

        push_launchUDP=QtGui.QPushButton('Launch UDP interface') #Button to launch UDP interface.
        push_range=QtGui.QPushButton('Apply to Range')
        push_all=QtGui.QPushButton('Apply to All')

        push_launchUDP.setStyleSheet(s.btnStyle)
        push_range.setStyleSheet(s.btnStyle)
        push_all.setStyleSheet(s.btnStyle)

        push_launchUDP.clicked.connect(self.UDPstart)
        push_range.clicked.connect(self.programRange)
        push_all.clicked.connect(self.programAll)

        self.hboxProg.addWidget(push_launchUDP)
        self.hboxProg.addWidget(push_range)
        self.hboxProg.addWidget(push_all)

        vbox1.addLayout(self.hboxProg)

        self.setLayout(vbox1)
        self.vW.setFixedWidth(self.size().width())
        #print '-------'
        #print self.vW.size().width()
        #print self.scrlArea.size().width()
        #print '-------'
        #self.vW.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        #self.scrlArea.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        #self.vW.setFixedWidth(self.sizeHint().width())

    def updateStopOptions(self, event):
        print event   

    def eventFilter(self, object, event):
        #print object
        if event.type()==QtCore.QEvent.Resize:
            self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width()) #Always set vW width to window width - scrollbar width.
        #if event.type()==QtCore.QEvent.Paint:
        #    self.vW.setFixedWidth(event.size().width()-object.verticalScrollBar().width())
        #print self.vW.size().width()
        return False

    def resizeWidget(self,event): #Dummy function - unnecessary vestige.
        pass

    def sendParams(self): #UPDATE WITH RELEVANT STUFF ONCE CONNECTION TO MBED READY TO BE MADE.
        g.ser.write(str(float(self.topEdits[0].text()))+"\n") #Recipient partner IP.
        g.ser.write(str(float(self.topEdits[1].text()))+"\n") #Recipient partner port.
        g.ser.write(str(float(self.btmEdits[0].text()))+"\n") #Sending partner IP.
        g.ser.write(str(float(self.btmEdits[1].text()))+"\n") #Sending partner port.

    def UDPstart(self):

        # Capture pertinent parameters.
        sndip = self.topEdits[0].text()
        sndport = self.topEdits[1].text()
        rcvip = self.btmEdits[0].text()
        rcvport = self.btmEdits[1].text()

        #job="40"
        #g.ser.write(job+"\n")   # sends the job
        
        #self.sendParams()

        self.thread=QtCore.QThread()    #Instantiate thread object.
        self.getData=getData([[g.w,g.b]], sndip, sndport, rcvip, rcvport)    #Instantiate a getData object.
        self.getData.moveToThread(self.thread)      #Cause getData object to be ran in the thread object.
        self.thread.started.connect(self.getData.runUDP)     #Start thread and assign it ('connect to') task of running runUDP.
        self.getData.finished.connect(self.thread.quit)     #Once task finishes connect it to ending the thread.
        self.getData.finished.connect(self.getData.deleteLater)     #Clear some memory, again, in response to 'finished' signal (getData).
        self.thread.finished.connect(self.getData.deleteLater)      #Clear some memory, again, in response to 'finished' signal (thread).
        self.getData.sendData.connect(f.updateHistory)      #Typical example of 'signal and slot'. FUnction from within thread calls function outside it.
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)
        self.getData.changeArcStatus.connect(f.interfaceAntenna.changeArcStatus.emit)

        self.thread.start()

    def disableProgPanel(self,state):
        if state==True:
            self.hboxProg.setEnabled(False)
        else:
            self.hboxProg.setEnabled(True)


    def programRange(self):

        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

        rangeDev=self.makeDeviceList(True)

        job="33"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev, A, pw, B, stopTime, stopBatchSize)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.runUDP)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()
        

    def programAll(self):
        stopTime=int(self.btmEdits[0].text())
        B=int(self.topEdits[2].text())
        stopBatchSize=int(self.btmEdits[1].text())

        A=float(self.topEdits[0].text())
        pw=float(self.topEdits[1].text())/1000000

        rangeDev=self.makeDeviceList(False)

        job="33"
        g.ser.write(job+"\n")   # sends the job

        self.sendParams()

        self.thread=QtCore.QThread()
        self.getData=getData(rangeDev, A, pw, B, stopTime, stopBatchSize)
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.runUDP)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.sendData.connect(f.updateHistory)
        self.getData.highlight.connect(f.cbAntenna.cast)
        self.getData.displayData.connect(f.displayUpdate.cast)
        self.getData.updateTree.connect(f.historyTreeAntenna.updateTree.emit)
        self.getData.disableInterface.connect(f.interfaceAntenna.disable.emit)

        self.thread.start()

    def makeDeviceList(self,isRange):
        #if g.checkSA=False:
        rangeDev=[] # initialise list which will contain the SA devices contained in the user selected range of devices
        #rangeMax=0;
        if isRange==False:
            minW=1
            maxW=g.wline_nr
            minB=1
            maxB=g.bline_nr
        else:
            minW=g.minW
            maxW=g.maxW
            minB=g.minB
            maxB=g.maxB            


        # Find how many SA devices are contained in the range
        if g.checkSA==False:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    rangeDev.append([w,b])
            #rangeMax=(wMax-wMin+1)*(bMax-bMin+1)
        else:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    for cell in g.customArray:
                        if (cell[0]==w and cell[1]==b):
                            rangeDev.append(cell)

        return rangeDev

    # FUNCTION FOR OPENING FILE BROWSER - UNDER CONSTRUCTION.
    def findUDPMAPfile(self):
        path = QtCore.QFileInfo(QtGui.QFileDialog().getOpenFileName(self, 'Open file', "*.txt"))
        #path=fname.getOpenFileName()

        customArray = []
        name=path.fileName()

        file=QtCore.QFile(path.filePath())
        file.open(QtCore.QIODevice.ReadOnly)

        textStream=QtCore.QTextStream(file)
        error=0
        while not textStream.atEnd():
            line = textStream.readLine()
            try:
                if (line): #Empty line check.
                    if (line[0] != '#'): #1st chacters is # -> comment; ignore.
                        preid, postid, w, b = line.split(", ")
                        customArray.append([int(preid), int(postid), int(w),int(b)])
                        if (int(w)<1 or int(w)>g.wline_nr or int(b)<1 or int(b)>g.bline_nr or preid<0 or postid<0):
                            error=1
            except ValueError:
                error=1
        file.close()

        # check if positions read are correct
        if (error==1):
            #self.errorMessage=QtGui.QErrorMessage()
            #self.errorMessage.showMessage("Custom array file is formatted incorrectly!")
            errMessage = QtGui.QMessageBox()
            errMessage.setText("Device to synapse mapping file formatted incorrectly, or selected devices outside of array range!")
            errMessage.setIcon(QtGui.QMessageBox.Critical)
            errMessage.setWindowTitle("Error")
            errMessage.exec_()
            return False
        else:
            self.UDPmapFName.setText(name)

            #Create connectivity matrix from list.
            customArray = np.array(customArray)
            g.ConnMat = np.zeros((np.max(customArray[:,0])+1, np.max(customArray[:,1])+1, 3)) #ConnMat(x,y,z): x-> connection exists (1/0), y-> w address, z-> b address.

            for element in range(len(customArray[:,0])):
                g.ConnMat[customArray[element, 0], customArray[element, 1], :] = [1, customArray[element, 2], customArray[element, 3]]

            #print(g.ConnMat)
            return True
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = UDPmod()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 