# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
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

from __future__ import absolute_import, division, print_function, unicode_literals

import json, os, socket, random, subprocess, sys, time, uuid, yaml
from codecs import open
from os.path import abspath, expanduser, join
from .console import confirm
from .encoding import string_types, to_bytes
from .filesystem import from_template, try_remove, try_symlink
from .exception import TimeoutError
from .subprocess import cmd


CONFIG_FILENAME = u'config.yaml'
METADATA_FILENAME = u'metadata.yaml'

DEFAULT_ENVIRONMENTS_FILE = abspath(expanduser(u'~/.juju/environments.yaml'))
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

ALL_STATES = PENDING, INSTALLED, STARTED, STOPPED, NOT_STARTED, ERROR, UNKNOWN = \
    (u'pending', u'installed', u'started', u'stopped', u'not-started', u'error', u'unknown')

UNKNOWN_STATES = (UNKNOWN,)
PENDING_STATES = (PENDING, INSTALLED)
STARTED_STATES = (STARTED,)
STOPPED_STATES = (STOPPED,)
ERROR_STATES = (ERROR, NOT_STARTED)

# Some Amazon EC2 constraints, waiting for instance-type to be implemented ...
M1_SMALL = u'arch=amd64 cpu-cores=1 cpu-power=100 mem=1.5G'
M1_MEDIUM = u'arch=amd64 cpu-cores=1 cpu-power=200 mem=3.5G'
C1_MEDIUM = u'arch=amd64 cpu-cores=2 cpu-power=500 mem=1.5G'


def juju_do(command, environment=None, options=None, fail=True, log=None, **kwargs):
    u"""
    Execute a command ``command`` into environment ``environment``.

    **Known issue**:

    Locking Juju status 'are you sure you want to continue connecting (yes/no)'.

    We need a way to confirm our choice ``cmd(u'juju status --environment %s' % environment, cli_input=u'yes\\n')``
    seem to not work as expected. This happens the first time (and only the first time) juju connect to a freshly
    deployed environment.

    Solution : http://askubuntu.com/questions/123072/ssh-automatically-accept-keys::

        $ echo 'StrictHostKeyChecking no' >> ~/.ssh/config
    """
    is_destroy = (command == u'destroy-environment')
    command = [u'sudo', u'juju', command] if command == u'destroy-environment' else [u'juju', command]
    if isinstance(environment, string_types) and environment != u'default':
        command += [u'--environment', environment]
    if isinstance(options, list):
        command += options
    env = os.environ.copy()
    env[u'HOME'] = expanduser(u'~/')
    env[u'JUJU_HOME'] = expanduser(u'~/.juju')
    if is_destroy:
        # FIXME Automate yes answer to destroy-environment
        c_string = u' '.join([unicode(arg) for arg in command])
        return subprocess.check_call(c_string, shell=True) if fail else subprocess.call(c_string, shell=True)
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

# Environments ---------------------------------------------------------------------------------------------------------

def add_environment(environment, type, region, access_key, secret_key, control_bucket, default_series,
                    environments=None):
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


def get_environment(environment, environments=None, get_status=False, status_timeout=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environment = environments_dict[u'default'] if environment == u'default' else environment
    try:
        environment_dict = environments_dict[u'environments'][environment]
    except KeyError:
        raise ValueError(to_bytes(u'No environment with name {0}.'.format(environment)))
    if get_status:
        environment_dict[u'status'] = Environment(name=environment).status(timeout=status_timeout)
    return environment_dict


def get_environments(environments=None, get_status=False, status_timeout=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    environments = {}
    for environment in environments_dict[u'environments'].iteritems():
        informations = environment[1]
        if get_status:
            try:
                informations[u'status'] = Environment(name=environment[0]).status(timeout=status_timeout)
            except RuntimeError:
                informations[u'status'] = UNKNOWN
        environments[environment[0]] = informations
    return (environments, environments_dict[u'default'])


def get_environments_count(environments=None):
    environments = environments or DEFAULT_ENVIRONMENTS_FILE
    environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
    return len(environments_dict[u'environments'])

# Units ----------------------------------------------------------------------------------------------------------------

def get_unit_path(service, number, *args):
    return join(u'/var/lib/juju/agents/unit-{0}-{1}/charm'.format(service, number), *args)

# Helpers --------------------------------------------------------------------------------------------------------------

__get_ip = None


def get_ip():
    global __get_ip
    if __get_ip is None:
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

    Attribute ``local_config`` must be set by derived class to an instance of ``serialization.PickelableObject``.
    This should be loaded from a file that is local to the unit by ``__init__``. This file is used to store service/
    unit-specific configuration. In EBU's project called OSCIED, this file is even read by the encapsulated python
    code of the worker (celery daemon).

    **Example usage**

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

    >>> from os.path import dirname
    >>> here = abspath(expanduser(dirname(__file__)))
    >>> here = join(here, u'../../..' if u'build/lib' in here else u'..', u'tests')
    >>> metadata = join(here, u'metadata.yaml')
    >>> config = join(here, u'config.yaml')

    Trigger some hooks:

    >>> my_hooks = MyCharmHooks(metadata, config, DEFAULT_OS_ENV, force_disable_juju=True) # doctest: +ELLIPSIS
    [DEBUG] Using juju False, reason: Disabled by user.
    [DEBUG] Load metadatas from file ...
    >>>
    >>> my_hooks.trigger(u'install')
    [HOOK] Execute MyCharmHooks hook install
    [DEBUG] hello world, install some packages with self.cmd(...)
    [HOOK] Exiting MyCharmHooks hook install
    >>>
    >>> my_hooks.trigger(u'config-changed')
    [HOOK] Execute MyCharmHooks hook config-changed
    [REMARK] update services based on self.config and update self.local_config !
    [HOOK] Exiting MyCharmHooks hook config-changed
    >>>
    >>> my_hooks.trigger(u'start')
    [HOOK] Execute MyCharmHooks hook start
    [INFO] start services
    [HOOK] Exiting MyCharmHooks hook start
    >>>
    >>> my_hooks.trigger(u'stop')
    [HOOK] Execute MyCharmHooks hook stop
    [INFO] stop services
    [HOOK] Exiting MyCharmHooks hook stop
    >>>
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
            self.private_address = socket.getfqdn(self.unit_get(u'private-address'))
            self.public_address = socket.getfqdn(self.unit_get(u'public-address'))
        except (subprocess.CalledProcessError, OSError) as e:
            reason = e
            self.juju_ok = False
            if default_config is not None:
                self.load_config(default_config)
            self.env_uuid = default_os_env[u'JUJU_ENV_UUID']
            self.name = default_os_env[u'JUJU_UNIT_NAME']
            self.private_address = self.public_address = socket.getfqdn(get_ip())
        self.directory = os.getcwd()
        self.debug(u'Using juju {0}, reason: {1}'.format(self.juju_ok, reason))
        self.load_metadata(metadata)

    # ------------------------------------------------------------------------------------------------------------------

    @property
    def id(self):
        u"""
        Returns the id extracted from the unit's name.

        **Example usage**

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.name = u'oscied-storage/3'
        >>> hooks.id
        3
        """
        return int(self.name.split(u'/')[1])

    @property
    def name_slug(self):
        return self.name.replace(u'/', u'-')

    # FIXME add cache decorator
    @property
    def is_leader(self):
        u"""
        Returns True if current unit is the leader of the peer-relation.

        By convention, the leader is the unit with the *smallest* id (the *oldest* unit).
        """
        try:
            rel_ids = self.relation_ids(u'peer')
            if not rel_ids:
                return True  # no peer relation, so we're a leader that feels alone !
            assert len(rel_ids) == 1, u'Expect only 1 peer relation id: {0}'.format(rel_ids)
            peers = self.relation_list(rel_ids[0])
            self.debug(u'us={0} peers={1}'.format(self.name, peers))
            return len(peers) == 0 or self.name <= min(peers)
        except Exception as e:
            self.remark(u'Bug during leader detection: {0}'.format(repr(e)))
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

    # FIXME add memoize decorator
    def unit_get(self, attribute):
        if self.juju_ok:
            return self.cmd([u'unit-get', attribute])['stdout'].strip()
        raise NotImplementedError(to_bytes(u'FIXME juju-less unit_get not yet implemented'))

    # FIXME add memoize decorator
    def relation_get(self, attribute=None, unit=None, relation_id=None):
        if self.juju_ok:
            command = [u'relation-get']
            if relation_id is not None:
                command += [u'-r', relation_id]
            command += filter(None, [attribute, unit])
            return self.cmd(command)['stdout'].strip()
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_get not yet implemented'))

    # FIXME add memoize decorator
    def relation_ids(self, relation_name=u''):
        if self.juju_ok:
            result = self.cmd([u'relation-ids', u'--format', u'json', relation_name], fail=False)
            return json.loads(result[u'stdout']) if result[u'returncode'] == 0 else None
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_ids not yet implemented'))

    # FIXME add memoize decorator
    def relation_list(self, relation_id=None):
        if self.juju_ok:
            command = [u'relation-list', u'--format', u'json']
            if relation_id is not None:
                command += [u'-r', relation_id]
            result = self.cmd(command, fail=False)
            return json.loads(result[u'stdout']) if result[u'returncode'] == 0 else None
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_list not yet implemented'))

    def relation_set(self, **kwargs):
        if self.juju_ok:
            command = [u'relation-set']
            command += [u'{0}={1}'.format(key, value) for key, value in kwargs.iteritems()]
            return self.cmd(command)
        raise NotImplementedError(to_bytes(u'FIXME juju-less relation_set not yet implemented'))

    # Convenience methods for logging ----------------------------------------------------------------------------------

    def debug(self, message):
        u"""Convenience method for logging a debug-related message."""
        if self.config.verbose:
            return self.log(u'[DEBUG] {0}'.format(message))

    def info(self, message):
        u"""Convenience method for logging a standard message."""
        return self.log(u'[INFO] {0}'.format(message))

    def hook(self, message):
        u"""Convenience method for logging the triggering of a hook."""
        return self.log(u'[HOOK] {0}'.format(message))

    def remark(self, message):
        u"""Convenience method for logging an important remark."""
        return self.log(u'[REMARK] {0} !'.format(message))

    # ------------------------------------------------------------------------------------------------------------------

    def load_config(self, config):
        u"""
        Updates ``config`` attribute with given configuration.

        **Example usage**

        >>> from os.path import dirname
        >>> here = abspath(expanduser(dirname(__file__)))
        >>> config = join(here, u'../../..' if u'build/lib' in here else u'..', u'tests/config.yaml')
        >>>
        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hasattr(hooks.config, u'pingu') or hasattr(hooks.config, u'rabbit_password')
        False
        >>> hooks.load_config({u'pingu': u'bi bi'})
        >>> print(hooks.config.pingu)
        bi bi
        >>> hooks.config.verbose = True
        >>>
        >>> hooks.load_config(config)  # doctest: +ELLIPSIS
        [DEBUG] Load config from file ...
        [DEBUG] Convert boolean option ... true -> True
        [DEBUG] Convert boolean option ... true -> True
        [DEBUG] Convert boolean option ... true -> True
        >>> hasattr(hooks.config, u'rabbit_password')
        True
        """
        self.config.__dict__.update(load_unit_config(config, log=self.debug))

    def save_local_config(self):
        u"""Save or update local configuration file only if this instance has the attribute ``local_config``."""
        if self.local_config is not None:
            self.debug(u'Save (updated) local configuration {0}'.format(self.local_config))
            self.local_config.write()

    def load_metadata(self, metadata):
        u"""
        Set ``metadata`` attribute with given metadatas, ``metadata`` can be:

        * The filename of a charm metadata file (e.g. ``metadata.yaml``)
        * A dictionary containing the metadatas.

        **Example usage**

        >>> from nose.tools import assert_equal
        >>> from os.path import dirname
        >>> here = abspath(expanduser(dirname(__file__)))
        >>> metadata = join(here, u'../../..' if u'build/lib' in here else u'..', u'tests/metadata.yaml')

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.metadata
        >>> hooks.load_metadata({u'ensemble': u'oscied'})
        >>> assert_equal(hooks.metadata, {u'ensemble': u'oscied'})
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

    def cmd(self, command, logging=True, **kwargs):
        u"""Calls the ``command`` and returns a dictionary with *stdout*, *stderr*, and the *returncode*."""
        return cmd(command, log=self.debug if logging else None, **kwargs)

    def template2config(self, template, config, values):
        from_template(template, config, values)
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

    def __init__(self, name=u'default', charms_path=u'charms', config=CONFIG_FILENAME, release=None, auto=False,
                 min_timeout=15):
        self.name = name
        self.charms_path = charms_path
        self.config = config
        self.release = release
        self.auto = auto
        self.min_timeout = min_timeout

    def status(self, fail=False, timeout=15):
        u"""Return the status of the environment or None in case of time-out [TODO verify other conditions]."""
        if timeout is not None and timeout < self.min_timeout:
            raise ValueError(to_bytes(u'A time-out of {0} for status is dangerous, please increase it to {1}+ or set it'
                             u' to None'.format(timeout, self.min_timeout)))
        status_dict = juju_do(u'status', self.name, timeout=timeout, fail=fail)
        if fail and not status_dict:
            raise RuntimeError(to_bytes(u'Unable to retrieve status of environment {0}.'.format(self.name)))
        return status_dict

    def is_bootstrapped(self, timeout=15):
        u"""Return True if the environment is bootstrapped (status returns something)."""
        try:
            return bool(self.status(timeout=timeout))
        except:
            return False

    def symlink_local_charms(self, default_path=u'default'):
        u"""Symlink charms default directory to directory of current release."""
        release_symlink = abspath(join(self.charms_path, self.release))
        try_remove(release_symlink)
        try_symlink(abspath(join(self.charms_path, default_path)), release_symlink)

    def sync_tools(self, all_tools=True):
        u"""Copy tools from the official bucket into a local environment."""
        options = [u'--all'] if all_tools else None
        return juju_do(u'sync-tools', self.name, options=options)

    def bootstrap(self, synchronize_tools=False, wait_started=False, started_states=STARTED_STATES,
                  error_states=ERROR_STATES, timeout=615, status_timeout=15, polling_delay=30):
        u"""
        Terminate all machines and other associated resources for an environment and bootstrap it.

        :param kwargs: Extra arguments for juju_do(), options is not allowed.
        """
        print(u'Cleanup and bootstrap environment {0}'.format(self.name))
        print(u'[WARNING] This will terminate all units deployed into environment {0} by juju !'.format(self.name))
        if self.auto or confirm(u'do it now', default=False):
            self.destroy(remove_default=True)
            if synchronize_tools:
                self.sync_tools(all_tools=True)
            result = juju_do(u'bootstrap', self.name)
            if wait_started:
                start_time = time.time()
                while True:
                    time_zero = time.time()
                    try:
                        state = self.status(timeout=status_timeout)[u'machines'][u'0'][u'agent-state']
                    except (KeyError, TypeError):
                        state = UNKNOWN
                    delta_time = time.time() - start_time
                    timeout_time = timeout - delta_time
                    print(u'State of juju bootstrap machine is {0}, time-out{1}'.format(
                          state, u' in {0:.0f} seconds'.format(timeout_time) if timeout_time > 0 else u'!'))
                    if state in started_states:
                        print(u'Environment bootstrapped in approximatively {0:.0f} seconds'.format(delta_time))
                        break
                    elif state in error_states:
                        raise RuntimeError(u'Bootstrap failed with state {0}.'.format(state))
                    if delta_time > timeout:
                        raise TimeoutError(u'Bootstrap time-out with state {0}.'.format(state))
                    time.sleep(max(0, polling_delay - (time.time() - time_zero)))
            return result

    def destroy(self, environments=None, remove_default=False, remove=False, timeout=15):
        # FIXME simpler algorithm
        environments = environments or DEFAULT_ENVIRONMENTS_FILE
        environments_dict = yaml.load(open(environments, u'r', encoding=u'utf-8'))
        name = environments_dict[u'default'] if self.name == u'default' else self.name
        if name not in environments_dict[u'environments']:
            raise IndexError(to_bytes(u'No environment with name {0}.'.format(name)))
        if not remove_default and name == environments_dict[u'default']:
            raise RuntimeError(to_bytes(u'Cannot remove default environment {0}.'.format(name)))
        result = juju_do(u'destroy-environment', name) if self.is_bootstrapped(timeout=timeout) else None
        if remove:
            # Check if environment destroyed otherwise a lot of trouble with $/€ !
            if self.is_boostrapped(timeout=timeout):
                raise RuntimeError(to_bytes(u'Environment {0} not removed, it is still alive.'.format(name)))
            else:
                del environments_dict[u'environments'][name]
                open(environments, u'w', encoding=u'utf-8').write(yaml.safe_dump(environments_dict))
        return result

    # Services

    def get_service_config(self, service, options=None, fail=True):
        return juju_do(u'get', self.name, options=[service], fail=fail)

    def get_service(self, service, default=None, fail=True, timeout=15):
        status_dict = self.status(fail=fail, timeout=timeout)
        if not status_dict:
            return default
        try:
            return status_dict[u'services'][service]
        except KeyError:
            if fail:
                raise RuntimeError(to_bytes(u'Service {0} not found in environment {1}.'.format(service, self.name)))
        return default

    def expose_service(self, service, fail=True):
        return juju_do(u'expose', self.name, options=[service], fail=fail)

    def unexpose_service(self, service, fail=True):
        return juju_do(u'unexpose', self.name, options=[service], fail=fail)

    def destroy_service(self, service, fail=True):
        return juju_do(u'destroy-service', self.name, options=[service], fail=fail)

    # Units

    def ensure_num_units(self, charm, service, constraints=None, expose=False, local=True, num_units=1, release=None,
                         repository=None, required=True, terminate=False, to=None, units_number_to_keep=None, fail=True,
                         timeout=None):
        u"""
        Ensure ``num_units`` units of ``service`` into ``environment`` by adding new or destroying useless units first !

        At the end of this method, the number of running units can be greater as ``num_units`` because this algorithm
        will not destroy units with number in ``units_number_to_keep``.

        Some of the argument are forwarded to underlying methods (add_units, deploy_units, destroy_unit or nothing)
        depending on the required action.

        * Set local to False to deploy non-local charms.
        * Set required to False to bypass this method in automatic mode.
        * Set units_number_to_keep to a (list, tuple, ...) with the units you want to protect against destruction.
        """
        results = {}
        release = release or self.release
        repository = repository or (self.charms_path if local else None)
        s = u'' if num_units is None or num_units < 2 else u's'
        print(u'Deploy {0} as {1} (ensure {2} instance{3})'.format(charm, service or charm, num_units, s))
        if self.auto and required or confirm(u'do it now', default=False):
            assert(num_units is None or num_units >= 0)
            units_dict = self.get_units(service, default=None, fail=False, timeout=timeout)
            units_count = None if units_dict is None else len(units_dict)
            if num_units is None and units_count:
                results[u'destroy_service'] = self.destroy_service(service)
            elif units_count is None:
                results[u'deploy_units'] = self.deploy_units(
                    charm, service, num_units=num_units, to=to, config=self.config, constraints=constraints,
                    local=local, release=release, repository=repository)
            elif units_count < num_units:
                num_units = num_units - units_count
                results[u'add_units'] = self.add_units(service or charm, num_units=num_units, to=to)
            elif units_count > num_units:
                num_units = units_count - num_units
                destroyed = {}
                # Sort units by status to kill the useless units before any others !
                # FIXME implement status comparison for sorting ??
                for status in (ERROR, NOT_STARTED, PENDING, INSTALLED, STARTED):
                    if num_units == 0:
                        break
                    for number, unit_dict in units_dict.items():
                        if num_units == 0:
                            break
                        if units_number_to_keep is not None and number in units_number_to_keep:
                            continue
                        unit_status = unit_dict.get(u'agent-state', status)
                        if unit_status == status or unit_status not in ALL_STATES:
                            self.destroy_unit(service, number, terminate=False)
                            destroyed[number] = unit_dict
                            del units_dict[number]
                            num_units -= 1
                if terminate:
                    time.sleep(5)
                    for unit_dict in destroyed.itervalues():
                        # FIXME handle failure (multiple units same machine, machine busy, missing ...)
                        self.destroy_machine(unit_dict[u'machine'])
                results[u'destroy_unit'] = destroyed
                return results
            if expose:
                results[u'expose_service'] = self.expose_service(service)
            return results

    def destroy_unit(self, service, number, terminate, delay_terminate=5, fail=True, timeout=None):
        name = u'{0}/{1}'.format(service, number)
        unit_dict = self.get_unit(service, number, default=None, fail=fail, timeout=timeout)
        if unit_dict is not None:
            if terminate:
                juju_do(u'destroy-unit', self.name, options=[name])
                time.sleep(delay_terminate)  # FIXME ideally a flag https://bugs.launchpad.net/juju-core/+bug/1206532
                return self.destroy_machine(unit_dict[u'machine'])
            return juju_do(u'destroy-unit', self.name, options=[name])

    def get_unit(self, service, number, default=None, fail=True, timeout=None):
        # FIXME maybe none if missing or something else
        name = u'{0}/{1}'.format(service, number)
        service_dict = self.get_service(service, default=None, fail=fail, timeout=timeout)
        if service_dict is not None:
            try:
                return service_dict[u'units'][name]
            except KeyError:
                if fail:
                    raise RuntimeError(to_bytes(u'No unit with name {0} on environment {1}.'.format(name, self.name)))
        return default

    def add_units(self, service, num_units=1, to=None):
        options = [u'--num-units', num_units]
        if to is not None:
            options += [u'--to', to]
        options += [service]
        return juju_do(u'add-unit', self.name, options=options)

    def deploy_units(self, charm, service=None, num_units=1, to=None, config=None, constraints=None, local=False,
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
        return juju_do(u'deploy', self.name, options=options)

    def get_units(self, service, default=None, fail=True, timeout=None):
        service_dict = self.get_service(service, default=None, fail=fail, timeout=timeout)
        if service_dict is None:
            return default
        units_dict = service_dict.get(u'units', None)
        if units_dict is None:
            return default
        return {name.split(u'/')[1]: infos for name, infos in units_dict.iteritems()}

    def get_units_count(self, service, default=None, fail=True, timeout=None):
        service_dict = self.get_service(default=None, fail=fail, timeout=timeout)
        if service_dict is None:
            return default
        units_dict = service_dict.get(u'units', None)
        if units_dict is None:
            return default
        return len(units_dict)

    # Machines

    def cleanup_machines(self, fail=True, timeout=None):
        environment_dict = self.status(fail=fail, timeout=timeout) or {}
        machines = environment_dict.get(u'machines', {}).iterkeys()
        busy_machines = [u'0']  # the machine running the juju daemon !
        for s_dict in environment_dict.get(u'services', {}).itervalues():
            busy_machines = (busy_machines +
                             [u_dict.get(u'machine', None) for u_dict in s_dict.get(u'units', {}).itervalues()])
        idle_machines = [machine for machine in machines if machine not in busy_machines]
        if idle_machines:
            return juju_do(u'destroy-machine', self.name, options=idle_machines)

    def destroy_machine(self, machine):
        return juju_do(u'destroy-machine', self.name, options=[machine])

    # Relations

    def add_relation(self, service1, service2, relation1=None, relation2=None):
        u"""Add a relation between 2 services. Knowing that the relation may already exists."""
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
            member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
            result = None
            try:
                result = juju_do(u'add-relation', self.name, options=[member1, member2])
            except RuntimeError as e:
                # FIXME get status of service before adding relation may be cleaner.
                if not u'already exists' in unicode(e):
                    raise
            return result

    def remove_relation(self, service1, service2, relation1=None, relation2=None):
        u"""Remove a relation between 2 services. Knowing that the relation may not exists."""
        print(u'Add relation between {0} and {1}'.format(service1, service2))
        if self.auto or confirm(u'do it now', default=False):
            member1 = service1 if relation1 is None else u'{0}:{1}'.format(service1, relation1)
            member2 = service2 if relation2 is None else u'{0}:{1}'.format(service2, relation2)
            try:
                result = juju_do(u'remove-relation', self.name, options=[member1, member2])
            except RuntimeError as e:
                # FIXME get status of service before removing relation may be cleaner.
                if not u'exists' in unicode(e):
                    raise
            return result


class DeploymentScenario(object):

    def __init__(self, environments, **kwargs):
        parser = self.get_parser(**kwargs)
        args = vars(parser.parse_args())
        auto = args.pop(u'auto')
        charms_path = args.pop(u'charms_path')
        release = args.pop(u'release')
        self.environments = environments
        for environment in environments:
            environment.auto = auto
            environment.charms_path = charms_path
            environment.release = environment.release or release
            self.__dict__.update({environment.name: environment})  # A shortcut
        # FIXME use metaclass instead of updating __dict__ if it does add attributes to the class.
        self.__dict__.update(args)

    def get_parser(self, epilog=u'', charms_path=u'charms', release=u'raring', auto=False):
        HELP_A = u'Toggle automatic confirmation of the actions, WARNING: Use it with care.'
        HELP_M = u'Directory (repository) of any local charm.'
        HELP_R = u'Ubuntu serie to deploy by JuJu.'
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=epilog)
        parser.add_argument(u'-a', u'--auto',        action=u'store_true', help=HELP_A, default=auto)
        parser.add_argument(u'-m', u'--charms_path', action=u'store',      help=HELP_M, default=charms_path)
        parser.add_argument(u'-r', u'--release',     action=u'store',      help=HELP_R, default=release)
        return parser

    def run(self):
        raise NotImplementedError(u'Here should be implemented the deployment scenario.')


# Simulation -----------------------------------------------------------------------------------------------------------

# DISCLAIMER: Ideally this module will implement a simulated juju_do to make it possible to use the same methods to
# drive a real or a simulated juju process ... The following code is a partial/light implementation of ...
# Do not use it for your own purposes !!!

class SimulatedUnit(object):
    u"""A simulated unit with a really simple state machine having a latency to start and stop."""

    def __init__(self, start_latency_range, stop_latency_range, state=PENDING):
        self.counter = self.next_state = None
        self.state = state
        self.start_latency_range = start_latency_range
        self.stop_latency_range = stop_latency_range

    def start(self):
        self.counter = random.randint(*self.start_latency_range)
        self.next_state = STARTED

    def stop(self):
        self.counter = random.randint(*self.stop_latency_range)
        self.next_state = STOPPED

    def tick(self):
        if self.counter:
            self.counter -= 1
            if self.counter == 0:
                self.state = self.next_state
                self.next_state = None


class SimulatedUnits(object):
    u"""Manage a set of simulated units."""

    def __init__(self, start_latency_range, stop_latency_range):
        self.start_latency_range = start_latency_range
        self.stop_latency_range = stop_latency_range  # FIXME not yet used by this simulator ...
        self.units = {}
        self.number = 0

    def ensure_num_units(self, num_units=1, units_number_to_keep=None):
        u"""Ensure ``num_units`` units by adding new units or destroying useless units first !"""
        assert(num_units is None or num_units >= 0)
        units_count = len(self.units)
        if num_units is None:
            self.units = {}
            return u'Simulate destruction of service.'
        if units_count < num_units:
            num_units = num_units - units_count
            for i in xrange(num_units):
                unit = SimulatedUnit(self.start_latency_range, self.stop_latency_range)
                unit.start()
                self.units[self.number] = unit
                self.number += 1
            return u'Simulate deployment of {0} units.'.format(num_units)
        if units_count > num_units:
            num_units = units_count - num_units
            destroyed = {}
            # Sort units by status to kill the useless units before any others !
            # FIXME implement status comparison for sorting ??
            for state in (ERROR, NOT_STARTED, PENDING, INSTALLED, STARTED):
                if num_units == 0:
                    break
                for number, unit in self.units.items():
                    if num_units == 0:
                        break
                    if units_number_to_keep is not None and number in units_number_to_keep:
                        continue
                    if unit.state == state or unit.state not in ALL_STATES:
                        destroyed[number] = unit
                        unit.stop()
                        num_units -= 1
            return destroyed

    def tick(self):
        u"""Increment time of 1 tick and remove units that are in STOPPED state."""
        for number, unit in self.units.items():
            unit.tick()
            if unit.state == STOPPED:
                del self.units[number]
