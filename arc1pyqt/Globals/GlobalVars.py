####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib
matplotlib.rcParams['backend'] = 'Qt5Agg'
import matplotlib.pyplot as mpl
import numpy as np
import serial

Mnow = 1000

baudrate = '921600'

readOptions = ['Classic', 'TIA', 'TIA4P']
readOption = 0

# active wordline
w = 1
# active bitline
b = 1
# total number of word-/bitlines
N = 32
# read voltage
Vread = 0.5
# read cycles for resistance readout
readCycles = 50

# serial connection
ser = serial.Serial()

# Main data container
Mhistory = [[[] for bit in range(33)] for word in range(33)]
# arrays of floats updated each time Mhistory is updated to be used for data
# display
MList = [[np.array([]) for bit in range(33)] for word in range(33)]
PList = [[np.array([]) for bit in range(33)] for word in range(33)]
PWList = [[np.array([]) for bit in range(33)] for word in range(33)]
PMarkerList = [[np.array([]) for bit in range(33)] for word in range(33)]

wline_nr = 32
bline_nr = 32

minW = 1
minB = 1
maxW = 1
maxB = 1

# Tag dictionaries
tagDict={'S R':'Read',\
         'P':'Pulse'}

# Data display callbacks
DispCallbacks = {}

# number of points to plot
dispPoints = 100

# top edge colour
maxM = 100000000
# bottom edge colour
minM = 100

# Colormap setup: a list of QColor objects
color_tuple = mpl.cm.rainbow
qColorList = []


for i in range(color_tuple.N):
    aux_color = QtGui.QColor()
    aux_color.setRgbF(color_tuple(i)[0], color_tuple(i)[1],
            color_tuple(i)[2], color_tuple(i)[3])
    qColorList.append(aux_color)

qColorList = qColorList[::-1] # revert the list

scaling_factor = 1

customArray = []
checkSA = False

# Global variables for data handling

workingDirectory = []
saveFileName = []

# File patterns for file dialogs
SAVE_FI_PATTERN = 'Session file (*.csv);;Compressed Session file (*.csv.gz)'
OPEN_FI_PATTERN = 'Session files (*.csv *.csv.gz)'

####################################
# ArC One mode variables
sessionMode = 0
sessionName = 'Package 1'
sneakPathOption = 1

waitCondition = QtCore.QWaitCondition()
mutex = QtCore.QMutex()
globalDisable = False

####################################

local_version = 1
remote_version = 1
