from PyQt5.QtCore import QLine, QRect
from PyQt5.QtGui import QColor, QPaintEvent, QPainter, QResizeEvent
from PyQt5.QtWidgets import QWidget, QLayout, QVBoxLayout, QLabel, QGraphicsScene, QGraphicsView, \
    QScrollArea, QSizePolicy, QGridLayout, QScrollBar

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
    def __init__(self):
        super().__init__()

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
        print('New canvas size: ', w, '  ', h)

    def canvasPaintEvent(self, ev : QPaintEvent):
        repaintRect = ev.rect()
        repaintArea = Rectangle(repaintRect.x(), repaintRect.y(), repaintRect.width(),
                repaintRect.height())

        cells = self.layoutEngine.getVisibleCells(repaintArea)

        painter = QPainter(self.w)
        for cellNum, cell in cells.items():
            rect = QRect(cell.x, cell.y, cell.width, cell.height)
            painter.drawRect(rect)

