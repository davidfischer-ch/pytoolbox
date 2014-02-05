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

import os
from functools import wraps
from .console import confirm
from .subprocess import cmd


def confirm_it(message, default=False, abort_message=u'Operation aborted by the user'):
    u"""Ask for confirmation before calling the decorated method."""
    def _confirm_it(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if confirm(message, default=default):
                return f(*args, **kwargs)
            print(abort_message)
        return wrapper
    return _confirm_it


def disable_iptables():
    u"""
    Stop the iptables service if necessary, execute the decorated method and then reactivate iptables if it was
    previously stopped.
    """
    def _disable_iptables(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                try:
                    cmd(u'sudo service iptables stop', shell=True)
                    print(u'Disable iptables')
                    has_iptables = True
                except:
                    has_iptables = False
                return f(*args, **kwargs)
            finally:
                if has_iptables:
                    print(u'Enable iptables')
                    cmd(u'sudo service iptables start', shell=True)
        return wrapper
    return _disable_iptables


def root_required(error_message=u'This script must be run as root.'):
    u"""Raise an exception if the current user is not root."""
    def _root_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not os.geteuid() == 0:
                raise RuntimeError(error_message)
            return f(*args, **kwargs)
        return wrapper
    return _root_required
