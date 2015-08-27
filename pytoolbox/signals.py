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

import collections, inspect, signal

from . import exceptions, module

_all = module.All(globals())

handlers_by_signal = collections.defaultdict(list)


def propagate_handler(signum, frame):
    errors = {}
    for handler in reversed(handlers_by_signal[signum]):
        try:
            handler(signum, frame)
        except Exception as e:
            errors[handler] = e
    if errors:
        raise RuntimeError(errors)


def register_handler(signum, handler, append=True, reset=False):
    old_handler = signal.getsignal(signum)
    signal.signal(signum, propagate_handler)
    if inspect.isfunction(old_handler) and old_handler != propagate_handler:
        handlers_by_signal[signum].append(old_handler)
    handlers = handlers_by_signal[signum]
    if not append and handlers:
        raise exceptions.MultipleSignalHandlersError(signum=signum, handlers=handlers)
    if reset:
        try:
            handlers.clear()
        except AttributeError:
            # < Python 3.3
            del handlers[:]
    handlers.append(handler)


def register_callback(signum, callback, append=True, reset=False, args=None, kwargs=None):
    return register_handler(signum, lambda s, f: callback(*(args or []), **(kwargs or {})), append, reset)

__all__ = _all.diff(globals())
