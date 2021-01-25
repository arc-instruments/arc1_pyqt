from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5 import QtGui, QtWidgets
import numpy as np
import collections
import struct

from .. import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from . import functions as f
from ..VirtualArC import VirtualArC


###########################################
# Signal Routers
###########################################
# Class which routes signals (socket) where instantiated
class CBAntenna(QObject):
    # Used for highlighting/deselecting devices on the crossbar panel
    selectDeviceSignal=pyqtSignal(int, int)
    deselectOld=pyqtSignal()
    redraw=pyqtSignal()
    reformat=pyqtSignal()
    # and signals updating the current select device
    recolor=pyqtSignal(float, int, int)

    def __init__(self):
        super().__init__()

    def cast(self,w,b):
        self.selectDeviceSignal.emit(w,b)


class DisplayUpdateAntenna(QObject):
    updateSignal_short=pyqtSignal()
    updateSignal=pyqtSignal(int, int, int,  int,    int)
                        #   w,   b,   type, points, slider
    updateLog=pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def cast(self):
        self.updateSignal_short.emit()


# Class which routes signals (socket) where instantiated
class HistoryTreeAntenna(QObject):
    # used for signaling the device history tree list to update its contents
    updateTree=pyqtSignal(int,int)
    updateTree_batch = pyqtSignal(int, int, int)
    clearTree=pyqtSignal()
    changeSessionName=pyqtSignal()
    rebuildTreeTopLevel = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()


class InterfaceAntenna(QObject):
    disable=pyqtSignal(bool)
    reformat=pyqtSignal()
    changeArcStatus=pyqtSignal(str)
    changeSessionMode=pyqtSignal(str)
    updateHW=pyqtSignal()
    lastDisplaySignal=pyqtSignal()

    globalDisable=False

    def __init__(self):
        super().__init__()

    def wakeUp(self):
        APP.waitCondition.wakeAll()

    def cast(self, value):
        if self.globalDisable==False:
            self.disable.emit(value)
            #sleep(0.1)
            self.lastDisplaySignal.emit()

    def castArcStatus(self, value):
        if self.globalDisable==False:
            self.changeArcStatus.emit(value)

    def toggleGlobalDisable(self, value):
        self.globalDisable=value


class SAantenna(QObject):
    disable=pyqtSignal(int, int)
    enable=pyqtSignal(int, int)

    def __init__(self):
        super().__init__()


class HoverAntenna(QObject):

    displayHoverPanel=pyqtSignal(int, int, int, int, int, int)
    hideHoverPanel=pyqtSignal()

    def __init__(self):
        super().__init__()


class AddressAntenna(QObject):
    def __init__(self):
        super().__init__()

    def update(self, w,b):
        CB.word, CB.bit = w,b
        f.cbAntenna.selectDeviceSignal.emit(w, b)

