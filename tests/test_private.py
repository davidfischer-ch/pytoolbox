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

from pytoolbox.private import _parse_kwargs_string

from . import base


class TestPrivate(base.TestCase):

    tags = ('private', )

    def test_parse_kwargs_string(self):
        self.dict_equal(_parse_kwargs_string('year=1950 ;  style=jazz', year=int, style=str), {
            'year': 1950, 'style': 'jazz'
        })
        self.dict_equal(_parse_kwargs_string(' like_it=True ', like_it=lambda x: x == 'True'), {'like_it': True})

    def test_parse_kwargs_string_key_error(self):
        with self.raises(KeyError):
            _parse_kwargs_string(' pi=3.1416; ru=2', pi=float)

    def test_parse_kwargs_string_value_error(self):
        with self.raises(ValueError):
            _parse_kwargs_string(' a_number=yeah', a_number=int)
