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

import uuid, yaml
from six import string_types
from py_subprocess import cmd
#from juju.environment.config import EnvironmentsConfig


def juju_do(command, environment, options=None, fail=True):
    u"""
    Execute a command ``command`` into environment ``environment``.

    **Known issue:**

    Locking Juju status 'are you sure you want to continue connecting (yes/no)'.

    We need a way to confirm our choice, pyutils.cmd('juju status --environment %s' % environment,
    cli_input='yes\n') seem to not work as expected. This happens the first time (and only the first
    time) juju connect to a freshly deployed environment.

    Solution : http://askubuntu.com/questions/123072/ssh-automatically-accept-keys

    .. code-block:: bash

        $ echo 'StrictHostKeyChecking no' >> ~/.ssh/config
    """
    command = ['juju', command, '--environment', environment]
    if isinstance(options, list):
        command.extend(options)
    print('Executing command %s' % command)
    result = cmd(command, fail=False)
    if result['returncode'] != 0 and fail:
        raise RuntimeError('Subprocess failed %s : %s.' % (' '.join(command), result['stderr']))
    return yaml.load(result['stdout'])


def load_unit_config(config, log=None):
    u"""
    Returns a dictionary containing the options names as keys and options default values as values.
    The parameter ``config`` can be:

    * The filename of a charm configuration file (e.g. ``config.yaml``).
    * A dictionary containing already loaded options names as keys and options values as values.
    """
    if isinstance(config, string_types):
        if log is not None:
            log('Load config from file %s' % config)
        with open(config) as f:
            options = yaml.load(f)['options']
            config = {}
            for option in options:
                config[option] = options[option]['default']
    for option, value in config.iteritems():
        if str(value).lower() in ('false', 'true'):
            config[option] = True if str(value).lower() == 'true' else False
            if log is not None:
                log('Convert boolean option %s %s -> %s' % (option, value, config[option]))
    return config


def save_unit_config(filename, service, config, log=None):
    with open(filename, 'w') as f:
        for option, value in config.iteritems():
            if isinstance(value, bool):
                config[option] = 'True' if value else 'False'
        config = {service: config}
        f.write(yaml.safe_dump(config))


# Environments -------------------------------------------------------------------------------------

def add_environment(environments, name, type, region, access_key, secret_key, control_bucket,
                    default_series):
#    environments_dict = EnvironmentsConfig()
#    environments_dict.load(environments)
#    if environments_dict.get(name):
#        raise ValueError('The name %s is already used by another environment.' % name)
    environments_dict = yaml.load(open(environments))
    if name in environments_dict['environments']:
        raise ValueError('The name %s is already used by another environment.' % name)
    if type == 'ec2':
        environment = {
            'type': type, 'region': region, 'access-key': access_key, 'secret-key': secret_key,
            'control-bucket': control_bucket, 'default-series': default_series,
            'ssl-hostname-verification': True, 'juju-origin': 'ppa',
            'admin-secret': uuid.uuid4().hex}
    else:
        raise NotImplementedError('Registration of %s type of environment not yet implemented.' %
                                  type)
    environments_dict['environments'][name] = environment
    open(environments, 'w').write(yaml.safe_dump(environments_dict))
    try:
        return juju_do('bootstrap', name)
    except RuntimeError as e:
        if 'configuration error' in str(e):
            del environments_dict['environments'][name]
            open(environments, 'w').write(yaml.safe_dump(environments_dict))
            raise ValueError('Cannot add environment %s (%s).' % (name, e))
        raise


def destroy_environment(environments, name, remove=False):
    environments_dict = yaml.load(open(environments))
    if name not in environments_dict['environments']:
        raise IndexError('No environment with name %s.' % name)
    if name == environments_dict['default']:
        raise NotImplementedError('Cannot remove default environment %s.' % name)
    try:
        return juju_do('destroy-environment', name)
    finally:
        # FIXME : check if environment destroyed otherwise a lot of trouble with $/€ !
        if remove:
            del environments_dict['environments'][name]
            open(environments, 'w').write(yaml.safe_dump(environments_dict))

#def get_environment_status(environment):
#    return juju_do('status', environment)


def get_environments(environments, get_status=False):
    environments_dict = yaml.load(open(environments))
    environments = {}
    for environment in environments_dict['environments'].iteritems():
        informations = environment[1]
        #if get_status:
        #    informations['status'] = get_environment_status(environment[0])
        environments[environment[0]] = informations
    return (environments, environments_dict['default'])


def get_environments_count(environments):
    environments_dict = yaml.load(open(environments))
    return len(environments_dict['environments'])


# Services -----------------------------------------------------------------------------------------

def destroy_service(environment, service, fail=True):
    return juju_do('destroy-service', environment, [service], fail=fail)


# Units --------------------------------------------------------------------------------------------

def add_units(environment, service, num_units):
    return juju_do('add-unit', environment, ['--num-units', str(num_units), service])


def add_or_deploy_units(environment, service, num_units, **kwargs):
    if get_units_count(environment, service) == 0:
        return deploy_units(environment, service, num_units, **kwargs)
    else:
        return add_units(environment, service, num_units)


def deploy_units(environment, service, num_units, config=None, constraints=None, local=False,
                 release=None, repository=None):
    options = ['--num-units', str(num_units)]
    if config is not None:
        options.extend(['--config', config])
    if constraints is not None:
        options.extend(['--constraints', constraints])
    if release is not None:
        service = '%s/%s' % (release, service)
    if local:
        service = 'local:%s' % service
    if repository is not None:
        options.extend(['--repository', repository])
    options.extend([service])
    return juju_do('deploy', environment, options)


def get_unit(environment, service, number):
    name = '%s/%s' % (service, number)
    return juju_do('status', environment, [name])['services'][service]['units'][name]


def get_units(environment, service):
    units = {}
    try:
        units_dict = juju_do('status', environment, [service])['services'][service]['units']
    except KeyError:
        return {}
    for unit in units_dict.iteritems():
        number = unit[0].split('/')[1]
        units[number] = unit[1]
    return units


def get_units_count(environment, service):
    try:
        return len(juju_do('status', environment, [service])['services'][service]['units'].keys())
    except KeyError:
        return 0


def remove_unit(environment, service, number, terminate):
    name = '%s/%s' % (service, number)
    try:
        unit_dict = get_unit(environment, service, number)
    except KeyError:
        raise IndexError('No unit with name %s/%s on environment %s.' %
                         (service, number, environment))
    if terminate:
        juju_do('remove-unit', environment, [name])
        return juju_do('terminate-machine', environment, [str(unit_dict['machine'])])
    return juju_do('remove-unit', environment, [name])


# Relations ----------------------------------------------------------------------------------------

def add_relation(environment, service1, service2, relation1=None, relation2=None):
    member1 = service1 if relation1 is None else '%s:%s' % (service1, relation1)
    member2 = service2 if relation2 is None else '%s:%s' % (service2, relation2)
    return juju_do('add-relation', environment, [member1, member2])
