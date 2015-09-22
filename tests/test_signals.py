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

import os, signal

from pytoolbox import exceptions, signals

from . import base


class TestSignals(base.TestCase):

    tags = ('signals', )

    def append_list_callback(self, number):
        self.flag = True
        self.list.append(number)

    def raise_handler(self, signum, frame):
        raise AssertionError

    def set_flag_handler(self, signum, frame):
        self.flag = True

    def set_flag_callback(self, *args, **kwargs):
        self.assertEqual(args, (None, ))
        self.flag = True

    def setUp(self):
        # reset signal handlers
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.name = self.flag = None
        self.list = []

    def tearDown(self):
        if self.name:
            self.assertTrue(self.flag, self.name)
            if self.list:
                self.assertListEqual(self.list, sorted(self.list), self.name)

    def test_handler(self):
        self.name = 'test_handler'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_handler_reset(self):
        self.name = 'test_handler_reset'
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler, reset=True)
        signals.register_handler(signal.SIGTERM, self.set_flag_handler, reset=True)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback(self):
        self.name = 'test_callback'
        signals.register_callback(signal.SIGTERM, self.set_flag_callback, args=[None])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callbacks_call_order_is_lifo(self):
        self.name = 'test_callbacks_call_order_is_lifo'
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[3])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[2])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[1])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback_unauthorized_append(self):
        self.name = 'test_callback_unauthorized_append'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        with self.assertRaises(exceptions.MultipleSignalHandlersError):
            signals.register_callback(signal.SIGTERM, self.set_flag_callback, append=False, args=[None])
        os.kill(os.getpid(), signal.SIGTERM)
