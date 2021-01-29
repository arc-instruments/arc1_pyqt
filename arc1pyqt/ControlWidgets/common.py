from PyQt5.QtGui import QColor
import numpy as np

resistanceColorGradient = []

def _rainbow(x=0):
    # clip values between 0 and 256
    if x > 255:
        x = 255
    elif x < 0:
        x = 0

    r = np.abs(2.0 * x/255.0 - 0.5)
    g = np.sin(x/255.0 * np.pi)
    b = np.cos(x/255.0 * np.pi/2)

    return (
        1.0 if r > 1.0 else r,
        1.0 if g > 1.0 else g,
        1.0 if b > 1.0 else b)

for i in range(256):
    color = QColor()
    (r, g, b) = _rainbow(i)
    color.setRgbF(r, g, b, 1.0)
    resistanceColorGradient.insert(0, color)
