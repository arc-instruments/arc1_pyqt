from PyQt5 import QtGui, QtCore, QtWidgets

import Globals.GlobalVars as VARS
import Globals.GlobalStyles as STYLE
import Globals.GlobalFunctions as FUNCS


def makeDeviceList(isRange):
    """
    Generate a list of crosspoints to apply a function. Setting ``isRange`` to
    ``True`` will generate a device list containing only the devices selected
    in the main crossbar panel; ``False`` will return all the devices in the
    crossbar.
    """

    devices = []

    if isRange == False:
        minW = 1
        maxW = VARS.wline_nr
        minB = 1
        maxB = VARS.bline_nr
    else:
        minW = VARS.minW
        maxW = VARS.maxW
        minB = VARS.minB
        maxB = VARS.maxB

    # Find how many SA devices are contained in the range
    if VARS.checkSA == False:
        for w in range(minW, maxW+1):
            for b in range(minB, maxB+1):
                devices.append([w, b])
    else:
        for w in range(minW, maxW+1):
            for b in range(minB, maxB+1):
                for device in VARS.customArray:
                    if (device[0] == w and device[1] == b):
                        devices.append(device)

    return devices


class BaseProgPanel(QtWidgets.QWidget):

    def __init__(self, title, description="", short=False):
        super().__init__()
        self.title = title
        self.description = description
        self.short = short

    def execute(self, wrapper, entrypoint=None):
        """
        This functions schedules a wrapper for execution taking care of the
        standard signals. The wrapped action (``wrapper``) will be passed
        along a thread which will call the ``entrypoint`` function of
        ``wrapper``. If ``entrypoint`` is None the default ``wrapper.run``
        entrypoint will be used.
        """
        if VARS.ser.port is None:
            return

        if entrypoint is None:
            entrypoint = wrapper.run

        self.threadWrapper = wrapper
        self.thread = QtCore.QThread()

        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(entrypoint)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.sendData.connect(FUNCS.updateHistory)
        self.threadWrapper.highlight.connect(FUNCS.cbAntenna.cast)
        self.threadWrapper.displayData.connect(FUNCS.displayUpdate.cast)
        self.threadWrapper.updateTree.connect(FUNCS.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(FUNCS.interfaceAntenna.cast)
        self.thread.finished.connect(self._onThreadFinished)
        self.thread.start()

    def _onThreadFinished(self):
        """ Clean up running threads and wake up the interface """
        if self.thread is None:
            return

        FUNCS.interfaceAntenna.wakeUp()
        self.thread.wait()
        self.threadWrapper.deleteLater()
        self.threadWrapper = None
        self.thread = None

    def makeControlButton(self, text, slot=None):
        btn = QtWidgets.QPushButton(text)
        btn.setStyleSheet(STYLE.btnStyle)
        if slot is not None:
            btn.clicked.connect(slot)
        return btn


class BaseThreadWrapper(QtCore.QObject):
    """
    Base class for runnable objects that takes care of allocating the
    signals and enabling/disabling the interface as needed. Subclasses
    should still emit the ``displayData`` or ``updateTree`` signals to
    force interface update. This is intentional because the way data are
    communicated to the interface is application dependent.

    Subclasses only need to decorate the target runner function with the
    ``BaseThreadWrapper.runner`` decorator. For instance

    >>> class ModuleThreadWrapper(BaseThreadWrapper):
    >>>     def __init__(self):
    >>>         super().__init__()
    >>>
    >>>     @BaseThreadWrapper.runner
    >>>     def do_stuff(self):
    >>>         do_some_number_crunching()

    The run function can then be connected to the ``start`` signal of a
    QThread as usual.
    """

    finished = QtCore.pyqtSignal()
    """ Process has finished """
    sendData = QtCore.pyqtSignal(int, int, float, float, float, str)
    """ Transfer data to be written to the session log """
    highlight = QtCore.pyqtSignal(int, int)
    """ Highlight a device in the crossbar view """
    displayData = QtCore.pyqtSignal()
    """ Force data display update """
    updateTree = QtCore.pyqtSignal(int, int)
    """ Force device tree update """
    disableInterface = QtCore.pyqtSignal(bool)
    """ Toggle interface interaction """

    def runner(func):
        def inner(self):
            self.disableInterface.emit(True)
            func(self)
            self.disableInterface.emit(False)
            self.finished.emit()
            self.displayData.emit()
        return inner


