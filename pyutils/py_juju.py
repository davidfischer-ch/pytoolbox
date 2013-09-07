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

import json, os, subprocess, sys, time, uuid, yaml
from codecs import open
from functools import wraps
from kitchen.text.converters import to_bytes
from six import string_types
from py_console import confirm
from py_exception import TimeoutError
from py_subprocess import cmd

DEFAULT_ENVIRONMENTS_FILE = os.path.abspath(os.path.expanduser(u'~/.juju/environments.yaml'))
DEFAULT_OS_ENV = {
    u'APT_LISTCHANGES_FRONTEND': u'none',
    u'CHARM_DIR': u'/var/lib/juju/units/oscied-storage-0/charm',
    u'DEBIAN_FRONTEND': u'noninteractive',
    u'_JUJU_CHARM_FORMAT': u'1',
    u'JUJU_AGENT_SOCKET': u'/var/lib/juju/units/oscied-storage-0/.juju.hookcli.sock',
    u'JUJU_CLIENT_ID': u'constant',
    u'JUJU_ENV_UUID': u'878ca8f623174911960f6fbed84f7bdd',
    u'JUJU_PYTHONPATH': u':/usr/lib/python2.7/dist-packages:/usr/lib/python2.7'
                        u':/usr/lib/python2.7/plat-x86_64-linux-gnu'
                        u':/usr/lib/python2.7/lib-tk'
                        u':/usr/lib/python2.7/lib-old'
                        u':/usr/lib/python2.7/lib-dynload'
                        u':/usr/local/lib/python2.7/dist-packages'
                        u':/usr/lib/pymodules/python2.7',
    u'_': u'/usr/bin/python',
    u'JUJU_UNIT_NAME': u'oscied-storage/0',
    u'PATH': u'/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin',
    u'PWD': u'/var/lib/juju/units/oscied-storage-0/charm',
    u'SHLVL': u'1'
}

ALL_STATES = PENDING, STARTED, NOT_STARTED, ERROR = (u'pending', u'started', u'not-started', u'error')
PENDING_STATES, STARTED_STATES, ERROR_STATES = (PENDING,), (STARTED,), (ERROR, NOT_STARTED)


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
    options = [u'--num-units', num_units]
    if to is not None:
        options += [u'--to', to]
    options += [service]
    return juju_do(u'add-unit', environment, options=options)


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


def ensure_num_units(environment, charm, service, num_units=1, **kwargs):
    assert(num_units >= 0 or num_units is None)
    units = get_units(environment, service, none_if_missing=True)
    units_count = None if units is None else len(units)
    if num_units is None:
        return units_count if units_count is None else destroy_service(environment, service)
    if units_count is None:
        return deploy_units(environment, charm, service, num_units, **kwargs)
    if units_count < num_units:
        num_units = num_units - units_count
        return add_units(environment, service or charm, num_units, **kwargs)
    if units_count > num_units:
        destroy_machine = kwargs.get('destroy_machine', None)
        num_units = units_count - num_units
        destroyed = {}
        # FIXME short by status (started last)
        for i in range(num_units):
            number, unit_dict = units.popitem()
            destroy_unit(environment, service, number, destroy_machine=False)
            destroyed[number] = unit_dict
        if destroy_machine:
            time.sleep(5)
            for unit_dict in destroyed.values():
                # FIXME handle failure (multiple units same machine, machine busy, missing ...)
                destroy_machine(environment, unit_dict[u'machine'])
        return destroyed

def get_unit(environment, service, number):
    name = u'{0}/{1}'.format(service, number)
    return juju_do(u'status', environment)[u'services'][service][u'units'][name]


def get_units(environment, service, none_if_missing=False):
    units = {}
    try:
        units_dict = juju_do(u'status', environment)[u'services'][service][u'units']
    except KeyError:
        return None if none_if_missing else {}
    for unit in units_dict.iteritems():
        number = unit[0].split(u'/')[1]
        units[number] = unit[1]
    return units


def get_units_count(environment, service, none_if_missing=False):
    try:
        units_dict = juju_do(u'status', environment)[u'services'][service][u'units']
        return len(units_dict.keys())
    except KeyError:
        return None if none_if_missing else 0


def destroy_unit(environment, service, number, destroy_machine, delay_destroy=5):
    name = u'{0}/{1}'.format(service, number)
    try:
        unit_dict = get_unit(environment, service, number)
    except KeyError:
        raise IndexError(to_bytes(u'No unit with name {0}/{1} on environment {2}.'.format(
                         service, number, environment)))
    if destroy_machine:
        juju_do(u'destroy-unit', environment, options=[name])
        time.sleep(delay_destroy)  # FIXME ideally a --terminate flag https://bugs.launchpad.net/juju-core/+bug/1218790
        return destroy_machine(environment, unit_dict[u'machine'])
    return juju_do(u'destroy-unit', environment, options=[name])


def get_unit_path(service, number, *args):
    return os.path.join(u'/var/lib/juju/agents/unit-{0}-{1}/charm'.format(service, number), *args)


# Machines -------------------------------------------------------------------------------------------------------------

def destroy_machine(environment, machine):
    juju_do(u'destroy-machine', environment, options=[machine])


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

__get_ip = None


def get_ip():
    global __get_ip
    if __get_ip is None:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((u'8.8.8.8', 80))
        __get_ip = s.getsockname()[0]
        s.close()
    return __get_ip


class CharmConfig(object):

    def __init__(self):
        self.verbose = False

    def __repr__(self):
        return unicode(self.__dict__)


class CharmHooks(object):
    u"""
    A base class to build charms based on python hooks, callable even if juju is not installed.

    The following attributes are set by ``__init__``: TODO

    * ``local_config`` must be set by derived class to an instance of ``py_serialization.PickelableObject``.
    This should be loaded from a file that is local to the unit by ``__init__``. This file is used to store service/
    unit-specific configuration. In EBU's project called OSCIED, this file is even read by the encapsulated python
    code of the worker (celery daemon).

    **Example usage**:

    >>> class MyCharmHooks(CharmHooks):
    ...
    ...     def hook_install(self):
    ...         self.debug(u'hello world, install some packages with self.cmd(...)')
    ...
    ...     def hook_config_changed(self):
    ...         self.remark(u'update services based on self.config and update self.local_config')
    ...
    ...     def hook_start(self):
    ...         self.info(u'start services')
    ...
    ...     def hook_stop(self):
    ...         self.info(u'stop services')
    ...

    >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
    >>> metadata = os.path.join(here, u'../tests/metadata.yaml')
    >>> config = os.path.join(here, u'../tests/config.yaml')

    Trigger some hooks:

    >>> my_hooks = MyCharmHooks(metadata, config, DEFAULT_OS_ENV, force_disable_juju=True) # doctest: +ELLIPSIS
    [DEBUG] Using juju False, reason: Disabled by user.
    [DEBUG] Load metadatas from file ...

    >>> my_hooks.trigger(u'install')
    [HOOK] Execute MyCharmHooks hook install
    [DEBUG] hello world, install some packages with self.cmd(...)
    [HOOK] Exiting MyCharmHooks hook install

    >>> my_hooks.trigger(u'config-changed')
    [HOOK] Execute MyCharmHooks hook config-changed
    [REMARK] update services based on self.config and update self.local_config !
    [HOOK] Exiting MyCharmHooks hook config-changed

    >>> my_hooks.trigger(u'start')
    [HOOK] Execute MyCharmHooks hook start
    [INFO] start services
    [HOOK] Exiting MyCharmHooks hook start

    >>> my_hooks.trigger(u'stop')
    [HOOK] Execute MyCharmHooks hook stop
    [INFO] stop services
    [HOOK] Exiting MyCharmHooks hook stop

    >>> my_hooks.trigger(u'not_exist')
    Traceback (most recent call last):
        ...
    AttributeError: 'MyCharmHooks' object has no attribute 'hook_not_exist'
    """

    def __init__(self, metadata, default_config, default_os_env, force_disable_juju=False):
        self.config = CharmConfig()
        self.local_config = None
        reason = u'Life is good !'
        try:
            if force_disable_juju:
                raise OSError(to_bytes(u'Disabled by user.'))
            self.juju_ok = True
            self.load_config(json.loads(self.cmd([u'config-get', u'--format=json'])['stdout']))
            self.env_uuid = os.environ.get(u'JUJU_ENV_UUID')
            self.name = os.environ[u'JUJU_UNIT_NAME']
            self.private_address = self.unit_get(u'private-address')
            self.public_address = self.unit_get(u'public-address')
        except (subprocess.CalledProcessError, OSError) as e:
            reason = e
            self.juju_ok = False
            if default_config is not None:
                self.load_config(default_config)
            self.env_uuid = default_os_env[u'JUJU_ENV_UUID']
            self.name = default_os_env[u'JUJU_UNIT_NAME']
            self.private_address = self.public_address = get_ip()
        self.debug(u'Using juju {0}, reason: {1}'.format(self.juju_ok, reason))
        self.load_metadata(metadata)

    # ------------------------------------------------------------------------------------------------------------------

    @property
    def id(self):
        u"""
        Returns the id extracted from the unit's name.

        **Example usage**:

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.name = u'oscied-storage/3'
        >>> hooks.id
        3
        """
        return int(self.name.split(u'/')[1])

    @property
    def is_leader(self):
        u"""
        Returns True if current unit is the leader of the peer-relation.

        By convention, the leader is the unit with the *smallest* id (the *oldest* unit).
        """
        try:
            ids = [int(i.split(u'/')[1]) for i in self.relation_list(None)]
            self.debug(u'id={0} ids={1}'.format(self.id, ids))
            return len(ids) == 0 or self.id <= min(ids)
        except Exception as e:
            self.debug(u'Bug during leader detection: {0}'.format(repr(e)))
            return True

    # Maps calls to charm helpers methods and replace them if called in standalone -------------------------------------

    def log(self, message):
        if self.juju_ok:
            return self.cmd([u'juju-log', message], logging=False)  # Avoid infinite loop !
        print(message)
        return None

    def open_port(self, port, protocol=u'TCP'):
        if self.juju_ok:
            return self.cmd([u'open-port', u'{0}/{1}'.format(port, protocol)])
        return self.debug(u'Open port {0} ({1})'.format(port, protocol))

    def close_port(self, port, protocol=u'TCP'):
        if self.juju_ok:
            return self.cmd([u'close-port', u'{0}/{1}'.format(port, protocol)])
        return self.debug(u'Close port {0} ({1})'.format(port, protocol))

    def unit_get(self, attribute):
        if self.juju_ok:
            return self.cmd([u'unit-get', attribute])['stdout'].strip()
        raise NotImplementedError(to_bytes(u'FIXME juju-less unit_get not yet implemented'))

    def relation_get(self, attribute=None, unit=None, relation_id=None):
        if self.juju_ok:
            command = [u'relation-get']
            if relation_id is not None:
                command += [u'-r', relation_id]
            command += filter(None, [attribute, unit])
            return self.cmd(command)['stdout'].strip()
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_get not yet implemented'))

    def relation_ids(self, relation_name):
        if self.juju_ok:
            return [int(id) for id in self.cmd([u'relation-ids', relation_name])['stdout'].split()]
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_ids not yet implemented'))

    def relation_list(self, relation_id=None):
        if self.juju_ok:
            command = [u'relation-list']
            if relation_id is not None:
                command += [u'-r', relation_id]
            return self.cmd(command)['stdout'].split()
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_list not yet implemented'))

    def relation_set(self, **kwargs):
        if self.juju_ok:
            command = [u'relation-set']
            command += [u'{0}={1}'.format(key, value) for key, value in kwargs.items()]
            return self.cmd(command)
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_set not yet implemented'))

    # Convenience methods for logging ----------------------------------------------------------------------------------

    def debug(self, message):
        u"""
        Convenience method for logging a debug-related message.
        """
        if self.config.verbose:
            return self.log(u'[DEBUG] {0}'.format(message))

    def info(self, message):
        u"""
        Convenience method for logging a standard message.
        """
        return self.log(u'[INFO] {0}'.format(message))

    def hook(self, message):
        u"""
        Convenience method for logging the triggering of a hook.
        """
        return self.log(u'[HOOK] {0}'.format(message))

    def remark(self, message):
        u"""
        Convenience method for logging an important remark.
        """
        return self.log(u'[REMARK] {0} !'.format(message))

    # ------------------------------------------------------------------------------------------------------------------

    def load_config(self, config):
        u"""
        Updates ``config`` attribute with given configuration.

        **Example usage**:

        >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        >>> config = os.path.join(here, u'../tests/config.yaml')

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hasattr(hooks.config, u'pingu') or hasattr(hooks.config, u'rabbit_password')
        False
        >>> hooks.load_config({u'pingu': u'bi bi'})
        >>> print(hooks.config.pingu)
        bi bi
        >>> hooks.config.verbose = True

        >>> hooks.load_config(config)  # doctest: +ELLIPSIS
        [DEBUG] Load config from file ...
        [DEBUG] Convert boolean option verbose true -> True
        [DEBUG] Convert boolean option email_tls true -> True
        [DEBUG] Convert boolean option cleanup true -> True
        >>> hasattr(hooks.config, u'rabbit_password')
        True
        """
        self.config.__dict__.update(load_unit_config(config, log=self.debug))

    def save_local_config(self):
        u"""
        Save or update local configuration file only if this instance has the attribute ``local_config``.
        """
        if self.local_config is not None:
            self.debug(u'Save (updated) local configuration {0}'.format(self.local_config))
            self.local_config.write()

    def load_metadata(self, metadata):
        u"""
        Set ``metadata`` attribute with given metadatas, ``metadata`` can be:

        * The filename of a charm metadata file (e.g. ``metadata.yaml``)
        * A dictionary containing the metadatas.

        **Example usage**:

        >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        >>> metadata = os.path.join(here, u'../tests/metadata.yaml')

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.metadata
        >>> hooks.load_metadata({u'ensemble': u'oscied'})
        >>> hooks.metadata
        {u'ensemble': u'oscied'}
        >>> hooks.config.verbose = True
        >>> hooks.load_metadata(metadata)  # doctest: +ELLIPSIS
        [DEBUG] Load metadatas from file ...
        >>> print(hooks.metadata[u'maintainer'])
        OSCIED Main Developper <david.fischer.ch@gmail.com>
        """
        if isinstance(metadata, string_types):
            self.debug(u'Load metadatas from file {0}'.format(metadata))
            with open(metadata, u'r', u'utf-8') as f:
                metadata = yaml.load(f)
        self.metadata = metadata

    # ------------------------------------------------------------------------------------------------------------------

    def cmd(self, command, input=None, cli_input=None, fail=True, logging=True):
        u"""
        Calls the ``command`` and returns a dictionary with stdout, stderr, and the returncode.
        """
        return cmd(command, input=input, cli_input=cli_input, fail=fail, log=self.debug if logging else None)

    def template2config(self, template, config, values):
        with open(template, u'r', u'utf-8') as template_file:
            data = template_file.read()
            data = data.format(**values)
            with open(config, u'w', u'utf-8') as config_file:
                config_file.write(data)
                self.remark(u'File {0} successfully generated'.format(config))

    # ------------------------------------------------------------------------------------------------------------------

    def trigger(self, hook_name=None):
        u"""
        Triggers a hook specified in ``hook_name``, defaults to ``sys.argv[1]``.

        Hook's name is the nice hook name that one can find in official juju documentation.
        For example if ``config-changed`` is mapped to a call to ``self.hook_config_changed()``.

        A ``ValueError`` containing a usage string is raised if a bad number of argument is given.
        """
        if hook_name is None:
            if len(sys.argv) != 2:
                raise ValueError(to_bytes(u'Usage {0} hook_name (e.g. config-changed)'.format(sys.argv[0])))
            hook_name = sys.argv[1]

        try:  # Call the function hooks_...
            self.hook(u'Execute {0} hook {1}'.format(self.__class__.__name__, hook_name))
            getattr(self, u'hook_{0}'.format(hook_name.replace(u'-', u'_')))()
            self.save_local_config()
        except subprocess.CalledProcessError as e:
            self.log(u'Exception caught:')
            self.log(e.output)
            raise
        finally:
            self.hook(u'Exiting {0} hook {1}'.format(self.__class__.__name__, hook_name))


class Environment(object):

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

    def __init__(self, name, config=u'config.yaml', release=None, auto=False, **kwargs):
        self.name = name
        self.config = config
        self.release = release
        self.auto = auto
        self.__dict__.update(kwargs)

    @print_stdouts
    def bootstrap(self, **kwargs):
        print(u'Cleanup and bootstrap environment {0}'.format(self.name))
        if self.auto or confirm(u'do it now', default=False):
            destroy_environment(self.name, remove_default=True)
            sync_tools(self.name, all_tools=True)
            return (True, [bootstrap_environment(self.name, **kwargs)])
        return (False, [None])

    @print_stdouts
    def ensure_num_units(self, charm, service, num_units=1, expose=False, required=True, **kwargs):
        kwargs['release'] = kwargs.get('release', self.release)
        kwargs['local'] = kwargs.get('local', True)
        kwargs['repository'] = kwargs.get('repository', self.charms_path if kwargs['local'] else None)
        s = u's' if num_units > 1 else u''
        print(u'Deploy {0} as {1} (ensure {2} instance{3})'.format(charm, service, num_units, s))
        stdouts = [None] * 2
        if self.auto and required or confirm(u'do it now', default=False):
            stdouts[0] = ensure_num_units(self.name, charm, service, num_units=num_units, config=self.config, **kwargs)
            if expose:
                stdouts[1] = expose_service(self.name, service)
            return (True, stdouts)
        return (False, stdouts)

    # Services
    def get_service_config(self, service, **kwargs):
        return get_service_config(self.name, service, **kwargs)

    @print_stdouts
    def unexpose_service(self, service):
        print(u'Unexpose service {0}'.format(service))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [unexpose_service(self.name, service)])
        return (False, [None])

    # Units
    def get_unit(self, service, number):
        return get_unit(self.name, service, number)

    def get_units(self, service):
        return get_units(self.name, service)

    # Relations
    @print_stdouts
    def add_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [add_relation(self.name, service1, service2)])
        return (False, [None])

    @print_stdouts
    def remove_relation(self, service1, service2):
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            return (True, [remove_relation(self.name, service1, service2)])
        return (False, [None])


class DeploymentScenario(object):

    def main(self, environments, **kwargs):
        parser = self.get_parser(**kwargs)
        args = vars(parser.parse_args())
        charms_path = args.pop(u'charms_path')
        release = args.pop(u'release')
        auto = args.pop(u'auto')
        self.environments = environments
        for environment in environments:
            environment.charms_path = charms_path
            environment.release = environment.release or release
            environment.auto = auto
            self.__dict__.update({environment.name: environment})  # A shortcut
        self.__dict__.update(args)
        self.run()

    def get_parser(self, epilog=u'', charms_path=u'.', release=u'raring', auto=False):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=epilog)
        parser.add_argument(u'-m', u'--charms_path', action=u'store',      default=charms_path)
        parser.add_argument(u'-r', u'--release',     action=u'store',      default=release)
        parser.add_argument(u'-a', u'--auto',        action=u'store_true', default=auto)
        return parser

    def run(self):
        raise NotImplementedError(u'Here should be implemented the deployment scenario.')
