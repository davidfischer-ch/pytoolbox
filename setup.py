#!/usr/bin/env python
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

import sys
from codecs import open
from setuptools import setup, find_packages

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print('Converting code to Python 3 helped by 2to3')
    kwargs['use_2to3'] = True
    kwargs['use_2to3_exclude_fixers'] = ['lib2to3.fixes.fix_import']

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = """
Development Status :: 4 - Beta
Intended Audience :: Developers
Framework :: Flask
License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: Implementation :: CPython
Topic :: Software Development :: Libraries :: Python Modules
"""

not_yet_tested = """
Operating System :: MacOS :: MacOS X
Operating System :: Unix
"""

keywords = [
    'celery', 'ffmpeg', 'django', 'flask', 'json', 'juju', 'mock', 'mongodb', 'rsync', 'rtp', 'smpte 2022-1', 'screen',
    'subprocess'
]

install_requires = [
    'argparse',     # FIXME version
    'mock',         # FIXME version
    'passlib',      # FIXME version
    'pyaml',        # FIXME version
    'pycallgraph',  # FIXME version
    'pygal',        # FIXME version
    'pymongo',      # FIXME version
    'pytz',         # FIXME version
    'six',          # FIXME version
]

extras_require = {
    'django':    ['django'],   # FIXME version
    'flask':     ['flask'],    # FIXME version
    'mongo':     ['celery'],   # FIXME version
    'smpte2022': ['fastxor'],  # FIXME version
}

# Why not installing following packages for python 3 ?
#
# * hashlib, ipaddr: Part of python 3 standard library
# * sudo pip-3.3 install kitchen -> AttributeError: 'module' object has no attribute 'imap'
# * sudo pip-3.3 install ming    -> File "/tmp/pip_build_root/ming/setup.py", line 5, SyntaxError: invalid syntax

if major < 3:
    extras_require['ming'] = ['ming']  # FIXME version
    try:
        import hashlib
    except ImportError:
        install_requires.append('hashlib')  # FIXME version
    install_requires += [
        'ipaddr',   # FIXME version
        'kitchen',  # FIXME version
    ]

description = 'Toolbox for Python scripts'

if len(sys.argv) > 1 and sys.argv[1] in ('develop', 'install', 'test'):
    old_args = sys.argv[:]
    sys.argv = [old_args[0]] + [arg for arg in old_args if '--extra' in arg or '--help' in arg]
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=description)
    for extra in extras_require.keys():
        parser.add_argument('--extra-{0}'.format(extra), action='store_true',
                            help='Install dependencies for the module/feature {0}.'.format(extra))
    parser.add_argument('--extra-all', action='store_true', help='Install dependencies for all modules/features.')
    args = vars(parser.parse_args())

    for extra, enabled in sorted(args.items()):
        extra = extra.replace('extra_', '')
        if (args['extra_all'] or enabled) and extra in extras_require:
            print('Enable dependencies for feature/module {0}'.format(extra))
            install_requires += extras_require[extra]
    sys.argv = [arg for arg in old_args if not '--extra' in arg]

setup(name='pytoolbox',
      version='8.1.0-beta',
      packages=find_packages(exclude=['tests']),
      description=description,
      long_description=open('README.rst', 'r', encoding='utf-8').read(),
      author='David Fischer',
      author_email='david.fischer.ch@gmail.com',
      url='https://github.com/davidfischer-ch/pytoolbox',
      license='EUPL 1.1',
      classifiers=filter(None, classifiers.split('\n')),
      keywords=keywords,
      extras_require=extras_require,
      install_requires=install_requires,
      tests_require=['coverage', 'mock', 'nose'],
      # Thanks to https://github.com/graingert/django-browserid/commit/46c763f11f76b2f3ba365b164196794a37494f44
      test_suite='tests.pytoolbox_runtests.main', **kwargs)
