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
from pytoolbox.unittest import runtests

def main():
    # Ignore django module (how to filter by module ?) + ignore ming module if Python > 2.x
    ignore = (u'forms.py|models.py|signals.py|storage.py|views.py|widgets.py|pytoolbox_tags.py' +
              (u'|session.py|schema.py' if sys.version_info[0] > 2 else u''))
    return runtests(__file__, cover_packages=[u'pytoolbox'], packages=[u'pytoolbox', u'tests'], ignore=ignore)

if __name__ == u'__main__':
    main()
