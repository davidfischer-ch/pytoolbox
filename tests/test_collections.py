# -*- coding: utf-8 -*-

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

from nose.tools import eq_
from pytoolbox.collections import pygal_deque


class TestCollections(object):

    def test_pygal_deque(self):
        p = pygal_deque(maxlen=4)

        p.append(5)
        eq_(p.list(fill=False), [5])
        p.append(5)
        p.append(5)
        eq_(p.list(fill=False), [5, None, 5])
        p.append(5)
        eq_(p.list(fill=False), [5, None, None, 5])
        p.append(5)
        eq_(p.list(fill=False), [5, None, None, 5])
        p.append(None)
        eq_(p.list(fill=False), [5, None, None, 5])
        p.append(None)
        eq_(p.list(fill=False), [5, None, None, 5])
        p.append(5)
        eq_(p.list(fill=False), [5, None, None, 5])
        eq_(p.list(fill=True), [5, 5, 5, 5])
        p.append(1)
        eq_(p.list(fill=False), [5, None, 5, 1])
        p.append(None)
        eq_(p.list(fill=False), [5, 5, 1, 1])
        p.append(None)
        eq_(p.list(fill=False), [5, 1, None, 1])
        eq_(p.list(fill=True), [5, 1, 1, 1])
        p.append(None)
        eq_(p.list(fill=False), [1, None, None, 1])
        p.append(2)
        p.append(3)
        eq_(p.list(fill=False), [1, 1, 2, 3])
        p.append(None)
        p.append(2)
        eq_(p.list(fill=False), [2, 3, 3, 2])
