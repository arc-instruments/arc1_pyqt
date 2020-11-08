import sys
import os
import os.path
import subprocess
from functools import partial
from PyQt5 import QtCore, QtWidgets

from ..Globals import styles


class ModulePathWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(QtWidgets.QLabel(
            '<strong>'+
            'ArC ONE will look for modules in these directories'+
            '</strong>'))
        layout.addWidget(QtWidgets.QLabel(
            'Directories will be created if they do not exist'))

        paths = QtCore.QStandardPaths.standardLocations(
            QtCore.QStandardPaths.AppDataLocation)

        for p in paths:
            path = os.path.join(p, 'ProgPanels')
            container = QtWidgets.QHBoxLayout()
            container.setSpacing(20)
            label = QtWidgets.QLabel(path)
            label.setStyleSheet("""QLabel { font-family: monospace; }""")
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.Maximum)
            label.setSizePolicy(sizePolicy)
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse |
                QtCore.Qt.TextSelectableByKeyboard)
            container.addWidget(label)

            button = QtWidgets.QPushButton("Open")
            button.setMinimumWidth(50)
            button.setStyleSheet(styles.btnStyle2)
            button.clicked.connect(partial(self.onButtonClicked, path))
            container.addWidget(button)
            layout.addItem(container)

        self.setLayout(layout)

    def onButtonClicked(self, path):

        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as exc:
                msg = 'Folder was not found and could not be created'
                box = QtWidgets.QMessageBox()
                box.setIcon(QtWidgets.QMessageBox.Critical)
                box.setText(msg)
                box.setWindowTitle("Error")
                box.exec_()
                return

        if sys.platform == 'win32':
            os.startfile(os.path.normpath(path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', os.path.normpath(path)], check=True)
        else:
            # fall back to xdg-open for most unix-likes
            subprocess.run(['xdg-open', os.path.normpath(path)], check=True)

    @staticmethod
    def modulePathDialog():
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Module paths")
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(ModulePathWidget(dialog))
        dialog.setLayout(layout)

        return dialog
