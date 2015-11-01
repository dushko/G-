import heapq
import queue
from queue import Queue
from threading import Lock

from PIL import Image, ImageQt

import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap

from g.core.db.dbthumbs import DBThumbs

class ReaderTask(object):
    def __init__(self, priority : int, path : str):
        self.priority = priority
        self.path = path

    def __lt__(self, other):
        return self.priority < other.priority


class WorkerReader(QThread):
    newThumb = pyqtSignal(int, str, QPixmap)

    def __init__(self):
        super().__init__()
        self.tasksAdd = Queue()
        self.tasksRemove = Queue()
        self.thumbWidth = 200
        self.enabled = True

    def addTask(self, thumbNumber : int, path : str):
        task = (thumbNumber, path)
        self.tasksAdd.put(task)

    def stop(self):
        self.enabled = False

    def run(self):
        toRead = []
        counter = 0
        sleepTime = 0.01
        while self.enabled:
            try:
                while True:
                    task = self.tasksAdd.get(False)
                    if task not in toRead:
                        heapq.heappush(toRead, task)
            except queue.Empty as _:
                pass

            try:
                while True:
                    task = self.tasksRemove.get(False)
                    if task in toRead:
                        toRead.remove(task)
            except queue.Empty as _:
                pass

            heapq.heapify(toRead)

            if len(toRead) != 0:
                counter = 0
                task = heapq.heappop(toRead)
                path = task[1]
                thumbId = task[0]
                size = (160, 140)
                im = Image.open(path)
                im.thumbnail(size)
                pic = ImageQt.toqpixmap(im)
                self.newThumb.emit(thumbId, path, pic)

            time.sleep(sleepTime)
            counter += 1
            if counter > 100:
                sleepTime = 1.0

class ThumbReader(QObject):
    thumbReady = pyqtSignal(int, str, QPixmap)

    def __init__(self, dbThumbs : DBThumbs):
        super().__init__()
        self.thread = QThread()
        self.worker = None
        self.startWorker()

    def add(self, thumbNumber : int, path : str):
        self.worker.addTask(thumbNumber, path)

    def getByFilePathAsync(self, paths : list):
        pass

    def onNewThumb(self, thumbId : int, path : str, pic : QPixmap):
        self.thumbReady.emit(thumbId, path, pic)

    def startWorker(self):
        self.worker = WorkerReader()
        self.worker.newThumb.connect(self.onNewThumb)
        self.worker.start()
