__author__ = 'norman'

from math import ceil


from g.gui.common.rectangle import Rectangle

class LayoutEngine(object):
    def __init__(self):
        self.__height = 0
        self.__width = 0
        self.__cellsTotal = 0

        self.__cellWidth = 160
        self.__cellHeight = 160
        self.__cellSpacer = 0

        self.__rows = 0
        self.__columns = 0

    def getCellWidth(self):
        return self.__cellWidth

    def updateWidth(self, width : int):
        self.__width = width
        self.__updateLayout()

    def getSize(self):
        return self.__width, self.__height

    def getHeight(self):
        return self.__height
    def getWidth(self):
        return self.__width

    def updateCells(self, n : int, width : int, height : int):
        assert(width > 0 and height > 0)

        self.__cellHeight = height
        self.__cellWidth = width
        self.__cellsTotal = n
        self.__updateLayout()
        self.cells = {}

    def _getCellPosition(self, cellNum : int):
        row, col = divmod(cellNum, self.__columns)

        x = col * self.__cellWidth
        y = row * self.__cellHeight
        return x, y

    def getCellRect(self, cellNum : int) -> Rectangle:
        return self.cells.get(cellNum)

    def getCell(self, row : int, col : int):
        x = col * self.__cellWidth
        y = row * self.__cellHeight

        return Rectangle(x, y, self.__cellWidth, self.__cellHeight)

    def getVisibleCells(self, area : Rectangle):
        """
        Returns rectangles of cells, which are visible in area

        :param area: Visible area
        :return: areas of cells, which should be shown
        """
        startCol = max(area.x // self.__cellWidth, 0)
        endCol = min(max(ceil((area.x + area.width) / self.__cellWidth) - 1, 0), self.__columns - 1)
        startRow = max(area.y // self.__cellHeight, 0)
        endRow = max(ceil((area.y + area.height) / self.__cellHeight) - 1, 0)

        self.cells.clear()
        for row in range(startRow, endRow + 1):
            for col in range(startCol, endCol + 1):
                cellNum = col + row * self.__columns
                if cellNum >= self.__cellsTotal:
                    continue
                self.cells[cellNum] = self.getCell(row, col)

        return self.cells

    def __updateLayout(self):
        self.__columns = max(self.__width // self.__cellWidth, 1)
        self.__rows = self.__cellsTotal // self.__columns
        if self.__rows % self.__columns:
            self.__rows += 1
        self.__height = self.__rows * self.__cellHeight

        freeHSpace = self.__width % self.__cellWidth
        if freeHSpace < (self.__columns + 1):
            self.__cellSpacer = 0
        else:
            self.__cellSpacer = freeHSpace // self.__columns
