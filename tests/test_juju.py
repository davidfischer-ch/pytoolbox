# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Description    : Toolbox for Python scripts
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

import sys
from mock import call, Mock
from nose.tools import assert_equal, assert_raises
from pytoolbox.unittest import mock_cmd

DEFAULT = {u'charms_path': u'.', u'config': u'config.yaml'}

ADD_UNIT        = [u'juju', u'add-unit',        u'--environment', u'maas']
DEPLOY          = [u'juju', u'deploy',          u'--environment', u'maas']
DESTROY_UNIT    = [u'juju', u'destroy-unit',    u'--environment', u'maas']
DESTROY_SERVICE = [u'juju', u'destroy-service', u'--environment', u'maas']

CFG = [u'--config', u'config.yaml']
N, R = u'--num-units', u'--repository'

TEST_UNITS_SQL_2  = {0: {}, 1: {}}
TEST_UNITS_LAMP_4 = {0: {}, 1: {}, 2: {}, 3: {}}
TEST_UNITS_LAMP_5 = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}

class TestEnvironment(object):

    def test_ensure_num_units(self):
        import pytoolbox.subprocess
        old_cmd = pytoolbox.subprocess.cmd
        cmd = pytoolbox.subprocess.cmd = mock_cmd()
        try:  # Ensure that juju_do uses mock'ed cmd()
            del sys.modules['pytoolbox.juju']
        except:
            pass
        import pytoolbox.juju
        from pytoolbox.juju import PENDING, STARTED, ERROR
        TEST_UNITS_SQL_5  = {0: {'agent-state': STARTED}, 1: {'agent-state': PENDING}, 2: {'agent-state': ERROR},
                             3: {}, 4: {'agent-state': ERROR}}
        pytoolbox.juju.get_units = Mock(return_value=None)
        pytoolbox.juju.get_unit = Mock(return_value=None)
        environment = pytoolbox.juju.Environment(u'maas', release=u'raring', auto=True)
        environment.__dict__.update(DEFAULT)
        print(environment.ensure_num_units(u'mysql', u'my_mysql', num_units=2))
        print(environment.ensure_num_units(u'lamp',  None,        num_units=4))
        assert_raises(ValueError, environment.ensure_num_units, None, u'salut')
        pytoolbox.juju.get_units = Mock(return_value=TEST_UNITS_SQL_2)
        print(environment.ensure_num_units(u'mysql', u'my_mysql', num_units=5))
        pytoolbox.juju.get_units = Mock(return_value=TEST_UNITS_LAMP_4)
        print(environment.ensure_num_units(None, u'lamp', num_units=5))
        pytoolbox.juju.get_units = Mock(return_value=TEST_UNITS_SQL_5)
        print(environment.ensure_num_units(u'mysql', u'my_mysql', num_units=1, units_number_to_keep=[1]))
        pytoolbox.juju.get_units = Mock(return_value=TEST_UNITS_LAMP_5)
        print(environment.ensure_num_units(u'mysql', u'my_mysql', num_units=None))
        [call_args[1].pop(u'env') for call_args in cmd.call_args_list]
        a_eq = assert_equal
        a = cmd.call_args_list
        #assert_equal(len(a), 8)
        a_eq(a[0], call(DEPLOY + [N, 2] + CFG + [R, u'.', u'local:raring/mysql', u'my_mysql'], fail=False, log=None))
        a_eq(a[1], call(DEPLOY + [N, 4] + CFG + [R, u'.', u'local:raring/lamp',  u'lamp'],     fail=False, log=None))
        a_eq(a[2], call(ADD_UNIT + [N, 3] + [u'my_mysql'], fail=False, log=None))
        a_eq(a[3], call(ADD_UNIT + [N, 1] + [u'lamp'],     fail=False, log=None))
        a_eq(a[4], call(DESTROY_UNIT + [u'my_mysql/2'], fail=False, log=None))
        a_eq(a[5], call(DESTROY_UNIT + [u'my_mysql/3'], fail=False, log=None))
        a_eq(a[6], call(DESTROY_UNIT + [u'my_mysql/4'], fail=False, log=None))
        a_eq(a[7], call(DESTROY_UNIT + [u'my_mysql/0'], fail=False, log=None))
        a_eq(a[8], call(DESTROY_SERVICE + [u'my_mysql'], fail=False, log=None))
        pytoolbox.subprocess.cmd = old_cmd

