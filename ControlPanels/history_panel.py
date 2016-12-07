####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore

import pyqtgraph as pg
import numpy as np

import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g


class history_panel(QtGui.QWidget):
    
    def __init__(self):
        super(history_panel, self).__init__()
        self.initUI()
        
    def initUI(self):   

        self.dieName = QtGui.QLineEdit('Package1')
        self.dieName.setFont(fonts.font1)
        self.dieName.textChanged.connect(self.changeSessionNameManualy)

        self.historyTree = QtGui.QTreeWidget()
        self.historyTree.setHeaderLabel('Device History')
        self.historyTree.itemClicked.connect(self.changeDisplayToSelectedItem)
        self.historyTree.itemDoubleClicked.connect(self.displayResults)

        f.historyTreeAntenna.updateTree.connect(self.updateTree)
        f.historyTreeAntenna.updateTree_short.connect(self.updateTree_short)
        f.historyTreeAntenna.clearTree.connect(self.clearTree)
        f.historyTreeAntenna.changeSessionName.connect(self.changeSessionName)

        mainLayout=QtGui.QVBoxLayout()
        mainLayout.addWidget(self.dieName)
        mainLayout.addWidget(self.historyTree)

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        self.topLevelItems=[]
        self.resultWindow=[]

        self.setLayout(mainLayout)

    def changeSessionNameManualy(self, txt):
        g.sessionName=txt
        print txt

    def changeSessionName(self):
        self.dieName.setText(g.sessionName)

    def clearTree(self):
        self.historyTree.clear()

    def updateTree_short(self):
        self.updateTree(g.w,g.b)

    def updateTree(self,w,b):
        existingItem=self.historyTree.findItems("W=" + str(w) + " | B=" + str(b), QtCore.Qt.MatchExactly,0)

        if existingItem==[]:        # if no entry for that adress exists, make a new one
            newTag=self.formatItemText(w,b) # format the text of the new history entry item taken form the dictionary of the prog panels
            if newTag:
                newTree=QtGui.QTreeWidgetItem(self.historyTree)
                newTree.setText(0,"W=" + str(w) + " | B=" + str(b))
                self.deunderline()                                  # deunderline every tree top level item
                newTree.setFont(0,fonts.history_top_underline)      # underline the current one
                newTree.setWhatsThis(0,str(w)+','+str(b))   # set a tag for the item
                newTree.setWhatsThis(1,str(-1))
                newTree.setWhatsThis(2,str(0))
                newTree.setWhatsThis(3,str(0))
                newTree.setWhatsThis(4,str(0))
                #newTree.itemClicked.connect(self.changeDisplayToSelectedItem)
                newItem=QtGui.QTreeWidgetItem(newTree)
                newItem.setWhatsThis(0,str(w)+','+str(b))

                
                newItem.setWhatsThis(1,newTag[0])
                newItem.setWhatsThis(2,newTag[1])
                newItem.setWhatsThis(3,newTag[2])
                newItem.setWhatsThis(4,newTag[3])
                newItem.setWhatsThis(5,newTag[4])
                if newTag[0]=='Read':              # special cases of pulse and read are handlesd separately
                    newTag[0]='Read x 1'
                if newTag[0]=='Pulse':
                    newTag[0]='Pulse x 1'

                newItem.setText(0,newTag[0])
                newItem.setFont(0,fonts.history_child)
        else:                                       # if the CB crosspoint has been pulsed before, add in the reepctive tree stack
            self.deunderline()
            existingItem[0].setFont(0,fonts.history_top_underline)
            newTag=self.formatItemText(w,b)
            #print newTag
            if newTag:

                if existingItem[0].child(0):            # if a child exists in the stack (which is always true, this function might be unecessary)
                    if newTag[0] in existingItem[0].child(0).text(0):  # if previously the same operation has been performed
                        if newTag[0]=='Read' or newTag[0]=='Pulse':       # for Read and Pulse special cases, add the trailing integer by +1
                            string=str(existingItem[0].child(0).text(0))
                            #print string
                            nr=[int(s) for s in string.split(' ') if s.isdigit()][-1]
                            #print nr
                            nr=nr+1
                            newTag[0]=newTag[0]+' x '+str(nr)
                            existingItem[0].child(0).setText(0,newTag[0])
                        else:                                   # if it's not pulse or read, add a new item
                            newItem=QtGui.QTreeWidgetItem()
                            newItem.setWhatsThis(0,str(w)+','+str(b))
                            newItem.setWhatsThis(1,newTag[0])
                            newItem.setWhatsThis(2,newTag[1])
                            newItem.setWhatsThis(3,newTag[2])
                            newItem.setWhatsThis(4,newTag[3])
                            newItem.setWhatsThis(5,newTag[4])

                            existingItem[0].insertChild(0,newItem)
                            newItem.setText(0,newTag[0])
                            newItem.setFont(0,fonts.history_child)

                    else:
                        newItem=QtGui.QTreeWidgetItem()
                        newItem.setWhatsThis(0,str(w)+','+str(b))
                        newItem.setWhatsThis(1,newTag[0])
                        newItem.setWhatsThis(2,newTag[1])
                        newItem.setWhatsThis(3,newTag[2])
                        newItem.setWhatsThis(4,newTag[3])
                        newItem.setWhatsThis(5,newTag[4])
                        existingItem[0].insertChild(0,newItem)
                        if newTag[0]=='Read':
                            newTag[0]='Read x 1'
                        if newTag[0]=='Pulse':
                            newTag[0]='Pulse x 1'
                        newItem.setText(0,newTag[0])
                        newItem.setFont(0,fonts.history_child)

        self.update()

    def displayResults(self,item):
        if item.whatsThis(2)=='1':  # if there are results to be displayed
            pos=item.whatsThis(0).split(',')
            w=int(pos[0])
            b=int(pos[1])

            tag=item.whatsThis(1)
            startPoint=int(item.whatsThis(3))
            endPoint=int(item.whatsThis(4))
            tagKey=item.whatsThis(5)

            print "#########"
            print startPoint
            print endPoint

            raw=g.Mhistory[w][b][startPoint:endPoint+1]
            #print raw
           # print tagKey
            

            # Display results in a new window based on the tag
            # the tag selects the type of results processing and display.

            # ===============================
            # Curve Tracer
            if tagKey=='CT':

                lastRun=raw

                resistance=[]
                voltage=[]
                current=[]
                abs_current=[]

                #print raw
                #print currentRunTag

                # Find nr of cycles
                lineNr=1
                totalCycles=0
                resistance.append([])
                voltage.append([])
                current.append([])
                abs_current.append([])

                resistance[totalCycles].append(lastRun[0][0])
                voltage[totalCycles].append(lastRun[0][1])
                current[totalCycles].append(lastRun[0][1]/lastRun[lineNr][0])
                abs_current[totalCycles].append(abs(current[totalCycles][-1]))


                #print resistance
                #for line in range(1,len(lastRun)):  # take all data lines without the first and last one (which are _s and _e)
                while lineNr<len(lastRun)-1:
                    currentRunTag=lastRun[lineNr][3];

                    while (currentRunTag == lastRun[lineNr][3]):
                        resistance[totalCycles].append(lastRun[lineNr][0])
                        voltage[totalCycles].append(lastRun[lineNr][1])
                        current[totalCycles].append(lastRun[lineNr][1]/lastRun[lineNr][0])
                        abs_current[totalCycles].append(abs(current[totalCycles][-1]))

                        lineNr+=1;
                        if lineNr==len(lastRun):
                            break
                    totalCycles+=1;
                    resistance.append([])
                    voltage.append([])
                    current.append([])
                    abs_current.append([])

                #print lastRun[-1][0]
                #print totalCycles


                resistance[totalCycles-1].append(lastRun[-1][0])
                voltage[totalCycles-1].append(lastRun[-1][1])
                current[totalCycles-1].append(lastRun[-1][1]/lastRun[-1][0])
                abs_current[totalCycles-1].append(abs(current[totalCycles-1][-1]))

                #print voltage

                # setup display
                self.resultWindow.append(QtGui.QWidget())
                self.resultWindow[-1].setGeometry(100,100,1000,400)
                self.resultWindow[-1].setWindowTitle("Curve Tracer: W="+ str(w) + " | B=" + str(b))
                self.resultWindow[-1].setWindowIcon(QtGui.QIcon(os.getcwd()+'/Graphics/'+'icon3.png')) 
                self.resultWindow[-1].show()

                pen1=QtGui.QPen()
                pen1.setColor(QtCore.Qt.red)

                view=pg.GraphicsLayoutWidget()

                label_style = {'color': '#000000', 'font-size': '10pt'}


                self.plot_abs=view.addPlot()
                #self.plot_abs.addLegend()
                #self.curveAbs=self.plot_abs.plot(pen=pen1, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
                self.plot_abs.getAxis('left').setLabel('Current', units='A', **label_style)
                self.plot_abs.getAxis('bottom').setLabel('Voltage', units='V', **label_style)
                self.plot_abs.setLogMode(False, True)
                self.plot_abs.getAxis('left').setGrid(50)
                self.plot_abs.getAxis('bottom').setGrid(50)

                view.nextColumn()  # go to next row and add the next plot

                self.plot_IV=view.addPlot()
                self.plot_IV.addLegend()
                #self.curveIV=self.plot_IV.plot(pen=pen1, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
                self.plot_IV.getAxis('left').setLabel('Current', units='A', **label_style) 
                self.plot_IV.getAxis('bottom').setLabel('Voltage', units='V', **label_style) 
                self.plot_IV.getAxis('left').setGrid(50) 
                self.plot_IV.getAxis('bottom').setGrid(50) 

                view.nextColumn()  # go to next row and add the next plot

                self.plot_R=view.addPlot()
                #self.plot_R.addLegend()
                #self.curveR=self.plot_R.plot(pen=pen1, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
                self.plot_R.getAxis('left').setLabel('Resistance', units='Ohms', **label_style)
                self.plot_R.getAxis('bottom').setLabel('Voltage', units='V', **label_style)
                self.plot_R.setLogMode(False, True)
                #self.plot_R.setYRange(np.log10(min(resistance))/10, np.log10(max(resistance))*10)
                self.plot_R.getAxis('left').setGrid(50)
                self.plot_R.getAxis('bottom').setGrid(50)

                resLayout = QtGui.QVBoxLayout()
                resLayout.addWidget(view)
                resLayout.setContentsMargins(0,0,0,0)

                self.resultWindow[-1].setLayout(resLayout)

                # setup range for resistance plot
                maxRes_arr=[]
                minRes_arr=[]

                for cycle in range(1,totalCycles+1):
                    maxRes_arr.append(max(resistance[cycle-1]))
                    minRes_arr.append(min(resistance[cycle-1]))

                maxRes=max(maxRes_arr)
                minRes=max(minRes_arr)

                #self.plot_R.setYRange(np.log10(min([minRes, 1000000000])/10), np.log10(min([maxRes, 1000000000])*10)) #Deal with infinities appropriately.

                for cycle in range(1,totalCycles+1):
                    aux1=self.plot_abs.plot(pen=(cycle,totalCycles), symbolPen=None, symbolBrush=(cycle,totalCycles), symbol='s', symbolSize=5, pxMode=True, name='Cycle '+str(cycle))
                    aux1.setData(np.asarray(voltage[cycle-1]),np.asarray(abs_current[cycle-1]))
                    #aux1.setYRange(max(abs_current[cycle-1]), self.max_without_inf(abs_current[cycle-1]))

                    aux2=self.plot_IV.plot(pen=(cycle,totalCycles), symbolPen=None, symbolBrush=(cycle,totalCycles), symbol='s', symbolSize=5, pxMode=True, name='Cycle '+str(cycle))
                    aux2.setData(np.asarray(voltage[cycle-1]),np.asarray(current[cycle-1]))

                    aux3=self.plot_R.plot(pen=(cycle,totalCycles), symbolPen=None, symbolBrush=(cycle,totalCycles), symbol='s', symbolSize=5, pxMode=True, name='Cycle '+str(cycle))
                    aux3.setData(np.asarray(voltage[cycle-1]),np.asarray(resistance[cycle-1]))
                    #aux3.setYRange(max(resistance[cycle-1]), self.max_without_inf(resistance[cycle-1]))
                
                self.plot_R.setYRange(np.log10(self.min_without_inf(resistance, g.inf)),np.log10(self.max_without_inf(resistance, g.inf)))
                self.plot_abs.setYRange(np.log10(self.min_without_inf(abs_current, 0.0)),np.log10(self.max_without_inf(abs_current, 0.0)))


                #self.curveAbs.setData(np.asarray(V),np.asarray(C_abs))
                #self.curveIV.setData(np.asarray(V),np.asarray(C))
                #self.curveR.setData(np.asarray(V),np.asarray(R))
                self.resultWindow[-1].update()

            # ===============================
            # SwitchSeeker
            if tagKey=='SS2':

                lastRun=raw

                # Initialisations
                pulseNr=0
                deltaR=[]
                initR=[]
                ampl=[]
                Rs=[]

                # Holds under and overshoot voltages
                over=[]
                under=[]
                offshoots=[] # holds both in order

                max_dR=0 # holds maximum normalised resistance offset during a train of reads

                # Find the pulse amplitudes and the resistance (averaged over the read sequence) after each pulse train
                index=0
                print "entered here"
                #print "last run and len", lastRun, len(lastRun)
                for i, r in enumerate(lastRun):
                    print i, r
                #return 0
                while index < len(lastRun):

                    if index<len(lastRun) and lastRun[index][2] == 0: # if this is the first read pulse of a read sequence:
                        start_index=index # record the start index
                        readAvgRun=0 # initialise average resistance during a read run accumulator
                        idx=0 # counts nr of reads 
                        # If the line contains 0 amplitude and 0 width, then we're entering a read run
                        while index<len(lastRun) and lastRun[index][2] == 0:
                            idx+=1 # increment the counter
                            readAvgRun+=lastRun[index][0] # add to accumulator
                            index+=1 # increment the global index as we're advancing through the pulse run
                            if index>len(lastRun)-1:    # if the index exceeded the lenght of the run, exit
                                break
                        readAvgRun=readAvgRun/idx # When we exit the while loop we are at the end of the reading run

                        print "index=",index

                        Rs.append(readAvgRun) # append with this resistance

                        for i in range(idx):    # find the maximum deviation from the average read during a read sequence (helps future plotting of the confidence bar)
                        # maybe not the best way to do this but still
                            if abs(lastRun[start_index+i][0]-readAvgRun)/readAvgRun>max_dR:
                                max_dR=abs(lastRun[start_index+i][0]-readAvgRun)/readAvgRun
                    print "Stage 2"
                    print index
                    #print len(lastRun)
                    # if both amplitude and pw are non-zero, we are in a pulsing run
                    if index<len(lastRun) and lastRun[index][1] != 0 and lastRun[index][2] != 0: # if this is the first  pulse of a write sequence:
                        while index<len(lastRun) and lastRun[index][1] != 0 and lastRun[index][2] != 0:
                            index+=1 # increment the index
                            print "in read: ", index

                            if index==len(lastRun)-1: # if the index exceeded the lenght of the run, exit
                                break
                        ampl.append(lastRun[index-1][1]) # record the pulse voltage at the end 


                # Record initial resistances and delta R.
                print len(ampl)
                print len(Rs)
                for i in range(len(ampl)):
                    initR.append(Rs[i])
                    deltaR.append((Rs[i+1]-Rs[i])/Rs[i])

                confX=[0, 0]
                confY=[-max_dR, max_dR] 

                # setup display
                self.resultWindow.append(QtGui.QWidget())
                self.resultWindow[-1].setGeometry(100,100,1000,500)
                self.resultWindow[-1].setWindowTitle("SwitchSeeker: W="+ str(w) + " | B=" + str(b))
                self.resultWindow[-1].setWindowIcon(QtGui.QIcon(os.getcwd()+'/Graphics/'+'icon3.png')) 
                self.resultWindow[-1].show()

                pen1=QtGui.QPen()
                pen1.setColor(QtCore.Qt.red)

                view=pg.GraphicsLayoutWidget()

                label_style = {'color': '#000000', 'font-size': '10pt'}

                self.plot_japan=view.addPlot()
                self.curveJapan=self.plot_japan.plot(pen=None, symbolPen=None, symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
                self.plot_japan.getAxis('left').setLabel('dM/M0', **label_style)
                self.plot_japan.getAxis('bottom').setLabel('Voltage', units='V', **label_style)
                self.plot_japan.getAxis('left').setGrid(50)
                self.plot_japan.getAxis('bottom').setGrid(50)

                #view.nextColumn()  # go to next row and add the next plot

                #view3D=gl.GLViewWidget()

                #scatter1=gl.GLScatterPlotItem

                #self.plot_3D=view.addPlot()
                #self.curve3D=self.plot_3D.plot(pen=pen1, symbolPen=None, symbolBrush=(255,0,0), symbol='s', symbolSize=5, pxMode=True)
                #self.plot_3D.getAxis('left').setLabel('Current (A)')
                #self.plot_3D.getAxis('bottom').setLabel('Voltage (V)')
                #self.plot_3D.getAxis('left').setGrid(50)
                #self.plot_3D.getAxis('bottom').setGrid(50) 

                resLayout = QtGui.QHBoxLayout()
                resLayout.addWidget(view)
                resLayout.setContentsMargins(0,0,0,0)

                self.resultWindow[-1].setLayout(resLayout)

                self.curveJapan.setData(np.asarray(ampl),np.asarray(deltaR))
                #self.curve3D.setData(np.asarray(ampl),np.asarray(initR),np.asarray(deltaR))
                #self.curveIV.setData(np.asarray(V),np.asarray(C))
                #self.curveR.setData(np.asarray(V),np.asarray(R))
                self.resultWindow[-1].update()


            # Retention data processing and display
            if tagKey=='RET':

                lastRun=raw
                timePoints=[]
                m=[]

                for point in raw:
                    tag=str(point[3]) 
                    tagCut=tag[4:]
                    try:
                        timePoint=float(tagCut)
                        timePoints.append(timePoint)
                        m.append(point[0])
                    except ValueError:
                        pass

                # subtract the first point from all timepoints
                firstPoint=timePoints[0]
                for i in range(len(timePoints)):
                    timePoints[i]=timePoints[i]-firstPoint

                view=pg.GraphicsLayoutWidget()
                label_style = {'color': '#000000', 'font-size': '10pt'}

                #pen1=QtGui.QPen()
                #pen1.setColor(QtCore.Qt.blue)

                self.plot_ret=view.addPlot()
                self.curveRet=self.plot_ret.plot(symbolPen=None, symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
                self.plot_ret.getAxis('left').setLabel('Resistance', units='Ohms', **label_style)
                self.plot_ret.getAxis('bottom').setLabel('Time', units='s', **label_style)
                self.plot_ret.getAxis('left').setGrid(50)
                self.plot_ret.getAxis('bottom').setGrid(50)

                resLayout = QtGui.QHBoxLayout()
                resLayout.addWidget(view)
                resLayout.setContentsMargins(0,0,0,0)

                self.resultWindow.append(QtGui.QWidget())
                self.resultWindow[-1].setGeometry(100,100,1000,400)
                self.resultWindow[-1].setWindowTitle("Retention: W="+ str(w) + " | B=" + str(b))
                self.resultWindow[-1].setWindowIcon(QtGui.QIcon(os.getcwd()+'/Graphics/'+'icon3.png')) 
                self.resultWindow[-1].show()


                self.resultWindow[-1].setLayout(resLayout)

                self.plot_ret.setYRange(min(m)/1.5,max(m)*1.5)
                self.curveRet.setData(np.asarray(timePoints),np.asarray(m))
                #self.curve3D.setData(np.asarray(ampl),np.asarray(initR),np.asarray(deltaR))
                #self.curveIV.setData(np.asarray(V),np.asarray(C))
                #self.curveR.setData(np.asarray(V),np.asarray(R))
                self.resultWindow[-1].update()

            if tagKey=='VOL':
                print "VolatilityRead"
        pass

    def min_without_inf(self, lst, exclude):
        maxim=1e100
        for value in lst:
            if type(value)==list:
                value=self.min_without_inf(value, exclude)
                if value<maxim:
                    maxim=value
            else:
                if value<maxim and value!=exclude:
                    maxim=value

        return maxim


    def max_without_inf(self, lst, exclude):
        maxim=0
        for value in lst:
            if type(value)==list:
                value=self.max_without_inf(value, exclude)
                if value>maxim:
                    maxim=value
            else:
                if value>maxim and value!=exclude:
                    maxim=value

        return maxim

    def changeDisplayToSelectedItem(self,item):
        if item.whatsThis(1)=='-1':
            pos=item.whatsThis(0).split(',')
            f.cbAntenna.selectDeviceSignal.emit(int(pos[0]),int(pos[1]))
            f.displayUpdate.updateSignal_short.emit()

    def deunderline(self):
        if self.historyTree.topLevelItemCount()>0:
            for i in range(self.historyTree.topLevelItemCount()):
                self.historyTree.topLevelItem(i).setFont(0,fonts.history_top)

    def formatItemText(self,w,b):
        tag=[]
        tagString=g.Mhistory[w][b][-1][3]
        currentTagKey=[]
        for tagKey in g.tagDict.keys():
            if tagKey in tagString:
                tag.append(g.tagDict[tagKey])
                currentTagKey=tagKey

        # if the operation is a custom pulsing script (such as SS or CT or FF),
        # return also the start and stop indexes for the raw data
        indexList=[0,0]
        results=0

        #make a list of just the tags
        auxArr=g.Mhistory[w][b][::-1]
        tagList=[]
        for point in auxArr:
            tagList.append(str(point[3]))

        #print tag

        if tag: # error catch

            if tag[0]!='Read' and tag[0]!='Pulse':
                results=1
                indexList[1]=len(g.Mhistory[w][b])-1
                try:
                    # find index of the start of the run
                    indexList[0]=indexList[1]-tagList.index(currentTagKey+'_s')
                except ValueError:
                    pass

            tag.append(str(results))     # marks if results can be displayed or not
            tag.append(str(indexList[0]))
            tag.append(str(indexList[1]))
            tag.append(str(currentTagKey))

        return tag
     
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = history_panel()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()  