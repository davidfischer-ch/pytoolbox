from __future__ import annotations

from unittest import mock

import pytest
from pytoolbox import juju
from pytoolbox.juju import PENDING, STARTED, ERROR

ADD_UNIT = ['juju', 'add-unit', '--environment', 'maas']
DEPLOY = ['juju', 'deploy', '--environment', 'maas']
DESTROY_UNIT = ['juju', 'destroy-unit', '--environment', 'maas']
DESTROY_SERVICE = ['juju', 'destroy-service', '--environment', 'maas']

CFG = ['--config', 'config.yaml']
N = '--num-units'
R = '--repository'


def test_environment_ensure_num_units() -> None:
    with mock.patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}

        env = juju.Environment('maas', release='raring', auto=True)
        env.get_units = mock.Mock(return_value=None)
        env.get_unit = mock.Mock(return_value=None)
        env.__dict__.update({'charms_path': '.', 'config': 'config.yaml'})

        assert env.ensure_num_units('mysql', 'my_mysql', num_units=2) == {'deploy_units': None}
        assert env.ensure_num_units('lamp', None, num_units=4) == {'deploy_units': None}

        with pytest.raises(ValueError):
            env.ensure_num_units(None, 'salut')

        env.get_units = mock.Mock(return_value={0: {}, 1: {}})
        assert env.ensure_num_units('mysql', 'my_mysql', num_units=5) == {'add_units': None}

        env.get_units = mock.Mock(return_value={0: {}, 1: {}, 2: {}, 3: {}})
        assert env.ensure_num_units(None, 'lamp', num_units=5) == {'add_units': None}

        env.get_units = mock.Mock(return_value={
            0: {'agent-state': STARTED},
            1: {'agent-state': PENDING},
            2: {'agent-state': ERROR},
            3: {},
            4: {'agent-state': ERROR}
        })
        env.get_unit = mock.Mock(return_value={})
        env.ensure_num_units('mysql', 'my_mysql', num_units=1, units_number_to_keep=[1])
        env.get_units = mock.Mock(return_value={0: {}, 1: {}, 2: {}, 3: {}, 4: {}})

        env.ensure_num_units('mysql', 'my_mysql', num_units=None)
        for call_args in cmd.call_args_list:
            call_args[1].pop('env')

        kwargs = {'fail': False, 'log': None}
        assert len(cmd.call_args_list) == 9
        cmd.assert_has_calls([
            mock.call([*DEPLOY, N, '2', *CFG, R, '.', 'local:raring/mysql', 'my_mysql'], **kwargs),
            mock.call([*DEPLOY, N, '4', *CFG, R, '.', 'local:raring/lamp', 'lamp'], **kwargs),
            mock.call([*ADD_UNIT, N, '3', 'my_mysql'], **kwargs),
            mock.call([*ADD_UNIT, N, '1', 'lamp'], **kwargs),
            mock.call([*DESTROY_UNIT, 'my_mysql/2'], **kwargs),
            mock.call([*DESTROY_UNIT, 'my_mysql/3'], **kwargs),
            mock.call([*DESTROY_UNIT, 'my_mysql/4'], **kwargs),
            mock.call([*DESTROY_UNIT, 'my_mysql/0'], **kwargs),
            mock.call([*DESTROY_SERVICE, 'my_mysql'], **kwargs)
        ])
