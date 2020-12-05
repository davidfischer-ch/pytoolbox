from pytoolbox.comparison import SlotsEqualityMixin

from . import base


class Point2D(SlotsEqualityMixin):

    __slots__ = ('x', 'y', 'name')

    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name


class Point2Dv2(Point2D):
    pass


class Point3D(SlotsEqualityMixin):

    __slots__ = ('x', 'y', 'z', 'name')

    def __init__(self, x, y, z, name):
        self.x = x
        self.y = y
        self.z = z
        self.name = name


class TestSlotsEqualityMixin(base.TestCase):

    tags = ('comparison', )

    def test_equality_same_class(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point2D(10, -3, 'dot')
        p3 = Point2D(10, -4, 'dot')
        self.equal(p1, p2)
        self.not_equal(p1, p3)

    def test_equality_inheritance(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point2Dv2(10, -3, 'dot')
        p3 = Point2Dv2(10, -4, 'dot')
        self.equal(p1, p2)
        self.not_equal(p1, p3)

    def test_equality_different_class(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point3D(10, -3, 5, 'dot')
        p3 = Point3D(10, -4, 2, 'dot')
        self.not_equal(p1, p2)
        self.not_equal(p1, p3)
