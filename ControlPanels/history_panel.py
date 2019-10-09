####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets
from functools import partial

import pyqtgraph as pg
import numpy as np
import re

import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Graphics


class history_panel(QtWidgets.QWidget):
    
    def __init__(self):
        super(history_panel, self).__init__()
        self.initUI()
        
    def initUI(self):   

        self.dieName = QtWidgets.QLineEdit('Package1')
        self.dieName.setFont(fonts.font1)
        self.dieName.textChanged.connect(self.changeSessionNameManualy)

        self.historyTree = QtWidgets.QTreeWidget()
        self.historyTree.setHeaderLabel('Device History')
        self.historyTree.itemClicked.connect(self.changeDisplayToSelectedItem)
        self.historyTree.itemDoubleClicked.connect(self.displayResults)

        f.historyTreeAntenna.updateTree.connect(self.updateTree)
        f.historyTreeAntenna.updateTree_short.connect(self.updateTree_short)
        f.historyTreeAntenna.clearTree.connect(self.clearTree)
        f.historyTreeAntenna.changeSessionName.connect(self.changeSessionName)

        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.dieName)
        mainLayout.addWidget(self.historyTree)

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        self.topLevelItems=[]
        self.resultWindow=[]

        self.setLayout(mainLayout)

    def changeSessionNameManualy(self, txt):
        g.sessionName=txt

    def changeSessionName(self):
        self.dieName.setText(g.sessionName)

    def clearTree(self):
        self.historyTree.clear()

    def updateTree_short(self):
        self.updateTree(g.w,g.b)

    def updateTree(self,w,b):
        existingItem=self.historyTree.findItems("W=" + str(w) + " | B=" + str(b), QtCore.Qt.MatchExactly,0)

        if existingItem==[]:        # if no entry for that adress exists, make a new one
            newTag=self.formatItemText(w,b) # format the text of the new history entry item taken from the dictionary of the prog panels
            if newTag:
                newTree=QtWidgets.QTreeWidgetItem(self.historyTree)
                newTree.setText(0,"W=" + str(w) + " | B=" + str(b))
                self.deunderline()                                  # deunderline every tree top level item
                newTree.setFont(0,fonts.history_top_underline)      # underline the current one
                newTree.setWhatsThis(0,str(w)+','+str(b))   # set a tag for the item
                newTree.setWhatsThis(1,str(-1))
                newTree.setWhatsThis(2,str(0))
                newTree.setWhatsThis(3,str(0))
                newTree.setWhatsThis(4,str(0))
                #newTree.itemClicked.connect(self.changeDisplayToSelectedItem)
                newItem=QtWidgets.QTreeWidgetItem(newTree)
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
            if newTag:

                if existingItem[0].child(0):            # if a child exists in the stack (which is always true, this function might be unecessary)
                    if newTag[0] in existingItem[0].child(0).text(0):  # if previously the same operation has been performed
                        if newTag[0]=='Read' or newTag[0]=='Pulse':       # for Read and Pulse special cases, add the trailing integer by +1
                            string=str(existingItem[0].child(0).text(0))
                            nr=[int(s) for s in string.split(' ') if s.isdigit()][-1]
                            nr=nr+1
                            newTag[0]=newTag[0]+' x '+str(nr)
                            existingItem[0].child(0).setText(0,newTag[0])
                        else:                                   # if it's not pulse or read, add a new item
                            newItem=QtWidgets.QTreeWidgetItem()
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
                        newItem=QtWidgets.QTreeWidgetItem()
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
            tagKey=str(item.whatsThis(5))

            #print "#########"
            #print startPoint
            #print endPoint

            raw=g.Mhistory[w][b][startPoint:endPoint+1]

            # Display results in a new window based on the tag
            # the tag selects the type of results processing and display.

            if tagKey=='VOL':
                pass

            if tagKey=='stdp':

                reg=re.compile(r'-?[0-9\.]+')

                i=0
                list_dt=[]
                Mbefore=0
                Mafter=0
                dG=[]
                dt=0
                while i<len(raw):
                    stdp_tag=str(raw[i][3])
                    if "before" in stdp_tag:
                        Mbefore=raw[i][0]
                        Mafter=raw[i+1][0]
                        dt=float(re.findall(reg,stdp_tag)[0])
                        list_dt.append(dt)
                        dG.append((1/Mafter-1/Mbefore)/(1/Mbefore))
                        i+=2
                    else:
                        i+=1


                # setup display
                self.resultWindow.append(QtWidgets.QWidget())
                self.resultWindow[-1].setGeometry(100,100,500,500)
                self.resultWindow[-1].setWindowTitle("STDP: W="+ str(w) + " | B=" + str(b))
                self.resultWindow[-1].setWindowIcon(Graphics.getIcon('appicon'))
                self.resultWindow[-1].show()

                view=pg.GraphicsLayoutWidget()
                label_style = {'color': '#000000', 'font-size': '10pt'}

                #pen1=QtGui.QPen()
                #pen1.setColor(QtCore.Qt.blue)

                self.plot_stdp=view.addPlot()
                self.curve_stdp=self.plot_stdp.plot(pen=None, symbolPen=None, symbolBrush=(0,0,255), symbol='s', symbolSize=5, pxMode=True)
                self.plot_stdp.getAxis('left').setLabel('dG/G0', **label_style)
                self.plot_stdp.getAxis('bottom').setLabel('deltaT', units='s', **label_style)
                self.plot_stdp.getAxis('left').setGrid(50)
                self.plot_stdp.getAxis('bottom').setGrid(50)
                self.curve_stdp.setData(np.asarray(list_dt),np.asarray(dG))

                resLayout = QtWidgets.QHBoxLayout()
                resLayout.addWidget(view)
                resLayout.setContentsMargins(0,0,0,0)

                self.resultWindow[-1].setLayout(resLayout)

                self.resultWindow[-1].update()

            # Only phase 3 has exploitable results
            if str(tagKey) in g.DispCallbacks:
                widget = g.DispCallbacks[tagKey](w, b, raw, self)
                self.resultWindow.append(widget)
                widget.show()
                widget.update()

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
        tagPartsUnder = str(tagString).split("_") # underscore delimited tags
        for tagKey in g.tagDict.keys():
            # As the program stands we have two sets of tags
            # either the regular XYZ_s, XYZ_i, XYZ_e for most
            # modules, or space delimited for reads and stdp
            # so first check the most standard case
            if len(tagPartsUnder) > 1 and tagPartsUnder[0] == tagKey:
                tag.append(g.tagDict[tagKey])
                currentTagKey=tagKey
                break
            # and the just revert to the old behaviour
            elif str(tagString).startswith(tagKey):
                tag.append(g.tagDict[tagKey])
                currentTagKey=tagKey
                break


        # if the operation is a custom pulsing script (such as SS or CT or FF or STDP or Endurance),
        # return also the start and stop indexes for the raw data
        indexList=[0,0]
        results=0

        #make a list of just the tags
        auxArr=g.Mhistory[w][b][::-1]
        tagList=[]
        for point in auxArr:
            tagList.append(str(point[3]))


        if tag: # error catch

            if tag[0]!='Read' and tag[0]!='Pulse':
                results=1
                indexList[1]=len(g.Mhistory[w][b])-1
                try:
                    # find index of the start of the run
                    lastIndex = None
                    for (i, text) in enumerate(tagList):
                        if text.startswith(currentTagKey) and text.endswith('_s'):
                            lastIndex = i
                            break

                    # This should not happen but in case it does drop back to the
                    # legacy behaviour
                    if lastIndex is None:
                        print("index is NONE!!!")
                        lastIndex = tagList.index(currentTagKey+'_s')

                    indexList[0] = indexList[1] - lastIndex
                except ValueError:
                    pass

            tag.append(str(results))     # marks if results can be displayed or not
            tag.append(str(indexList[0]))
            tag.append(str(indexList[1]))
            tag.append(str(currentTagKey))

        return tag

