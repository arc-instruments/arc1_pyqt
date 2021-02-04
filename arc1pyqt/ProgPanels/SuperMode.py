from PyQt5 import QtCore, QtGui, QtWidgets
import sys, os
import pickle
import pkgutil
import importlib
import json
import time
import threading

import arc1pyqt.ProgPanels.SMUtils
import arc1pyqt.ProgPanels.SMUtils.Loops
from arc1pyqt.ProgPanels.SMUtils.Loops import Loop, End
from arc1pyqt import Graphics
from arc1pyqt import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from arc1pyqt.Globals import functions, styles, fonts
from arc1pyqt.modutils import BaseThreadWrapper, BaseProgPanel, \
        makeDeviceList, ModTag


progPanelList_basic=[]
progPanelList_basic_loops=[]


mutex = QtCore.QMutex()

# Modules that are not compatible with SuperMode or there
# is no point in trying to run them within that context.
MODULE_BLACKLIST = (
    "arc1pyqt.ProgPanels.SuperMode",
    "arc1pyqt.ProgPanels.CT_LIVE",
    "arc1pyqt.ProgPanels.MultiBias",
)

def _load_modules(mod):

    mods = []
    # List all non-package modules
    for (_, modname, ispkg) in pkgutil.iter_modules(mod.__path__):
        if ispkg:
            continue
        mods.append(".".join([mod.__name__, modname]))

    for x in MODULE_BLACKLIST:
        try:
            mods.remove(x)
        except:
            # that's fine; it probably isn't there
            pass

    return mods


progPanelList_basic = _load_modules(arc1pyqt.ProgPanels.SMUtils)
progPanelList_basic_loops = _load_modules(arc1pyqt.ProgPanels.SMUtils.Loops)


placed_module_height=20


module_id_dict={}
globalID=0


tag = "SM"


class ThreadWrapper(BaseThreadWrapper):
    global mutex

    updateAddress=QtCore.pyqtSignal(int, int)
    globalDisableInterface=QtCore.pyqtSignal(bool)

    execute=QtCore.pyqtSignal(int)

    def __init__(self, mainChain_indexes, deviceList):
        super().__init__()
        self.mainChain_indexes=mainChain_indexes
        self.deviceList=deviceList

    @BaseThreadWrapper.runner
    def run(self):
        self.globalDisableInterface.emit(True)

        for device in self.deviceList:
            self.updateAddress.emit(device[0],device[1])
            self.ping_and_resolveLoops(self.mainChain_indexes)

        self.globalDisableInterface.emit(False)

    def ping_and_resolveLoops(self, chain):
        i=0
        while i<len(chain):
            module=chain[i]
            if isinstance(module, Loop.Loop):
                times=module.loopTimes()
                for endLoopIndex, module_aux in enumerate(reversed(chain)):
                    if module_aux=='End':
                        if self.checkLoopOrder(chain[i+1:len(chain)-endLoopIndex-1]):
                            break
                #print "times= ", times
                for j in range(times):
                    self.ping_and_resolveLoops(chain[i+1:len(chain)-endLoopIndex-1])
                i=len(chain)-endLoopIndex
                #print "i= ", i
            elif module!='End':
                mutex.lock()
                self.execute.emit(module)
                APP.waitCondition.wait(mutex)
                #time.sleep(0.01)
                mutex.unlock()

                i+=1

    def checkLoopOrder(self, chain):
        # Checks the order of Start and End loops.
        sumOfLoops=0
        for module in chain:
            if isinstance(module, Loop.Loop):
                sumOfLoops+=1
            if module=='End':
                sumOfLoops-=1
            if sumOfLoops<0:
                return False
        if sumOfLoops!=0:
            return False
        else:
            return True


class DraggableButton(QtWidgets.QPushButton):

    what="A Button"
    name="A Button"

    def __init__(self, moduleName):
        self.what = moduleName
        self.name = self.what.split(".")[-1]
        super().__init__(self.name)
        self.setStyleSheet("font-size: 7pt; min-height: 15px;")
        if moduleName=='Loop':
            self.setText("Start Loop")
        if moduleName=='End':
            self.setText("End Loop")

        self.setFixedHeight(20)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-module"):
            event.setDropAction(QtCore.Qt.QMoveAction)
            event.accept()
        else:
            event.ignore()

    def startDrag(self, event):
        global globalID

        ## selected is the relevant person object
        self.ID=str(globalID)
        #thisID=QtCore.QByteArray(self.ID)
        thisID=self.ID.encode()
        module_id_dict[self.ID]=self.associate()
        globalID+=1

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-module", thisID)
        #mimeData.setText(self.what)
        mimeData.setText(self.name)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = QtWidgets.QWidget.grab(self)

        drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.setPixmap(pixmap)
        result = drag.exec_(QtCore.Qt.MoveAction)

    def mouseMoveEvent(self, event):
        self.startDrag(event)

    def associate(self):
        thisPanel = importlib.import_module(self.what)
        panel_class = getattr(thisPanel, self.name)
        thisModule = panel_class(short=True)
        return thisModule


class DraggableButtonPlaced(QtWidgets.QPushButton):

    displayModule = QtCore.pyqtSignal(QtWidgets.QWidget)
    deleteContainer = QtCore.pyqtSignal()
    toggle_transparency=QtCore.pyqtSignal(bool)
    decrementCount=QtCore.pyqtSignal()

    what="A Draggable Button"
    def __init__(self, *args):
        super().__init__(*args)
        self.what=args[0]
        try:
            self.module=args[1]
        except:
            self.module=""
        self.setMinimumHeight(placed_module_height)
        width = self.fontMetrics().boundingRect(self.what).width() + 30
        self.setMaximumWidth(width)


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-module-placed"):
            event.setDropAction(QtCore.Qt.QMoveAction)
            event.accept()
        else:
            event.ignore()

    def startDrag(self, event):
        self.setVisible(False)
        self.deleteContainer.emit()
        self.deleteLater()
        selected = self.ID

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-module-placed", selected)
        mimeData.setText(self.what)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = QtWidgets.QWidget.grab(self)

        drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.setPixmap(pixmap)
        result = drag.exec_(QtCore.Qt.MoveAction)

        if result:
            pass
        else:
            self.decrementCount.emit()
            self.setVisible(True)

    def mouseMoveEvent(self, event):
        self.startDrag(event)

    def mouseDoubleClickEvent(self, event):
        self.displayModule.emit(self.module)
        if self.what=="Loop":
            self.setStyleSheet(styles.loop_style_top_selected)
        elif self.what=="End":
            self.setStyleSheet(styles.loop_style_bot_selected)
        else:
            self.setStyleSheet(styles.selectedStyle)


class DraggableLoopPlaced(DraggableButtonPlaced):
    def __init__(self, *args):
        global loop_style_top
        super().__init__(*args)
        self.setStyleSheet(styles.loop_style_top)
        self.setFixedHeight(16)
        self.setFixedWidth(120)
        self.setContentsMargins(0,14,0,0)


class DraggableLoopPlacedEnd(DraggableButtonPlaced):
    def __init__(self, *args):
        global loop_style_top
        super().__init__(*args)
        self.setStyleSheet(styles.loop_style_bot)
        self.setFixedHeight(16)
        self.setFixedWidth(120)
        self.setContentsMargins(0,0,0,14)


class DraggableButtonPlacedDummy(DraggableButtonPlaced):
    def __init__(self, *args):
        super().__init__("")
        self.setStyleSheet(styles.dummy_style)
        self.setFixedWidth(100)


class DropZone(QtWidgets.QWidget):

    routeModule = QtCore.pyqtSignal(QtWidgets.QWidget)

    lastPosition=0
    def __init__(self):
        super().__init__()
        self.setFixedWidth(100)
        self.setMinimumHeight(100)
        self.setAcceptDrops(True)
        #self.setWidgetResizable(True)
        self.initUI()

    def initUI(self):
        self.vbox=QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.Alignment(QtCore.Qt.AlignTop))
        self.vbox.setContentsMargins(0,0,0,0)
        self.vbox.setSpacing(0)
        self.setLayout(self.vbox)
        self.count=0

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-module"):
            self.dummyBtn=DraggableButtonPlacedDummy("Dummy")
            self.setMinimumHeight(placed_module_height*self.count+1)
            event.accept()
        elif event.mimeData().hasFormat("application/x-module-placed"):
            self.dummyBtn=DraggableButtonPlacedDummy("Dummy")
            self.setMinimumHeight(placed_module_height*self.count+1)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-module") or event.mimeData().hasFormat("application/x-module-placed"):
            if event.mimeData().hasFormat("application/x-module"):
                self.setFixedHeight(placed_module_height*(self.count+1))
            elif event.mimeData().hasFormat("application/x-module-placed"):
                self.setFixedHeight(placed_module_height*(self.count))

            event.setDropAction(QtCore.Qt.MoveAction)

            index=''

            widg = self.childAt(event.pos())
            if isinstance(widg, DraggableButtonPlacedDummy):
                pass
            elif isinstance(widg, DraggableButtonPlaced):
                widg2=widg
                widg2.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
                widg=self.childAt(event.pos())
                widg2.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
                index = self.vbox.indexOf(widg)
            elif isinstance(widg, CenterWidget):
                index = self.vbox.indexOf(widg)
            elif isinstance(widg, QtWidgets.QWidget):
                pass

            if index!='':

                self.vbox.insertWidget(index, self.dummyBtn)
                event.accept()

        else:
            event.ignore()

    def dropEvent(self, event):
        data = event.mimeData()

        if event.mimeData().hasFormat("application/x-module"):
            self.count+=1
            index = self.vbox.indexOf(self.dummyBtn)
            self.dummyBtn.deleteLater()

            mod_key = data.data("application/x-module").data().decode()
            #associatedModule=module_id_dict[str(data.data("application/x-module"))]
            associatedModule=module_id_dict[mod_key]
            if data.text() not in ['Loop','End']:
                newBtn=DraggableButtonPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='Loop':
                newBtn=DraggableLoopPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.setText("Start Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='End':
                newBtn=DraggableLoopPlacedEnd(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.setText("End Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)

            newWidget=CenterWidget(newBtn)
            newBtn.deleteContainer.connect(newWidget.deleteContainer)
            newBtn.decrementCount.connect(self.decrement_and_resize)
            self.vbox.insertWidget(index, newWidget)
            self.setMinimumHeight(placed_module_height*self.count)

            event.accept()

        elif event.mimeData().hasFormat("application/x-module-placed"):

            index = self.vbox.indexOf(self.dummyBtn)
            self.dummyBtn.deleteLater()

            associatedModule=module_id_dict[str(data.data("application/x-module-placed"))]

            if data.text() not in ['Loop','End']:
                newBtn=DraggableButtonPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='Loop':
                newBtn=DraggableLoopPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.setText("Start Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='End':
                newBtn=DraggableLoopPlacedEnd(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.setText("End Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            #newBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

            newWidget=CenterWidget(newBtn)
            newBtn.deleteContainer.connect(newWidget.deleteContainer)
            newBtn.decrementCount.connect(self.decrement_and_resize)
            self.vbox.insertWidget(index, newWidget)

            event.accept()

    def decrement_and_resize(self):
        self.count-=1
        self.resizeHeight()

    def resizeHeight(self):
        if self.count*placed_module_height<=placed_module_height:
            self.setFixedHeight(placed_module_height)
        else:
            self.setFixedHeight(self.count*placed_module_height)

    def dragLeaveEvent(self, event):
        self.dummyBtn.deleteLater()

    def routerDisplayModule(self, module):
        self.routeModule.emit(module)
        layoutItems=self.vbox
        for btn in [layoutItems.itemAt(i).widget().btn for i in range(layoutItems.count())]:
            if btn.what=='Loop':
                btn.setStyleSheet(styles.loop_style_top)
            elif btn.what=='End':
                btn.setStyleSheet(styles.loop_style_bot)
            else:
                btn.setStyleSheet(styles.unselectedStyle)


class CenterWidget(QtWidgets.QWidget):
    def __init__(self, btn):
        super().__init__()
        self.setFixedHeight(placed_module_height)
        self.setContentsMargins(0,0,0,0)
        self.btn=btn
        self.initUI()

    def initUI(self):
        layout=QtWidgets.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.btn)
        layout.addStretch()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def deleteContainer(self):
        #self.parent=None
        self.hide()
        self.deleteLater()


class SuperMode(BaseProgPanel):

    def __init__(self):
        super().__init__(\
                title='SuperMode', \
                description='Make sequence of tests', \
                short=False)
        self.initUI()

    def initUI(self):
        global EdgeBtn_style

        mainLayout=QtWidgets.QVBoxLayout()

        hbox=QtWidgets.QHBoxLayout()
        vboxLeft=QtWidgets.QVBoxLayout()
        vboxLeft.setContentsMargins(0,0,0,0)
        vboxLeft.setSpacing(0)

        self.vboxMid=QtWidgets.QVBoxLayout()
        self.dropWidget=DropZone()
        sizePolicy=QtWidgets.QSizePolicy()
        sizePolicy.setVerticalPolicy(QtWidgets.QSizePolicy.Expanding)
        self.dropWidget.setSizePolicy(sizePolicy)

        self.moduleLayout=QtWidgets.QVBoxLayout()

        moduleEdit=QtWidgets.QWidget()
        moduleEdit.setMinimumWidth(500)
        moduleEdit.setLayout(self.moduleLayout)

        moduleViewscrlArea=QtWidgets.QScrollArea()
        moduleViewscrlArea.setWidget(moduleEdit)
        moduleViewscrlArea.setContentsMargins(0,0,0,0)
        moduleViewscrlArea.setWidgetResizable(True)
        moduleViewscrlArea.setMinimumWidth(400)
        moduleViewscrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        moduleViewscrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        #moduleViewscrlArea.installEventFilter(self)

        separator1=QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.HLine)
        separator1.setLineWidth(2)

        separator2=QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.HLine)
        separator2.setLineWidth(2)

        separator3=QtWidgets.QFrame()
        separator3.setFrameShape(QtWidgets.QFrame.HLine)
        separator3.setLineWidth(2)

        for (_, modinfo) in APP.modules.items():
            if modinfo.module is None or modinfo.toplevel is None:
                continue
            if modinfo.module.__name__.startswith(MODULE_BLACKLIST):
                continue
            btn = DraggableButton(modinfo.module.__name__)
            vboxLeft.addWidget(btn)

        vboxLeft.addWidget(separator1)

        for module in progPanelList_basic:
            btn=DraggableButton(module)
            vboxLeft.addWidget(btn)
        vboxLeft.addWidget(separator2)

        progPanelList_basic_loops.reverse()
        for module in progPanelList_basic_loops:
            btn=DraggableButton(module)
            vboxLeft.addWidget(btn)
        vboxLeft.addWidget(separator3)

        vboxLeft.addStretch()

        push_save = QtWidgets.QPushButton("Save")
        push_save.clicked.connect(self.saveSequence)
        push_save.setStyleSheet(styles.btnStyle2)
        push_load = QtWidgets.QPushButton("Load")
        push_load.clicked.connect(self.loadSequence)
        push_load.setStyleSheet(styles.btnStyle2)

        self.loaded_label = QtWidgets.QLabel()
        self.loaded_label.setStyleSheet(styles.style1)

        vboxLeft.addWidget(self.loaded_label)
        vboxLeft.addWidget(push_load)
        vboxLeft.addWidget(push_save)

        startBtn=QtWidgets.QPushButton("Start")
        startBtn.setStyleSheet(styles.EdgeBtn_style)
        startWidg=CenterWidget(startBtn)

        stopBtn=QtWidgets.QPushButton("End")
        stopBtn.setStyleSheet(styles.EdgeBtn_style)
        stopWidg=CenterWidget(stopBtn)

        self.vboxMid.addWidget(startWidg)
        self.vboxMid.addWidget(self.dropWidget)
        self.vboxMid.addWidget(stopWidg)
        self.vboxMid.addStretch()

        self.vboxMid.setAlignment(QtCore.Qt.Alignment(QtCore.Qt.AlignTop))

        self.containerWidget=QtWidgets.QWidget()
        self.containerWidget.setLayout(self.vboxMid)
        self.containerWidget.setSizePolicy(sizePolicy)
        #containerWidget.setSizePolicy(sizePolicy)

        self.scrlArea=QtWidgets.QScrollArea()
        self.scrlArea.setWidget(self.containerWidget)
        self.scrlArea.setContentsMargins(0,0,0,0)
        self.scrlArea.setWidgetResizable(True)
        self.scrlArea.setFixedWidth(140)
        self.scrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        hbox.addLayout(vboxLeft)
        hbox.addWidget(self.scrlArea)
        hbox.addWidget(moduleViewscrlArea)

        vboxLeft.addStretch()

        clearBtn=QtWidgets.QPushButton("Clear")
        clearBtn.setStyleSheet(styles.btnStyle_clearChain)
        clearBtn.clicked.connect(self.clearChain)

        vboxLeft.addWidget(clearBtn)

        self.dropWidget.routeModule.connect(self.displayModule)

        self.hboxProg=QtWidgets.QHBoxLayout()

        push_single=QtWidgets.QPushButton('Apply to One')
        push_range=QtWidgets.QPushButton('Apply to Range')
        push_all=QtWidgets.QPushButton('Apply to All')

        push_single.setStyleSheet(styles.btnStyle)
        push_range.setStyleSheet(styles.btnStyle)
        push_all.setStyleSheet(styles.btnStyle)

        push_single.clicked.connect(self.programOne)
        push_range.clicked.connect(self.programRange)
        push_all.clicked.connect(self.programAll)

        self.hboxProg.addWidget(push_single)
        self.hboxProg.addWidget(push_range)
        self.hboxProg.addWidget(push_all)

        #mainLayout.addWidget(titleLabel)
        mainLayout.addLayout(hbox)
        mainLayout.addLayout(self.hboxProg)

        self.setLayout(mainLayout)
        self.show()

    def saveSequence(self):

        filters = ['Test sequence (*.json)', 'All files (*.*)']

        layout = self.dropWidget.vbox
        items = [layout.itemAt(i).widget().btn.module for i in range(layout.count())]

        if not self.checkLoopOrder(items):
            self.throw_wrong_loops_dialogue()
            return

        if APP.workingDirectory:
            curDir = APP.workingDirectory
        else:
            curDir = ''

        (saveFileName, fltr) = QtWidgets.QFileDialog.getSaveFileName(self,
            'Save File', curDir, ';;'.join(filters))

        if (not saveFileName) or (len(saveFileName) == 0):
            return

        if (fltr == filters[0]) and (not saveFileName.lower().endswith('.json')):
            finalSaveFileName = saveFileName + ".json"
        else:
            finalSaveFileName = saveFileName

        chainList = []
        for mod in items:
            fullmodname = ".".join([
                mod.__class__.__module__,
                mod.__class__.__name__])
            chainList.append([fullmodname, mod.extractPanelData()])

        if os.path.exists(finalSaveFileName):
            res = QtWidgets.QMessageBox.question(self, '',
                "File %s exists. Overwrite?" % finalSaveFileName,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if res == QtWidgets.QMessageBox.No:
                return

        with open(finalSaveFileName, 'w') as f:
            json.dump(chainList, f)

    def loadSequence(self):
        global globalID
        proceed = False

        filters = ['Test sequence (*.json)', 'All files (*.*)']

        if self.dropWidget.vbox.count() > 0:
            reply = QtWidgets.QMessageBox.question(self,
                "Load a measurement chain",
                "Loading a chain will replace the current one. Continue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.Yes:
                return

        for i in reversed(range(self.dropWidget.vbox.count())):
            self.dropWidget.vbox.itemAt(i).widget().setParent(None)

        self.dropWidget.count = 0
        self.dropWidget.resizeHeight()
        self.dropWidget.routerDisplayModule(None)
        self.dropWidget.update()

        try:
            path = QtCore.QFileInfo(QtWidgets.QFileDialog().\
                getOpenFileName(self, 'Load file', '',
                filter=';;'.join(filters))[0])
        except IndexError:
            return

        name = path.fileName()
        self.loaded_label.setText(name)

        with open(path.filePath(), 'rb') as inputFile:
            chainList = json.load(inputFile)

        globalID = 0

        for (modpath, data) in chainList:
            if modpath is None:
                continue

            (modname, classname) = modpath.rsplit('.', 1)
            panelMod = importlib.import_module(modname)
            klass = getattr(panelMod, classname)
            panel = klass(short=True)
            panel.setPanelData(data)

            if classname == 'Loop':
                newBtn = DraggableLoopPlaced(classname, panel)
                newBtn.setText("Start Loop")
            elif classname == 'End':
                newBtn = DraggableLoopPlacedEnd(classname, panel)
                newBtn.setText("End Loop")
            else:
                newBtn = DraggableButtonPlaced(classname, panel)

            newBtn.ID = str(globalID).encode()
            module_id_dict[newBtn.ID] = panel

            newBtn.displayModule.connect(self.dropWidget.routerDisplayModule)

            newCenterWidget = CenterWidget(newBtn)
            newBtn.deleteContainer.connect(newCenterWidget.deleteContainer)
            newBtn.decrementCount.connect(self.dropWidget.decrement_and_resize)

            self.dropWidget.vbox.addWidget(newCenterWidget)
            globalID += 1

        self.dropWidget.count = self.dropWidget.vbox.count()
        self.dropWidget.resizeHeight()
        self.dropWidget.update()

    def displayModule(self, module):
        try:
            # delete previous widget
            self.moduleLayout.itemAt(0).widget().setParent(None)
        except:
            pass
        self.moduleLayout.addWidget(module)

    def extractModuleChain(self):
        layoutItems=self.dropWidget.vbox
        items = [layoutItems.itemAt(i).widget().btn.module for i in range(layoutItems.count())]
        result=self.checkLoopOrder(items)
        if result:
            mainChain_indexes=[]
            self.mainChain=items
            for i, module in enumerate(items):
                if isinstance(module, Loop.Loop):
                    mainChain_indexes.append(module)
                elif isinstance(module, End.End):
                    mainChain_indexes.append('End')
                else:
                    mainChain_indexes.append(i)
            return mainChain_indexes
        else:
            return False

    def checkLoopOrder(self, items):

        # every loop start represents a 1
        # every loop end represents a -1
        # if at any point is the sum <0 after iterating through all items in the chain
        # then the loop start and ends are misplaced

        sumOfLoops=0
        for module in items:
            if isinstance(module, Loop.Loop):
                sumOfLoops+=1
            if isinstance(module, End.End):
                sumOfLoops-=1
            if sumOfLoops<0:
                return False
        if sumOfLoops!=0:
            return False
        else:
            return True

    def clearChain(self):

        reply = QtWidgets.QMessageBox.Yes

        if self.dropWidget.vbox.count()>0:
            reply = QtWidgets.QMessageBox.question(self, "Clear chain",
                "Are you sure?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Yes:
            for i in reversed(range(self.dropWidget.vbox.count())):
                self.dropWidget.vbox.itemAt(i).widget().setParent(None)

            self.dropWidget.count=0
            self.dropWidget.resizeHeight()
            self.dropWidget.routerDisplayModule(None)
            self.loaded_label.setText("")

    def throw_wrong_loops_dialogue(self):
        reply = QtWidgets.QMessageBox.question(self, "Wrong chain loops",
            "There is something wrong with the ordering of the Start and End loops. Please check.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)

    def programOne(self):
        devs = [[CB.word, CB.bit]]
        self.programDevs(devs)

    def programRange(self):
        devs = makeDeviceList(True)
        self.programDevs(devs)

    def programAll(self):
        devs = makeDeviceList(False)
        self.programDevs(devs)

    def programDevs(self, devs):
        if HW.ArC is None:
            return

        mainChain_indexes = self.extractModuleChain()

        if mainChain_indexes == False:
            self.throw_wrong_loops_dialogue()
        else:
            self.thread = QtCore.QThread()
            self.threadWrapper = ThreadWrapper(mainChain_indexes, devs)
            self.finalise_thread_initialisation()
            self.thread.start()

    def finalise_thread_initialisation(self):
        self.threadWrapper.moveToThread(self.thread)
        self.thread.started.connect(self.threadWrapper.run)
        self.threadWrapper.finished.connect(self.thread.quit)
        self.threadWrapper.finished.connect(self.threadWrapper.deleteLater)
        self.thread.finished.connect(self.threadWrapper.deleteLater)
        self.threadWrapper.updateAddress.connect(functions.addressAntenna.update)
        self.threadWrapper.globalDisableInterface.connect(functions.interfaceAntenna.toggleGlobalDisable)
        self.threadWrapper.disableInterface.connect(functions.interfaceAntenna.cast)
        self.threadWrapper.execute.connect(self.singleExecute)

    def singleExecute(self, index):
        #print "###### EXECUTING ", index
        #time.sleep(0.001)
        self.mainChain[index].programOne()


tags = { 'top': ModTag(tag, "SuperMode", None) }
