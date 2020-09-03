from .. import Graphics
from PyQt5 import QtCore, QtGui, QtWidgets


class _SvgLogo:

    def __init__(self, img):
        self.img = Graphics.getSvgRenderer(img)

    def paint(self, painter, x, y, w, h):
        self.img.render(painter, QtCore.QRectF(x, y, w, h))

    def width(self):
        return self.img.defaultSize().width()

    def height(self):
        return self.img.defaultSize().height()


class _PixmapLogo:

    def __init__(self, img):
        self.img = Graphics.getPixmap(img)

    def paint(self, painter, x, y, w, h):
        painter.drawPixmap(x, y, w, h, self.img)

    def width(self):
        return self.img.width()

    def height(self):
        return self.img.height()


class LogoLabelWidget(QtWidgets.QLabel):

    """
    A simple logo label widget. Displays a logo on top of a coloured label.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.color = (0, 0, 0)
        self.img = None
        self.logoAlignment = (QtCore.Qt.AlignHCenter, QtCore.Qt.AlignVCenter)
        self.logoScale = 1.0

    def setSvgResource(self, img):
        self.img = _SvgLogo(img)
        self.update()

    def setPixmapResource(self, img):
        self.img = _PixmapLogo(img)
        self.update()

    def setColor(self, red, green, blue):
        self.color = (red, green, blue)
        self.update()

    def setLogoAlignment(self, horizontal, vertical):
        self.logoAlignment = (horizontal, vertical)
        self.update()

    def setLogoScaling(self, scale):
        self.logoScale = scale

    def _getPosition(self, logo_w, logo_h):
        halign = self.logoAlignment[0]
        if halign == QtCore.Qt.AlignLeft:
            logo_x = 0.0
        elif halign == QtCore.Qt.AlignRight:
            logo_x = self.width() - logo_w
        elif halign == QtCore.Qt.AlignHCenter:
            logo_x = (self.width() - logo_w)/2.0
        else:
            raise ValueError("Unknown H-alignment", halign)

        valign = self.logoAlignment[1]
        if valign == QtCore.Qt.AlignTop:
            logo_y = 0.0
        elif valign == QtCore.Qt.AlignBottom:
            logo_y = self.height() - logo_h
        elif valign == QtCore.Qt.AlignVCenter:
            logo_y = (self.height() - logo_h)/2.0
        else:
            raise ValueError("Unknown V-alignment", valign)

        return (logo_x, logo_y)

    def minimumSizeHint(self):
        if self.img is not None:
            w = self.img.width()*self.logoScale
            h = self.img.height()*self.logoScale
            return QtCore.QSize(w, h)
        return QtCore.QSize(0, 0)

    def draw(self):
        if self.img is not None:
            logo_w = self.img.width()*self.logoScale
            logo_h = self.img.height()*self.logoScale
            (logo_x, logo_y) = self._getPosition(logo_w, logo_h)

        pixmap = QtGui.QPixmap(self.size())
        painter = QtGui.QPainter(pixmap)

        pen = QtGui.QPen()
        rect = self.rect()
        painter.fillRect(rect, QtGui.QColor(*self.color))
        if self.img is not None:
            self.img.paint(painter, logo_x, logo_y, logo_w, logo_h)

        painter.end()
        self.setPixmap(pixmap)

    def resizeEvent(self, evt):
        self.draw()
        super().resizeEvent(evt)
