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

import os, time, uuid, yaml
from codecs import open
from kitchen.text.converters import to_bytes
from six import string_types
from py_console import confirm
from py_exception import TimeoutError
from py_subprocess import cmd, screen_kill, screen_launch, screen_list

DEFAULT_ENVIRONMENTS_FILE = os.path.abspath(os.path.expanduser('~/.juju/environments.yaml'))
STARTED_STATES = ('started',)
ERROR_STATES = ('not-started', 'error')


def juju_do(command, environment=None, options=None, screen_name=None, fail=True, log=None, **kwargs):
    u"""
    Execute a command ``command`` into environment ``environment``.

    **Known issue:**

    Locking Juju status 'are you sure you want to continue connecting (yes/no)'.

    We need a way to confirm our choice, ``cmd(u'juju status --environment %s' % environment,
    cli_input=u'yes\n')? ?  seem to not work as expected. This happens the first time (and only the
    first time) juju connect to a freshly deployed environment.

    Solution : http://askubuntu.com/questions/123072/ssh-automatically-accept-keys

    .. code-block:: bash

        $ echo 'StrictHostKeyChecking no' >> ~/.ssh/config
    """
    command = [u'juju', command]
    if isinstance(environment, string_types) and environment != 'default':
        command.extend([u'--environment', environment])
    if isinstance(options, list):
        command.extend(options)
    env = os.environ.copy()
    env['HOME'] = os.path.expanduser('~/')
    env['JUJU_HOME'] = os.path.expanduser('~/.juju')
    if screen_name:
        return screen_launch(command, fail=fail, log=log, env=env, **kwargs)
    else:
        result = cmd(command, fail=False, log=log, env=env, **kwargs)
    if result[u'returncode'] != 0 and fail:
        raise RuntimeError(to_bytes(u'Subprocess failed {0} : {1}.'.format(u' '.join(command), result[u'stderr'])))
    return yaml.load(result[u'stdout'])


def load_unit_config(config, log=None):
    u"""
    Returns a dictionary containing the options names as keys and options default values as values.
    The parameter ``config`` can be:

    * The filename of a charm configuration file (e.g. ``config.yaml``).
    * A dictionary containing already loaded options names as keys and options values as values.
    """
    if isinstance(config, string_types):
        if hasattr(log, '__call__'):
            log(u'Load config from file {0}'.format(config))
        with open(config, u'r', encoding=u'utf-8') as f:
            options = yaml.load(f)[u'options']
            config = {}
            for option in options:
                config[option] = options[option][u'default']
    for option, value in config.iteritems():
        if unicode(value).lower() in (u'false', u'true'):
            config[option] = True if unicode(value).lower() == u'true' else False
            if hasattr(log, '__call__'):
                log(u'Convert boolean option {0} {1} -> {2}'.format(option, value, config[option]))
    return config


def save_unit_config(filename, service, config, log=None):
    with open(filename, u'w', encoding=u'utf-8') as f:
        for option, value in config.iteritems():
            if isinstance(value, bool):
                config[option] = u'True' if value else u'False'
        config = {service: config}
        f.write(yaml.safe_dump(config))


def launch_log(environment, screen_name, log=None):
    return ('screenlog.0', juju_do('debug-log', ['-L'], screen_name=screen_name, communicate=False, log=log))

# Environments ---------------------------------------------------------------------------------------------------------

def bootstrap_environment(environment, wait_started=False, started_states=STARTED_STATES, error_states=ERROR_STATES,
                          timeout=600, polling_delay=10, environments=None):
    juju_do('bootstrap', environment)
    if wait_started:
        start_time = time.time()
        while True:
            state = get_environment_status(environment)['machines']['0']['agent-state']
            if state in started_states:
                break
            elif state in error_states:
                raise RuntimeError(u'Bootstrap failed with state {0}.'.format(state))
            if time.time() - start_time > timeout:
                raise TimeoutError(u'Bootstrap time-out with state {0}.'.format(state))
            time.sleep(polling_delay)


def add_environment(environment, type, region, access_key, secret_key, control_bucket,
                    default_series, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
#    environments_dict = EnvironmentsConfig()
#    environments_dict.load(environments)
#    if environments_dict.get(name):
#        raise ValueError(to_bytes('The name %s is already used by another environment.' % name))
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    if environment == 'default':
        raise ValueError(to_bytes(u'Cannot create an environment with name {0}.'.format(environment)))
    if environment in environments_dict[u'environments']:
        raise ValueError(to_bytes(u'The name {0} is already used by another environment.'.format(environment)))
    if type == u'ec2':
        environment_dict = {
            u'type': type, u'region': region, u'access-key': access_key, u'secret-key': secret_key,
            u'control-bucket': control_bucket, u'default-series': default_series, u'ssl-hostname-verification': True,
            u'juju-origin': u'ppa', u'admin-secret': uuid.uuid4().hex}
    else:
        raise NotImplementedError(to_bytes(u'Registration of {0} type of environment not yet implemented.'.format(type)))
    environments_dict[u'environments'][environment] = environment_dict
    open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
    try:
        return juju_do(u'bootstrap', environment)
    except RuntimeError as e:
        if u'configuration error' in unicode(e):
            del environments_dict[u'environments'][environment]
            open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
            raise ValueError(to_bytes(u'Cannot add environment {0} ({1}).'.format(environment, e)))
        raise


def destroy_environment(environment, remove_default=False, remove=False, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environment = environments_dict[u'default'] if environment == 'default' else environment
    if environment not in environments_dict[u'environments']:
        raise IndexError(to_bytes(u'No environment with name {0}.'.format(environment)))
    if not remove_default and environment == environments_dict[u'default']:
        raise RuntimeError(to_bytes(u'Cannot remove default environment {0}.'.format(environment)))
    try:
        get_environment_status(environment)
        alive = True
    except:
        alive = False
    if alive:
        juju_do(u'destroy-environment', environment)
    if remove:
        try:
            # Check if environment destroyed otherwise a lot of trouble with $/€ !
            get_environment_status(environment)
            raise RuntimeError(to_bytes(u'Environment {0} not removed, it is still alive.'.format(environment)))
        except:
            del environments_dict[u'environments'][environment]
            open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))


def get_environment(environment, get_status=False, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environment = environments_dict[u'default'] if environment == 'default' else environment
    try:
        environment_dict = environments_dict[u'environments'][environment]
    except KeyError:
        raise ValueError(to_bytes(u'No environment with name {0}.'.format(environment)))
    if get_status:
        environment_dict['status'] = get_environment_status(environment)
    return environment_dict


def get_environment_status(environment):
    return juju_do('status', environment)


def get_environments(get_status=False, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environments = {}
    for environment in environments_dict[u'environments'].iteritems():
        informations = environment[1]
        if get_status:
            try:
                informations['status'] = get_environment_status(environment[0])
            except RuntimeError:
                informations['status'] = 'UNKNOWN'
        environments[environment[0]] = informations
    return (environments, environments_dict[u'default'])


def get_environments_count(environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    return len(environments_dict[u'environments'])


# Services -------------------------------------------------------------------------------------------------------------

def expose_service(environment, service, fail=True):
    return juju_do('expose', environment, [service], fail=fail)


def unexpose_service(environment, service, fail=True):
    return juju_do('unexpose', environment, [service], fail=fail)


def destroy_service(environment, service, fail=True):
    return juju_do(u'destroy-service', environment, [service], fail=fail)


# Units ----------------------------------------------------------------------------------------------------------------

def add_units(environment, service, num_units, to=None, **kwargs):
    options = [u'--num-units', unicode(num_units)]
    if to is not None:
        options.extend([u'--to', to])
    options.extend([service])
    return juju_do(u'add-unit', environment, options)


def add_or_deploy_units(environment, service, num_units, num_is_target=False, **kwargs):
    actual_count = get_units_count(environment, service)
    if actual_count == 0:
        return deploy_units(environment, service, num_units, **kwargs)
    else:
        num_units = max(num_units - actual_count, 0) if num_is_target else num_units
        if num_units > 0:
            return add_units(environment, service, num_units, **kwargs)


def deploy_units(environment, service, num_units, to=None, config=None, constraints=None,
                 local=False, release=None, repository=None):
    options = [u'--num-units', unicode(num_units)]
    if to is not None:
        options.extend([u'--to', to])
    if config is not None:
        options.extend([u'--config', config])
    if constraints is not None:
        options.extend([u'--constraints', constraints])
    if release is not None:
        service = u'{0}/{1}'.format(release, service)
    if local:
        service = u'local:{0}'.format(service)
    if repository is not None:
        options.extend([u'--repository', repository])
    options.extend([service])
    return juju_do(u'deploy', environment, options)


def get_unit(environment, service, number):
    name = u'{0}/{1}'.format(service, number)
    return juju_do(u'status', environment)[u'services'][service][u'units'][name]


def get_units(environment, service):
    units = {}
    try:
        units_dict = juju_do(u'status', environment)[u'services'][service][u'units']
    except KeyError:
        return {}
    for unit in units_dict.iteritems():
        number = unit[0].split(u'/')[1]
        units[number] = unit[1]
    return units


def get_units_count(environment, service):
    try:
        units_dict = juju_do(u'status', environment)[u'services'][service][u'units']
        return len(units_dict.keys())
    except KeyError:
        return 0


def destroy_unit(environment, service, number, destroy_machine):
    name = u'{0}/{1}'.format(service, number)
    try:
        unit_dict = get_unit(environment, service, number)
    except KeyError:
        raise IndexError(to_bytes(u'No unit with name {0}/{1} on environment {2}.'.format(service, number, environment)))
    if destroy_machine:
        juju_do(u'destroy-unit', environment, [name])
        return juju_do(u'destroy-machine', environment, [unicode(unit_dict[u'machine'])])
    return juju_do(u'destroy-unit', environment, [name])


# Relations ------------------------------------------------------------------------------------------------------------

def add_relation(environment, service1, service2, relation1=None, relation2=None):
    u"""Add a relation between 2 services. Knowing that the relation may already exists."""
    member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
    member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
    try:
        return juju_do(u'add-relation', environment, [member1, member2])
    except RuntimeError as e:
        # FIXME get status of service before adding relation may be cleaner.
        if not 'already exists' in unicode(e):
            raise

def remove_relation(environment, service1, service2, relation1=None, relation2=None):
    u"""Remove a relation between 2 services. Knowing that the relation may not exists."""
    member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
    member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
    try:
        return juju_do(u'remove-relation', environment, [member1, member2])
    except RuntimeError as e:
        # FIXME get status of service before removing relation may be cleaner.
        if not 'exists' in unicode(e):
            raise

# Helpers --------------------------------------------------------------------------------------------------------------

class DeploymentScenario(object):

    def main(self):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
        from oscied_lib.pyutils.py_unicode import configure_unicode
        configure_unicode()
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                                epilog=u'''Show interesting informations about a running orchestrator.''')
        parser.add_argument(u'-p', u'--charms_deploy_path', action=u'store',      default='../../deploy')
        parser.add_argument(u'-r', u'--release',            action=u'store',      default='raring')
        parser.add_argument(u'-a', u'--auto',               action=u'store_true', default=False)
        args = parser.parse_args()
        self.charms_deploy_path = os.path.abspath(os.path.expanduser(args.charms_deploy_path))
        self.release, self.auto = args.release, args.auto
        self.environment, self.config = u'default', u'config.yaml'
        self.run()

    def launch_log(self, screen_name, log=None):
        return launch_log(self.environment, screen_name, log=log)

    def bootstrap(self, environment, **kwargs):
        self.environment = environment
        print(u'Cleanup and bootstrap environment {0}'.format(self.environment))
        if self.auto or confirm(u'do it now', default=False):
            destroy_environment(self.environment, remove_default=True)
            bootstrap_environment(self.environment, **kwargs)

    def deploy(self, service, num_units=1, num_is_target=True, release=None, expose=False, required=True, **kwargs):
        release = release or self.release
        local = (u'oscied' in service)
        repository = self.charms_deploy_path if local else None
        s = u's' if num_units > 1 else ''
        print(u'Deploy {0} ({1} instance{2})'.format(service, num_units, s))
        if self.auto and required or confirm(u'do it now', default=False):
            add_or_deploy_units(self.environment, service, num_units, num_is_target=num_is_target, config=self.config,
                                local=local, release=release, repository=repository, **kwargs)
            if expose:
                expose_service(self.environment, service)
            return True
        return False

    def add_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            add_relation(self.environment, service1, service2)

    def remove_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            remove_relation(self.environment, service1, service2)

    def unexpose_service(self, service):
        print(u'Unexpose service {0}'.format(service))
        if self.auto or confirm(u'do it now', default=False):
            unexpose_service(self.environment, service)

    def run(self):
        raise NotImplementedError(u'Here should be implemented the deployment scenario.')
