import os.path
try:
    import importlib.resources as importlib_resources
except (ModuleNotFoundError, ImportError):
    import importlib_resources

from PyQt5 import QtCore, QtGui, QtSvg


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

_svg_files = [
    'display-res.svg',
    'display-cond.svg',
    'display-cur.svg',
    'display-abs-cur.svg'
]

_pixmaps = {}
_svgs = {}


# WARNING: A QtWidgets.QApplication MUST be instantiated
# before loading the pixmaps from file!
def initialise():
    for x in _pixmap_files:
        with importlib_resources.path(__name__, x) as res:
            with open(res, 'rb') as f:

                img = os.path.splitext(x)[0]
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(f.read())

                _pixmaps[img] = pixmap

    for x in _svg_files:
        with importlib_resources.path(__name__, x) as res:
            with open(res, 'rb') as f:
                img = os.path.splitext(x)[0]
                svg = QtSvg.QSvgRenderer(f.read())
                _svgs[img] = svg


def getPixmap(name):
    return _pixmaps[name]


def getIcon(name):
    return QtGui.QIcon(_pixmaps[name])


def getSvgRenderer(name):
    """
    Get the underlying renderer object to render directly
    on a QPainter
    """
    return _svgs[name]


def getSvgScaled(name, ratio=1.0):
    """
    Convert an SVG into a pixmap
    """

    svg = getSvgRenderer(name)
    img_w = svg.defaultSize().width()*ratio
    img_h = svg.defaultSize().height()*ratio

    img = QtGui.QPixmap(img_w, img_h)
    img.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(img)
    svg.render(painter)

    return img

def getSvgIcon(name, ratio=1.0):
    """
    Convert an SVG into an Icon
    (SVG -> Pixmap -> Icon)
    """
    return QtGui.QIcon(getSvgScaled(name, ratio=ratio))
