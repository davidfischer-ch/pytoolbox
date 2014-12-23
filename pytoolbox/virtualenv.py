# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import itertools
from os.path import exists, join

from .filesystem import find_recursive
from .subprocess import rsync

__all__ = ('relocate', )


def relocate(source_directory, destination_directory, encoding='utf-8'):

    if not exists(destination_directory):
        rsync(source_directory, destination_directory, destination_is_dir=True, makedest=True, recursive=True)

    b_source_directory = source_directory.encode(encoding)
    b_destination_directory = destination_directory.encode(encoding)

    for filename in itertools.chain.from_iterable(
        find_recursive(destination_directory, ['*.egg-link', '*.pth', '*.pyc', 'RECORD']),
        find_recursive(join(destination_directory, 'bin'), '*'),
        find_recursive(join(destination_directory, 'src'), '*.so')
    ):
        with open(filename, 'r+b') as f:
            content = f.read().replace(b_source_directory, b_destination_directory)
            f.seek(0)
            f.write(content)
            f.truncate()
