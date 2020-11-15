import sys
from PyQt5 import QtCore, QtGui, QtWidgets


class HistoryTreeItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, model, parent=None):
        super().__init__(parent)
        # reference to model, to pick up properties of items
        self._model = model

    def paint(self, painter, option, index):
        # if it's toplevel paint it bold
        if self._model.isTopLevel(index):
            option.font.setPointSize(10)
            option.font.setWeight(QtGui.QFont.Bold)
            # and underline it if it's active
            option.font.setUnderline(self._model.isActive(index))
        else:
            # otherwise it's just a child node
            option.font.setPointSize(8)
        # otherwise just use superclass painter
        super().paint(painter, option, index)


class HistoryTreeItem:

    def __init__(self, w=-1, b=-1, start=-1, end=-1, descr="", tag="", parent=None):

        # any children
        self.children = []

        # coordinates
        self._w = w
        self._b = b

        # range in history
        self._start = start
        self._end = end

        # description
        self._descr = descr

        # tag
        self._tag = tag

        # parent
        self._parent = parent

        # if it's currently selected or not
        self._active = False

    @property
    def coords(self):
        return (self._w, self._b)

    def setCoords(self, w, b):
        (self._w, self._b) = (w, b)

    @property
    def range(self):
        return (self._start, self._end)

    def setRange(self, start, end):
        (self._start, self._end) = (start, end)

    @property
    def description(self):
        return self._descr

    def setDescription(self, descr):
        self._descr = descr

    @property
    def tag(self):
        return self._tag

    def setTag(self, tag):
        self._tag = tag

    @property
    def active(self):
        return self._active

    def setActive(self, what):
        self._active = what

    def child(self, row):
        try:
            return self.children[row]
        except IndexError:
            return None

    def childCount(self):
        return len(self.children)

    def parent(self):
        return self._parent

    def appendChild(self, item):
        item._parent = self
        self.children.append(item)

    def removeChild(self, row):
        self.children.pop(row)

    def clear(self):
        self.children.clear()

    def row(self):
        if self.parent() is None:
            return 0

        parent = self.parent()

        return parent.indexOf(self)

    def indexOf(self, item):
        return self.children.index(item)

    def data(self, col):
        return (self._w, self._b, self._start, self._end, self._descr, self._tag)

    def __str__(self):
        return "W=%d|B=%d - [%d:%d] - %s (%s)" % \
            (self._w, self._b, self._start, self._end,
                self._descr, self._tag)


class HistoryTreeModel(QtCore.QAbstractItemModel):

    def __init__(self, data=None, title=None, parent=None):
        super().__init__()

        # header title, if any
        self._title = title

        # dummy root item
        self._root = HistoryTreeItem(-1, -1, -1, -1, "", None)

        # add any given data to the tree
        if data:
            for child in data:
                self._root.appendChild(child)

    def index(self, row, col, parent_idx=None):

        if not parent_idx or not parent_idx.isValid():
            parent = self._root
            parent_idx = self.createIndex(0, 0, parent)
        else:
            parent = parent_idx.internalPointer()

        if not super().hasIndex(row, col, parent_idx):
            return QtCore.QModelIndex()

        child = parent.child(row)

        if child is not None:
            return super().createIndex(row, col, child)

        return QtCore.QModelIndex()

    def appendTopLevel(self, item):

        self.beginInsertRows(QtCore.QModelIndex(), 0, item.childCount()-1)
        self._root.appendChild(item)
        self.endInsertRows()

        return self.createIndex(self._root.childCount()-1, 0, item)

    def appendChild(self, item, parentIdx=None):

        # no parent means append to root
        if parentIdx is None:
            parent = self._root
            idx = QtCore.QModelIndex()
        else:
            parent = parentIdx.internalPointer()
            idx = parentIdx

        self.beginInsertRows(idx, 0, item.childCount()-1)
        parent.appendChild(item)
        self.endInsertRows()

        return self.createIndex(parent.childCount()-1, 0, item)

    def children(self):
        return self._root.children

    def appendChildFromParts(self, w, b, start, end, descr, tag):
        self.beginInsertRows(QtCore.QModelIndex(), 0, item.childCount()-1)
        self._root.appendChild(HistoryTreeItem(w, b, start, end, descr, tag))
        self.endInsertRows()

    def removeChild(self, row):
        child = self._root.child(row)
        idx = self.createIndex(row, 0, child)
        self.beginRemoveRows(idx, row, 0)
        self._root.removeChild(row)
        self.endRemoveRows()

    def clear(self):
        self.beginResetModel()
        self._root.clear()
        self.endResetModel()

    def clearTopLevel(self, w, b):
        toplevelIdx = self.findTopLevel(w, b)
        if toplevelIdx is None:
            return
        toplevel = toplevelIdx.internalPointer()
        self.beginResetModel()
        toplevel.clear()
        self.endResetModel()

    def parent(self, idx):
        if not idx.isValid():
            return QtCore.QModelIndex()

        p = idx.internalPointer().parent()
        if p:
            return super().createIndex(p.row(), 0, p)
        return QtCore.QModelIndex()

    def rowCount(self, parent_idx):

        if parent_idx.isValid():
            return parent_idx.internalPointer().childCount()
        return self._root.childCount()

    def columnCount(self, *args):
        return 1

    def data(self, idx, role):
        if not idx.isValid():
            return None

        child = idx.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            if self.isTopLevel(idx):
                return "W=%d | B=%d" % (child.coords)
            return child.description
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if self._title:
                return self._title
            return ''

        return None

    def isTopLevel(self, idx):
        # if parent of index is the root node, then an entry
        # is considered as top-level
        return idx.internalPointer().parent() == self._root

    def isActive(self, idx):
        return idx.internalPointer().active

    def setActive(self, row, what):
        idx = self.createIndex(row, 0, self._root.children[row])
        self.setActiveIdx(idx, what)

    def setActiveIdx(self, idx, what):
        idx.internalPointer().setActive(what)
        self.dataChanged.emit(idx, idx)

    def setItemDescription(self, row, what, parentIdx=None):
        if parentIdx is None:
            parent = self._root
        else:
            parent = parentIdx.internalPointer()

        item = parentIdx.internalPointer().child(row)
        item.setDescription(what)

        idx = self.createIndex(row, 0, item)
        self.dataChanged.emit(idx, idx)

    def isRoot(self, idx):
        return idx.internalPointer() == self._root

    def findTopLevel(self, word, bit):
        for i in range(self._root.childCount()):
            item = self._root.child(i)
            if item.coords == (word, bit):
                return self.createIndex(i, 0, item)
        return None
