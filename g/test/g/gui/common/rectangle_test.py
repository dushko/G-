import unittest

from g.gui.common.rectangle import Rectangle


class RectangleTestCase(unittest.TestCase):

    def test_eq(self):
        a = Rectangle(0, 10, 20, 30)
        b = Rectangle(0, 10, 20, 30)
        c = Rectangle(10, 10, 20, 30)

        t = a == b
        self.assertTrue(a == b)

        self.assertEqual(a, b)
        self.assertEqual(b, a)
        self.assertNotEqual(c, a)
        self.assertNotEqual(c, a)
        self.assertNotEqual(c, b)
        self.assertNotEqual(b, c)

if __name__ == '__main__':
    unittest.main()
