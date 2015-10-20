import unittest

from g.gui.common.layoutengine import LayoutEngine
from g.gui.common.rectangle import Rectangle



class MyTestCase(unittest.TestCase):
    def test_size(self):
        le = LayoutEngine()
        le.updateWidth(20)
        le.updateCells(40, 10, 10)

        area = Rectangle(0, 0, 20, 20)
        cells = le.getVisibleCells(area)
        exp = {0: Rectangle(0, 0, 10, 10), 1: Rectangle(10, 0, 10, 10),
               2: Rectangle(0, 10, 10, 10), 3: Rectangle(10, 10, 10, 10)}
        self.assertEqual(200, le.getHeight())
        self.assertDictEqual(exp, cells)

        le.updateWidth(30)
        area = Rectangle(0, 1, 13, 20)
        cells = le.getVisibleCells(area)
        exp = {0: Rectangle(0, 0, 10, 10), 1: Rectangle(10, 0, 10, 10),
               3: Rectangle(0,10, 10, 10), 4: Rectangle(10,10, 10, 10),
               6: Rectangle(0,20, 10, 10), 7: Rectangle(10,20, 10, 10)}
        self.assertEqual(140, le.getHeight())
        self.assertDictEqual(cells, exp)

        cells = le.getVisibleCells(Rectangle(15, 15, 3, 3))
        self.assertDictEqual(cells, {4: Rectangle(10, 10, 10, 10)})

        # test layout with spacing
        le.updateWidth(23)
        cells = le.getVisibleCells(Rectangle(0, 0, 23, 5))
        self.assertDictEqual(cells, {0: Rectangle(0, 0, 10, 10), 1: Rectangle(10, 0, 10, 10)})

        # test not full layout
        le.updateCells(3, 10, 20)
        le.updateWidth(20)
        cells = le.getVisibleCells(Rectangle(0, 20, 20, 15))
        self.assertDictEqual(cells, {2: Rectangle(0, 20, 10, 20)})

if __name__ == '__main__':
    unittest.main()
