####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

from PyQt5.QtGui import QFont

font1 = QFont()
font1.setPointSize(12)
font1.setBold(True)

font2 = QFont()
font2.setPointSize(10)
font2.setBold(False)

font3 = QFont()
font3.setPointSize(9)
font3.setBold(False)

history_child = QFont()
history_child.setPointSize(8)
history_child.setBold(False)

history_top = QFont()
history_top.setPointSize(10)
history_top.setBold(True)

history_top_underline = QFont()
history_top_underline.setPointSize(10)
history_top_underline.setBold(True)
history_top_underline.setUnderline(True)
