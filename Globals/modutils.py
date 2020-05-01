from PyQt5 import QtGui, QtCore, QtWidgets

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


