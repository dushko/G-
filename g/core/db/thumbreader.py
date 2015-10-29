import queue
from queue import Queue

import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

from g.core.db.dbthumbs import DBThumbs

class WorkerReader(QThread):
    newThumb = pyqtSignal(str, QPixmap)

    def __init__(self):
        super().__init__()
        self.tasksAdd = Queue()
        self.tasksRemove = Queue()
        self.thumbWidth = 200
        self.enabled = True

    def addTasks(self, paths : list):
        for p in paths:
            self.tasksAdd.put(p)

    def stop(self):
        self.enabled = False

    def run(self):
        toRead = set()
        counter = 0
        sleepTime = 0.01
        while self.enabled:
            try:
                while True:
                    task = self.tasksAdd.get(False)
                    toRead.add(task)
            except queue.Empty as _:
                pass

            try:
                while True:
                    task = self.tasksRemove.get(False)
                    toRead.discard(task)
            except queue.Empty as _:
                pass

            if len(toRead) != 0:
                counter = 0
                path = toRead.pop()
                print('reading thumb ', path)
                pic = QPixmap(path).scaledToWidth(self.thumbWidth)
                self.newThumb.emit(path, pic)

            time.sleep(sleepTime)
            counter += 1
            if counter > 100:
                sleepTime = 1.0

class ThumbReader(QObject):
    thumbReady = pyqtSignal(str, QPixmap)

    def __init__(self, dbThumbs : DBThumbs):
        super().__init__()
        self.thread = QThread()
        self.worker = None
        self.startWorker()

    def add(self, path : str):
        self.worker.addTasks([path])

    def getByFilePathAsync(self, paths : list):
        pass

    def onNewThumb(self, path : str, pic : QPixmap):
        self.thumbReady.emit(path, pic)

    def startWorker(self):
        self.worker = WorkerReader()
        self.worker.newThumb.connect(self.onNewThumb)
        self.worker.start()
