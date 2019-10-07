import os.path
import importlib.resources
from PyQt5 import QtCore, QtGui


_pixmap_files = [
    'aboutSection.png',
    'clear.png',
    'icon3.png',
    'new.png',
    'NewSeshLogoDrawing2.png',
    'newSeshLogo.png',
    'open.png',
    'platform_manager.png',
    'save.png',
    'splash2.png'
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

