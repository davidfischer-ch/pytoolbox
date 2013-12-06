# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

import math, os
from nose.tools import assert_equal, assert_raises
from pytoolbox.encoding import csv_reader
from pytoolbox.filesystem import try_remove
from pytoolbox.serialization import PickleableObject

here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
here = os.path.join(here, u'../../..' if u'build/lib' in here else u'..', u'tests')


class MyPoint(PickleableObject):

    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y)


class TestSerialization(object):

    def test_PickleableObject(self):
        p1 = MyPoint(name=u'My point', x=6, y=-3)
        p1.write(u'test.pkl')
        p2 = MyPoint.read(u'test.pkl', store_filename=True)
        assert_equal(p2.__dict__,
                     {u'y': -3, u'x': 6, u'_pickle_filename': u'test.pkl', u'name': u'My point'})
        p2.write()
        p2.write(u'test2.pkl')
        os.remove(u'test.pkl')
        os.remove(u'test2.pkl')
        p2.write()
        assert(not os.path.exists(u'test2.pkl'))
        assert_equal(p2._pickle_filename, u'test.pkl')
        os.remove(u'test.pkl')
        p2.write(u'test2.pkl', store_filename=True)
        assert(not os.path.exists(u'test.pkl'))
        assert_equal(p2._pickle_filename, u'test2.pkl')
        del p2._pickle_filename
        assert_raises(ValueError, p2.write)
        os.remove(u'test2.pkl')
        try_remove(u'test3.pkl')
        p3 = MyPoint.read(u'test3.pkl', store_filename=True, create_if_error=True, name=u'Default point', x=3, y=-6)
        assert_equal(p3.__dict__,
                     {u'x': 3, u'y': -6, u'_pickle_filename': u'test3.pkl', u'name': u'Default point'})
        os.remove(u'test3.pkl')
        assert_raises(IOError, MyPoint.read, u'test3.pkl')

    def test_csv_reader(self):
        values, i = [(u'David', u'Vélo'), (u'Michaël', u'Tennis de table'), (u'Loïc', u'Piano')], 0
        for name, hobby in csv_reader(os.path.join(here, u'unicode.csv')):
            assert_equal((name, hobby), values[i])
            i += 1
