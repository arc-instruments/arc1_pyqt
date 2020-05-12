import os.path
import collections
import inspect
from pkgutil import iter_modules
import importlib.util as imputil
from glob import glob

from PyQt5 import QtGui, QtCore, QtWidgets

from . import state
APP = state.app
HW = state.hardware
CB = state.crossbar

from .Globals import GlobalStyles as STYLE
from .Globals import GlobalFunctions as FUNCS


ModDescriptor = collections.namedtuple('ModDescriptor', \
        ['module', 'name', 'display', 'toplevel', 'callback'])
"""
ModDescriptor describes everything the interface needs to create
programming panels. The fields of this named tuple are

* ``module``: actual module object
* ``name``: name of the module
* ``display``: display label for the tree
* ``toplevel``: toplevel widget for the toplevel tag; can be ``None``
* ``callback``: callback for data display; can be ``None``

Users typically don't need to make descriptors. They will be created
accordingly on program load.
"""

ModTag = collections.namedtuple('ModTag', ['tag', 'name', 'callback'])
"""
A module tag. Every module needs to provide a toplevel tag under a module-local
variable named ``tags``. For instance a module named `TestModule` may have
the following ``tags`` setup.

>>> tags = { 'top': ModTag('TM', 'TestModule', TestModule.showData) }

Additional subtags can be provided if functionality of the modules may be
split in multiple entities (see for example
`arc1pyqt.ProgPanels.MultiStateSeeker`). These can be added as ``subtags``
which is again a list of `ModTag`s. Of course ``subtags`` can be omitted
if no such functionality is wanted (probably for most cases).

>>> tags = {
>>>     'top': ModTag('TM', 'TestModule', None),
>>>     'subtags': [ ModTag('TSM', 'TestSubModule', TestModule.subModData) ]
>>> }

"""


def __registerTagsFromModule(module, kls=None):
    """
    Add all compatible tags for module in the global tag registry. Modules
    that actually want to display something in the GUI should also point the
    the toplevel widget that should be displayed through the ``kls`` variable.
    If ``kls`` is None then ``module`` is a hidden module (read-outs and
    pulses are such).
    """

    # top tag
    top = module.tags['top']
    if top.callback is not None:
        display = "%s*" % top.name
    else:
        display = top.name

    descriptor = ModDescriptor(module, top.name, display, kls, top.callback)
    APP.modules[top.tag] = descriptor

    if 'subtags' not in module.tags.keys():
        return

    for tag in module.tags['subtags']:
        if tag.callback is not None:
            display = "%s*" % tag.name
        else:
            display = tag.name
        descriptor = ModDescriptor(module, tag.name, display, None,\
                tag.callback)
        APP.modules[tag.tag] = descriptor


def discoverModules(paths, namespace=""):
    """
    Discover modules under ``paths`` and load them into the global
    module list if possible. Argument ``namespace`` provides the
    module (either real or not) that these modules will be loaded
    under. If empty they are added to the toplevel module (not
    recommended).

    Compatible modules should

    * Have a set of tags associated with them under the ``tags``
      variable (see `arc1pyqt.modutils.ModTag`).
    * Have a main class with the same name as the name of the
      file (sans the .py extension, obviously). For instance
      TestModule.py should contain a TestModule class as a
      top level entry point.
    * Said class should inherit from `arc1pyqt.modutils.BaseProgPanel`.
    """

    for p in paths:
        for (finder, name, ispkg) in iter_modules([p]):
            if ispkg:
                continue
            loader = finder.find_module(name)
            try:
                if namespace != "":
                    mod_full = '%s.%s' % (namespace, name)
                else:
                    mod_full = name

                spec = imputil.spec_from_file_location(mod_full, loader.path)
                mod = imputil.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # we need a tag defined
                if not hasattr(mod, 'tags'):
                    continue

                # now check containing classes
                for _, kls in inspect.getmembers(mod, inspect.isclass):

                    # entry point should be a class named after the file
                    if kls.__name__ != name:
                        continue

                    # and subclass ``BaseProgPanel``
                    if not issubclass(kls, BaseProgPanel):
                        continue

                    # if we made it here, add the module to the modlist
                    __registerTagsFromModule(mod, kls)

            except Exception as exc:
                print("Exception encountered while importing module")
                continue


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
        maxW = HW.conf.words
        minB = 1
        maxB = HW.conf.bits
    else:
        minW = CB.limits['words'][0]
        maxW = CB.limits['words'][1]
        minB = CB.limits['bits'][0]
        maxB = CB.limits['words'][1]

    # Find how many SA devices are contained in the range
    if CB.checkSA == False:
        for w in range(minW, maxW+1):
            for b in range(minB, maxB+1):
                devices.append([w, b])
    else:
        for w in range(minW, maxW+1):
            for b in range(minB, maxB+1):
                for device in CB.customArray:
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
        if HW.ArC is None:
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


