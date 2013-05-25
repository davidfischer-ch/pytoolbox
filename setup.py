#!/usr/bin/env python2
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
#

from setuptools import setup, find_packages

setup(name='pyutils',
      version='1.0',
      author='David Fischer',
      author_email='david.fischer.ch@gmail.com',
      description='Some Python utility functions',
      #entry_points={'console_scripts': [
      #    'export-albums=sharepics.bin:export_albums',
      #    'generate-albums-metadata=sharepics.bin:generate_albums_metadata',
      #    'generate-pics-uuid=sharepics.bin:generate_pics_uuid']},
      #include_package_data=True,
      install_requires=['argparse', 'hashlib', 'ipaddr', 'mock'],
      license='GPLv3',
      py_modules=['pyutils'],
      tests_require=['nose'],
      url='https://github.com/davidfischer-ch/pyutils')

