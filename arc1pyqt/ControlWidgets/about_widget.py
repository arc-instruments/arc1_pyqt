####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import os
import platform

from .. import Graphics
from ..version import VersionInfo, vercmp
from . import LogoLabelWidget

from .. import state
HW = state.hardware


class AboutWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.firmwareRead = False
        self.initUI()

    def initUI(self):

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)

        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        logoTop = LogoLabelWidget()
        logoTop.setColor(255, 255, 255)
        logoTop.setPixmapResource('about-banner')
        mainLayout.addWidget(logoTop)

        botHLay=QtWidgets.QHBoxLayout()
        botHLay.setContentsMargins(0,0,0,0)

        spacerWidget=QtWidgets.QWidget()
        spacerWidget.setFixedWidth(172)
        spacerWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Expanding)

        p = spacerWidget.palette()
        p.setColor(spacerWidget.backgroundRole(), QtCore.Qt.white)
        spacerWidget.setPalette(p)

        botHLay.addWidget(spacerWidget)
        botHLay.setSpacing(0)

        infoLay=QtWidgets.QVBoxLayout()
        infoLay.setContentsMargins(0,10,0,10)
        infoLay.setSpacing(0)

        line0=QtWidgets.QLabel()
        line1=QtWidgets.QLabel()
        line2=QtWidgets.QLabel()
        line3=QtWidgets.QLabel()
        line4=QtWidgets.QLabel()
        line5=QtWidgets.QLabel()
        line6=QtWidgets.QLabel()
        line7=QtWidgets.QLabel()

        system = "%s %s" % (platform.system(), platform.architecture()[0])
        pyver = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
        vinfo = VersionInfo()
        version = vinfo.local
        try:
            remote = vinfo.remote
            if vercmp(version, remote) <= 0:
                # no update available
                remote = None
        except:
            # remote version could not be retrieved
            remote = None

        if remote is None:
            line0.setText("ArC ONE: <b>%s</b> System: <b>%s</b> "
                    "Python: <b>%s</b> Qt: <b>%s</b>  " %
                    (version, system, pyver, QtCore.QT_VERSION_STR))
        else:
            line0.setText("ArC ONE: <b>%s</b> "
                    "(<span style=\"color:red;\">%s available</span>) "
                    "System: <b>%s</b> Python: <b>%s</b> Qt: <b>%s</b>  " %
                    (version, remote, system, pyver, QtCore.QT_VERSION_STR))
        line1.setText('75 Sirocco, 33 Channel Way')
        line2.setText('Ocean Village')
        line3.setText('Southampton, UK')
        line4.setText('SO14 3JF')
        line5.setText('www.arc-instruments.co.uk')
        line6.setText('office@arc-instruments.co.uk')
        line7.setText('+44 777 235 0889')

        infoLay.addWidget(line1)
        infoLay.addWidget(line2)
        infoLay.addWidget(line3)
        infoLay.addWidget(line4)
        infoLay.addItem(QtWidgets.QSpacerItem(5, 10))
        infoLay.addStretch()
        infoLay.addWidget(line5)
        infoLay.addWidget(line6)
        infoLay.addWidget(line7)
        infoLay.addItem(QtWidgets.QSpacerItem(5, 10))
        infoLay.addStretch()
        infoLay.addWidget(line0)

        self.lineFW = QtWidgets.QLabel(" ")

        self._updateFirmwareLabel()

        infoLay.addWidget(self.lineFW)
        botHLay.addLayout(infoLay)

        mainLayout.addStretch()
        mainLayout.addLayout(botHLay)

        self.setLayout(mainLayout)

    def _updateFirmwareLabel(self):
        if (HW.ArC is not None) and (hasattr(HW.ArC, 'firmware_version')):
            if self.firmwareRead:
                version = HW.ArC.firmware_version()
                self.lineFW.setText(self._formatFirmwareText(version))
            else:
                self.lineFW.setText(self._formatFirmwareText(None))
            self.lineFW.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            self.lineFW.linkActivated.connect(self._onFirmwareLabelClicked)
        else:
            self.firmwareRead = False
            self.lineFW.setText(" ")

    def _onFirmwareLabelClicked(self, *args):
        version = HW.ArC.firmware_version()
        self.lineFW.setText(self._formatFirmwareText(version))
        self.firmwareRead = True

    def _formatFirmwareText(self, version):
        if version is None:
            versionText = "Unknown"
        elif version == (-1, -1):
            versionText = "< 9.3"
        else:
            versionText = "%d.%d" % (version[0], version[1])

        return "Firmware: <b>%s</b> " \
            "<a href=\"update\">Retrieve</a>" % versionText

    def showEvent(self, evt):
        super().showEvent(evt)
        self._updateFirmwareLabel()
