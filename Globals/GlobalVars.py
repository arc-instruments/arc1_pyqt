####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt4 import QtCore
from PyQt4 import QtGui
import matplotlib.pyplot as mpl
import numpy as np

import serial

Mnow=1000

Mnow_str=QtCore.QString('1000')
Mnow_position_str=QtCore.QString('W=0 | B=0')

baudrate='921600'

readOptions=['Classic', 'TIA', 'TIA4P']
#                0        1        2		# important that readtypes are in this order
readOption=0;

w=1
b=1

N=32

Vread=0.5
readCycles=50
ser=serial.Serial() # serial object

Mhistory=[[[] for bit in range(33)] for word in range(33)] 	# Main data container
# arrays of floats updated each time Mhistory is updated to be used for data display
MList=[[np.array([]) for bit in range(33)] for word in range(33)]	
PList=[[np.array([]) for bit in range(33)] for word in range(33)]	
PWList=[[np.array([]) for bit in range(33)] for word in range(33)]	
PMarkerList=[[np.array([]) for bit in range(33)] for word in range(33)]	

wline_nr=32
bline_nr=32

minW=1
minB=1
maxW=1
maxB=1

# Tag dictionaries
tagDict={	'S R':'Read',\
		 	'P':'Pulse'}

dispPoints=100

maxM=100000000						# Value of resistance for top edge color
minM=100 							# Value of resistance for bottom edge color

minMlog=np.log10(minM)
normMlog=np.log10(maxM)-minMlog

####################################
# Colormap setup
# creates a list of QColor objects

color_tuple=mpl.cm.rainbow

qColorList=[]

for i in range(color_tuple.N):
	aux_color=QtGui.QColor()
	aux_color.setRgbF(color_tuple(i)[0], color_tuple(i)[1], color_tuple(i)[2], color_tuple(i)[3])
	qColorList.append(aux_color)

qColorList=qColorList[::-1] # revert the list

####################################
customArray=[]
checkSA=False

####################################
# Global variables for data saving

workingDirectory=[]
saveFileName=[]

####################################
# ArC One mode variables
sessionMode=0
sessionName='Package 1'
sneakPathOption=0

####################################
# UDP module globals.
ConnMat = np.zeros((1,1,1)) #ConnMat(x,y,z): x-> input neuron, y-> output neuron, z-> =1: connection exists (1/0), =2: w address, =3: b address, =4: last operation pre? (0) or post? (1)
opEdits = [] #LTP/LTD parameter list.
partcode = (65, 68, 83) #Holds decimanl values of ASCII characters 'a' (axon), 'd' (dendrite) and 's' (synapse).
