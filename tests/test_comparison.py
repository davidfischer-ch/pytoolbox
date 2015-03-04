# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest
from pytoolbox.comparison import SlotsEqualityMixin
from pytoolbox.unittest import FilterByTagsMixin


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


class TestSlotsEqualityMixin(FilterByTagsMixin, unittest.TestCase):

    tags = ('comparison', )

    def test_equality_same_class(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point2D(10, -3, 'dot')
        p3 = Point2D(10, -4, 'dot')
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def test_equality_inheritance(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point2Dv2(10, -3, 'dot')
        p3 = Point2Dv2(10, -4, 'dot')
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def test_equality_different_class(self):
        p1 = Point2D(10, -3, 'dot')
        p2 = Point3D(10, -3, 5, 'dot')
        p3 = Point3D(10, -4, 2, 'dot')
        self.assertNotEqual(p1, p2)
        self.assertNotEqual(p1, p3)
