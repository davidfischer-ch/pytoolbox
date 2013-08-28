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
from py_subprocess import cmd

DEFAULT_ENVIRONMENTS_FILE = os.path.abspath(os.path.expanduser(u'~/.juju/environments.yaml'))
STARTED_STATES = (u'started',)
ERROR_STATES = (u'not-started', u'error')


def juju_do(command, environment=None, options=None, fail=True, log=None, **kwargs):
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
    command = [u'sudo', u'juju', command] if command == u'destroy-environment' else [u'juju', command]
    if isinstance(environment, string_types) and environment != u'default':
        command += [u'--environment', environment]
    if isinstance(options, list):
        command += options
    env = os.environ.copy()
    env[u'HOME'] = os.path.expanduser(u'~/')
    env[u'JUJU_HOME'] = os.path.expanduser(u'~/.juju')
    result = cmd(command, fail=False, log=log, env=env, **kwargs)
    if result[u'returncode'] != 0 and fail:
        command_string = u' '.join([unicode(arg) for arg in command])
        raise RuntimeError(to_bytes(u'Subprocess failed {0} : {1}.'.format(command_string, result[u'stderr'])))
    return yaml.load(result[u'stdout'])


def load_unit_config(config, log=None):
    u"""
    Returns a dictionary containing the options names as keys and options default values as values.
    The parameter ``config`` can be:

    * The filename of a charm configuration file (e.g. ``config.yaml``).
    * A dictionary containing already loaded options names as keys and options values as values.
    """
    if isinstance(config, string_types):
        if hasattr(log, u'__call__'):
            log(u'Load config from file {0}'.format(config))
        with open(config, u'r', encoding=u'utf-8') as f:
            options = yaml.load(f)[u'options']
            config = {}
            for option in options:
                config[option] = options[option][u'default']
    for option, value in config.iteritems():
        if unicode(value).lower() in (u'false', u'true'):
            config[option] = True if unicode(value).lower() == u'true' else False
            if hasattr(log, u'__call__'):
                log(u'Convert boolean option {0} {1} -> {2}'.format(option, value, config[option]))
    return config


def save_unit_config(filename, service, config, log=None):
    with open(filename, u'w', encoding=u'utf-8') as f:
        for option, value in config.iteritems():
            if isinstance(value, bool):
                config[option] = u'True' if value else u'False'
        config = {service: config}
        f.write(yaml.safe_dump(config))


# Tools ----------------------------------------------------------------------------------------------------------------

def sync_tools(environment, all_tools=True):
    options = [u'--all'] if all_tools else None
    return juju_do(u'sync-tools', environment, options=options)


# Environments ---------------------------------------------------------------------------------------------------------

def bootstrap_environment(environment, wait_started=False, started_states=STARTED_STATES, error_states=ERROR_STATES,
                          timeout=600, polling_delay=10):
    result = juju_do(u'bootstrap', environment)
    if wait_started:
        start_time = time.time()
        while True:
            state = get_environment_status(environment)[u'machines'][u'0'][u'agent-state']
            if state in started_states:
                break
            elif state in error_states:
                raise RuntimeError(u'Bootstrap failed with state {0}.'.format(state))
            if time.time() - start_time > timeout:
                raise TimeoutError(u'Bootstrap time-out with state {0}.'.format(state))
            time.sleep(polling_delay)
    return result


def add_environment(environment, type, region, access_key, secret_key, control_bucket,
                    default_series, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
#    environments_dict = EnvironmentsConfig()
#    environments_dict.load(environments)
#    if environments_dict.get(name):
#        raise ValueError(to_bytes(u'The name %s is already used by another environment.' % name))
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    if environment == u'default':
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
    environment = environments_dict[u'default'] if environment == u'default' else environment
    if environment not in environments_dict[u'environments']:
        raise IndexError(to_bytes(u'No environment with name {0}.'.format(environment)))
    if not remove_default and environment == environments_dict[u'default']:
        raise RuntimeError(to_bytes(u'Cannot remove default environment {0}.'.format(environment)))
    try:
        get_environment_status(environment)
        alive = True
    except:
        alive = False
    result = juju_do(u'destroy-environment', environment) if alive else None
    if remove:
        try:
            # Check if environment destroyed otherwise a lot of trouble with $/€ !
            get_environment_status(environment)
            raise RuntimeError(to_bytes(u'Environment {0} not removed, it is still alive.'.format(environment)))
        except:
            del environments_dict[u'environments'][environment]
            open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
    return result

def get_environment(environment, get_status=False, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environment = environments_dict[u'default'] if environment == u'default' else environment
    try:
        environment_dict = environments_dict[u'environments'][environment]
    except KeyError:
        raise ValueError(to_bytes(u'No environment with name {0}.'.format(environment)))
    if get_status:
        environment_dict[u'status'] = get_environment_status(environment)
    return environment_dict


def get_environment_status(environment):
    return juju_do(u'status', environment)


def get_environments(get_status=False, environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environments = {}
    for environment in environments_dict[u'environments'].iteritems():
        informations = environment[1]
        if get_status:
            try:
                informations[u'status'] = get_environment_status(environment[0])
            except RuntimeError:
                informations[u'status'] = u'UNKNOWN'
        environments[environment[0]] = informations
    return (environments, environments_dict[u'default'])


def get_environments_count(environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    return len(environments_dict[u'environments'])


# Services -------------------------------------------------------------------------------------------------------------

def get_service_config(environment, service, options=None, fail=True):
    return juju_do(u'get', environment, options=[service], fail=fail)


def expose_service(environment, service, fail=True):
    return juju_do(u'expose', environment, options=[service], fail=fail)


def unexpose_service(environment, service, fail=True):
    return juju_do(u'unexpose', environment, options=[service], fail=fail)


def destroy_service(environment, service, fail=True):
    return juju_do(u'destroy-service', environment, options=[service], fail=fail)


# Units ----------------------------------------------------------------------------------------------------------------

def add_units(environment, service, num_units=1, to=None, **kwargs):
    options = [u'--num-units', unicode(num_units)]
    if to is not None:
        options += [u'--to', to]
    options += [service]
    return juju_do(u'add-unit', environment, options=options)


def add_or_deploy_units(environment, charm, service, num_units=1, num_is_target=False, **kwargs):
    actual_count = get_units_count(environment, service)
    if actual_count == 0:
        return deploy_units(environment, charm, service, num_units, **kwargs)
    else:
        num_units = max(num_units - actual_count, 0) if num_is_target else num_units
        if num_units > 0:
            return add_units(environment, service, num_units, **kwargs)


def deploy_units(environment, charm, service=None, num_units=1, to=None, config=None, constraints=None, local=False,
                 release=None, repository=None):
    service = service or charm
    if not charm:
        raise ValueError('Charm is required.')
    options = [u'--num-units', num_units]
    if to is not None:
        options += [u'--to', to]
    if config is not None:
        options += [u'--config', config]
    if constraints is not None:
        options += [u'--constraints', constraints]
    if release is not None:
        charm = u'{0}/{1}'.format(release, charm)
    if local:
        charm = u'local:{0}'.format(charm)
    if repository is not None:
        options += [u'--repository', repository]
    options += filter(None, [charm, service])
    return juju_do(u'deploy', environment, options=options)


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
        raise IndexError(to_bytes(u'No unit with name {0}/{1} on environment {2}.'.format(
                         service, number, environment)))
    if destroy_machine:
        juju_do(u'destroy-unit', environment, options=[name])
        return juju_do(u'destroy-machine', environment, options=[unicode(unit_dict[u'machine'])])
    return juju_do(u'destroy-unit', environment, options=[name])


def get_unit_path(service, number, *args):
    return os.path.join(u'/var/lib/juju/agents/unit-{0}-{1}/charm'.format(service, number), *args)


# Relations ------------------------------------------------------------------------------------------------------------

def add_relation(environment, service1, service2, relation1=None, relation2=None):
    u"""Add a relation between 2 services. Knowing that the relation may already exists."""
    member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
    member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
    try:
        return juju_do(u'add-relation', environment, options=[member1, member2])
    except RuntimeError as e:
        # FIXME get status of service before adding relation may be cleaner.
        if not u'already exists' in unicode(e):
            raise

def remove_relation(environment, service1, service2, relation1=None, relation2=None):
    u"""Remove a relation between 2 services. Knowing that the relation may not exists."""
    member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
    member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
    try:
        return juju_do(u'remove-relation', environment, options=[member1, member2])
    except RuntimeError as e:
        # FIXME get status of service before removing relation may be cleaner.
        if not u'exists' in unicode(e):
            raise

# Helpers --------------------------------------------------------------------------------------------------------------

from functools import wraps

def print_stdouts(func):
    @wraps(func)
    def with_print_stdouts(*args, **kwargs):
        result = func(*args, **kwargs)
        if result[0]:
            for stdout in result[1]:
                if stdout:
                    print(stdout)
        return result
    return with_print_stdouts


class DeploymentScenario(object):

    def main(self, **kwargs):
        parser = self.get_parser(**kwargs)
        self.__dict__.update(vars(parser.parse_args()))
        self.run()

    def get_parser(self, epilog=u'', charms_path=u'.', environment=u'default', config=u'config.yaml', release=u'raring',
                   auto=False):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=epilog)
        parser.add_argument(u'-m', u'--charms_path', action=u'store', default=charms_path)
        parser.add_argument(u'-e', u'--environment', action=u'store', default=environment)
        parser.add_argument(u'-c', u'--config',      action=u'store', default=config)
        parser.add_argument(u'-r', u'--release',     action=u'store', default=release)
        parser.add_argument(u'-a', u'--auto',        action=u'store_true', default=auto)
        return parser

    @print_stdouts
    def bootstrap(self, environment, **kwargs):
        self.environment = environment
        print(u'Cleanup and bootstrap environment {0}'.format(self.environment))
        if self.auto or confirm(u'do it now', default=False):
            destroy_environment(self.environment, remove_default=True)
            sync_tools(self.environment, all_tools=True)
            return (True, [bootstrap_environment(self.environment, **kwargs)])
        return (False, [None])

    @print_stdouts
    def deploy(self, charm, service, expose=False, required=True, **kwargs):
        kwargs['release'] = kwargs.get('release', self.release)
        kwargs['num_is_target'] = kwargs.get('num_is_target', True)
        kwargs['local'] = kwargs.get('local', True)
        kwargs['repository'] = kwargs.get('repository', self.charms_path if kwargs['local'] else None)
        num_units = kwargs.get('num_units', 1)
        s = u's' if num_units > 1 else u''
        print(u'Deploy {0} as {1} ({2} instance{3})'.format(charm, service, num_units, s))
        stdouts = [None] * 2
        if self.auto and required or confirm(u'do it now', default=False):
            stdouts[0] = add_or_deploy_units(self.environment, charm, service, config=self.config, **kwargs)
            if expose:
                stdouts[1] = expose_service(self.environment, service)
            return (True, stdouts)
        return (False, stdouts)

    # Services
    def get_service_config(self, service, **kwargs):
        return get_service_config(self.environment, service, **kwargs)

    @print_stdouts
    def unexpose_service(self, service):
        print(u'Unexpose service {0}'.format(service))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [unexpose_service(self.environment, service)])
        return (False, [None])

    # Units
    def get_unit(self, service, number):
        return get_unit(self.environment, service, number)

    def get_units(self, service):
        return get_units(self.environment, service)

    # Relations
    @print_stdouts
    def add_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [add_relation(self.environment, service1, service2)])
        return (False, [None])

    @print_stdouts
    def remove_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [remove_relation(self.environment, service1, service2)])
        return (False, [None])

    def run(self):
        raise NotImplementedError(u'Here should be implemented the deployment scenario.')
