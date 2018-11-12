#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# **************************************************************************************************
#                              PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2018 David Fischer. All rights reserved.
#
# **************************************************************************************************
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# EUPL v. 1.1 as provided by the European Commission. This project is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function

import itertools, os, setuptools, shutil, subprocess, sys
from codecs import open  # pylint:disable=redefined-builtin
from setuptools.command import develop, install, test

import pytoolbox

try:
    # Check if import succeed and print the exception because setup() stack-trace is useless
    from tests import pytoolbox_runtests  # noqa
except Exception as e:
    sys.stderr.write(
        'WARNING importing pytoolbox_runtests raised the following error: '
        '{0}{1.linesep}'.format(e, os))

PY2 = sys.version_info[0] < 3

install_requires = [
    'argparse',
    'pyaml',
    'python-magic',
    'pytz',
    'six'
]

extras_require = {
    'atlassian': ['jira'],
    'aws': ['boto3'],
    'django': ['django'],
    'django_filter': ['django-filter'],
    'django_formtools': ['django-formtools'],
    'flask': ['flask'],
    'imaging': ['pillow'],
    'jinja2': ['jinja2'],
    'logging': ['termcolor'],
    'mongo': ['celery', 'passlib', 'pymongo'],
    'network': ['tldextract'],
    'rest_framework': ['django-oauth-toolkit', 'djangorestframework>=3'],
    'selenium': ['selenium'],
    'smpte2022': ['fastxor'],
    'unittest': ['mock', 'nose'],
    'vision': ['dlib', 'keras', 'numpy', 'opencv-python', 'tensorflow'],
    'voluptuous': ['voluptuous']
}

# Why not installing following packages for python 3 ?
#
# * hashlib, ipaddr: Part of python 3 standard library
# * sudo pip-3.3 install kitchen -> AttributeError: 'module' object has no attribute 'imap'

if PY2:
    try:
        import hashlib  # noqa
    except ImportError:
        install_requires.append('hashlib')
    install_requires.extend([
        'backports.lzma',
        'ipaddr',
        'kitchen'
    ])


def get_command_with_extras(cls, extras_require):

    class WithExtra(cls):

        user_options = list(itertools.chain(cls.user_options, [
            ('extra-all', None, 'Install dependencies for all features.')
        ], [
            (
                'extra-{0}'.format(e.replace('_', '-')), None,
                'Install dependencies for the feature {0}.'.format(e)
            ) for e in sorted(extras_require.keys())
        ]))
        boolean_options = list(itertools.chain(
            getattr(cls, 'boolean_options', []), ['extra-all'], [o[0] for o in user_options]
        ))

        def initialize_options(self):
            cls.initialize_options(self)
            self.extra_all = None
            for extra in extras_require.keys():
                setattr(self, 'extra_{0}'.format(extra), None)

        def finalize_options(self):
            cls.finalize_options(self)
            for extra in extras_require.keys():
                if (
                    (self.extra_all or getattr(self, 'extra_{0}'.format(extra))) and
                    extra in extras_require
                ):
                    print('Enable dependencies for feature/module {0}'.format(extra))
                    self.distribution.install_requires.extend(
                        self.distribution.extras_require[extra])

    return WithExtra


class docs(setuptools.Command):

    description = 'Generate documentation using Sphinx'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from pytoolbox import encoding, filesystem
        from pytoolbox.subprocess import cmd

        encoding.configure_unicode()

        docs_directory = os.path.join(os.path.dirname(__file__), 'docs')
        source_directory = os.path.join(docs_directory, 'source')
        package_directory = os.path.join(os.path.dirname(__file__), 'pytoolbox')

        # Cleanup previously generated restructured files
        for path in filesystem.find_recursive(
            source_directory, r'^pytoolbox.*\.rst$', unix_wildcards=False
        ):
            os.remove(path)

        cmd([
            'sphinx-apidoc', '--force', '--module-first', '--separate', '-o',
            source_directory, package_directory
        ])
        shutil.rmtree(os.path.join(docs_directory, 'build', 'html'), ignore_errors=True)
        subprocess.check_call(['make', 'html'], cwd=docs_directory)


setuptools.setup(
    cmdclass={
        'docs': docs,
        'develop': get_command_with_extras(develop.develop, extras_require),
        'install': get_command_with_extras(install.install, extras_require),
        'test': get_command_with_extras(test.test, extras_require)
    },
    name='pytoolbox',
    version=pytoolbox.__version__,
    packages=setuptools.find_packages(exclude=['tests']),
    package_data={
        'pytoolbox.ai.vision.face.detect': ['data/*'],
        'pytoolbox.ai.vision.face.recognize': ['data/*']
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=[
        'coverage', 'mock', 'nose', 'nose-exclude',
        'sphinx>=1.3.1', 'sphinx_rtd_theme'  # This is for the documentation
    ],
    test_suite='tests.pytoolbox_runtests.main',
    use_2to3=True,
    use_2to3_exclude_fixers=['lib2to3.fixes.fix_import'],

    # Meta-data for upload to PyPI
    author='David Fischer',
    author_email='david.fischer.ch@gmail.com',
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'Framework :: Flask',
        'License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    description='Toolbox for Python scripts',
    keywords=[
        'celery', 'ffmpeg', 'django', 'flask', 'json', 'juju', 'mock', 'mongodb', 'pil', 'rsync',
        'rtp', 'selenium', 'smpte 2022-1', 'screen', 'subprocess'
    ],
    license='EUPL 1.1',
    long_description=open('README.rst', 'r', encoding='utf-8').read(),
    url='https://github.com/davidfischer-ch/pytoolbox'
)
