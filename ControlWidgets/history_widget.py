####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from functools import partial
from PyQt5 import QtGui, QtCore, QtWidgets

import pyqtgraph as pg
import numpy as np

import Globals.GlobalStyles as s
import Globals.GlobalFonts as fonts
import Globals.GlobalFunctions as f
import Globals.GlobalVars as g
import Graphics


class HistoryWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
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

        # if no entry for that adress exists, make a new one
        if existingItem==[]:
            # format the text of the new history entry item taken from the
            # dictionary of the prog panels
            newTag=self.formatItemText(w,b)
            if newTag:
                newTree=QtWidgets.QTreeWidgetItem(self.historyTree)
                newTree.setText(0,"W=" + str(w) + " | B=" + str(b))
                # deunderline every tree top level item
                self.deunderline()
                # underline the current one
                newTree.setFont(0,fonts.history_top_underline)
                # set a tag
                newTree.setWhatsThis(0,str(w)+','+str(b))
                newTree.setWhatsThis(1,str(-1))
                newTree.setWhatsThis(2,str(0))
                newTree.setWhatsThis(3,str(0))
                newTree.setWhatsThis(4,str(0))
                newItem=QtWidgets.QTreeWidgetItem(newTree)
                newItem.setWhatsThis(0,str(w)+','+str(b))

                newItem.setWhatsThis(1,newTag[0])
                newItem.setWhatsThis(2,newTag[1])
                newItem.setWhatsThis(3,newTag[2])
                newItem.setWhatsThis(4,newTag[3])
                newItem.setWhatsThis(5,newTag[4])

                # Special cases of pulse and read are handled separately
                if newTag[0]=='Read':
                    newTag[0]='Read x 1'
                if newTag[0]=='Pulse':
                    newTag[0]='Pulse x 1'

                newItem.setText(0,newTag[0])
                newItem.setFont(0,fonts.history_child)
        # if the CB crosspoint has been pulsed before, add in the reepctive
        # tree stack
        else:
            self.deunderline()
            existingItem[0].setFont(0,fonts.history_top_underline)
            newTag=self.formatItemText(w,b)
            if newTag:

                # if a child exists in the stack (which is always true, this
                # function might be unecessary)
                if existingItem[0].child(0):
                    # if previously the same operation has been performed
                    if newTag[0] in existingItem[0].child(0).text(0):
                        # for Read and Pulse special cases, add the trailing
                        # integer by +1
                        if newTag[0]=='Read' or newTag[0]=='Pulse':
                            string=str(existingItem[0].child(0).text(0))
                            nr=[int(s) for s in string.split(' ') if s.isdigit()][-1]
                            nr=nr+1
                            newTag[0]=newTag[0]+' x '+str(nr)
                            existingItem[0].child(0).setText(0,newTag[0])
                        # if it's not pulse or read, add a new item
                        else:
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

        # Results to be displayed
        if item.whatsThis(2)=='1':
            pos=item.whatsThis(0).split(',')
            w=int(pos[0])
            b=int(pos[1])

            tag=item.whatsThis(1)
            startPoint=int(item.whatsThis(3))
            endPoint=int(item.whatsThis(4))
            tagKey=str(item.whatsThis(5))

            raw=g.Mhistory[w][b][startPoint:endPoint+1]

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
            # check for standard read/pulse tags
            if tagString.startswith(('P', 'S R', 'F R')):
                tag.append(g.tagDict[tagKey])
                currentTagKey=tagKey
                break
            # then any regular '_'-delimited tags
            elif len(tagPartsUnder) > 1 and tagPartsUnder[0] == tagKey:
                    tag.append(g.tagDict[tagKey])
                    currentTagKey=tagKey
                    break
            # ignore unknown or intermediate tags
            else:
                pass


        # if the operation is a custom pulsing script (such as SS or CT or FF
        # or STDP or Endurance), return also the start and stop indexes for the
        # raw data
        indexList=[0,0]
        results=0

        #make a list of just the tags
        auxArr=g.Mhistory[w][b][::-1]
        tagList=[]
        for point in auxArr:
            tagList.append(str(point[3]))

        if tag:
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
                        lastIndex = tagList.index(currentTagKey+'_s')

                    indexList[0] = indexList[1] - lastIndex
                except ValueError:
                    pass

            # marks if results can be displayed or not
            tag.append(str(results))
            tag.append(str(indexList[0]))
            tag.append(str(indexList[1]))
            tag.append(str(currentTagKey))

        return tag

