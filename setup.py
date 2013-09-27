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

import os, sys
from codecs import open
from setuptools import setup

os.chdir(os.path.abspath(os.path.dirname(__file__)))

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print('Converting code to Python 3 helped by 2to3')
    kwargs['use_2to3'] = True

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = """
Development Status :: 4 - Beta
Intended Audience :: Developers
Framework :: Flask
License :: OSI Approved :: GNU GPLv3
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: Implementation :: CPython
Topic :: Software Development :: Libraries :: Python Modules
"""

not_yet_tested = """
Operating System :: MacOS :: MacOS X
Operating System :: Unix
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
"""

keywords = ['ffmpeg', 'django', 'flask', 'json', 'juju', 'mock', 'mongodb', 'rsync', 'screen', 'subprocess']

install_requires = [
    'argparse',  # FIXME version
    'django',    # FIXME version
    'flask',     # FIXME version
    'mock',      # FIXME version
    'pyaml',     # FIXME version
    'pymongo',   # FIXME version
    'pygal',     # FIXME version
    'six'        # FIXME version
]

if major < 3:
    install_requires += [
        'hashlib',   # FIXME version
        'ipaddr',   # FIXME version
        'kitchen',  # FIXME version
        'ming'      # FIXME version
    ]

setup(name='pyutils',
    version='v4.8.7-beta',
    packages=['pyutils'],
    description='Some Python utility functions',
    long_description=open('README.rst', 'r', encoding='utf-8').read(),
    author='David Fischer',
    author_email='david.fischer.ch@gmail.com',
    url='https://github.com/davidfischer-ch/pyutils',
    license='GNU GPLv3',
    classifiers=filter(None, classifiers.split('\n')),
    keywords=keywords,
    install_requires=install_requires,
    setup_requires=['coverage', 'mock', 'nose'],
    tests_require=['coverage', 'mock', 'nose'],
    # Thanks to https://github.com/graingert/django-browserid/commit/46c763f11f76b2f3ba365b164196794a37494f44
    test_suite='tests.runtests.main', **kwargs)
