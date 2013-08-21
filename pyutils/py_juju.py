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

import os, uuid, yaml
from codecs import open
from kitchen.text.converters import to_bytes
from six import string_types
from py_subprocess import cmd


def juju_do(command, environment=None, options=None, fail=True, log=None):
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
    result = cmd(command, fail=False, log=log, env=env)
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


# Environments -------------------------------------------------------------------------------------

def add_environment(environments, name, type, region, access_key, secret_key, control_bucket,
                    default_series):
#    environments_dict = EnvironmentsConfig()
#    environments_dict.load(environments)
#    if environments_dict.get(name):
#        raise ValueError(to_bytes('The name %s is already used by another environment.' % name))
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    if name == 'default':
        raise ValueError(to_bytes(u'Cannot create an environment with name {0}.'.format(name)))
    if name in environments_dict[u'environments']:
        raise ValueError(to_bytes(u'The name {0} is already used by another environment.'.format(name)))
    if type == u'ec2':
        environment = {
            u'type': type, u'region': region, u'access-key': access_key, u'secret-key': secret_key,
            u'control-bucket': control_bucket, u'default-series': default_series, u'ssl-hostname-verification': True,
            u'juju-origin': u'ppa', u'admin-secret': uuid.uuid4().hex}
    else:
        raise NotImplementedError(to_bytes(u'Registration of {0} type of environment not yet implemented.'.format(type)))
    environments_dict[u'environments'][name] = environment
    open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
    try:
        return juju_do(u'bootstrap', name)
    except RuntimeError as e:
        if u'configuration error' in unicode(e):
            del environments_dict[u'environments'][name]
            open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
            raise ValueError(to_bytes(u'Cannot add environment {0} ({1}).'.format(name, e)))
        raise


def destroy_environment(environments, name, remove=False):
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    name = environments_dict[u'default'] if name == 'default' else name
    if name not in environments_dict[u'environments']:
        raise IndexError(to_bytes(u'No environment with name {0}.'.format(name)))
    if name == environments_dict[u'default']:
        raise NotImplementedError(to_bytes(u'Cannot remove default environment {0}.'.format(name)))
    try:
        get_environment_status(name)
        alive = True
    except:
        alive = False
    if alive:
        juju_do(u'destroy-environment', name)
    if remove:
        try:
            # Check if environment destroyed otherwise a lot of trouble with $/€ !
            get_environment_status(name)
            raise RuntimeError(to_bytes(u'Environment {0} not removed, it is still alive.'.format(name)))
        except:
            del environments_dict[u'environments'][name]
            open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))


def get_environment(environments, name, get_status=False):
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    name = environments_dict[u'default'] if name == 'default' else name
    try:
        environment = environments_dict[u'environments'][name]
    except KeyError:
        raise ValueError(to_bytes(u'No environment with name {0}.'.format(name)))
    if get_status:
        environment['status'] = get_environment_status(name)
    return environment


def get_environment_status(environment):
    return juju_do('status', environment)


def get_environments(environments, get_status=False):
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


def get_environments_count(environments):
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    return len(environments_dict[u'environments'])


# Services -----------------------------------------------------------------------------------------

def destroy_service(environment, service, fail=True):
    return juju_do(u'destroy-service', environment, [service], fail=fail)


# Units --------------------------------------------------------------------------------------------

def add_units(environment, service, num_units, to=None, **kwargs):
    options = [u'--num-units', unicode(num_units)]
    if to is not None:
        options.extend([u'--to', to])
    options.extend([service])
    return juju_do(u'add-unit', environment, options)


def add_or_deploy_units(environment, service, num_units, **kwargs):
    if get_units_count(environment, service) == 0:
        return deploy_units(environment, service, num_units, **kwargs)
    else:
        return add_units(environment, service, num_units)


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


# Relations ----------------------------------------------------------------------------------------

def add_relation(environment, service1, service2, relation1=None, relation2=None):
    u"""Add a relation between 2 services. Knowing that the relation may already exists."""
    member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
    member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
    try:
        return juju_do(u'add-relation', environment, [member1, member2])
    except RuntimeError as e:
        # FIXME get status of service and before adding relation may be cleaner.
        if not 'already exists' in unicode(e):
            raise
