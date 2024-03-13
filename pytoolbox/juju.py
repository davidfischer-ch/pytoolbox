# pylint:disable=too-many-lines
from __future__ import annotations

import argparse
import json
import os
import socket
import random
import subprocess
import sys
import time
import uuid
import yaml

from . import console, filesystem, module, subprocess as py_subprocess  # pylint:disable=reimported
from .argparse import FullPaths, is_dir

_all = module.All(globals())

CONFIG_FILENAME = 'config.yaml'
METADATA_FILENAME = 'metadata.yaml'

DEFAULT_ENVIRONMENTS_FILE = os.path.abspath(os.path.expanduser('~/.juju/environments.yaml'))
DEFAULT_OS_ENV = {
    'APT_LISTCHANGES_FRONTEND': 'none',
    'CHARM_DIR': '/var/lib/juju/units/oscied-storage-0/charm',
    'DEBIAN_FRONTEND': 'noninteractive',
    '_JUJU_CHARM_FORMAT': '1',
    'JUJU_AGENT_SOCKET': '/var/lib/juju/units/oscied-storage-0/.juju.hookcli.sock',
    'JUJU_CLIENT_ID': 'constant',
    'JUJU_ENV_UUID': '878ca8f623174911960f6fbed84f7bdd',
    'JUJU_PYTHONPATH': ':/usr/lib/python2.7/dist-packages:/usr/lib/python2.7'
                       ':/usr/lib/python2.7/plat-x86_64-linux-gnu'
                       ':/usr/lib/python2.7/lib-tk'
                       ':/usr/lib/python2.7/lib-old'
                       ':/usr/lib/python2.7/lib-dynload'
                       ':/usr/local/lib/python2.7/dist-packages'
                       ':/usr/lib/pymodules/python2.7',
    '_': '/usr/bin/python',
    'JUJU_UNIT_NAME': 'oscied-storage/0',
    'PATH': '/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin',
    'PWD': '/var/lib/juju/units/oscied-storage-0/charm',
    'SHLVL': '1'
}

ALL_STATES = PENDING, INSTALLED, STARTED, STOPPED, NOT_STARTED, ERROR, UNKNOWN = \
    ('pending', 'installed', 'started', 'stopped', 'not-started', 'error', 'unknown')

UNKNOWN_STATES = (UNKNOWN,)
PENDING_STATES = (PENDING, INSTALLED)
STARTED_STATES = (STARTED,)
STOPPED_STATES = (STOPPED,)
ERROR_STATES = (ERROR, NOT_STARTED)

# Some Amazon EC2 constraints, waiting for instance-type to be implemented ...
M1_SMALL = 'arch=amd64 cpu-cores=1 cpu-power=100 mem=1.5G'
M1_MEDIUM = 'arch=amd64 cpu-cores=1 cpu-power=200 mem=3.5G'
C1_MEDIUM = 'arch=amd64 cpu-cores=2 cpu-power=500 mem=1.5G'

ENVIRONMENT_COMMANDS = ('destroy-environment', )
SUPER_COMMANDS = ('destroy-environment', )


def juju_do(command, environment=None, options=None, fail=True, log=None, **kwargs):
    """
    Execute a command `command` into environment `environment`.

    **Known issue**:

    Locking Juju status 'are you sure you want to continue connecting (yes/no)'.

    We need a way to confirm our choice
    ``cmd('juju status --environment %s' % environment, cli_input='yes\\n')``
    seem to not work as expected. This happens the first time (and only the first time)
    juju connect to a freshly deployed environment.

    Solution : http://askubuntu.com/questions/123072/ssh-automatically-accept-keys::

        $ echo 'StrictHostKeyChecking no' >> ~/.ssh/config
    """
    is_destroy = command == 'destroy-environment'
    arguments = ['sudo', 'juju', command] if command in SUPER_COMMANDS else ['juju', command]

    if isinstance(environment, str) and environment != 'default':
        arguments += \
            [environment] if command in ENVIRONMENT_COMMANDS else ['--environment', environment]

    if isinstance(options, list):
        arguments += [str(o) for o in options]

    env = os.environ.copy()
    env['HOME'] = os.path.expanduser('~/')
    env['JUJU_HOME'] = os.path.expanduser('~/.juju')

    if is_destroy:
        # TODO Automate yes answer to destroy-environment
        method = subprocess.check_call if fail else subprocess.call
        return method(arguments)
    result = py_subprocess.cmd(arguments, fail=False, log=log, env=env, **kwargs)

    if result['returncode'] != 0 and fail:
        raise RuntimeError(f"Subprocess failed {' '.join(arguments)} : {result['stderr']}.")

    return yaml.safe_load(result['stdout'])


def load_unit_config(config, log=None):
    """
    Returns a dictionary containing the options names as keys and options default values as values.

    The parameter `config` can be:

    * The path of a charm configuration file (e.g. `config.yaml`).
    * A dictionary containing already loaded options names as keys and options values as values.
    """
    if isinstance(config, str):

        if hasattr(log, '__call__'):
            log(f'Load config from file {config}')

        with open(config, encoding='utf-8') as f:
            options = yaml.safe_load(f)['options']
            config = {}
            for option in options:
                config[option] = options[option]['default']

    for option, value in config.items():
        if str(value).lower() in ('false', 'true'):  # pylint:disable=use-set-for-membership
            config[option] = str(value).lower() == 'true'
            if hasattr(log, '__call__'):
                log(f'Convert boolean option {option} {value} -> {config[option]}')

    return config


def save_unit_config(path, service, config):
    with open(path, 'w', encoding='utf-8') as f:
        for option, value in config.items():
            if isinstance(value, bool):
                config[option] = str(value)
        config = {service: config}
        f.write(yaml.safe_dump(config))


# Environments -------------------------------------------------------------------------------------

def add_environment(
    environment,
    kind,
    region,
    access_key,
    secret_key,
    control_bucket,
    default_series,
    environments=None
):
    with open(environments or DEFAULT_ENVIRONMENTS_FILE, encoding='utf-8') as f:
        environments_dict = yaml.safe_load(f)

    if environment == 'default':
        raise ValueError(f'Cannot create an environment with name {environment}.')

    if environment in environments_dict['environments']:
        raise ValueError(f'The name {environment} is already used by another environment.')

    if kind == 'ec2':
        environment_dict = {
            'type': kind,
            'region': region,
            'access-key': access_key,
            'secret-key': secret_key,
            'control-bucket': control_bucket,
            'default-series': default_series,
            'ssl-hostname-verification': True,
            'juju-origin': 'ppa',
            'admin-secret': uuid.uuid4().hex
        }
    else:
        raise NotImplementedError(f'Registration of {kind} type of environment.')

    environments_dict['environments'][environment] = environment_dict

    with open(environments, 'w', encoding='utf-8') as f:
        f.write(yaml.safe_dump(environments_dict))

    try:
        return juju_do('bootstrap', environment)
    except RuntimeError as ex:
        if 'configuration error' in str(ex):
            del environments_dict['environments'][environment]
            with open(environments, 'w', encoding='utf-8') as f:
                f.write(yaml.safe_dump(environments_dict))
            raise ValueError(f'Cannot add environment {environment} ({ex}).') from ex
        raise


def get_environment(environment, environments=None, get_status=False, status_timeout=None):
    with open(environments or DEFAULT_ENVIRONMENTS_FILE, encoding='utf-8') as f:
        environments_dict = yaml.safe_load(f)

    environment = environments_dict['default'] if environment == 'default' else environment
    try:
        environment_dict = environments_dict['environments'][environment]
    except KeyError as ex:
        raise ValueError(f'No environment with name {environment}.') from ex

    if get_status:
        environment_dict['status'] = Environment(name=environment).status(timeout=status_timeout)

    return environment_dict


def get_environments(environments=None, get_status=False, status_timeout=None):
    with open(environments or DEFAULT_ENVIRONMENTS_FILE, encoding='utf-8') as f:
        environments_dict = yaml.safe_load(f)

    environments = {}
    for environment in environments_dict['environments'].items():
        information = environment[1]
        if get_status:
            try:
                information['status'] = \
                    Environment(name=environment[0]).status(timeout=status_timeout)
            except RuntimeError:
                information['status'] = UNKNOWN
        environments[environment[0]] = information

    return environments, environments_dict['default']


def get_environments_count(environments=None):
    with open(environments or DEFAULT_ENVIRONMENTS_FILE, encoding='utf-8') as f:
        return len(yaml.safe_load(f)['environments'])


# Units --------------------------------------------------------------------------------------------

def get_unit_path(service, number, *args):
    return os.path.join(f'/var/lib/juju/agents/unit-{service}-{number}/charm', *args)


# Helpers ------------------------------------------------------------------------------------------

__get_ip = None  # pylint:disable=invalid-name


def get_ip():
    global __get_ip  # pylint:disable=global-statement,invalid-name
    if __get_ip is None:
        host = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host.connect(('8.8.8.8', 80))
        __get_ip = host.getsockname()[0]
        host.close()
    return __get_ip


class CharmConfig(object):  # pylint:disable=too-few-public-methods

    def __init__(self):
        self.verbose = False

    def __repr__(self):
        return str(self.__dict__)


class CharmHooks(object):  # pylint:disable=too-many-instance-attributes,too-many-public-methods
    """
    A base class to build charms based on python hooks, callable even if juju is not installed.

    Attribute `local_config` must be set by derived class to an instance of
    `serialization.PickelableObject`. This should be loaded from a file that is local to the unit
    by `__init__`. This file is used to store service/ unit-specific configuration. In EBU's project
    called OSCIED, this file is even read by the encapsulated python code of the worker
    (celery daemon).

    **Example usage**

    >>> class MyCharmHooks(CharmHooks):
    ...
    ...     def hook_install(self):
    ...         self.debug('hello world, install some packages with self.cmd(...)')
    ...
    ...     def hook_config_changed(self):
    ...         self.remark('update services based on self.config and update self.local_config')
    ...
    ...     def hook_start(self):
    ...         self.info('start services')
    ...
    ...     def hook_stop(self):
    ...         self.info('stop services')
    ...
    >>> import os
    >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
    >>> here = os.path.join(here, '../../..' if 'build/lib' in here else '..', 'tests')
    >>> metadata = os.path.join(here, 'metadata.yaml')
    >>> config = os.path.join(here, 'config.yaml')

    Trigger some hooks:

    >>> my_hooks = MyCharmHooks(metadata, config, DEFAULT_OS_ENV, force_disable_juju=True)
    [DEBUG] Using juju False, reason: Disabled by user.
    [DEBUG] Load metadata from file ...
    >>>
    >>> my_hooks.trigger('install')
    [HOOK] Execute MyCharmHooks hook install
    [DEBUG] hello world, install some packages with self.cmd(...)
    [HOOK] Exiting MyCharmHooks hook install
    >>>
    >>> my_hooks.trigger('config-changed')
    [HOOK] Execute MyCharmHooks hook config-changed
    [REMARK] update services based on self.config and update self.local_config !
    [HOOK] Exiting MyCharmHooks hook config-changed
    >>>
    >>> my_hooks.trigger('start')
    [HOOK] Execute MyCharmHooks hook start
    [INFO] start services
    [HOOK] Exiting MyCharmHooks hook start
    >>>
    >>> my_hooks.trigger('stop')
    [HOOK] Execute MyCharmHooks hook stop
    [INFO] stop services
    [HOOK] Exiting MyCharmHooks hook stop
    >>>
    >>> my_hooks.trigger('not_exist')
    Traceback (most recent call last):
        ...
    AttributeError: 'MyCharmHooks' object has no attribute 'hook_not_exist'
    """

    def __init__(self, metadata, default_config, default_os_env, force_disable_juju=False):
        self.config = CharmConfig()
        self.local_config = None
        reason = 'Life is good !'
        try:
            if force_disable_juju:
                raise OSError('Disabled by user.')
            self.juju_ok = True
            self.load_config(json.loads(self.cmd(['config-get', '--format=json'])['stdout']))
            self.env_uuid = os.environ.get('JUJU_ENV_UUID')
            self.name = os.environ['JUJU_UNIT_NAME']
            self.private_address = socket.getfqdn(self.unit_get('private-address'))
            self.public_address = socket.getfqdn(self.unit_get('public-address'))
        except (subprocess.CalledProcessError, OSError) as ex:
            reason = ex
            self.juju_ok = False
            if default_config is not None:
                self.load_config(default_config)
            self.env_uuid = default_os_env['JUJU_ENV_UUID']
            self.name = default_os_env['JUJU_UNIT_NAME']
            self.private_address = self.public_address = socket.getfqdn(get_ip())
        self.directory = os.getcwd()
        self.debug(f'Using juju {self.juju_ok}, reason: {reason}')
        self.load_metadata(metadata)

    # ----------------------------------------------------------------------------------------------

    @property
    def identifier(self):
        """
        Returns the id extracted from the unit's name.

        **Example usage**

        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.name = 'oscied-storage/3'
        >>> hooks.identifier
        3
        """
        return int(self.name.split('/')[1])

    @property
    def name_slug(self):
        return self.name.replace('/', '-')

    # TODO add cache decorator
    @property
    def is_leader(self):
        """
        Returns True if current unit is the leader of the peer-relation.

        By convention, the leader is the unit with the *smallest* id (the *oldest* unit).
        """
        try:
            if not (rel_ids := self.relation_ids('peer')):
                return True  # no peer relation, so we're a leader that feels alone !
            assert len(rel_ids) == 1, f'Expect only 1 peer relation id: {rel_ids}'
            peers = self.relation_list(rel_ids[0])
            self.debug(f'us={self.name} peers={peers}')
            return len(peers) == 0 or self.name <= min(peers)
        except Exception as ex:  # pylint:disable=broad-except
            self.remark(f'Bug during leader detection: {repr(ex)}')
            return True

    # Maps calls to charm helpers functions and replace them if called in standalone ---------------

    def log(self, message):
        if self.juju_ok:
            return self.cmd(['juju-log', message], logging=False)  # Avoid infinite loop !
        print(message)
        return None

    def open_port(self, port, protocol='TCP'):
        if self.juju_ok:
            return self.cmd(['open-port', f'{port}/{protocol}'])
        return self.debug(f'Open port {port} ({protocol})')

    def close_port(self, port, protocol='TCP'):
        if self.juju_ok:
            return self.cmd(['close-port', f'{port}/{protocol}'])
        return self.debug(f'Close port {port} ({protocol})')

    # TODO add memoize decorator
    def unit_get(self, attribute):
        if self.juju_ok:
            return self.cmd(['unit-get', attribute])['stdout'].strip()
        raise NotImplementedError('FIXME juju-less unit_get not yet implemented')

    # TODO add memoize decorator
    def relation_get(self, attribute=None, unit=None, relation_id=None):
        if self.juju_ok:
            command = ['relation-get']
            if relation_id is not None:
                command += ['-r', relation_id]
            command += [_f for _f in (attribute, unit) if _f]
            return self.cmd(command)['stdout'].strip()
        raise NotImplementedError('FIXME juju-less relation_get not yet implemented')

    # TODO add memoize decorator
    def relation_ids(self, relation_name=''):
        if self.juju_ok:
            result = self.cmd(['relation-ids', '--format', 'json', relation_name], fail=False)
            return json.loads(result['stdout']) if result['returncode'] == 0 else None
        raise NotImplementedError('FIXME juju-less relation_ids not yet implemented')

    # TODO add memoize decorator
    def relation_list(self, relation_id=None):
        if self.juju_ok:
            command = ['relation-list', '--format', 'json']
            if relation_id is not None:
                command += ['-r', relation_id]
            result = self.cmd(command, fail=False)
            return json.loads(result['stdout']) if result['returncode'] == 0 else None
        raise NotImplementedError('FIXME juju-less relation_list not yet implemented')

    def relation_set(self, **kwargs):
        if self.juju_ok:
            command = ['relation-set']
            command += [f'{k}={v}' for k, v in kwargs.items()]
            return self.cmd(command)
        raise NotImplementedError('FIXME juju-less relation_set not yet implemented')

    # Convenience methods for logging --------------------------------------------------------------

    def debug(self, message):
        """Convenience method for logging a debug-related message."""
        return self.log(f'[DEBUG] {message}') if self.config.verbose else None

    def info(self, message):
        """Convenience method for logging a standard message."""
        return self.log(f'[INFO] {message}')

    def hook(self, message):
        """Convenience method for logging the triggering of a hook."""
        return self.log(f'[HOOK] {message}')

    def remark(self, message):
        """Convenience method for logging an important remark."""
        return self.log(f'[REMARK] {message} !')

    # ----------------------------------------------------------------------------------------------

    def load_config(self, config):
        """
        Updates `config` attribute with given configuration.

        **Example usage**

        >>> import os
        >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        >>> config = os.path.join(
        ...     here, '../../..' if 'build/lib' in here else '..', 'tests/config.yaml')
        >>>
        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hasattr(hooks.config, 'pingu') or hasattr(hooks.config, 'rabbit_password')
        False
        >>> hooks.load_config({'pingu': 'bi bi'})
        >>> hooks.config.pingu
        'bi bi'
        >>> hooks.config.verbose = True
        >>> hooks.load_config(config)
        [DEBUG] Load config from file ...
        [DEBUG] Convert boolean option ... true -> True
        [DEBUG] Convert boolean option ... true -> True
        [DEBUG] Convert boolean option ... true -> True
        >>> hasattr(hooks.config, 'rabbit_password')
        True
        """
        self.config.__dict__.update(load_unit_config(config, log=self.debug))

    def save_local_config(self):
        """
        Save or update local configuration file only if this instance has the attribute
        `local_config`.
        """
        if self.local_config is not None:
            self.debug(f'Save (updated) local configuration {self.local_config}')
            self.local_config.write()

    def load_metadata(self, metadata):
        """
        Set `metadata` attribute with given metadata, `metadata` can be:

        * The path of a charm metadata file (e.g. `metadata.yaml`)
        * A dictionary containing the metadata.

        **Example usage**

        >>> import os
        >>> here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        >>> metadata = os.path.join(
        ...     here, '../../..' if 'build/lib' in here else '..', 'tests/metadata.yaml')
        >>> hooks = CharmHooks(None, None, DEFAULT_OS_ENV, force_disable_juju=True)
        >>> hooks.metadata
        >>> hooks.load_metadata({'ensemble': 'oscied'})
        >>> hooks.metadata
        {'ensemble': 'oscied'}
        >>> hooks.config.verbose = True
        >>> hooks.load_metadata(metadata)
        [DEBUG] Load metadata from file ...
        >>> hooks.metadata['maintainer']
        'OSCIED Main Developper <david.fischer.ch@gmail.com>'
        """
        if isinstance(metadata, str):
            self.debug(f'Load metadata from file {metadata}')
            with open(metadata, encoding='utf-8') as f:
                metadata = yaml.safe_load(f)
        self.metadata = metadata

    # ----------------------------------------------------------------------------------------------

    def cmd(self, command, logging=True, **kwargs):
        """
        Calls the `command` and returns a dictionary with `stdout`, `stderr`, and the `returncode`.
        """
        return py_subprocess.cmd(command, log=self.debug if logging else None, **kwargs)

    def template_to_config(self, template, config, values):
        filesystem.from_template(template, config, values)
        self.remark(f'File {config} successfully generated')

    # ----------------------------------------------------------------------------------------------

    def trigger(self, hook_name=None):
        """
        Triggers a hook specified in `hook_name`, defaults to ``sys.argv[1]``.

        Hook's name is the nice hook name that one can find in official juju documentation.
        For example if `config-changed` is mapped to a call to ``self.hook_config_changed()``.

        A `ValueError` containing a usage string is raised if a bad number of argument is given.
        """
        if hook_name is None:
            if len(sys.argv) != 2:
                raise ValueError(f'Usage {sys.argv[0]} hook_name (e.g. config-changed)')
            hook_name = sys.argv[1]

        try:  # Call the function hooks_...
            self.hook(f'Execute {self.__class__.__name__} hook {hook_name}')
            getattr(self, f"hook_{hook_name.replace('-', '_')}")()
            self.save_local_config()
        except subprocess.CalledProcessError as ex:
            self.log('Exception caught:')
            self.log(ex.output)
            raise
        finally:
            self.hook(f'Exiting {self.__class__.__name__} hook {hook_name}')


class Environment(object):  # pylint:disable=too-many-instance-attributes,too-many-public-methods

    def __init__(
        self,
        name='default',
        charms_path='charms',
        config=CONFIG_FILENAME,
        release=None,
        auto=False,
        min_timeout=15
    ):
        self.name = name
        self.charms_path = os.path.abspath(charms_path)
        self.config = config
        self.release = release
        self.auto = auto
        self.min_timeout = min_timeout
        self._properties = None

    def properties(self, cached=False):
        """
        Return a dictionary with properties of the environments as returned by juju get-environment
        (type, ...).

        Set cached to True to allow using cached value of "properties". Caching should be used only
        if the properties you are interested to read, e.g. type, does not change at all!
        """
        if not self._properties or not cached:
            self._properties = juju_do('get-environment', self.name)
        return self._properties

    def status(self, fail=False, timeout=15):
        """
        Return the status of the environment or None in case of time-out
        [TODO verify other conditions].
        """
        if timeout is not None and timeout < self.min_timeout:
            raise ValueError(
                f'A time-out of {timeout} for status is dangerous, '
                f'please increase it to {self.min_timeout}+ or set it to None')
        status_dict = juju_do('status', self.name, timeout=timeout, fail=fail)
        if fail and not status_dict:
            raise RuntimeError(f'Unable to retrieve status of environment {self.name}.')
        return status_dict

    def is_bootstrapped(self, timeout=15):
        """Return True if the environment is bootstrapped (status returns something)."""
        try:
            return bool(self.status(timeout=timeout))
        except Exception:  # pylint:disable=broad-except
            return False

    def symlink_local_charms(self, default_path='default'):
        """Symlink charms default directory to directory of current release."""
        release_symlink = os.path.join(self.charms_path, self.release)
        filesystem.remove(release_symlink)
        filesystem.symlink(os.path.join(self.charms_path, default_path), release_symlink)

    def sync_tools(self, all_tools=True):
        """Copy tools from the official bucket into a local environment."""
        options = ['--all'] if all_tools else None
        return juju_do('sync-tools', self.name, options=options)

    def bootstrap(
        self,
        cleanup=True,
        synchronize_tools=False,
        wait_started=False,
        started_states=STARTED_STATES,
        error_states=ERROR_STATES,
        timeout=600,
        status_timeout=15,
        polling_delay=30
    ):  # pylint:disable=too-many-branches,too-many-locals
        """
        Bootstrap an environment, (optional) terminate all machines and other associated resources
        before the bootstrap.
        """
        if cleanup:
            print(f'Cleanup and bootstrap environment {self.name}')
            print('[WARNING] This will terminate all units deployed into environment '
                  f'{self.name} by juju !')
        else:
            print(f'Bootstrap environment {self.name}')

        if not self.auto and not console.confirm('do it now', default=False):
            return None

        if cleanup:
            self.destroy(force=True, remove_default=True)
        if synchronize_tools:
            self.sync_tools(all_tools=True)
        try:
            result = juju_do('bootstrap', self.name)
        except RuntimeError as ex:
            result = None
            if 'already' not in str(ex):
                raise

        if not wait_started:
            return result

        start_time = time.time()
        while True:
            time_zero = time.time()
            try:
                state = self.status(timeout=status_timeout)['machines']['0']['agent-state']
            except (KeyError, TypeError):
                state = UNKNOWN

            delta_time = time.time() - start_time
            timeout_time = timeout - delta_time

            _msg = f' in {timeout_time:.0f} seconds' if timeout_time > 0 else '!'
            print(f'State of juju bootstrap machine is {state}, time-out{_msg}')

            if state in started_states:
                print(f'Environment bootstrapped in approximatively {delta_time:.0f} seconds')
                break
            if state in error_states:
                raise RuntimeError(f'Bootstrap failed with state {state}.')
            if delta_time > timeout:
                raise TimeoutError(f'Bootstrap time-out with state {state}.')
            time.sleep(max(0, polling_delay - (time.time() - time_zero)))
        return result

    def destroy(
        self,
        environments=None,
        force=True,
        remove_default=False,
        remove=False,
        timeout=15
    ):
        # TODO simpler algorithm
        with open(environments or DEFAULT_ENVIRONMENTS_FILE, encoding='utf-8') as f:
            environments_dict = yaml.safe_load(f)

        name = environments_dict['default'] if self.name == 'default' else self.name

        if name not in environments_dict['environments']:
            raise IndexError(f'No environment with name {name}.')

        if not remove_default and name == environments_dict['default']:
            raise RuntimeError(f'Cannot remove default environment {name}.')

        options = ['--force'] if force else []
        result = None

        if self.is_bootstrapped(timeout=timeout):
            result = juju_do('destroy-environment', name, options)

        if remove:
            # Check if environment destroyed otherwise a lot of trouble with $/€ !
            if self.is_bootstrapped(timeout=timeout):
                raise RuntimeError(f'Environment {name} not removed, it is still alive.')

            del environments_dict['environments'][name]
            with open(environments, 'w', encoding='utf-8') as f:
                f.write(yaml.safe_dump(environments_dict))
        return result

    # Services

    def get_service_config(self, service, fail=True):
        return juju_do('get', self.name, options=[service], fail=fail)

    def get_service(self, service, default=None, fail=True, timeout=15):
        if not (status_dict := self.status(fail=fail, timeout=timeout)):
            return default
        try:
            return status_dict['services'][service]  # pylint: disable=unsubscriptable-object
        except KeyError as ex:
            if fail:
                raise RuntimeError(
                    f'Service {service} not found in environment {self.name}.') from ex
        return default

    def expose_service(self, service, fail=True):
        return juju_do('expose', self.name, options=[service], fail=fail)

    def unexpose_service(self, service, fail=True):
        return juju_do('unexpose', self.name, options=[service], fail=fail)

    def destroy_service(self, service, fail=True):
        return juju_do('destroy-service', self.name, options=[service], fail=fail)

    # Units

    def ensure_num_units(
        self,
        charm,
        service,
        constraints=None,
        expose=False,
        local=True,
        num_units=1,
        release=None,
        repository=None,
        required=True,
        terminate=False,
        to=None,
        units_number_to_keep=None,
        timeout=None
    ):  # pylint:disable=invalid-name,too-many-arguments,too-many-branches,too-many-locals
        """
        Ensure `num_units` units of `service` into `environment` by adding new or destroying useless
        units first !

        At the end of this method, the number of running units can be greater as `num_units` because
        this algorithm will not destroy units with number in `units_number_to_keep`.

        Some of the argument are forwarded to underlying methods (add_units, deploy_units,
        destroy_unit or nothing) depending on the required action.

        The scale-down algorithm will sort the units by status to kill the useless units before any
        others!

        * Set local to False to deploy non-local charms.
        * Set num_units to None to ensure the service does not exist.
        * Set required to False to bypass this method in automatic mode.
          WARNING: IT MEANS NO ACTION AT ALL.
        * Set units_number_to_keep to a (list, tuple, ...) with the units you want to protect
          against destruction.

        **Example usage**

        ::

            >> from functools import partial
            >> e = Environment(config=None)
            >> e.bootstrap(wait_started=True)
            >> ensure = partial(e.ensure_num_units, charm='ubuntu', local=False, terminate=True)

        Ensure the charm ubuntu is deployed as the service vanilla with 10 machines, and exposed::

            >> ensure(service='vanilla', expose=True, num_units=5)
            Deploy ubuntu as vanilla (ensure 5 instances)
            do it now ? [y/N]: y
            {'deploy_units': None, 'expose_service': None}

        Ensure the service unwanted does not exist (was not deployed)::

            >> ensure(service='unwanted', num_units=None)
            {}

        Ensure the service vanilla scale-down to 1 unit, keeping unit number 3
        (previously 5 machines)::

            >> ensure(service='vanilla', num_units=1, units_number_to_keep=[3])
            {'destroy_unit': {0: {'agent-state': 'started',
                                  'agent-version': '1.16.6.1',
                                  'machine': '1',
                                  'public-address': '10.0.3.115'},
                              4: {'agent-state': 'pending',
                                  'agent-version': '1.16.6.1',
                                  'machine': '5',
                                  'public-address': '10.0.3.213'},
                              2: {'agent-state': 'started',
                                  'agent-version': '1.16.6.1',
                                  'machine': '3',
                                  'public-address': '10.0.3.23'},
                              1: {'agent-state': 'started',
                                  'agent-version': '1.16.6.1',
                                  'machine': '2',
                                  'public-address': '10.0.3.170'}}}
            >> ensure(service='vanilla', num_units=1, units_number_to_keep=[3])
            {}

        Scale-up the service vanilla again::

            >> ensure(service='vanilla', num_units=2)
            {'add_units': None}

        Scale-down the service vanilla to 0 units but keep it alive::

            >> ensure(service='vanilla', num_units=0)
            {'destroy_unit': {3: {'agent-state': 'started',
                                   'agent-version': '1.16.6.1',
                                   'machine': '4',
                                   'public-address': '10.0.3.50'},
                               5: {'agent-state': 'started',
                                   'agent-version': '1.16.6.1',
                                   'machine': '6',
                                   'public-address': '10.0.3.129'}}}

        Ensure the service another has 0 units but doesn't allow his destruction
        (the service does not exist)::

            >> ensure(service='another', num_units=0)
            {}

        Ensure the service vanilla does not exist at all::

            >> ensure(service='vanilla', num_units=None)
            {'destroy_service': None}

        """
        results = {}
        release = release or self.release
        repository = repository or (self.charms_path if local else None)
        s = '' if num_units is None or num_units < 2 else 's'

        print(f'Deploy {charm} as {service or charm} (ensure {num_units} instance{s})')

        if self.auto and required or console.confirm('do it now', default=False):

            assert num_units is None or num_units >= 0
            units_dict = self.get_units(service, default=None, fail=False, timeout=timeout)
            units_count = None if units_dict is None else len(units_dict)

            if num_units is None and units_count is not None:

                results['destroy_service'] = self.destroy_service(service)

            elif units_count is None:

                if num_units:  # avoid to deploy units if asked number of units is 0 or None
                    results['deploy_units'] = self.deploy_units(
                        charm, service,
                        num_units=num_units,
                        to=to,
                        config=self.config,
                        constraints=constraints,
                        local=local,
                        release=release,
                        repository=repository
                    )

            elif units_count < num_units:
                # avoid to add units if number of units to add is 0
                if num_units := num_units - units_count:
                    results['add_units'] = self.add_units(
                        service or charm,
                        num_units=num_units,
                        to=to)

            elif units_count > num_units:
                num_units = units_count - num_units
                destroyed = {}
                units_number_to_keep = \
                    [int(n) for n in units_number_to_keep] if units_number_to_keep else []

                # TODO implement status comparison for sorting ??
                for status in (ERROR, NOT_STARTED, PENDING, INSTALLED, STARTED):
                    if num_units == 0:
                        break
                    for number, unit_dict in list(units_dict.items()):
                        if num_units == 0:
                            break
                        if number in units_number_to_keep:
                            continue
                        unit_status = unit_dict.get('agent-state', status)
                        if unit_status == status or unit_status not in ALL_STATES:
                            self.destroy_unit(service, number, terminate=False)
                            destroyed[number] = unit_dict
                            del units_dict[number]
                            num_units -= 1

                if terminate:
                    time.sleep(5)
                    for unit_dict in destroyed.values():
                        # FIXME handle fail (multiple units same machine, machine busy, missing ...)
                        self.destroy_machine(unit_dict['machine'])
                results['destroy_unit'] = destroyed
                return results

            if expose:
                results['expose_service'] = self.expose_service(service)

        return results

    def destroy_unit(self, service, number, terminate, delay_terminate=5, fail=True, timeout=None):
        name = f'{service}/{number}'
        unit_dict = self.get_unit(service, number, default=None, fail=fail, timeout=timeout)
        if unit_dict is None:
            return None
        if terminate:
            juju_do('destroy-unit', self.name, options=[name])
            # TODO ideally a flag https://bugs.launchpad.net/juju-core/+bug/1206532
            time.sleep(delay_terminate)
            return self.destroy_machine(unit_dict['machine'])
        return juju_do('destroy-unit', self.name, options=[name])

    def get_unit(self, service, number, default=None, fail=True, timeout=None):
        # TODO maybe none if missing or something else
        name = f'{service}/{number}'
        service_dict = self.get_service(service, default=None, fail=fail, timeout=timeout)
        if service_dict is not None:
            try:
                return service_dict['units'][name]
            except KeyError as ex:
                if fail:
                    raise RuntimeError(
                        f'No unit with name {name} on environment {self.name}.') from ex
        return default

    def get_unit_public_address(self, service, number):
        """
        Return the public address of a unit. Use the most reliable value available
        (dns-name of the machine).
        """
        if self.properties(cached=True)['type'] == 'local':
            return self.get_unit(service, number)['public-address']

        # public-address may report a private address (172.x.x.x) with non-local deployments see
        # OSCIED #132, so we need this workaround (which cannot be used for local deployments).
        machine_number = self.get_unit(service, number)['machine']
        if status_dict := self.status():
            return status_dict['machines'][machine_number]['dns-name']
        raise ValueError(f'Unable to get public address of unit {service}/{number}')

    def wait_unit(
        self,
        service,
        number,
        started_states=STARTED_STATES,
        error_states=ERROR_STATES,
        timeout=180,
        polling_timeout=15,
        polling_delay=30
    ):
        start_time = time.time()
        while True:
            time_zero = time.time()
            try:
                state = self.get_unit(service, number, timeout=polling_timeout)['agent-state']
            except (KeyError, TypeError):
                state = UNKNOWN
            delta_time = time.time() - start_time
            if state in started_states:
                return state
            if state in error_states:
                raise RuntimeError(f'State of unit {service}/{number} is {state}')
            if delta_time > timeout:
                raise TimeoutError(f'State of unit {service}/{number} is {state}')
            time.sleep(max(0, polling_delay - (time.time() - time_zero)))

    def add_units(self, service, num_units=1, to=None):  # pylint:disable=invalid-name
        options = ['--num-units', num_units]
        if to is not None:
            options += ['--to', to]
        options += [service]
        return juju_do('add-unit', self.name, options=options)

    def deploy_units(
        self,
        charm,
        service=None,
        num_units=1,
        to=None,
        config=None,
        constraints=None,
        local=False,
        release=None,
        repository=None
    ):  # pylint:disable=invalid-name,too-many-arguments
        service = service or charm
        if not charm:
            raise ValueError('Charm is required.')
        options = ['--num-units', num_units]
        if to is not None:
            options += ['--to', to]
        if config is not None:
            options += ['--config', config]
        if constraints is not None:
            options += ['--constraints', constraints]
        if release is not None:
            charm = f'{release}/{charm}'
        if local:
            charm = f'local:{charm}'
        if repository is not None:
            options += ['--repository', repository]
        options += [_f for _f in (charm, service) if _f]
        return juju_do('deploy', self.name, options=options)

    def get_units(self, service, default=None, fail=True, timeout=None):
        service_dict = self.get_service(service, default=None, fail=fail, timeout=timeout)
        if service_dict is None:
            return default
        units_dict = service_dict.get('units', {})
        return {int(name.split('/')[1]): info for name, info in units_dict.items()}

    def get_units_count(self, service, default=None, fail=True, timeout=None):
        service_dict = self.get_service(service, default=None, fail=fail, timeout=timeout)
        if service_dict is None:
            return default
        units_dict = service_dict.get('units', {})
        return len(units_dict)

    # Machines

    def cleanup_machines(self, fail=True, timeout=None):
        environment_dict = self.status(fail=fail, timeout=timeout) or {}
        machines = environment_dict.get('machines', {}).keys()
        busy = ['0']  # the machine running the juju daemon !
        for s_dict in environment_dict.get('services', {}).values():
            busy.extend(u_dict.get('machine', None) for u_dict in s_dict.get('units', {}).values())
        idle = [m for m in machines if m not in busy]
        return juju_do('destroy-machine', self.name, options=idle) if idle else None

    def destroy_machine(self, machine):
        return juju_do('destroy-machine', self.name, options=[machine])

    # Relations

    def add_relation(self, service1, service2, relation1=None, relation2=None):
        """Add a relation between 2 services. Knowing that the relation may already exists."""
        print(f'Add relation between {service1} and {service2}')
        if not self.auto and not console.confirm('do it now', default=False):
            return None

        member1 = service1 if relation1 is None else f'{service1}:{relation1}'
        member2 = service2 if relation2 is None else f'{service2}:{relation2}'
        result = None
        try:
            result = juju_do('add-relation', self.name, options=[member1, member2])
        except RuntimeError as ex:
            # TODO get status of service before adding relation may be cleaner.
            if 'already exists' not in str(ex):
                raise
        return result

    def remove_relation(self, service1, service2, relation1=None, relation2=None):
        """Remove a relation between 2 services. Knowing that the relation may not exists."""
        print(f'Remove relation between {service1} and {service2}')
        if not self.auto and not console.confirm('do it now', default=False):
            return None

        member1 = service1 if relation1 is None else f'{service1}:{relation1}'
        member2 = service2 if relation2 is None else f'{service2}:{relation2}'
        try:
            result = juju_do('remove-relation', self.name, options=[member1, member2])
        except RuntimeError as ex:
            # TODO get status of service before removing relation may be cleaner.
            if 'exists' not in str(ex):
                raise
        return result


class DeploymentScenario(object):

    def __init__(self, environments, args=None, namespace=None, **kwargs):
        parser = self.get_parser(**kwargs)
        self.args = parser.parse_args(args=args, namespace=namespace)
        self.environments = environments
        for environment in environments:
            environment.auto = self.args.auto
            environment.charms_path = self.args.charms_path
            environment.release = environment.release or self.args.release
            self.__dict__.update({environment.name: environment})  # A shortcut

    @staticmethod
    def get_parser(
        epilog='',
        charms_path='charms',
        release='raring',
        auto=False
    ):  # pylint:disable=invalid-name
        HELP_A = 'Toggle automatic confirmation of the actions, WARNING: Use it with care.'
        HELP_M = 'Directory (repository) of any local charm.'
        HELP_R = 'Ubuntu serie to deploy by JuJu.'
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            epilog=epilog)
        arg = parser.add_argument
        arg('-a', '--auto', action='store_true', default=auto, help=HELP_A)
        arg('-m', '--charms_path', action=FullPaths, default=charms_path, type=is_dir, help=HELP_M)
        arg('-r', '--release', action='store', default=release, help=HELP_R)
        return parser

    def run(self):
        raise NotImplementedError('Here should be implemented the deployment scenario.')


# Simulation ---------------------------------------------------------------------------------------

# DISCLAIMER: Ideally this module will implement a simulated juju_do to make it possible to use the
# same methods to drive a real or a simulated juju process ... The following code is a partial/light
# implementation of ... Do not use it for your own purposes !!!

class SimulatedUnit(object):
    """A simulated unit with a really simple state machine having a latency to start and stop."""

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
    """Manage a set of simulated units."""

    def __init__(self, start_latency_range, stop_latency_range):
        self.start_latency_range = start_latency_range
        self.stop_latency_range = stop_latency_range  # TODO not yet used by this simulator ...
        self.units = {}
        self.number = 0

    def ensure_num_units(self, num_units=1, units_number_to_keep=None):
        """Ensure `num_units` units by adding new units or destroying useless units first !"""
        assert num_units is None or num_units >= 0

        units_count = len(self.units)

        if num_units is None:
            self.units = {}
            return 'Simulate destruction of service.'

        if units_count == num_units:
            return None

        if units_count < num_units:
            num_units = num_units - units_count
            for _ in range(num_units):
                unit = SimulatedUnit(self.start_latency_range, self.stop_latency_range)
                unit.start()
                self.units[self.number] = unit
                self.number += 1
            return f'Simulate deployment of {num_units} units.'

        # units_count > num_units
        num_units = units_count - num_units
        destroyed = {}
        # Sort units by status to kill the useless units before any others !
        # TODO implement status comparison for sorting ??
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
        """Increment time of 1 tick and remove units that are in STOPPED state."""
        for number, unit in self.units.items():
            unit.tick()
            if unit.state == STOPPED:
                del self.units[number]  # pylint: disable=unnecessary-dict-index-lookup


__all__ = _all.diff(globals())
