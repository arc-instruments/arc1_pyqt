from dataclasses import dataclass
import numpy as np
from PyQt5.QtCore import QMutex, QWaitCondition
from .instrument import HWConfig

@dataclass
class Crossbar:
    word = 1
    bit = 1
    limits = { 'words': (1, 1), 'bits': (1, 1) }
    history = [[[] for bit in range(33)] for word in range(33)]
    checkSA = False
    customArray = []

    def append(self, w, b, *args):
        self.history[w][b].append(list(args))


@dataclass
class Application:
    modules = { }
    sessionName = 'Package 1'
    workingDirectory = []
    saveFileName = []
    scalingFactor = 1.0
    displayPoints = 100
    globalDisable = False
    mutex = QMutex()
    waitCondition = QWaitCondition()


@dataclass
class Hardware:
    conf = HWConfig(words=32, bits=32, cycles=50, readmode=2, \
            sessionmode=0, sneakpath=1, Vread=0.5)
    ArC = None


# state variables
app = Application()
crossbar = Crossbar()
hardware = Hardware()
