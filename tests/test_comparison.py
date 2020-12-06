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
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point2D(10, -3, 'dot')
    point_3 = Point2D(10, -4, 'dot')
    if not (point_1 == point_2 and point_1 != point_3):
        raise ValueError()


def test_equality_inheritance():
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point2Dv2(10, -3, 'dot')
    point_3 = Point2Dv2(10, -4, 'dot')
    if not (point_1 == point_2 and point_1 != point_3):
        raise AssertionError()


def test_equality_different_class():
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point3D(10, -3, 5, 'dot')
    point_3 = Point3D(10, -4, 2, 'dot')
    if point_1 in (point_2, point_3):
        raise AssertionError()
