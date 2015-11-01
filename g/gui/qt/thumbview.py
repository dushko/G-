from PyQt5 import QtCore

from PIL import Image, ImageQt
from PyQt5.QtCore import QRect, QPoint, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPaintEvent, QPainter, QResizeEvent, QPixmap, \
    QImage
from PyQt5.QtWidgets import QWidget, QLabel, QScrollArea, QSizePolicy, QGridLayout

from g.core.db.nodes import PhotoNode
from g.gui.common.layoutengine import LayoutEngine
from g.gui.common.rectangle import Rectangle


class GScrollArea(QScrollArea):
    def __init__(self, *args):
        super().__init__(*args)
        self.resizeCallback = None

    def setResizeEventCallback(self, callback):
        self.resizeCallback = callback

    def resizeEvent(self, ev : QResizeEvent):
        super().resizeEvent(ev)

        if self.resizeCallback is not None:
            self.resizeCallback(ev)

class ThumbView(QWidget):
    needThumb = pyqtSignal(int, str)

    def __init__(self):
        self.counter = 0
        super().__init__()

        self.thumbWidth = 100
        self.thumbHeight = 80

        self.thumbs = {}
        self.items = []
        self.cellsInView = {}

        self.noThumbPixmap = QPixmap('data/gfx/noThumb.png')
        self.noThumbPixmap = self.resizeImage(self.noThumbPixmap,
                (self.thumbWidth, self.thumbHeight))

        self.canvas = GScrollArea()
        self.canvas.setResizeEventCallback(self.canvasResizeEvent)
        self.w = QWidget()
        self.w.paintEvent = self.canvasPaintEvent
        self.canvas.setWidget(self.w)
        self.canvas.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))


        label = QLabel('Thumbnails view')

        layout = QGridLayout()
        layout.addWidget(label, 0, 0, 1, 1)
        layout.addWidget(self.canvas, 1, 0, 1, 1)
        self.setLayout(layout)

        self.cnt = 0
        self.width = 500
        self.layoutEngine = LayoutEngine()
        self.layoutEngine.updateCells(0, 100, 100)
        self.layoutEngine.updateWidth(self.width)
        self.setCanvasSize(self.width, self.layoutEngine.getHeight())

    def canvasResizeEvent(self, ev : QResizeEvent):
        oldSize = ev.oldSize()
        newSize = ev.size()

        if oldSize.width() != newSize.width():
            self.updateLayout(newSize.width())

    def setItems(self, items):
        self.items = items
        nCells = len(items)
        print('Set items: ', nCells)
        self.layoutEngine.updateCells(nCells, 100, 100)
        self.updateLayout(self.layoutEngine.getWidth())
        self.w.repaint()

    def updateLayout(self, width):
        self.layoutEngine.updateWidth(width - 1)
        height = self.layoutEngine.getHeight()
        self.setCanvasSize(width, height)

    def repaintCanvas(self):
        self.w.repaint()

    def setCanvasSize(self, w, h):
        self.w.resize(w, h)

    def canvasPaintEvent(self, ev : QPaintEvent):
        print(self.counter, '  ', end='')
        self.counter += 1
        repaintRect = ev.rect()
        repaintArea = Rectangle(repaintRect.x(), repaintRect.y(), repaintRect.width(),
                repaintRect.height())

        painter = QPainter(self.w)

        thumbRequested = False
        cells = self.layoutEngine.getVisibleCells(repaintArea)
        for cellNum, cell in cells.items():
            thumb = self.items[cellNum]
            if thumb.getPath() in self.thumbs:
                self.drawThumnail(cellNum, self.thumbs[thumb.getPath()], thumb, cell, painter)
            else:
                if not thumbRequested:

                    self.needThumb.emit(cellNum, thumb.getPath())
                    thumbRequested = True
                self.drawThumnail(cellNum, self.noThumbPixmap, self.items[cellNum],
                        cell, painter)

    def drawThumnail(self, cellNum, pic, thumb : PhotoNode, cell : Rectangle, painter : QPainter):
        rect = QRect(cell.x, cell.y, cell.width, cell.height)
        bLeft = rect.bottomLeft()

        # draw name
        fontHeight = 20
        font = painter.font()
        font.setPixelSize(fontHeight)
        textTopRight = QPoint(bLeft.x(), bLeft.y() - fontHeight)
        textRect = QRect(textTopRight, rect.bottomRight())
        thumbName = thumb.name
        painter.drawText(textRect, Qt.AlignHCenter, thumbName)
        #painter.drawRect(rect)

        # draw thumb
        imageRect = QRect(rect.topLeft(), textRect.topRight())
        imageCenter = imageRect.center()
        imageX = int(imageCenter.x() - pic.width() / 2)
        imageY = int(imageCenter.y() - pic.height() / 2)
        imageOrigin = QPoint(imageX, imageY)
        painter.drawPixmap(imageOrigin, pic)

    @pyqtSlot(int, str, Image.Image)
    def updateThumb(self, thumbId : int, path : str, pic : Image.Image):
        thumb = ImageQt.toqimage(pic)
        thumb = self.resizeImage(thumb, (self.thumbWidth, self.thumbHeight))
        thumb = QPixmap.fromImage(thumb)

        self.thumbs[path] = thumb
        self.repaintCanvas()

    def resizeImage(self, img : QImage, size : tuple):
        x = img.width()
        y = img.height()

        if x <= size[0] and y <= size[1]:
            return img

        origK = img.height() / img.width()

        if x > size[0]:
            x = size[0]
            y = int(origK * x)

        if y > size[1]:
            y = size[1]
            x = (y / origK)

        return img.scaled(x, y, transformMode=QtCore.Qt.SmoothTransformation)
