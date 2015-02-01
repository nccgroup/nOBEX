#!/usr/bin/env python

import os, sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

from PyOBEX.client import BrowserClient
from PyOBEX.responses import *

class OBEXError(Exception):

    pass

class OBEXHandler:

    def __init__(self, address, port):
    
        self.client = BrowserClient(address, port)
        if not isinstance(self.client.connect(), ConnectSuccess):
            raise OBEXError, "Failed to connect"
        
        self.path = []
    
    def setpath(self, path):
    
        # Normalise the path.
        pieces = filter(lambda x: x, path.split("/"))
        
        if pieces == self.path:
            return True
        
        # Find a common path.
        common = []
        common_length = min(len(pieces), len(self.path))
        
        for i in range(common_length):
        
            if pieces[0] == self.path[0]:
                pieces.pop(0)
                common.append(self.path.pop(0))
            else:
                break
        
        # Leave any subdirectories of the common path.
        for subdir in self.path:
        
            response = self.client.setpath(to_parent = True)
            
            if isinstance(response, FailureResponse):
                # We couldn't leave a subdirectory. Put the remaining path
                # back together and return False to indicate an error.
                self.path = common + self.path
                return False
        
        # Construct a new path from the common path.
        self.path = common
        
        # Descend into the new path.
        for subdir in pieces:
        
            response = self.client.setpath(subdir)
            if isinstance(response, FailureResponse):
                # We couldn't enter a subdirectory, so just return False to
                # indicate an error.
                return False
            
            self.path.append(subdir)
        
        return True
    
    def listdir(self, subdir = ""):
    
        response = self.client.listdir(subdir.lstrip("/"))
        if isinstance(response, FailureResponse):
            return False
        
        headers, listing = response
        return listing


class OBEXScheduler(QThread):

    directoryListed = pyqtSignal(object, str)
    
    def __init__(self, handler):
    
        QThread.__init__(self)
        self.handler = handler
        self.items = []
        self.mutex = QMutex()
    
    def addItem(self, item):
    
        self.mutex.lock()
        self.items.append(item)
        self.mutex.unlock()
    
    def count(self):
    
        self.mutex.lock()
        number = len(self.items)
        self.mutex.unlock()
        
        return number
    
    def run(self):
    
        self.running = True
        while self.running:
        
            self.mutex.lock()
            try:
                item = self.items.pop()
            except IndexError:
                item = None
            self.mutex.unlock()
            
            if item:
                if self.handler.setpath(item.path):
                    result = self.handler.listdir()
                    if result:
                        self.directoryListed.emit(item, result)
                    else:
                        self.directoryListed.emit(item, "")
    
    def stop(self):
    
        self.running = False
        self.wait(5)


class Item:

    def __init__(self, path):
    
        self.path = path
        self.parent = None
        self.refreshed = False
        self.waiting = False
    
    def name(self):
    
        return self.path.split(u"/")[-1]
    
    def row(self):
    
        if self.parent:
            return self.parent.children.index(self)
        else:
            return 0

class DirectoryItem(Item):

    def __init__(self, path):
    
        Item.__init__(self, path)
        self.children = []

class FileItem(Item):

    def __init__(self, path):
    
        Item.__init__(self, path)


class OBEXModel(QAbstractItemModel):

    pendingRequest = pyqtSignal()
    noMoreRequests = pyqtSignal()
    
    def __init__(self, handler, parent = None):
    
        QAbstractItemModel.__init__(self, parent)
        
        self.rootItem = DirectoryItem(u"")
        
        self.scheduler = OBEXScheduler(handler)
        self.scheduler.directoryListed.connect(self.refresh)
        self.scheduler.start()
    
    def request_refresh(self, item):
    
        self.scheduler.addItem(item)
        item.waiting = True
        self.pendingRequest.emit()
    
    def refresh(self, item, xml):
    
        item.refreshed = True
        item.waiting = False
        
        if self.scheduler.count() == 0:
            self.noMoreRequests.emit()
        
        if not xml:
            return
        
        reader = QXmlStreamReader(xml)
        
        item.children = []
        
        while not reader.atEnd():
        
            token = reader.readNext()
            if token == reader.StartElement:
            
                if reader.name() == "file":
                    child = FileItem(item.path + u"/" + unicode(reader.attributes().value("name").toString()))
                elif reader.name() == "folder":
                    child = DirectoryItem(item.path + u"/" + unicode(reader.attributes().value("name").toString()))
                else:
                    continue
                
                child.parent = item
                item.children.append(child)
        
        self.layoutChanged.emit()
    
    def hasChildren(self, parent_index):
    
        if parent_index.isValid():
            parent = parent_index.internalPointer()
        else:
            parent = self.rootItem
        
        # File items have no children.
        # Directory items are assumed to have children until they have actually
        # been refreshed.
        
        if isinstance(parent, FileItem):
            return False
        elif parent.refreshed:
            return parent.children != []
        else:
            return True
    
    def rowCount(self, parent_index):
    
        if parent_index.isValid():
            parent = parent_index.internalPointer()
        else:
            parent = self.rootItem
        
        if not parent.refreshed:
            self.request_refresh(parent)
        
        return len(parent.children)
    
    def columnCount(self, parent_index):
    
        return 1
    
    def index(self, row, column, parent_index):
    
        if parent_index.isValid():
            parent = parent_index.internalPointer()
        else:
            parent = self.rootItem
        
        item = parent.children[row]
        return self.createIndex(row, column, item)
    
    def parent(self, index):
    
        # root item -> QModelIndex()
        # item -> parent (root item) -> QModelIndex()
        # item -> parent
        
        if not index.isValid():
            return QModelIndex()
        
        item = index.internalPointer()
        if item == self.rootItem:
            return QModelIndex()
        
        # Only items beneath the root item are examined from here.
        parent = item.parent
        
        if parent == self.rootItem:
            return QModelIndex()
        else:
            return self.createIndex(parent.row(), 0, parent)
    
    def flags(self, index):
    
        if not index.isValid():
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def data(self, index, role):
    
        if not index.isValid():
            return QVariant()
        
        if role == Qt.DisplayRole:
            item = index.internalPointer()
            return QVariant(item.name())
        elif role == Qt.UserRole:
            item = index.internalPointer()
            return QVariant(item.waiting)
        
        return QVariant()


class Delegate(QItemDelegate):

    needsRedraw = pyqtSignal()
    
    def __init__(self, movie, parent = None):
    
        QItemDelegate.__init__(self, parent)
        self.movie = movie
        self.movie.frameChanged.connect(self.needsRedraw)
        self.playing = False
    
    def startMovie(self):
        self.movie.start()
        self.playing = True
    
    def stopMovie(self):
        self.movie.stop()
        self.playing = False
    
    def paint(self, painter, option, index):
    
        waiting = index.data(Qt.UserRole).toBool()
        if waiting:
            option = option.__class__(option)
            pixmap = self.movie.currentPixmap()
            painter.drawPixmap(option.rect.topLeft(), pixmap)
            option.rect = option.rect.translated(pixmap.width(), 0)
        
        QItemDelegate.paint(self, painter, option, index)


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) != 3:
    
        sys.stderr.write("Usage: %s <address> <port>\n" % sys.argv[0])
        sys.exit(1)
    
    handler = OBEXHandler(sys.argv[1], int(sys.argv[2]))
    model = OBEXModel(handler)
    
    view = QTreeView()
    view.header().hide()
    view.setModel(model)
    view.show()
    
    animation = os.path.join(os.path.split(__file__)[0], "animation.gif")
    delegate = Delegate(QMovie(animation))
    view.setItemDelegate(delegate)
    delegate.needsRedraw.connect(view.viewport().update)
    model.pendingRequest.connect(delegate.startMovie)
    model.noMoreRequests.connect(delegate.stopMovie)
    
    # Run the event loop and tidy up nicely afterwards.
    result = app.exec_()
    handler.client.disconnect()
    sys.exit(result)
