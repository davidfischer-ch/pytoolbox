#!/usr/bin/env python

# **************************************************************************************************
#                              PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2023 David Fischer. All rights reserved.
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

from pathlib import Path
from setuptools.command import develop, install
import itertools, setuptools, subprocess, sys

import pytoolbox

if sys.argv[-1] == 'test':
    sys.exit('Run pytest instead.')

install_requires = [
    'argparse',
    'pyaml',
    'python-magic',
    'pytz',
    'requests',
    'termcolor'
]

try:
    import grp
    _ = grp
except ImportError:
    # Required on Windows
    install_requires.append('python-magic-bin')

extras_require = {
    'atlassian': [
        'jira'
    ],
    'aws': [
        'boto3'
    ],
    'django': [
        'django'
    ],
    'django_filter': [
        'django-filter'
    ],
    'django_formtools': [
        'django-formtools'
    ],
    'flask': [
        'flask'
    ],
    'imaging': [
        'pillow',
        'PyGObject'
    ],
    'jinja2': [
        'jinja2'
    ],
    'network': [
        'tldextract'
    ],
    'pandas': [
        'ezodf',
        'lxml',
        'pandas'
    ],
    'rest_framework': [
        'django-oauth-toolkit',
        'djangorestframework>=3'
    ],
    'selenium': [
        'selenium'
    ],
    'smpte2022': [
        'fastxor'
    ],
    'vision': [
        'dlib',
        'keras',
        'numpy',
        'opencv-python',
        'tensorflow'
    ],
    'voluptuous': [
        'voluptuous'
    ]
}

features = ['all'] + sorted(extras_require) + ['doc', 'test']

labels = {
    # Features
    'all': 'All Modules',
    'atlassian': 'Atlassian',
    'aws': 'AWS',
    'django': 'Django',
    'django_filter': 'Django Filter',
    'django_formtools': 'Django Form Tools',
    'flask': 'Flask',
    'imaging': 'Imaging',
    'jinja2': 'Jinja2',
    'logging': 'Logging',
    'network': 'Networking',
    'pandas': 'Pandas',
    'rest_framework': 'Django REST Framework',
    'selenium': 'Selenium',
    'smpte2022': 'SMPTE-2022',
    'unittest': 'Unit Test',
    'vision': 'Vision',
    'voluptuous': 'Voluptuous',

    # Actions
    'doc': 'Pytoolbox Docs',
    'test': 'Pytoolbox Tests',
}

extras_require.update({
    'all': sorted(set(itertools.chain.from_iterable(extras_require.values()))),
    'doc': [
        'sphinx>=6',
        'sphinx-rtd-theme>=1.2.2'
    ],
    'test': [
        'coverage>=7.2.7,<8',        # 07-06-2023 Released 29-05-2023
        'flake8>=6,<7',              # 07-06-2023 Released 23-11-2022
        'pylint>=2.17.4,<3',         # 07-06-2023 Released 06-05-2023
        'pytest>=7.3.1,<8',          # 07-06-2023 Released 14-04-2023
        'pytest-cov>=4.1.0,<5',      # 07-06-2023 Released 24-05-2023
        'pytest-pylint>=0.19.0,<1',  # 07-06-2023 Released 10-09-2022

        # For MyPy
        'PyGObject-stubs>=2.8.0',

         # 07-06-2023 Bug still not resolved
         # Bug https://github.com/tholo/pytest-flake8/issues/87
         # Fix https://github.com/tholo/pytest-flake8/pull/88/files
         # 'pytest-flake8'
    ]
})


def get_command_with_extras(cls):

    class WithExtra(cls):

        user_options = [
            *cls.user_options,
            *[
                (
                    f"extra-{feature.replace('_', '-')}", None,
                    f'Install dependencies for {labels[feature]}.'
                ) for feature in features
            ]
        ]

        boolean_options = [
            *getattr(cls, 'boolean_options', []),
            'extra-all',
            *[o[0] for o in user_options]
        ]

        def initialize_options(self):
            cls.initialize_options(self)
            for feature in features:
                setattr(self, f'extra_{feature}', None)

        def finalize_options(self):
            cls.finalize_options(self)
            for feature in features:
                if getattr(self, f'extra_{feature}'):
                    print(f'Enable dependencies for {labels[feature]}')
                    self.distribution.install_requires.extend(
                        self.distribution.extras_require[feature])

    return WithExtra


class DocsCommand(setuptools.Command):  # pylint:disable=duplicate-code

    description = 'Generate documentation using Sphinx'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from pytoolbox import filesystem
        project = Path(__file__).resolve().parent
        source = project / 'docs' / 'source'

        # Cleanup previously generated restructured files
        for path in filesystem.find_recursive(source, r'^pytoolbox.*\.rst$', regex=True):
            filesystem.remove(path)

        subprocess.run([
            'sphinx-apidoc',
            '--force',
            '--module-first',
            '--separate',
            '-o', source,
            project / 'pytoolbox'
        ], check=True)
        filesystem.remove(project / 'docs' / 'build' / 'html', recursive=True)
        subprocess.run(['make', 'html'], cwd=project / 'docs', check=True)


with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    cmdclass={
        'docs': DocsCommand,
        'develop': get_command_with_extras(develop.develop),
        'install': get_command_with_extras(install.install)
    },
    name='pytoolbox',
    python_requires='>=3.9',
    version=pytoolbox.__version__,
    packages=setuptools.find_packages(exclude=['tests']),
    package_data={
        'pytoolbox.ai.vision.face.detect': ['data/*'],
        'pytoolbox.ai.vision.face.recognize': ['data/*']
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=extras_require['test'],

    # Meta-data for upload to PyPI
    author='David Fischer',
    author_email='david@fisch3r.net',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    description='Toolbox for Python scripts',
    keywords=[
        'celery',
        'ffmpeg',
        'django',
        'flask',
        'json',
        'juju',
        'mock',
        'pillow',
        'rsync',
        'rtp',
        'selenium',
        'smpte 2022-1',
        'screen',
        'subprocess'
    ],
    license='EUPL 1.1',
    long_description=long_description,
    url='https://github.com/davidfischer-ch/pytoolbox'
)
