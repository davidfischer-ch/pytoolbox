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

from . import client
from .. import module

_all = module.All(globals())


class LiveTestCaseMixin(object):

    live_client_class = client.LiveClient

    def setUp(self):
        """Call super's setUp and instantiate a live test client, only once."""
        super(LiveTestCaseMixin, self).setUp()
        if not hasattr(self.__class__, 'client'):
            self.__class__.client = self.live_client_class(self.live_server_url)
        self.client = self.__class__.client

    @classmethod
    def tearDownClass(cls):
        """Quit the live-test client and call super's tearDownClass."""
        if hasattr(cls, 'client'):
            cls.client.quit()
        super(LiveTestCaseMixin, cls).tearDownClass()

    # Asserts

    def assertElementEqual(self, name, value, enabled=True):
        """Check the properties of an element. Works with both WebElement and Select."""
        self.assertElementIsEnabled(name) if enabled else self.assertElementIsDisabled(name)
        element = self.client.find_name(name)
        Select = self.client.web_driver.web_element_classes['select']
        method = self.assertSelectOptions if isinstance(element, Select) else self.assertElementValue
        method(name, value)

    def assertElementIsDisabled(self, name, *args, **kwargs):
        self.assertFalse(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsEnabled(self, name, *args, **kwargs):
        self.assertTrue(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsReadOnly(self, name):
        self.assertIsNotNone(self.client.find_name(name).get_attribute('readonly'))

    def assertElementValue(self, name, value, *args, **kwargs):
        element = self.client.find_name(name)
        operator = kwargs.pop('operator', lambda x: x)
        self.assertEqual(operator(element.get_attribute('value')), element.clean_value(value), *args, **kwargs)

    def assertSelectOptions(self, name, texts, *args, **kwargs):
        self.assertListEqual(sorted(o.text for o in self.client.find_name(name).all_selected_options),
                             sorted([texts] if isinstance(texts, str) else texts), *args, **kwargs)


__all__ = _all.diff(globals())
