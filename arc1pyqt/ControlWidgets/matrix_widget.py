from PyQt5 import QtGui, QtCore, QtWidgets
from . import DeviceWidget

from .. import state
HW = state.hardware
CB = state.crossbar
APP = state.app

from ..Globals import fonts


class MatrixWidget(QtWidgets.QWidget):

    def __init__(self, words=HW.conf.words, bits=HW.conf.bits, passive=False,\
            width=(22,50), height=(14,50), parent=None):
        super().__init__(parent=parent)
        # if passive no events will be emitted
        self.passive = passive
        self.cellWidth = width
        self.cellHeight = height
        self.words = words
        self.bits = bits
        self.initUI()

    def initUI(self):
        self.setLayout(self._makeArray(self.words, self.bits))

    @property
    def cells(self):
        try:
            return self._cells
        except:
            return None

    def redrawArray(self, words=HW.conf.words, bits=HW.conf.bits):
        QtWidgets.QWidget().setLayout(self.layout())
        self.setLayout(self._makeArray(words, bits))

    def _makeArray(self, words, bits):

        self.words = words
        self.bits = bits
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(0)

        self._cells = [[[] for x in range(0,bits+1)] for y in range(0,words+1)]

        for r in range(1,words+1):
            for c in range(1,bits+1):
                self._cells[r][c] = DeviceWidget(r, c, self.passive)
                self._cells[r][c].setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, \
                        QtWidgets.QSizePolicy.MinimumExpanding)
                self._cells[r][c].setMinimumWidth(self.cellWidth[0])
                self._cells[r][c].setMinimumHeight(self.cellHeight[0])
                self._cells[r][c].setMaximumWidth(self.cellWidth[1])
                self._cells[r][c].setMaximumHeight(self.cellHeight[1])
                self._cells[r][c].setWhatsThis(str(r)+" "+str(c))

                layout.addWidget(self._cells[r][c],r+1,c+1)
                layout.addItem(QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Minimum, \
                        QtWidgets.QSizePolicy.Expanding), 0, c+1)
            layout.addItem(QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Expanding), \
                    r+1, bits+2)

        lblFont = QtGui.QFont()
        lblFont.setPointSize(7)

        for w in range(1,words+1):
            layout.addItem(QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Expanding), \
                    w, 0)
            lbl = QtWidgets.QLabel()
            lbl.setText("%s " % w)
            lbl.setFont(lblFont)
            lbl.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
            layout.addWidget(lbl, w+1, 1)

        for b in range(1,bits+1):
            layout.addItem(QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Minimum, \
                    QtWidgets.QSizePolicy.Expanding), words+3, b+1)
            lbl = QtWidgets.QLabel()
            lbl.setText("%d" % b)
            lbl.setFont(lblFont)
            lbl.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
            layout.addWidget(lbl, words+2, b+1)

        return layout
