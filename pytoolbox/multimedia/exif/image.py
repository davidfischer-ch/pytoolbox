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

    class Orientation(OrderedEnum):
        NORMAL = 1
        HOR_FLIP = 2
        ROT_180_CCW = 3
        VERT_FLIP = 4
        HOR_FLIP_ROT_270_CW = 5
        ROT_90_CW = 6
        HOR_FLIP_ROT_90_CW = 7
        ROT_270_CW = 8
except ImportError:
    Orientation = lambda x: range(1, 9)[x-1]

from . import tag
from ... import module

_all = module.All(globals())


class Image(tag.TagSet):

    @property
    def copyright(self):
        return self.metadata['Iptc.Application2.Copyright'].data

    @property
    def description(self):
        return self.metadata['Exif.Image.ImageDescription'].data

    @property
    def height(self):
        return self.clean_number(self.metadata.exiv2.get_pixel_height())

    @property
    def orientation(self):
        data = self.metadata['Exif.Image.Orientation'].data
        try:
            return Orientation(data)
        except:
            return None

    @property
    def width(self):
        return self.clean_number(self.metadata.exiv2.get_pixel_width())

__all__ = _all.diff(globals())
