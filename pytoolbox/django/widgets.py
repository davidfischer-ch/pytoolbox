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

from django.forms import widgets
from django.utils.html import mark_safe


class CalendarDateInput(widgets.DateInput):
    def render(self, *args, **kwargs):
        html = super(CalendarDateInput, self).render(*args, **kwargs)
        return mark_safe(u'<div class="input-append date">{0}'
                         '<span class="add-on"><i class="icon-calendar"></i></span></div>'.format(html))


class ClockTimeInput(widgets.TimeInput):
    def render(self, *args, **kwargs):
        html = super(ClockTimeInput, self).render(*args, **kwargs)
        return mark_safe(u'<div class="input-append bootstrap-timepicker">{0}'
                         '<span class="add-on"><i class="icon-time"></i></span></div>'.format(html))
