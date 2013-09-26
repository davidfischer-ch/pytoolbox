#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import math, os
from nose.tools import assert_equal, assert_raises, raises
from pyutils.py_collections import pygal_deque
from pyutils.py_filesystem import try_remove
from pyutils.py_unittest import mock_cmd
from pyutils.py_serialization import PickleableObject
from pyutils.py_subprocess import cmd, screen_launch, screen_list, screen_kill
from pyutils.py_unicode import csv_reader
from pyutils.py_validation import validate_list


class MyPoint(PickleableObject):
    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y)


class TestPyutils(object):

    def test_cmd(self):
        cmd_log = mock_cmd()
        cmd([u'echo', u'it seem to work'], log=cmd_log)
        assert_equal(cmd(u'cat missing_file', fail=False, log=cmd_log)[u'returncode'], 1)
        validate_list(cmd_log.call_args_list, [
                r"call\(u*\"Execute \[u*'echo', u*'it seem to work'\]\"\)",
                r"call\(u*'Execute cat missing_file'\)"])
        assert(cmd(u'my.funny.missing.script.sh', fail=False)[u'stderr'] != u'')
        result = cmd(u'cat {0}'.format(__file__))
        # There are at least 30 lines in this source file !
        assert(len(result[u'stdout'].splitlines()) > 30)

    def test_screen(self):
        try:
            # Launch some screens
            assert_equal(len(screen_launch(u'my_1st_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            # List the launched screen sessions
            screens = screen_list(name=u'my_1st_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_1st_screen'))
            screens = screen_list(name=u'my_2nd_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_2nd_screen'))
        finally:
            # Cleanup
            kill_log = mock_cmd()
            screen_kill(name=u'my_1st_screen', log=kill_log)
            screen_kill(name=u'my_2nd_screen', log=kill_log)
            #raise NotImplementedError(kill_log.call_args_list)
            validate_list(kill_log.call_args_list, [
                r"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_1st_screen'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_1st_screen', u*'-X', u*'quit'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_2nd_screen'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)"])

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
        for name, hobby in csv_reader(u'unicode.csv'):
            assert_equal((name, hobby), values[i])
            i += 1

    def test_validate_list(self):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call([u'my_var', recursive=False])"], regexes)

    @raises(IndexError)
    def test_validate_list_fail_size(self):
        validate_list([1, 2], [1, 2, 3])

    @raises(ValueError)
    def test_validate_list_fail_value(self):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, u"call([u'my_var', recursive='error'])"], regexes)

    def test_pygal_deque(self):
        p = pygal_deque(maxlen=4)

        p.append(5)
        assert_equal(p.list, [5])
        p.append(5)
        p.append(5)
        assert_equal(p.list, [5, None, 5])
        p.append(5)
        assert_equal(p.list, [5, None, None, 5])
        p.append(5)
        assert_equal(p.list, [5, None, None, 5])
        p.append(None)
        assert_equal(p.list, [5, None, None, 5])
        p.append(None)
        assert_equal(p.list, [5, None, None, 5])
        p.append(5)
        assert_equal(p.list, [5, None, None, 5])
        p.append(1)
        assert_equal(p.list, [5, None, 5, 1])
        p.append(None)
        assert_equal(p.list, [5, 5, 1, 1])
        p.append(None)
        assert_equal(p.list, [5, 1, None, 1])
        p.append(None)
        assert_equal(p.list, [1, None, None, 1])
        p.append(2)
        p.append(3)
        assert_equal(p.list, [1, 1, 2, 3])
        p.append(None)
        p.append(2)
        assert_equal(p.list, [2, 3, 3, 2])
