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

try:
    from ...enum import OrderedEnum

    class ExposureMode(OrderedEnum):
        AUTO = 0
        MANUAL = 1
        BRACKET = 2
except ImportError:
    ExposureMode = {0: 'auto', 1: 'manual', 2: 'bracket'}.get

from . import tag
from ... import module

_all = module.All(globals())


class Photo(tag.TagSet):

    @property
    def date(self):
        return self.metadata.get_date()

    @property
    def exposure_mode(self):
        return ExposureMode(self.metadata['Exif.Photo.ExposureMode'].data)

    @property
    def exposure_time(self):
        return self.metadata['Exif.Photo.ExposureTime'].data

    @property
    def fnumber(self):
        return self.clean_number(self.metadata['Exif.Photo.FNumber'].data)

    @property
    def focal_length(self):
        return self.clean_number(self.metadata['Exif.Photo.FocalLength'].data)

    @property
    def iso_speed(self):
        return self.clean_number(self.metadata['Exif.Photo.ISOSpeedRatings'].data)

    @property
    def sensing_method(self):
        return self.metadata['Exif.Photo.SensingMethod'].data

    @property
    def white_balance(self):
        return self.metadata['Exif.Photo.WhiteBalance'].data

__all__ = _all.diff(globals())
