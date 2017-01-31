####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

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
	lastDisplaySignal=pyqtSignal()

	globalDisable=False

	def __init__(self):
		super(interfaceAntenna,self).__init__()

	def wakeUp(self):
		g.waitCondition.wakeAll()
		#print " --> waitCondition wakedAll"
	def cast(self, value):
		# if value==False:
		# 	g.waitCondition.wakeAll()
		# 	print " --> waitCondition wakedAll"
		if self.globalDisable==False:
			self.disable.emit(value)
			#sleep(0.1)
			self.lastDisplaySignal.emit()
			

	def castArcStatus(self, value):
		if self.globalDisable==False:
			self.changeArcStatus.emit(value)		

	def toggleGlobalDisable(self, value):
		self.globalDisable=value
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
	readTag='R'+str(g.readOption)
	if g.sessionMode==1:
		g.Mnow=m/2
	else:
		g.Mnow=m
	g.Mhistory[w][b].append([g.Mnow,a,pw,tag,readTag,g.Vread])
	

	g.w=w
	g.b=b
	cbAntenna.recolor.emit(m,w,b)

def updateHistory_CT(w,b,m,a,pw,tag):
	readTag='R2'
	print "received: ", m, a
	
	if g.sessionMode==1:
		g.Mnow=m/2
	else:
		g.Mnow=m

	g.Mhistory[w][b].append([g.Mnow,a,pw,tag,readTag,a])

	g.w=w
	g.b=b
	cbAntenna.recolor.emit(m,w,b)


def updateHistory_short(m,a,pw,tag):
	readTag='R'+str(g.readOption)
	if g.sessionMode==1:
		g.Mnow=m/2
	else:
		g.Mnow=m
	g.Mhistory[g.w][g.b].append([g.Mnow,a,pw,tag,readTag, g.Vread])
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

class addressAntenna(QObject):
	def __init__(self):
		super(addressAntenna,self).__init__()

	def update(self, w,b):
		g.w,g.b=w,b
		cbAntenna.selectDeviceSignal.emit(w, b)
addressAntenna=addressAntenna()

dataBuffer=[]

def getFloats(n):
	while g.ser.inWaiting()<n*4:
		pass
	values=g.ser.read(size=n*4)	# read n * 4 bits of data (n floats) from the input serial
	extracted=np.frombuffer(buffer(values), dtype=np.float32)
	return extracted	# returns a list of these floats






