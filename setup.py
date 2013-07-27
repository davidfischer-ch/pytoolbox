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

from setuptools import setup, sys

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print('Converting code to Python 3 helped by 2to3')
    kwargs['use_2to3'] = True

classifiers = """
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

not_yet_tested = """
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
"""

setup(name='pyutils',
      version='2.0.1-beta',
      packages=['pyutils'],
      description='Some Python utility functions',
      long_description=open('README.rst').read(),
      author='David Fischer',
      author_email='david.fischer.ch@gmail.com',
      url='https://github.com/davidfischer-ch/pyutils',
      license='GNU GPLv3',
      classifiers=filter(None, classifiers.split('\n')),
      keywords=['ffmpeg', 'flask', 'json', 'juju', 'mock', 'rsync', 'screen', 'subprocess'],
      install_requires=[
            'argparse',  # FIXME > 1.2
            'flask',     # ...
            'hashlib',   # ...
            'ipaddr',
            'ming',
            'mock',
            'six'],
      setup_requires=['coverage', 'nose'],
      tests_require=['coverage', 'nose'],
      test_suite='nose.main', **kwargs)
