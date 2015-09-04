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

from django import dispatch as _dispatch

from ..models import utils as _utils
from ... import module as _module

_all = _module.All(globals())


class InstanceSignal(_dispatch.Signal):

    def __init__(self, providing_args=None, use_caching=False):
        providing_args = providing_args or ['instance']
        if 'instance' not in providing_args:
            providing_args.insert(0, 'instance')
        return super(InstanceSignal, self).__init__(providing_args, use_caching)

    def send(self, sender=None, **named):
        return super(InstanceSignal, self).send(_utils.get_base_model(sender or named['instance']), **named)

    def send_robust(self, sender=None, **named):
        return super(InstanceSignal, self).send(_utils.get_base_model(sender or named['instance']), **named)

post_state_change = InstanceSignal(providing_args=['previous_state', 'result', 'args', 'kwargs'])

__all__ = _all.diff(globals())
