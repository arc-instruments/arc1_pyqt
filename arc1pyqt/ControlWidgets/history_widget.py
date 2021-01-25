####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os
from functools import partial
from PyQt5 import QtGui, QtCore, QtWidgets

import pyqtgraph as pg
import numpy as np

from .. import state
HW = state.hardware
APP = state.app
CB = state.crossbar
from ..Globals import functions, fonts
from .. import Graphics

from .history_tree_model import HistoryTreeItem, HistoryTreeModel
from .history_tree_model import HistoryTreeItemDelegate

class HistoryWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.dieName = QtWidgets.QLineEdit('Package1')
        self.dieName.setFont(fonts.font1)
        self.dieName.textChanged.connect(self.changeSessionNameManually)

        self.historyView = QtWidgets.QTreeView()
        self.historyView.setModel(HistoryTreeModel(title='Device History', parent=self))
        self.historyView.setItemDelegate(HistoryTreeItemDelegate(self.historyView.model(), self))
        self.historyView.clicked.connect(self._onClicked)
        self.historyView.doubleClicked.connect(self._displayResults)

        functions.historyTreeAntenna.updateTree.connect(self._updateTree)
        functions.historyTreeAntenna.updateTree_batch.connect(self._updateTree_batch)
        functions.historyTreeAntenna.rebuildTreeTopLevel.connect(self._rebuildTopLevel)
        functions.historyTreeAntenna.clearTree.connect(self._clearTree)
        functions.historyTreeAntenna.changeSessionName.connect(self.changeSessionName)
        functions.cbAntenna.selectDeviceSignal.connect(self._switchTopLevel)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.dieName)

        mainLayout.addWidget(self.historyView)

        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)

        self.resultWindow = []
        self.setLayout(mainLayout)

    def changeSessionNameManually(self, txt):
        APP.sessionName = txt

    def changeSessionName(self):
        self.dieName.setText(APP.sessionName)

    def _clearTree(self):
        self.historyView.model().clear()

    def _updateTree_batch(self, w, b, idx):
        # Update tree for a specific word/bit starting
        # from idx down to the latest item in the
        # device history
        for i in range(idx, len(CB.history[w][b])):
            self._updateTree(w, b, i)

    def _updateTree(self, w, b, historyIdx=-1):
        # historyIdx is used if we want to update the tree
        # using a specific end tag index rather than the last
        # tag available; this defaults to "the last added item"
        # which is typically an 'S R' tag, a 'P' tag or a regular
        # 'XXX_e' tag.

        existingItem = self.historyView.model().findTopLevel(w, b)

        if existingItem is None:
            # new (W|B) combination
            # add it to the root of the tree
            toplevel = HistoryTreeItem(w=w, b=b)
            idx = self.historyView.model().appendTopLevel(toplevel)
        else:
            # otherwise we will append stuff to the existing node
            # returned from `findTopLevel`
            toplevel = existingItem.internalPointer()
            idx = existingItem

        self._deunderline()
        toplevel.setActive(True)

        item = self.createItem(w, b, historyIdx)

        if toplevel.childCount() > 0:
            previousItem = toplevel.children[-1]
        else:
            previousItem = None

        # if the new item is read or pulse
        if item.description in ['Read', 'Pulse']:
            # and so is the previous item on the list
            if previousItem and previousItem.description.startswith(item.description):
                # just increase the counter of the previous one
                # no need to add a new item
                parts = previousItem.description.split(' × ')
                num = int(parts[-1]) + 1
                # change the description of the last child of toplevel
                self.historyView.model().setItemDescription(len(toplevel.children)-1,
                    '%s × %d' % (parts[0], num), idx)

                # exit early
                return
            else:
                # add it as x 1
                item.setDescription('%s × 1' % item.description)

        insertedIdx = self.historyView.model().appendChild(item, idx)

    def _displayResults(self, idx):
        item = idx.internalPointer()
        (w, b) = item.coords
        descr = item.description
        (start, end) = item.range
        tag = item.tag

        raw = CB.history[w][b][start:end+1]

        if tag in APP.modules.keys():
            cb = APP.modules[tag].callback

            if cb is None:
                return

            widget = cb(w, b, raw, self)
            self.resultWindow.append(widget)
            widget.show()
            widget.update()

    def _changeDisplayToSelectedItem(self, idx):
        model = self.historyView.model()

        if model.isRoot(idx):
            return

        # get the item's coordinates
        item = idx.internalPointer()
        (w, b) = item.coords

        # and check if there's a top level with those coords
        toplevel = self.historyView.model().findTopLevel(w, b)

        # something is wrong; there's nowhere to append
        # this should only happen when a device with no
        # active measurements has been selected in the crossbar
        if toplevel is None:
            return

        # change the active entry to the one matching W, B
        self._deunderline()
        self.historyView.model().setActiveIdx(toplevel, True)

    def _switchTopLevel(self, w, b):
        model = self.historyView.model()
        toplevel = self.historyView.model().findTopLevel(w, b)

        if toplevel is None:
            return

        self._deunderline()
        self.historyView.model().setActiveIdx(toplevel, True)

    def _onClicked(self, idx):
        self._changeDisplayToSelectedItem(idx)
        (w, b) = idx.internalPointer().coords
        functions.cbAntenna.selectDeviceSignal.emit(w, b)
        functions.displayUpdate.updateSignal_short.emit()

    def _deunderline(self):
        # deactivate all top-level children
        for (i, child) in enumerate(self.historyView.model().children()):
            self.historyView.model().setActive(i, False)

    def _rebuildTopLevel(self, w, b):
        # force rebuild of a toplevel entry
        # this may be required when a toplevel entry has corrupted data
        # and indices need to be updated to salvage as much as possible
        model = self.historyView.model()

        # first clear this toplevel
        model.clearTopLevel(w, b)

        # traverse the current history
        for (counter, row) in enumerate(CB.history[w][b]):
            tag = row[3]

            # and re-add data
            if 'S R' in tag or tag.endswith('_e') or tag == 'P':
                self._updateTree(w, b, counter)

    def createItem(self, w, b, historyIdx=-1):

        item = HistoryTreeItem()
        item.setCoords(w, b)

        # get the (full) tag of the last item in history
        # for instance RET_xxx_i
        tag = CB.history[w][b][historyIdx][3]
        # and that's the module tag, for instance RET
        modTag = None

        # try to split the tag
        # TAG_xxx_s -> ['TAG', 'xxx', 's']
        tagParts = tag.split("_")

        # so this is the actual tag to look for in APP.modules.
        # if there are no "_" in the tag then this is probably
        # a read or pulse tag ("P", "S R..." or "F R...")
        if len(tagParts) == 1:
            # pulse tags are always 'P' but read tags can be
            # either of 'S R2 V=X.Y' or 'S R V=X.Y' so take
            # AT MOST the first 3 characters of the tag
            # P -> P
            # S R2 V=X.Y -> S R
            # etc.
            # The read module is tagged with 'S R' so that way
            # we always get the correct one.
            # I know this is ugly but there is technical
            # baggage that come with this behaviour so if we
            # change that, people's log files will break
            modTag = tag[:3]
            standardTag = False
        else:
            # in this case the tag looks like TAG_xxxx_{s, i, e}
            # so get the first part ('TAG'). This is the
            # standard behaviour.
            modTag = tagParts[0]
            standardTag = True

        # check out if there's a module registered with the
        # tag. If not return None
        mod = APP.modules.get(modTag, None)

        # if there is a mod; great! put its name on the tree
        # item's description
        if mod:
            item.setDescription(mod.display)
        else:
            # no such module, don't know what to do with it
            # ignore
            return

        # get the start and end of the operation for non read/pulse actions
        start = 0
        end = 0

        if standardTag:
            # the end of the range is always the last entry (because, well...,
            # it just ended!)
            end = len(CB.history[w][b]) - 1

            try:
                lastIndex = None
                traverse = True

                # check first if we have stored the index of the tag
                # in the crossbar history data structure
                # [W][B][
                #   [.....],
                #   [.....],
                #   [R, V, PW, tag, readopt, Vread, startidx] <- last item for this (W,B)
                #                                     ^^^^
                #                         check if this is > 0
                # ]
                # for any non read/pulse tags (what we call standard tags) the last item on
                # the list should be an _e tag which typically saves this start index value.
                if CB.history[w][b][historyIdx][-1] > 0:
                    # great the start index of the block is stored
                    # this is our start, no need to traverse the tree backwards
                    start = CB.history[w][b][historyIdx][-1] + 1
                    traverse = False

                # traverse the entries in reverse (-1) to find the ranges
                # if for some reason the start index was not saved in the end
                # tag then resort to traverse the history backwards to find
                # the start tag; these shouldn't be triggered really
                if traverse:
                    for (i, row) in enumerate(CB.history[w][b][::-1]):

                        # and extract the tag from the history entry
                        # [Resistance, Voltage, PulseWidth, tag, read opt., Vread, startidx]
                        #                                   ^^^
                        #                                this one
                        tag = row[3]
                        # if this matches the current modTag and it's a start tag (_s)
                        # we found the start! stop traversing.
                        # we are using `startswith` rather than equality because
                        # tags might have multiple parts, such as MSS1, MSS2, MSS3
                        if tag.startswith(modTag) and tag.endswith('_s'):
                            lastIndex = i
                            break

                    if lastIndex is None:
                        lastIndex = tagList.index(modTag + '_s')
                    start = end - lastIndex
            except ValueError:
                pass

        # adjust tree item's ranges and tag
        item.setRange(start, end)
        item.setTag(modTag)

        return item
