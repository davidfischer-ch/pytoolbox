from pytoolbox.comparison import SlotsEqualityMixin


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


def test_equality_same_class():
    p1 = Point2D(10, -3, 'dot')
    p2 = Point2D(10, -3, 'dot')
    p3 = Point2D(10, -4, 'dot')
    if not (p1 == p2 and p1 != p3):
        raise ValueError()


def test_equality_inheritance():
    p1 = Point2D(10, -3, 'dot')
    p2 = Point2Dv2(10, -3, 'dot')
    p3 = Point2Dv2(10, -4, 'dot')
    if not (p1 == p2 and p1 != p3):
        raise AssertionError()


def test_equality_different_class():
    p1 = Point2D(10, -3, 'dot')
    p2 = Point3D(10, -3, 5, 'dot')
    p3 = Point3D(10, -4, 2, 'dot')
    if not (p1 != p2 and p1 != p3):
        raise AssertionError()
