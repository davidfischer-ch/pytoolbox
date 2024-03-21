#!/usr/bin/env python

# **************************************************************************************************
#                              PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2024 David Fischer. All rights reserved.
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
from __future__ import annotations

from pathlib import Path
from setuptools.command import develop, install
import itertools
import setuptools
import subprocess
import sys

import pytoolbox

if sys.argv[-1] == 'test':
    sys.exit('Run pytest instead.')

install_requires: list[str] = [
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

extras_require: dict[str, list[str]] = {
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
    'mongodb': [
        'pymongo'
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

features: list[str] = ['all'] + sorted(extras_require) + ['doc', 'test']

labels: dict[str, str] = {
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
    'mongodb': 'MongoDB',
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
        'sphinx>=7.2.6',           # 2024-03-19 Released 2023-09-14
        'sphinx-rtd-theme>=2.0.0'  # 2024-03-19 Released 2023-11-28
    ],
    'test': [
        'colored>=2.2.4',         # 2024-03-19 Released 2023-12-19
        'coverage>=7.4.4',        # 2024-03-19 Released 2024-03-14
        'flake8>=7.0.0',          # 2024-03-19 Released 2024-01-05
        'mypy>=1.9.0',            # 2024-03-19 Released 2024-03-08
        'pylint>=3.1.0',          # 2024-03-19 Released 2024-02-25
        'pytest>=8.1.1',          # 2024-03-19 Released 2024-03-09
        'pytest-cov>=4.1.0',      # 2024-03-19 Released 2023-05-24
        'pytest-pylint>=0.21.0',  # 2024-03-19 Released 2023-10-06
        'pytest-ruff>=0.3.1',     # 2024-03-19 Released 2024-03-09
        'ruff>=0.3.3',            # 2024-03-19 Released 2024-03-15
        # The library is not yet ready to be processed by ruff...

        # Stubs
        'PyGObject-stubs>=2.10.0',          # 2024-03-19 Released 2023-11-16
        'types-pytz>=2024.1.0.20240203',    # 2024-03-19 Released 2024-02-03
        'types-PyYAML>=6.0.12.20240311',    # 2024-03-19 Released 2023-09-23
        'types-requests>=2.31.0.20240311',  # 2024-03-19 Released 2023-10-18
        'types-urllib3>=1.26.25.14'         # 2024-03-19 Released 2023-07-20
    ]
})


def get_command_with_extras(cls: type) -> type:

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


long_description = Path('README.rst').read_text(encoding='utf-8')
setuptools.setup(
    cmdclass={
        'docs': DocsCommand,
        'develop': get_command_with_extras(develop.develop),
        'install': get_command_with_extras(install.install)
    },
    name='pytoolbox',
    python_requires='>=3.11',
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
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
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
