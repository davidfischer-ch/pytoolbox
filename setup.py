#!/usr/bin/env python
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

import os, sys
from codecs import open
from setuptools import setup, find_packages
try:
    # Check if import succeed and print the exception because setup() ciphered stack-trace is not useful
    from tests import pytoolbox_runtests
except Exception as e:
    sys.stderr.write('WARNING importing pytoolbox_runtests raised the following error: {0}{1.linesep}'.format(e, os))

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = """
Development Status :: 5 - Production/Stable
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
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Libraries :: Python Modules
"""

not_yet_tested = """
Operating System :: MacOS :: MacOS X
Operating System :: Unix
"""

keywords = [
    'celery', 'ffmpeg', 'django', 'flask', 'json', 'juju', 'mock', 'mongodb', 'rsync', 'rtp', 'selenium',
    'smpte 2022-1', 'screen', 'subprocess'
]

install_requires = [
    'argparse',
    'jinja2',
    'mock',
    'nose',
    'passlib',
    'pyaml',
    'pycallgraph',
    'pygal',
    'pymongo',
    'python-magic',
    'pytz',
    'six',
    'termcolor'
]

extras_require = {
    'atlassian':        ['jira'],
    'django':           ['django'],
    'django_filter':    ['django-filter'],
    'django_formtools': ['django-formtools'],
    'flask':            ['flask'],
    'mongo':            ['celery'],
    'rest_framework':   ['djangorestframework>=3'],
    'selenium':         ['selenium'],
    'smpte2022':        ['fastxor'],
    'voluptuous':       ['voluptuous']
}

# Why not installing following packages for python 3 ?
#
# * hashlib, ipaddr: Part of python 3 standard library
# * sudo pip-3.3 install kitchen -> AttributeError: 'module' object has no attribute 'imap'
# * sudo pip-3.3 install ming    -> File "/tmp/pip_build_root/ming/setup.py", line 5, SyntaxError: invalid syntax

PY3 = sys.version_info[0] > 2

if not PY3:
    extras_require['ming'] = ['ming']
    try:
        import hashlib
    except ImportError:
        install_requires.append('hashlib')
    install_requires += [
        'backports.lzma',
        'ipaddr',
        'kitchen'
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

setup(
    name='pytoolbox',
    version='10.2.0',
    packages=find_packages(exclude=['tests']),
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=['coverage==3.7.1', 'mock', 'nose', 'nose-exclude'],
    test_suite='tests.pytoolbox_runtests.main',
    use_2to3=PY3,
    use_2to3_exclude_fixers=['lib2to3.fixes.fix_import'],

    # Meta-data for upload to PyPI
    author='David Fischer',
    author_email='david.fischer.ch@gmail.com',
    classifiers=filter(None, classifiers.split(os.linesep)),
    description=description,
    keywords=keywords,
    license='EUPL 1.1',
    long_description=open('README.rst', 'r', encoding='utf-8').read(),
    url='https://github.com/davidfischer-ch/pytoolbox'
)
