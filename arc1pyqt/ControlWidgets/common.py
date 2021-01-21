from PyQt5.QtGui import QColor
import matplotlib.cm as cm

resistanceColorGradient = []

for i in range(cm.rainbow.N):
    color = QColor()
    color.setRgbF(cm.rainbow(i)[0], \
            cm.rainbow(i)[1], \
            cm.rainbow(i)[2], \
            cm.rainbow(i)[3])
    resistanceColorGradient.insert(0, color)
