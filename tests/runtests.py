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
from nose.tools import assert_equal, raises
from pyutils.py_mock import mock_cmd
from pyutils.py_serialization import JsoneableObject, PickleableObject
from pyutils.py_subprocess import cmd, screen_launch, screen_list, screen_kill
from pyutils.py_unicode import configure_unicode, csv_reader
from pyutils.py_validation import validate_list

configure_unicode()


class MyPoint(JsoneableObject, PickleableObject):
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
                ur"call\(u*\"Execute \[u*'echo', u*'it seem to work'\]\"\)",
                ur"call\(u*'Execute cat missing_file'\)"])
        assert(cmd(u'my.funny.missing.script.sh', fail=False)[u'stderr'] != u'')
        result = cmd(u'cat {0}'.format(__file__))
        # There are at least 30 lines in this source file !
        assert(len(result[u'stdout'].splitlines()) > 30)

    def test_screen(self):
        try:
            # Launch some screens
            assert_equal(screen_launch(u'my_1st_screen', u'top', fail=False)[u'stderr'], u'')
            assert_equal(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr'], u'')
            assert_equal(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr'], u'')
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
            validate_list(kill_log.call_args_list, [
                ur"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_1st_screen'\]\"\)",
                ur"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_1st_screen', u*'-X', u*'quit'\]\"\)",
                ur"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_2nd_screen'\]\"\)",
                ur"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)",
                ur"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)"])

    def test_PickleableObject(self):
        p1 = MyPoint(name=u'My point', x=6, y=-3)
        p1.write(u'test.pkl')
        p2 = MyPoint.read(u'test.pkl', store_filename=True)
        assert_equal(p2.__dict__,
                     {u'y': -3, u'x': 6, u'_pickle_filename': u'test.pkl', u'name': u'My point'})
        p2.write()
        delattr(p2, u'_pickle_filename')
        try:
            p2.write()
            raise ValueError(u'Must raise an AttributeError')
        except ValueError:
            pass
        finally:
            os.remove(u'test.pkl')

    def test_JsoneableObject(self):
        p1 = MyPoint(name=u'My point', x=8, y=-2)
        p2 = MyPoint.from_json(p1.to_json(include_properties=False))
        assert_equal((p1.x, p1.y), (p2.x, p2.y))

    @raises(AttributeError)
    def test_JsoneableObject_fail(self):
        p1 = MyPoint(name=u'My point', x=8, y=-2)
        MyPoint.from_json(p1.to_json(include_properties=True))

    def test_csv_reader(self):
        values, i = [(u'David', u'Vélo'), (u'Michaël', u'Tennis de table'), (u'Loïc', u'Piano')], 0
        for name, hobby in csv_reader(u'unicode.csv'):
            assert_equal((name, hobby), values[i])
            i += 1

    def test_validate_list(self):
        regexes = [ur'\d+', ur"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call([u'my_var', recursive=False])"], regexes)

    @raises(IndexError)
    def test_validate_list_fail_size(self):
        validate_list([1, 2], [1, 2, 3])

    @raises(ValueError)
    def test_validate_list_fail_value(self):
        regexes = [ur'\d+', ur"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, u"call([u'my_var', recursive='error'])"], regexes)

def runtests():
    import nose, sys
    sys.exit(nose.run(argv=[ __file__, u'--with-doctest', u'--with-coverage', u'--cover-package=pyutils', u'-vv',
                           u'../pyutils', u'tests']))

if __name__ == '__main__':
    runtests()
