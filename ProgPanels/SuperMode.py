from PyQt4 import QtCore, QtGui
import sys, os
import pickle
import importlib
import pickle

sys.path.append(os.path.abspath(os.getcwd()+'/ProgPanels/'))
sys.path.append(os.path.abspath(os.getcwd()+'/ProgPanels/Basic/'))
sys.path.append(os.path.abspath(os.getcwd()+'/ProgPanels/Basic/Loops'))

import Loop
import End


import GlobalFonts as fonts
import GlobalFunctions as f
import GlobalVars as g
import GlobalStyles as s

progPanelList=[]
progPanelList_basic=[]
progPanelList_basic_loops=[]

def loadProgModules():
    files = [f for f in os.listdir('ProgPanels') if f.endswith(".py")]  # populate prog panel dropbox
    for f in files:
        progPanelList.append(f[:-3])
    progPanelList.remove("SuperMode")
    print progPanelList
loadProgModules()

def loadProgModules_basic():
    files = [f for f in os.listdir('ProgPanels/Basic/') if f.endswith(".py")]  # populate prog panel dropbox
    for f in files:
        progPanelList_basic.append(f[:-3])
    print progPanelList_basic
loadProgModules_basic()

def loadProgModules_basic_loops():
    files = [f for f in os.listdir('ProgPanels/Basic/Loops') if f.endswith(".py")]  # populate prog panel dropbox
    for f in files:
        progPanelList_basic_loops.append(f[:-3])
    print progPanelList_basic_loops
loadProgModules_basic_loops()

placed_module_height=20

module_id_dict={}
globalID=0



tag="SM"
g.tagDict.update({tag:"SuperMode"})

class getData(QtCore.QObject):

    finished=QtCore.pyqtSignal()

    updateAddress=QtCore.pyqtSignal(int, int)
    disableInterface=QtCore.pyqtSignal(bool)
    changeArcStatus=QtCore.pyqtSignal(str)
    globalDisableInterface=QtCore.pyqtSignal(bool)

    execute=QtCore.pyqtSignal(int)

    def __init__(self,mainChain_indexes, deviceList):
        super(getData,self).__init__()
        self.mainChain_indexes=mainChain_indexes
        self.deviceList=deviceList

    def getIt(self):
        self.disableInterface.emit(True)
        self.globalDisableInterface.emit(True)

        global tag

        for device in self.deviceList:
            self.updateAddress.emit(device[0],device[1])
            self.ping_and_resolveLoops(self.mainChain_indexes)

        self.globalDisableInterface.emit(False)
        self.disableInterface.emit(False)
        
        self.finished.emit()

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
                print "times= ", times
                for j in range(times):
                    self.ping_and_resolveLoops(chain[i+1:len(chain)-endLoopIndex-1])
                i=len(chain)-endLoopIndex
                print "i= ", i
            elif module!='End':
                self.execute.emit(module)
                g.mutex.lock()
                g.waitCondition.wait(g.mutex)
                g.mutex.unlock()
                i+=1

    def checkLoopOrder(self, chain):
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

class draggableButton(QtGui.QPushButton):

    what="A Button"

    def __init__(self, moduleName):
        super(draggableButton,self).__init__(moduleName)
        self.what=moduleName
        if moduleName=='Loop':
            self.setText("Start Loop")
        if moduleName=='End':
            self.setText("End Loop")

        self.setFixedHeight(20)
        #super(draggableButton,self).setDragEnabled(True)
        

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
        thisID=QtCore.QByteArray(self.ID)
        module_id_dict[self.ID]=self.associate()
        print "Placed with id ", self.ID, " associated with ", module_id_dict[self.ID]
        globalID+=1

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-module", thisID)
        mimeData.setText(self.what)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = QtGui.QPixmap()
        pixmap = pixmap.grabWidget(self)
        drag.setPixmap(pixmap)

        drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.setPixmap(pixmap)
        result = drag.start(QtCore.Qt.MoveAction)
        #if result: # == QtCore.Qt.MoveAction:
            #self.model().removeRow(index.row())

    def mouseMoveEvent(self, event):
        self.startDrag(event)

    def associate(self):
        thisPanel = importlib.import_module(self.what)     # import the module
        panel_class = getattr(thisPanel, self.what)        # get it's main class 
        thisModule = panel_class(short=True)
        return thisModule

class draggableButtonPlaced(QtGui.QPushButton):

    displayModule = QtCore.pyqtSignal(QtGui.QWidget)
    deleteContainer = QtCore.pyqtSignal()
    toggle_transparency=QtCore.pyqtSignal(bool)
    decrementCount=QtCore.pyqtSignal()

    what="A Draggable Button"
    def __init__(self, *args):
        super(draggableButtonPlaced,self).__init__(*args)
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
        selected = QtCore.QByteArray(self.ID)

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-module-placed", selected)
        mimeData.setText(self.what)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = QtGui.QPixmap()
        pixmap = pixmap.grabWidget(self)
        drag.setPixmap(pixmap)

        drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.setPixmap(pixmap)
        result = drag.start(QtCore.Qt.MoveAction)

        if result:
            pass
            print "result exists"
        else:
            self.decrementCount.emit()
            self.setVisible(True)

    def mouseMoveEvent(self, event):
        self.startDrag(event)

    def mouseDoubleClickEvent(self, event):
        self.displayModule.emit(self.module)
        if self.what=="Loop":
            self.setStyleSheet(s.loop_style_top_selected)
        elif self.what=="End":
            self.setStyleSheet(s.loop_style_bot_selected)
        else: 
            self.setStyleSheet(s.selectedStyle)
        print self.module, " emitted"

class draggableLoopPlaced(draggableButtonPlaced):
    def __init__(self, *args):
        global loop_style_top
        super(draggableLoopPlaced,self).__init__(*args)
        self.setStyleSheet(s.loop_style_top)
        self.setFixedHeight(16)
        self.setFixedWidth(120)
        self.setContentsMargins(0,14,0,0)

class draggableLoopPlacedEnd(draggableButtonPlaced):
    def __init__(self, *args):
        global loop_style_top
        super(draggableLoopPlacedEnd,self).__init__(*args)
        self.setStyleSheet(s.loop_style_bot)
        self.setFixedHeight(16)
        self.setFixedWidth(120)
        self.setContentsMargins(0,0,0,14)

class draggableButtonPlacedDummy(draggableButtonPlaced):
    def __init__(self, *args):
        super(draggableButtonPlacedDummy,self).__init__("")
        self.setStyleSheet(s.dummy_style)
        self.setFixedWidth(100)

class dropZone(QtGui.QWidget):

    routeModule = QtCore.pyqtSignal(QtGui.QWidget)

    lastPosition=0
    def __init__(self):
        super(dropZone, self).__init__()
        self.setFixedWidth(100)
        self.setMinimumHeight(100)
        self.setAcceptDrops(True)
        #self.setWidgetResizable(True)
        self.initUI()

    def initUI(self):
        self.vbox=QtGui.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.Alignment(QtCore.Qt.AlignTop))
        self.vbox.setContentsMargins(0,0,0,0)
        self.vbox.setSpacing(0)
        self.setLayout(self.vbox)
        self.count=0
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-module"):
            self.dummyBtn=draggableButtonPlacedDummy("Dummy")
            self.setMinimumHeight(placed_module_height*self.count+1)
            event.accept()
        elif event.mimeData().hasFormat("application/x-module-placed"):
            self.dummyBtn=draggableButtonPlacedDummy("Dummy")
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
            if isinstance(widg, draggableButtonPlacedDummy):
                pass
            elif isinstance(widg, draggableButtonPlaced):
                widg2=widg
                widg2.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
                widg=self.childAt(event.pos())
                widg2.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
                index = self.vbox.indexOf(widg)
            elif isinstance(widg, centerWidget):
                index = self.vbox.indexOf(widg)
            elif isinstance(widg, QtGui.QWidget):
                pass

            if index!='':

                print "Dummy at index ", index, " | widget ", widg
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

            associatedModule=module_id_dict[str(data.data("application/x-module"))]
            if data.text() not in ['Loop','End']:
                newBtn=draggableButtonPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='Loop':
                newBtn=draggableLoopPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.setText("Start Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='End':
                newBtn=draggableLoopPlacedEnd(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module")
                newBtn.setText("End Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            #newBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

            newWidget=centerWidget(newBtn)
            newBtn.deleteContainer.connect(newWidget.deleteContainer)
            newBtn.decrementCount.connect(self.decrement_and_resize)
            self.vbox.insertWidget(index, newWidget)
            self.setMinimumHeight(placed_module_height*self.count)

            print "INDEX: ", index
            print self.count, self.height()
            event.accept()
            
        elif event.mimeData().hasFormat("application/x-module-placed"):
            #self.count+=1
            index = self.vbox.indexOf(self.dummyBtn)
            self.dummyBtn.deleteLater()

            associatedModule=module_id_dict[str(data.data("application/x-module-placed"))]
            if data.text() not in ['Loop','End']:
                newBtn=draggableButtonPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='Loop':
                newBtn=draggableLoopPlaced(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.setText("Start Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            elif data.text()=='End':
                newBtn=draggableLoopPlacedEnd(data.text(), associatedModule)
                newBtn.ID=data.data("application/x-module-placed")
                newBtn.setText("End Loop")
                newBtn.displayModule.connect(self.routerDisplayModule)
            #newBtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

            newWidget=centerWidget(newBtn)
            newBtn.deleteContainer.connect(newWidget.deleteContainer)
            newBtn.decrementCount.connect(self.decrement_and_resize)
            self.vbox.insertWidget(index, newWidget)
            #self.setMinimumHeight(30*self.count)

            print "INDEX: ", index
            print self.count, self.height()
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
                btn.setStyleSheet(s.loop_style_top)
            elif btn.what=='End':
                btn.setStyleSheet(s.loop_style_bot)
            else:
                btn.setStyleSheet(s.unselectedStyle)

class centerWidget(QtGui.QWidget):
    def __init__(self, btn):
        super(QtGui.QWidget,self).__init__()
        self.setFixedHeight(placed_module_height)
        self.setContentsMargins(0,0,0,0)
        self.btn=btn
        self.initUI()

    def initUI(self):
        layout=QtGui.QHBoxLayout()
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

class SuperMode(QtGui.QWidget):

    def __init__(self):
        super(SuperMode, self).__init__()
        self.initUI()
        
    def initUI(self):   
        global EdgeBtn_style

        mainLayout=QtGui.QVBoxLayout()

        #titleLabel = QtGui.QLabel('SuperMode')
        #titleLabel.setFont(fonts.font1)

        hbox=QtGui.QHBoxLayout()
        vboxLeft=QtGui.QVBoxLayout()
        vboxLeft.setContentsMargins(0,0,0,0)
        vboxLeft.setSpacing(2)

        self.vboxMid=QtGui.QVBoxLayout()
        
        self.dropWidget=dropZone()
        sizePolicy=QtGui.QSizePolicy()
        sizePolicy.setVerticalPolicy(QtGui.QSizePolicy.Expanding)
        self.dropWidget.setSizePolicy(sizePolicy)

        self.moduleLayout=QtGui.QVBoxLayout()

        moduleEdit=QtGui.QWidget()
        moduleEdit.setMinimumWidth(500)
        moduleEdit.setLayout(self.moduleLayout)

        
        moduleViewscrlArea=QtGui.QScrollArea()
        moduleViewscrlArea.setWidget(moduleEdit)
        moduleViewscrlArea.setContentsMargins(0,0,0,0)
        moduleViewscrlArea.setWidgetResizable(True)
        moduleViewscrlArea.setMinimumWidth(400)
        moduleViewscrlArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        moduleViewscrlArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        #moduleViewscrlArea.installEventFilter(self)
        

        separator1=QtGui.QFrame()
        separator1.setFrameShape(QtGui.QFrame.HLine); 
        separator1.setLineWidth(2)

        separator2=QtGui.QFrame()
        separator2.setFrameShape(QtGui.QFrame.HLine); 
        separator2.setLineWidth(2)

        separator3=QtGui.QFrame()
        separator3.setFrameShape(QtGui.QFrame.HLine); 
        separator3.setLineWidth(2)

        for module in progPanelList:
            btn=draggableButton(module)
            vboxLeft.addWidget(btn)
        vboxLeft.addWidget(separator1)


        for module in progPanelList_basic:
            btn=draggableButton(module)
            vboxLeft.addWidget(btn)
        vboxLeft.addWidget(separator2)


        progPanelList_basic_loops.reverse()
        for module in progPanelList_basic_loops:
            btn=draggableButton(module)
            vboxLeft.addWidget(btn)  
        vboxLeft.addWidget(separator3)      

        ###########################################
        # SAVING and LOADING

        vboxLeft.addStretch()

        push_save = QtGui.QPushButton("Save")
        push_save.clicked.connect(self.savePickle)
        push_save.setStyleSheet(s.btnStyle2)
        push_load = QtGui.QPushButton("Load")
        push_load.clicked.connect(self.loadPickle)
        push_load.setStyleSheet(s.btnStyle2)

        self.loaded_label = QtGui.QLabel()
        self.loaded_label.setStyleSheet(s.style1)

        vboxLeft.addWidget(self.loaded_label)
        vboxLeft.addWidget(push_load)
        vboxLeft.addWidget(push_save)

        ###########################################

        startBtn=QtGui.QPushButton("Start")
        startBtn.setStyleSheet(s.EdgeBtn_style)
        startWidg=centerWidget(startBtn)

        stopBtn=QtGui.QPushButton("End")
        stopBtn.setStyleSheet(s.EdgeBtn_style)
        stopWidg=centerWidget(stopBtn)

        self.vboxMid.addWidget(startWidg)
        self.vboxMid.addWidget(self.dropWidget)
        self.vboxMid.addWidget(stopWidg)
        self.vboxMid.addStretch()

        self.vboxMid.setAlignment(QtCore.Qt.Alignment(QtCore.Qt.AlignTop))

        self.containerWidget=QtGui.QWidget()
        self.containerWidget.setLayout(self.vboxMid)
        self.containerWidget.setSizePolicy(sizePolicy)
        #containerWidget.setSizePolicy(sizePolicy)

        self.scrlArea=QtGui.QScrollArea()
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

        clearBtn=QtGui.QPushButton("Clear")
        clearBtn.setStyleSheet(s.btnStyle_clearChain)
        clearBtn.clicked.connect(self.clearChain)

        vboxLeft.addWidget(clearBtn)

        self.dropWidget.routeModule.connect(self.displayModule)

        self.hboxProg=QtGui.QHBoxLayout()

        push_single=QtGui.QPushButton('Apply to One')
        push_range=QtGui.QPushButton('Apply to Range')
        push_all=QtGui.QPushButton('Apply to All')

        push_single.setStyleSheet(s.btnStyle)
        push_range.setStyleSheet(s.btnStyle)
        push_all.setStyleSheet(s.btnStyle)

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

    def savePickle(self):
        layoutItems=self.dropWidget.vbox
        items = [layoutItems.itemAt(i).widget().btn.module for i in range(layoutItems.count())]
        result=self.checkLoopOrder(items)
        if result:
            if g.workingDirectory:
                path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', g.workingDirectory, 'PKL(*.pkl)'))
                path=path_.filePath()
                saveFileName=path_.fileName()
                #g.workingDirectory=path_.filePath()
            else:
                path_ = QtCore.QFileInfo(QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', 'PKL(*.pkl)'))
                path=path_.filePath()
                saveFileName=path_.fileName()
                #g.workingDirectory=path_.filePath()     

            if not path.isEmpty():

                chainList=[]
                for module in items:
                    chainList.append([module.__class__.__name__, module.extractPanelParameters()])

                with open(unicode(path), 'wb') as output:
                    pickle.dump(chainList, output, pickle.HIGHEST_PROTOCOL)
              
            self.loaded_label.setText(saveFileName)
        else:
            print "Problems with loops dude. wtf."

    def loadPickle(self):
        global globalID
        reply = QtGui.QMessageBox.question(self, "Load a measurement chain",
            "Loading a measurement chain will replace the current one. Do you want to proceed?",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            for i in reversed(range(self.dropWidget.vbox.count())): 
                self.dropWidget.vbox.itemAt(i).widget().setParent(None)

            self.dropWidget.count=0
            self.dropWidget.resizeHeight()
            self.dropWidget.routerDisplayModule(None)
            self.dropWidget.update()
            print self.dropWidget.vbox.count()

            path = QtCore.QFileInfo(QtGui.QFileDialog().getOpenFileName(self, 'Load file', "*.pkl"))
            name=path.fileName()

            file=QtCore.QFile(path.filePath())

            with open(path.filePath(), 'rb') as inputFile:
                chainList= pickle.load(inputFile)
            globalID=0

            for moduleName, layoutWidgets in chainList:
                thisPanel = importlib.import_module(moduleName)     # import the module
                panel_class = getattr(thisPanel, moduleName)        # get it's main class 
                moduleHandle = panel_class(short=True) 
                moduleHandle.setPanelParameters(layoutWidgets)    
                print moduleName

                if moduleName not in ['Loop','End']:
                    newBtn=draggableButtonPlaced(moduleName, moduleHandle)
                    newBtn.ID=str(globalID)
                    module_id_dict[newBtn.ID]=moduleHandle
                    newBtn.displayModule.connect(self.dropWidget.routerDisplayModule)
                elif moduleName=='Loop':
                    newBtn=draggableLoopPlaced(moduleName, moduleHandle)
                    newBtn.ID=str(globalID)
                    module_id_dict[newBtn.ID]=moduleHandle
                    newBtn.setText("Start Loop")
                    newBtn.displayModule.connect(self.dropWidget.routerDisplayModule)
                elif moduleName=='End':
                    newBtn=draggableLoopPlacedEnd(moduleName, moduleHandle)
                    newBtn.ID=str(globalID)
                    module_id_dict[newBtn.ID]=moduleHandle
                    newBtn.setText("End Loop")
                    newBtn.displayModule.connect(self.dropWidget.routerDisplayModule)


                #newBtn=draggableButtonPlaced(moduleName, moduleHandle)
                #newBtn.ID=str(globalID)
                #module_id_dict[newBtn.ID]=moduleHandle
                #newBtn.displayModule.connect(self.dropWidget.routerDisplayModule)

                newCenterWidget=centerWidget(newBtn)
                newBtn.deleteContainer.connect(newCenterWidget.deleteContainer)
                newBtn.decrementCount.connect(self.dropWidget.decrement_and_resize)

                

                self.dropWidget.vbox.addWidget(newCenterWidget)
                globalID+=1

                print "Added module: ", moduleName, " at index ", self.dropWidget.vbox.count()-1

            #self.dropWidget.setFixedHeight(self.dropWidget.vbox.count()*placed_module_height)
            self.dropWidget.count=self.dropWidget.vbox.count()
            self.dropWidget.resizeHeight()
            self.dropWidget.update()

    def displayModule(self, module):
        try:
            self.moduleLayout.itemAt(0).widget().setParent(None) # delete previous widget
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
        print "Checking loop order..."

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
        if self.dropWidget.vbox.count()>0:
            reply = QtGui.QMessageBox.question(self, "Clear chain",
                "Are you sure?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            for i in reversed(range(self.dropWidget.vbox.count())): 
                self.dropWidget.vbox.itemAt(i).widget().setParent(None)

            self.dropWidget.count=0    
            self.dropWidget.resizeHeight()
            self.loaded_label.setText("")

    def throw_wrong_loops_dialogue(self):
        reply = QtGui.QMessageBox.question(self, "Wrong chain loops",
            "There is something wrong with the ordering of the Start and End loops. Please check.",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)        

    def programOne(self):
        if g.ser.port != None:
            mainChain_indexes = self.extractModuleChain()

            if mainChain_indexes==False:
                print "Problem with the Loops"
                self.throw_wrong_loops_dialogue()
            else:
                print "Starting..."
                self.thread=QtCore.QThread()
                self.getData=getData(mainChain_indexes, [[g.w,g.b]])
                self.finalise_thread_initialisation()
                self.thread.start()

    def programRange(self):
        if g.ser.port != None:
            print "Apply to Range"
            rangeDev=self.makeDeviceList(True)
            mainChain_indexes = self.extractModuleChain()

            if mainChain_indexes==False:
                print "Problem with the Loops"
                self.throw_wrong_loops_dialogue(self)
            else:
                print "Starting..."
                self.thread=QtCore.QThread()
                self.getData=getData(mainChain_indexes, rangeDev)
                self.finalise_thread_initialisation()
                self.thread.start()

    def programAll(self):
        if g.ser.port != None:
            print "Apply to All"
            rangeDev=self.makeDeviceList(False)
            mainChain_indexes = self.extractModuleChain()

            if mainChain_indexes==False:
                print "Problem with the Loops"
                self.throw_wrong_loops_dialogue()
            else:
                print "Starting..."
                self.thread=QtCore.QThread()
                self.getData=getData(mainChain_indexes, rangeDev)
                self.finalise_thread_initialisation()
                self.thread.start()

    def finalise_thread_initialisation(self):
        self.getData.moveToThread(self.thread)
        self.thread.started.connect(self.getData.getIt)
        self.getData.finished.connect(self.thread.quit)
        self.getData.finished.connect(self.getData.deleteLater)
        self.thread.finished.connect(self.getData.deleteLater)
        self.getData.updateAddress.connect(f.addressAntenna.update)
        self.getData.globalDisableInterface.connect(f.interfaceAntenna.toggleGlobalDisable)
        self.getData.disableInterface.connect(f.interfaceAntenna.cast)
        self.getData.execute.connect(self.execute)

    def execute(self, index):
        print "###### EXECUTING ", index
        self.mainChain[index].programOne()

    def makeDeviceList(self,isRange):
        #if g.checkSA=False:
        rangeDev=[] # initialise list which will contain the SA devices contained in the user selected range of devices
        #rangeMax=0;
        if isRange==False:
            minW=1
            maxW=g.wline_nr
            minB=1
            maxB=g.bline_nr
        else:
            minW=g.minW
            maxW=g.maxW
            minB=g.minB
            maxB=g.maxB            


        # Find how many SA devices are contained in the range
        if g.checkSA==False:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    rangeDev.append([w,b])
            #rangeMax=(wMax-wMin+1)*(bMax-bMin+1)
        else:
            for w in range(minW,maxW+1):
                for b in range(minB,maxB+1):
                    for cell in g.customArray:
                        if (cell[0]==w and cell[1]==b):
                            rangeDev.append(cell)

        return rangeDev

def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = SUperMode()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 