__author__ = 'norman'

def rectIntersect(a, b):
    x1, y1, w1, h1 = a[0], a[1], a[2], a[3]
    x2, y2, w2, h2 = b[0], b[1], b[2], b[3]

    r1left = x1
    r2left = x2
    r1right = x1 + w1
    r2right = x2 + w2
    r1bottom = y1 + h1
    r2bottom = y2 + h2
    r1top = y1
    r2top = y2

    left = max(r1left, r2left)
    right = min(r1right, r2right)
    bottom = min(r1bottom, r2bottom)
    top = max(r1top, r2top)

    width = right - left
    height = bottom - top

    if (width <= 0) or (height <= 0):
        return None
    else:
        return left, top, width, height


class Rectangle(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @staticmethod
    def fromSequence(r):
        return Rectangle(r[0], r[1], r[2], r[3])

    def intersect(self, other):
        a = (self.x, self.y, self.width, self.height)
        b = (other.x, other.y, other.width, other.height)
        c = rectIntersect(a, b)

        return Rectangle(c[0], c[1], c[2], c[3])

    def tuple(self):
        return self.x, self.y, self.width, self.height

    def list(self):
        return [self.x, self.y, self.width, self.height]

    def __getitem__(self, item):
        return self.list()[item]

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and \
                self.width == other.width and self.height == other.height
    def __str__(self):
        return 'Rectangle[%i, %i, %i, %i]' % self.tuple()
    def __repr__(self):
        return self.__str__()