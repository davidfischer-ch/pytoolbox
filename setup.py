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

from codecs import open
from setuptools import setup, sys

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print(u'Converting code to Python 3 helped by 2to3')
    kwargs[u'use_2to3'] = True

classifiers = u"""
Intended Audience :: Developers
License :: OSI Approved :: GNU GPLv3
Development Status :: 4 - Beta
Natural Language :: English
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Operating System :: MacOS :: MacOS X
Operating System :: Unix
Programming Language :: Python
Programming Language :: Python :: Implementation :: CPython
"""

not_yet_tested = u"""
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
"""

setup(name=u'pyutils',
      version=u'2.0.1-beta',
      packages=[u'pyutils'],
      description=u'Some Python utility functions',
      long_description=open(u'README.rst', u'r', encoding=u'utf-8').read(),
      author=u'David Fischer',
      author_email=u'david.fischer.ch@gmail.com',
      url=u'https://github.com/davidfischer-ch/pyutils',
      license=u'GNU GPLv3',
      classifiers=filter(None, classifiers.split('\n')),
      keywords=[u'ffmpeg', u'flask', u'json', u'juju', u'mock', u'rsync', u'screen', u'subprocess'],
      install_requires=[
            u'argparse',  # FIXME version
            u'flask',     # FIXME version
            u'hashlib',   # FIXME version
            u'ipaddr',    # FIXME version
            u'ming',      # FIXME version
            u'mock',      # FIXME version
            u'pyaml',     # FIXME version
            u'six'],      # FIXME version
      setup_requires=[u'coverage', u'nose'],
      tests_require=[u'coverage', u'nose'],
      test_suite=u'nose.main', **kwargs)
