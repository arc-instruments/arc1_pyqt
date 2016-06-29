
import GlobalVars as g
from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4 import QtGui
from time import sleep
import numpy as np


###########################################
# Signal Routers
###########################################
class cbAntenna(QObject): 		# class which routes signals (socket) where instantiated
    selectDeviceSignal=pyqtSignal(int, int) 	# used for highlighting/deselecting devices on the crossbar panel
    deselectOld=pyqtSignal()
    redraw=pyqtSignal()
    reformat=pyqtSignal()
    							# and signals updating the current select device
    recolor=pyqtSignal(float, int, int)

    def __init__(self):
        super(cbAntenna,self).__init__()

    def cast(self,w,b):
        self.selectDeviceSignal.emit(w,b)
cbAntenna=cbAntenna()


class displayUpdate(QObject):
	updateSignal_short=pyqtSignal()
	updateSignal=pyqtSignal(int, int, int, 	int, 	int)
						#   w,   b,   type, points, slider
	updateLog=pyqtSignal(int)

	def __init__(self):
		super(displayUpdate,self).__init__()

	def cast(self):
		self.updateSignal_short.emit()
displayUpdate=displayUpdate()


class historyTreeAntenna(QObject): 		# class which routes signals (socket) where instantiated
    updateTree=pyqtSignal(int,int) 	# used for signaling the device history tree list to update its contents							
    updateTree_short=pyqtSignal()
    clearTree=pyqtSignal()
    changeSessionName=pyqtSignal()

    def __init__(self):
        super(historyTreeAntenna,self).__init__()
historyTreeAntenna=historyTreeAntenna()


class interfaceAntenna(QObject):
	disable=pyqtSignal(bool)
	reformat=pyqtSignal()
	changeArcStatus=pyqtSignal(str)
	changeSessionMode=pyqtSignal(str)
	updateHW=pyqtSignal()

	def __init__(self):
		super(interfaceAntenna,self).__init__()
interfaceAntenna=interfaceAntenna()

# updates the range of devices for each pulsing script thread
######################################

###########################################

class SAantenna(QObject):
	disable=pyqtSignal(int, int)
	enable=pyqtSignal(int, int)

	def __init__(self):
		super(SAantenna,self).__init__()
SAantenna=SAantenna()

###########################################
# Update history function
###########################################
def updateHistory(w,b,m,a,pw,tag):
	g.Mhistory[w][b].append([m,a,pw,tag])
	g.Mnow=m
	# for data display purposes
	#g.MList[w][b]=np.append(g.MList[w][b],m)
	#g.PList[w][b]=np.append(g.PList[w][b],0)
	#g.PList[w][b]=np.append(g.PList[w][b],a)
	#g.PList[w][b]=np.append(g.PList[w][b],0)
	#g.PMarkerList[w][b]=np.append(g.PMarkerList[w][b],a)
	#g.PWList[w][b]=np.append(g.PWList[w][b],pw)

	g.w=w
	g.b=b
	cbAntenna.recolor.emit(m,w,b)


def updateHistory_short(m,a,pw,tag):
	g.Mhistory[g.w][g.b].append([m,a,pw,tag])
	#g.MList[g.w][g.b]=np.append(g.MList[g.w][g.b],m)
	#g.PList[g.w][g.b]=np.append(g.PList[g.w][g.b],0)
	#g.PList[g.w][g.b]=np.append(g.PList[g.w][g.b],a)
	#g.PList[g.w][g.b]=np.append(g.PList[g.w][g.b],0)
	#g.PMarkerList[g.w][g.b]=np.append(g.PMarkerList[g.w][g.b],a)
	#g.PWList[g.w][g.b]=np.append(g.PWList[g.w][g.b],pw)
	cbAntenna.recolor.emit(m,g.w,g.b)

###########################################
# UUpdate Hover panel
###########################################

class hoverAntenna(QObject):
	displayHoverPanel=pyqtSignal(int, int, int, int, int, int)
	hideHoverPanel=pyqtSignal()

	def __init__(self):
		super(hoverAntenna,self).__init__()

hoverAntenna=hoverAntenna()



