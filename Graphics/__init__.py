import os.path
import importlib.resources
from PyQt5 import QtCore, QtGui


_pixmap_files = [
    'about-banner.png',
    'clear.png',
    'appicon.png',
    'new.png',
    'new-session-banner.png',
    'open.png',
    'platform-manager.png',
    'save.png',
    'splash.png'
]


_pixmaps = {}


# WARNING: A QtWidgets.QApplication MUST be instantiated
# before loading the pixmaps from file!
def initialise():
    for x in _pixmap_files:
        with importlib.resources.path(__name__, x) as res:
            with open(res, 'rb') as f:

                img = os.path.splitext(x)[0]
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(f.read())

                _pixmaps[img] = pixmap


def getPixmap(name):
    return _pixmaps[name]


def getIcon(name):
    return QtGui.QIcon(_pixmaps[name])

