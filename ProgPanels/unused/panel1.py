import sys
from PyQt4 import QtGui
from PyQt4 import QtCore


class panel1(QtGui.QWidget):
    
    def __init__(self):
        super(panel1, self).__init__()
        self.initUI()
        
    def initUI(self):   
    	palette=QtGui.QPalette()
    	palette.setBrush(QtGui.QPalette.Background, QtGui.QColor(25,25,100))
    	self.setAutoFillBackground(True)
    	self.setPalette(palette)
        
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = panel1()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 