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

#if __name__ == '__main__':
#    import os, sys
#    from os.path import abspath, dirname, join
#    sys.path.append(abspath(dirname(dirname(__file__))))
#    sys.path.append(abspath(join(dirname(dirname(__file__)), 'pyutils')))

#from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
from nose import assert_equal
from pyutils.py_serialization import PickleableObject
from pyutils.py_subprocess import cmd, screen_launch, screen_list, screen_kill

#HELP_TRAVIS = 'Disable screen doctest for Travis CI'

#parser = ArgumentParser(
#    formatter_class=ArgumentDefaultsHelpFormatter,
#    epilog='''Generate a unique identifier (UUID) and save it into pictures's tags (EXIFv2).''')
#parser.add_argument('-t', '--travis', help=HELP_TRAVIS, action='store_true')
#args = parser.parse_args()

#if args.travis:
#    screen_kill.__doc__ = screen_launch.__doc__ = screen_list.__doc__ = ''


class MyPoint(PickleableObject):
    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y


class TestPyutils(object):

    def test_cmd(self):
        cmd(['echo', 'it seem to work'], log=None)  # FIXME todo
        #[DEBUG] Execute ['echo', 'it seem to work']
        assert_equal(cmd('cat missing_file', fail=False, log=None)['returncode'], 0)
        #[DEBUG] Execute cat missing_file
        assert(cmd('my.funny.missing.script.sh', fail=False)['stderr'] != '')
        result = cmd('cat %s' % __file__)
        assert_equal(result['stdout'].splitlines()[0], '#!/usr/bin/env python')

    def test_screen(self):
        #Launch some screens
        assert_equal(screen_launch('my_1st_screen', 'top', fail=False)['stderr'], '')
        assert_equal(screen_launch('my_2nd_screen', 'top', fail=False)['stderr'], '')
        assert_equal(screen_launch('my_2nd_screen', 'top', fail=False)['stderr'], '')
        #List the launched screen sessions
        assert_equal(screen_list(name=r'my_1st_screen'), ['....my_1st_screen'])
        assert_equal(screen_list(name=r'my_2nd_screen'), ['....my_2nd_screen', '....my_2nd_screen'])
        #Cleanup
        screen_kill(name='my_1st_screen', log=None)  # FIXME todo
        #Execute ['screen', '-ls', 'my_1st_screen']
        #Execute ['screen', '-S', '....my_1st_screen', '-X', 'quit']
        screen_kill(name='my_2nd_screen', log=None)  # FIXME todo
        #Execute ['screen', '-ls', 'my_2nd_screen']
        #Execute ['screen', '-S', '....my_2nd_screen', '-X', 'quit']
        #Execute ['screen', '-S', '....my_2nd_screen', '-X', 'quit']

    def test_PickleableObject(self):
        p1 = MyPoint(name='My point', x=6, y=-3)
        p1.write('test.pkl')
        p2 = MyPoint.read('test.pkl', store_filename=True)
        assert(p2.__dict__ == {'y': -3, 'x': 6, '_pickle_filename': 'test.pkl', 'name': 'My point'})
        p2.write()
        delattr(p2, '_pickle_filename')
        try:
            p2.write()
            raise ValueError('Must raise an AttributeError')
        except ValueError:
            pass
        finally:
            os.remove('test.pkl')

#if __name__ == '__main__':
#    import nose
#    nose.runmodule(argv=[__file__], exit=False)
