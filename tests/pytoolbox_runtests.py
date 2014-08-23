#!/usr/bin/env python
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

import sys
from os.path import dirname, join
from pytoolbox.network.http import download
from pytoolbox.unittest import runtests


def main():
    print('Download the test media assets')
    root = dirname(__file__)
    download('http://techslides.com/demos/sample-videos/small.mp4', join(root, 'small.mp4'))
    print('Run the tests with nose')
    # Ignore django module (how to filter by module ?) + ignore ming module if Python > 2.x
    ignore = ('fields.py|mixins.py|signals.py|storage.py|utils.py|widgets.py|pytoolbox_filters.py|'
              'pytoolbox_tags.py' + ('|session.py|schema.py' if sys.version_info[0] > 2 else ''))
    return runtests(__file__, cover_packages=['pytoolbox'], packages=['pytoolbox', 'tests'], ignore=ignore)

if __name__ == '__main__':
    main()
