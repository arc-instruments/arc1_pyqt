import sys
import os.path
import collections
import inspect
from pkgutil import iter_modules
import importlib.util as imputil
from glob import glob
from functools import partial
import itertools

from PyQt5 import QtGui, QtCore, QtWidgets

from . import state
APP = state.app
HW = state.hardware
CB = state.crossbar

from .Globals import styles, functions


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


def discoverModules(paths, namespace="", force_register=False):
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
            loader = finder.find_module(name)
            try:
                if namespace != "":
                    mod_full = '%s.%s' % (namespace, name)
                else:
                    mod_full = name

                spec = imputil.spec_from_file_location(mod_full, loader.path)
                mod = imputil.module_from_spec(spec)
                spec.loader.exec_module(mod)

                if ispkg and force_register:
                    if mod_full not in sys.modules.keys():
                        sys.modules[mod_full] = mod

                # now check containing classes
                for _, kls in inspect.getmembers(mod, inspect.isclass):

                    # entry point should be a class named after the file
                    if kls.__name__ != name:
                        continue

                    # and subclass ``BaseProgPanel``
                    if not issubclass(kls, BaseProgPanel):
                        continue

                    # if we made it here, add the module to the modlist
                    # if it has the correct tag
                    if hasattr(mod, 'tags'):
                        __registerTagsFromModule(mod, kls)

                # if this is a package; descend into it to discover further modules
                if ispkg:
                    if namespace != "":
                        discoverModules([os.path.join(p, name)],
                            '%s.%s' % (namespace, name))
                    else:
                        discoverModules([os.path.join(p, name)], namespace)


            except Exception as exc:
                print("Exception encountered while importing module", exc)
                continue


def compile_ui(src, dst, force=False, from_imports=True, rc_suffix='_rc'):
    """
    Compile a Qt Designer UI file (`src`) into a loadable python file (`dst`).
    This function will only generate the file if `src` is newer than `dst`
    unless `force` is set to `True`. This is a convenient wrapper around
    ``PyQt5.uic`` and can be quite convenient when an external module uses
    a UI file. For instance the following snippet will ensure that UI file
    `sample.ui` always generates `sample.py` before it is imported into
    the main module.

    >>> from os.path import join, dirname
    >>> from arc1pyqt.modutils import compile_ui
    >>> # get directory of present module
    >>> THIS_DIR = dirname(__file__)
    >>> # and compile it
    >>> compile_ui(join(THIS_DIR, 'sample.ui'), join(THIS_DIR, 'sample.py'))
    >>> # module sample now exists
    >>> from .sample import *

    There are two additional options that mirror ``PyQt5.uic`` behaviour.
    The first is `from_imports` which is used to generate imports relative
    to the package that hosts the UI file. By default this is true as most
    resource will probably be package-local. The second is `rc_suffix` which
    will be appended to any resource modules used by the (see also
    ``compile_rc``) UI file. By default this again mirrors ``PyQt5.uic``
    behaviour and it is `_rc`, but can be override if so required.
    """

    import PyQt5.uic as uic

    if os.path.exists(dst) and not force:
        src_mtime = os.path.getmtime(src)
        dst_mtime = os.path.getmtime(dst)

        if dst_mtime >= src_mtime:
            return

    with open(dst, 'w', encoding='utf-8') as out:
        uic.compileUi(src, out, execute=False, indent=4,
            from_imports=from_imports, resource_suffix=rc_suffix)


def compile_rc(files, dst, force=False):
    """
    Compile a list of Qt Designer resource files (qrc) `files` to a python
    module (`dst`). Similar to ``compile_ui`` this is a convenient wrapper
    around ``PyQt5.pyrcc_main``. Target will not be overwritten if it's
    newer than all of the input qrc files unless `force` is set to True.
    Input argument (`files`) can either be a string (for a single qrc file)
    or a list of strings (for many qrc files). Note that if you are using
    qrc file with Qt Designer target module MUST end in `_rc` unless a
    different suffix has been specified when invoking ``compile_ui``.

    So if a UI file (`sample.ui`) is to be compiled into a python module
    (`sample.py`) and makes use of a resources files (`sample.rc`) the
    following snippet will ensure that these are in sync when the module
    is loaded (using the default options).

    >>> from os.path import join, dirname
    >>> from arc1pyqt.modutils import compile_ui, compile_rc
    >>> # get directory of present module
    >>> THIS_DIR = dirname(__file__)
    >>> # and compile it
    >>> compile_ui(join(THIS_DIR, 'sample.ui'), join(THIS_DIR, 'sample.py'))
    >>> compile_rc(join(THIS_DIR, 'sample.qrc'), join(THIS_DIR, 'sample_rc.py'))
    >>> # module sample now exists and its resources are loaded properly
    >>> from .sample import *
    """

    from collections.abc import Iterable
    import PyQt5.pyrcc_main as rcc

    # ensure `files` is a list
    if not isinstance(files, Iterable) or isinstance(files, str):
        files = [files]

    overwrite = False

    if os.path.exists(dst) and not force:
        dst_mtime = os.path.getmtime(dst)
        for f in files:
            src_mtime = os.path.getmtime(f)
            # check if rc file is newer than destination
            if src_mtime > dst_mtime:
                # if yes, destination must be recreated
                overwrite = True
                break
    else:
        overwrite = True

    if overwrite:
        rcc.processResourceFile(files, dst, False)


def makeDeviceList(isRange):
    """
    Generate a list of crosspoints to apply a function. Setting ``isRange`` to
    ``True`` will generate a device list containing only the devices selected
    in the main crossbar panel; ``False`` will return all the devices in the
    crossbar.
    """

    if isRange == False:
        (minW, maxW) = (1, HW.conf.words)
        (minB, maxB) = (1, HW.conf.bits)
    else:
        (minW, maxW) = CB.limits['words']
        (minB, maxB) = CB.limits['bits']

    all_devices = itertools.product(range(minW, maxW+1), range(minB, maxB+1))

    # Find how many SA devices are contained in the range
    if not CB.checkSA:
        return list(all_devices)
    else:
        return [cell for cell in all_devices if cell in CB.customArray]


class BaseProgPanel(QtWidgets.QWidget):

    def __init__(self, title, description="", short=False):
        super().__init__()
        self.title = title
        self.description = description
        self.short = short
        self.propertyWidgets = {}
        self.thread = None
        self._deferredUpdates = {}

    def execute(self, wrapper, entrypoint=None, deferredUpdate=False):
        """
        This function schedules a wrapper for execution taking care of the
        standard signals. The wrapped action (`wrapper`) will be passed
        along a thread which will call the `entrypoint` function of
        `wrapper`. If `entrypoint` is None the default `wrapper.run`
        entrypoint will be used. Argument `deferredUpdate` prevents the history
        tree from updating until the thread operation has finished. This can
        be useful in situations where multiple different devices are used or
        when a module uses many individual operations that would otherwise
        trigger a tree update (for instance hundreds of reads/pulses over
        ten different devices).
        """
        if (HW.ArC is None) or (self.thread is not None):
            return

        if entrypoint is None:
            entrypoint = wrapper.run

        self.threadWrapper = wrapper
        self.thread = QtCore.QThread()

        # When deferring tree updates store current point in history for the
        # whole crossbar. Once the operation is finished the history tree will
        # then be populated starting from this point in history
        if deferredUpdate:
            for (r, row) in enumerate(CB.history):
                for (c, col) in enumerate(row):
                    self._deferredUpdates['%d%d' % (r, c)] = (r, c, len(col))

        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(entrypoint)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.sendData.connect(functions.updateHistory)
        self.threadWrapper.highlight.connect(functions.cbAntenna.cast)
        self.threadWrapper.displayData.connect(functions.displayUpdate.cast)
        if not deferredUpdate:
            self.threadWrapper.updateTree.connect(\
                functions.historyTreeAntenna.updateTree.emit)
        self.threadWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
        self.thread.finished.connect(partial(self._onThreadFinished, deferredUpdate))
        self.thread.start()

    def _onThreadFinished(self, deferredUpdate=False):
        """ Clean up running threads and wake up the interface """
        if self.thread is None:
            return

        functions.interfaceAntenna.wakeUp()
        self.thread.wait()
        self.threadWrapper.deleteLater()
        self.threadWrapper = None
        self.thread = None

        # If updates were deferred do them now in batch
        if deferredUpdate:
            for (_, (w, b, idx)) in self._deferredUpdates.items():
                functions.historyTreeAntenna.updateTree_batch.emit(w, b, idx)
            self._deferredUpdates.clear()

    def registerPropertyWidget(self, wdg, name):
        """
        Register a widget owned by this panel as a save-able property. If `wdg`
        is one of ``QtWidgets.QLineEdit``, ``QtWidgets.QComboBox``,
        ``QtWidgets.QCheckBox``, ``QtWidgets.QSpinBox`` and
        ``QtWidgets.QDoubleSpinBox`` their values will reinstated when
        `BaseProgPanel.setPanelData` is called. Also see
        `BaseProgPanel.extractPanelData`.
        """
        self.propertyWidgets[name] = wdg
        wdg.setProperty("key", name)

    def extractPanelData(self):
        """
        Iterate through all widgets registered as save-able with
        `BaseProgPanel.registerPropertyWidget` and collect their current
        values. This function will automatically process common widgets:
        ``QtWidgets.QLineEdit``, ``QtWidgets.QComboBox``,
        ``QtWidgets.QCheckBox``, ``QtWidgets.QSpinBox`` and
        ``QtWidgets.QDoubleSpinBox``.  If further data needs to be saved child
        widgets must override this functions

        >>> def extractPanelData(self):
        >>>     # call superclass function
        >>>     data = super().extractPanelData()
        >>>     data["foo"] = "bar"
        >>>     # more data collection
        >>>     return data
        """

        items = {}

        for (_, item) in self.propertyWidgets.items():
            key = item.property("key")
            wdg = item
            if key is None:
                continue

            if isinstance(item, QtWidgets.QLineEdit):
                data = wdg.text()
            elif isinstance(item, QtWidgets.QComboBox):
                data = wdg.currentIndex()
            elif isinstance(item, QtWidgets.QCheckBox):
                data = wdg.checkState()
            elif isinstance(item, QtWidgets.QSpinBox) or \
                isinstance(item, QtWidgets.QDoubleSpinBox):
                data = wdg.value()
            else:
                data = None

            if data is not None:
                items[key] = data

        return items

    def setPanelData(self, data):
        """
        Restore widget values from the dict `data`. Field keys are the same as
        defined with `BaseProgPanel.registerPropertyWidget`.  This function
        will only process common widgets: ``QtWidgets.QLineEdit``,
        ``QtWidgets.QComboBox``, ``QtWidgets.QCheckBox``,
        ``QtWidgets.QSpinBox`` and ``QtWidgets.QDoubleSpinBox``. If further
        state is required to be recovered from `data` child panels should
        override this function

        >>> def setPanelData(self, data):
        >>>     super().setPanelData(data)
        >>>     do_smth_with(data["key"])
        """

        for (k, value) in data.items():
            wdg = self.propertyWidgets.get(k, None)
            if wdg is None:
                continue

            if isinstance(wdg, QtWidgets.QLineEdit):
                wdg.setText(value)
            elif isinstance(wdg, QtWidgets.QComboBox):
                wdg.setCurrentIndex(value)
            elif isinstance(wdg, QtWidgets.QCheckBox):
                wdg.setChecked(value)
            elif isinstance(wdg, QtWidgets.QSpinBox) or \
                isinstance(wdg, QtWidgets.QDoubleSpinBox):
                wdg.setValue(value)

    def makeControlButton(self, text, slot=None):
        btn = QtWidgets.QPushButton(text)
        btn.setStyleSheet(styles.btnStyle)
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
        """
        Decorator used to signify a runnable function within a custom measuring
        thread as described in `BaseThreadWrapper`.
        """
        def inner(self):
            self.disableInterface.emit(True)
            func(self)
            self.disableInterface.emit(False)
            self.finished.emit()
            self.displayData.emit()
        return inner


