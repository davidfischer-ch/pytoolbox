#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

from nose.tools import assert_equal, assert_raises

from mock import Mock
from py_unittest import mock_cmd

DEFAULT = {u'local_charms_path': u'.', u'release': u'raring', u'auto': True,
           u'environment': u'maas', u'config': u'config.yaml'}

BASE = [u'juju', u'deploy', u'--environment', u'maas']
CFG = [u'--config', u'config.yaml']
N, R = u'--num-units', u'--repository'

class TestDeploymentScenario(object):

    def test_deploy(self):
        import py_subprocess
        old_cmd = py_subprocess.cmd
        cmd = py_subprocess.cmd = mock_cmd()
        import py_juju
        #add = py_juju.add_or_deploy_units = Mock(return_value='a')
        #expose = py_juju.expose_service = Mock(return_value='b')
        count = py_juju.get_units_count = Mock(return_value=0)
        scenario = py_juju.DeploymentScenario()
        scenario.__dict__.update(DEFAULT)
        print(scenario.deploy(u'mysql', u'my_mysql'))
        print(scenario.deploy(u'lamp',  None))
        assert_raises(ValueError, scenario.deploy, None, u'salut')
        [call[1].pop(u'env') for call in cmd.call_args_list]
        assert_equal(cmd.call_args_list, [
            call(BASE + [N, 1] + CFG + [R, u'.', u'local:raring/mysql', u'my_mysql'], fail=False, log=None),
            call(BASE + [N, 1] + CFG + [R, u'.', u'local:raring/lamp', u'lamp'], fail=False, log=None)])
        py_subprocess.cmd = old_cmd