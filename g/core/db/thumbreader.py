import heapq, queue, io
from queue import Queue

from PIL import Image

import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QEventLoop, QCoreApplication
from PyQt5.QtWidgets import QApplication

from g.core.db.dbthumbs import DbThumbsSqlite

def getThumb(path : str, size : tuple):
    im = Image.open(path)
    im.thumbnail(size)
    return im

def rawToPilIm(raw):
    inData = io.BytesIO(raw)
    im = Image.open(inData)
    return im

def pilImToRaw(im):
    out = io.BytesIO()
    im.save(out, format='JPEG', quality=90)
    data = out.getvalue()
    out.close()
    return data

class ReaderTask(object):
    def __init__(self, priority : int, path : str):
        self.priority = priority
        self.path = path

    def __lt__(self, other):
        return self.priority < other.priority


class WorkerReader(QThread):
    newThumb = pyqtSignal(int, str, Image.Image)

    def __init__(self, dbThumbs : DbThumbsSqlite):
        super().__init__()
        self.tasksAdd = Queue()
        self.tasksRemove = Queue()
        self.thumbWidth = 200
        self.enabled = True
        self.dbThumbs = dbThumbs

    def addTask(self, thumbNumber : int, path : str):
        task = (thumbNumber, path)

        try:
            while True:
                t = self.tasksAdd.get(False)
        except queue.Empty as _:
            pass

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
                size = (256, 256)

                task = heapq.heappop(toRead)
                path = task[1]
                thumbId = task[0]

                im = getThumb(path, size)
                self.newThumb.emit(thumbId, path, im)

            time.sleep(sleepTime)
            counter += 1
            if counter > 100:
                sleepTime = 1.0

class ThumbReader(QObject):
    thumbReady = pyqtSignal(int, str, Image.Image)

    def __init__(self, dbThumbs : DbThumbsSqlite):
        super().__init__()

        self.dbThumbs = dbThumbs
        self.thread = QThread()
        self.worker = None
        self.__startWorker()

    def add(self, thumbNumber : int, path : str):
        rawThumb = self.dbThumbs.getByFilePath(path)
        if rawThumb:
            self.thumbReady.emit(thumbNumber, path, rawToPilIm(rawThumb))
        else:
            self.worker.addTask(thumbNumber, path)

    def getByFilePathAsync(self, paths : list):
        pass

    def onNewThumb(self, thumbId : int, path : str, pic : Image.Image):
        #print('got thumb: ', path)
        self.dbThumbs.addByFilePath(path, pilImToRaw(pic))

        self.thumbReady.emit(thumbId, path, pic)

    def __startWorker(self):
        self.worker = WorkerReader(self.dbThumbs)
        self.worker.newThumb.connect(self.onNewThumb)
        self.worker.start()
