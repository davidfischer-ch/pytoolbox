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

import errno, grp, hashlib, inspect, json, logging, logging.handlers, pickle, pwd, os, re, shlex, \
    subprocess, sys, uuid
from bson.objectid import ObjectId
from datetime import datetime
from mongoengine import Document
from six import PY3, string_types

if PY3:
    from ipaddress import ip_address
    from unittest.mock import Mock
else:
    from ipaddr import IPAddress as ip_address
    from mock import Mock


# CRYPTO -------------------------------------------------------------------------------------------

def githash(data):
    u"""
    Return the blob of some data.

    This is how Git calculates the SHA1 for a file (or, in Git terms, a "blob")::

        sha1("blob " + filesize + "\0" + data)

    .. seealso::

        http://stackoverflow.com/questions/552659/assigning-git-sha1s-without-git

    **Example usage**

    >>> print(githash(''))
    e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
    >>> print(githash('give me some hash please'))
    abdd1818289725c072eff0f5ce185457679650be
    """
    s = hashlib.sha1()
    s.update("blob %u\0" % len(data))
    s.update(data)
    return s.hexdigest()


# DATETIME -----------------------------------------------------------------------------------------

def datetime_now(offset=None, format='%Y-%m-%d %H:%M:%S', append_utc=False):
    u"""
    Return the current UTC date and time.
    If format is not None, the date will be returned in a formatted string.

    :param offset: Offset added to datetime.utcnow() if set
    :type offset: datetime.timedelta
    :param format: Output date string formatting
    :type format: str
    :param append_utc: Append ' UTC' to date string
    :type append_utc: bool

    **Example usage**:

    >>> from datetime import timedelta
    >>> now = datetime_now(format=None)
    >>> future = datetime_now(offset=timedelta(hours=2, minutes=10), format=None)
    >>> print(future - now)  # doctest: +ELLIPSIS
    2:10:00...
    >>> assert(isinstance(datetime_now(), string_types))
    >>> assert(' UTC' not in datetime_now(append_utc=False))
    >>> assert(' UTC' in datetime_now(append_utc=True))
    """
    now = datetime.utcnow()
    if offset:
        now += offset
    return (now.strftime(format) + (' UTC' if append_utc else '')) if format else now


def datetime2str(date_time, format='%Y-%m-%d %H:%M:%S', append_utc=False):
    return date_time.strftime(format) + (' UTC' if append_utc else '')


def duration2secs(duration):
    u"""
    Returns the duration converted in seconds.

    **Example usage**:

    >>> duration2secs('00:10:00')
    600.0
    >>> duration2secs('01:54:17')
    6857.0
    >>> print(round(duration2secs('16.40'), 3))
    16.4
    """
    try:
        hours, minutes, seconds = duration.split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return float(duration)


def str2datetime(date, format='%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(date, format)


# EXCEPTION ----------------------------------------------------------------------------------------

class ForbiddenError(Exception):
    u"""
    A forbidden error.
    """
    pass


# FILESYSTEM ---------------------------------------------------------------------------------------

def first_that_exist(*paths):
    u"""
    Returns the first file/directory that exist.

    **Example usage**:

    >>> print(first_that_exist('', '/etc', '.'))
    /etc
    >>> print(first_that_exist('does_not_exist.com', '', '..'))
    ..
    """
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def get_size(path):
    u"""
    Returns the size of a file or directory.
    If given ``path`` is a directory (or symlink to a directory), then returned value is computed by
    summing the size of all files, and that recursively.
    """
    if os.path.isfile(path):
        return os.stat(path).st_size
    size = 0
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            size += os.stat(os.path.join(root, filename)).st_size
    return size


def try_makedirs(path):
    u"""
    Tries to recursive make directories (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if directory found and re-raise any other type of
    exception.

    **Example usage**:

    >>> import shutil
    >>> try_makedirs('/etc')
    False
    >>> try_makedirs('/tmp/salut/mec')
    True
    >>> shutil.rmtree('/tmp/salut/mec')
    """
    try:
        os.makedirs(path)
        return True
    except OSError as e:
        # File exists
        if e.errno == errno.EEXIST:
            return False
        raise  # Re-raise exception if a different error occurred


def try_remove(path):
    u"""
    Tries to remove a file/directory (which may not exists) without throwing an exception.
    Returns True if operation is successful, False if file/directory not found and re-raise any
    other type of exception.

    **Example usage**:

    >>> open('try_remove.example', 'w').write('salut')
    >>> try_remove('try_remove.example')
    True
    >>> try_remove('try_remove.example')
    False
    """
    try:
        os.remove(path)
        return True
    except OSError as e:
        # File does not exist
        if e.errno == errno.ENOENT:
            return False
        raise  # Re-raise exception if a different error occurred


def try_symlink(source, link_name):
    u"""
    Tries to symlink a file/directory (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if found & target is ``link_name`` and re-raise
    any other type of exception.

    **Example usage**:

    >>> a = try_remove('/tmp/does_not_exist')
    >>> a = try_remove('/tmp/does_not_exist_2')
    >>> a = try_remove('/tmp/link_etc')
    >>> a = try_remove(os.path.expanduser('~/broken_link'))

    Creating a symlink named /etc does fail - /etc already exist but does not refer to /home:

    >>> import shutil
    >>> try_symlink('/home', '/etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    Symlinking /etc to itself only returns that nothing changed:

    >>> try_symlink('/etc', '/etc')
    False

    Creating a symlink to an existing file has the following behaviour:

    >>> try_symlink('/etc', '/tmp/link_etc')
    True
    >>> try_symlink('/etc', '/tmp/link_etc')
    False
    >>> try_symlink('/etc/does_not_exist', '/tmp/link_etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists
    >>> try_symlink('/home', '/tmp/link_etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    Creating a symlink to a non existing has the following behaviour:

    >>> try_symlink('~/does_not_exist', '~/broken_link')
    True
    >>> try_symlink('~/does_not_exist', '~/broken_link')
    False
    >>> try_symlink('~/does_not_exist_2', '~/broken_link')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists
    >>> try_symlink('/home', '~/broken_link')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    >>> os.remove('/tmp/link_etc')
    >>> os.remove(os.path.expanduser('~/broken_link'))
    """
    try:
        source = os.path.expanduser(source)
        link_name = os.path.expanduser(link_name)
        os.symlink(source, link_name)
        return True
    except OSError as e1:
        # File exists
        if e1.errno == errno.EEXIST:
            try:
                if os.path.samefile(source, link_name):
                    return False
            except OSError as e2:
                # Handle broken symlink that point to same target
                target = os.path.expanduser(os.readlink(link_name))
                if e2.errno == errno.ENOENT:
                    if target == source:
                        return False
                    else:
                        raise OSError(errno.EEXIST, 'File exists')
                raise
        raise  # Re-raise exception if a different error occurred


def chown(path, user, group, recursive=False):
    u"""
    Change owner/group of a path, can be recursive. User and group can be a name or an id.
    """
    uid = pwd.getpwnam(user).pw_uid if isinstance(user, string_types) else user
    gid = grp.getgrnam(group).gr_gid if isinstance(group, string_types) else group
    if recursive:
        for root, dirnames, filenames in os.walk(path):
            os.chown(root, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(root, filename), uid, gid)
    else:
        os.chown(path, uid, gid)


# JSON ---------------------------------------------------------------------------------------------

## http://stackoverflow.com/questions/6255387/mongodb-object-serialized-as-json
class SmartJSONEncoderV1(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Document):
            return obj.to_mongo().to_dict()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super(SmartJSONEncoderV1, self).default(obj)


class SmartJSONEncoderV2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Document):
            # FIXME a way to return MongoEngine Document user's properties too (@property)
            return obj.to_mongo().to_dict()
        attributes = {}
        for a in inspect.getmembers(obj):
            if inspect.isroutine(a[1]) or inspect.isbuiltin(a[1]) or a[0].startswith('__'):
                continue
            attributes[a[0]] = a[1]
        return attributes


def json2object(json_string, something=None):
    u"""
    Deserialize the JSON string ``json_string`` to attributes of ``something``.

    .. warning:: Current implementation does not handle recursion.

    **Example usage**:

    Define the sample class and deserialize a JSON string to attributes of a new instance:

    >>> class Point(object):
    ...     def __init__(self, name=None, x=0, y=0):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    >>> p = Point()
    >>> assert(p.__dict__ == {'name': None, 'x':0, 'y': 0})
    >>> json2object('{"x":10,"y":20,"name":"My position"}', p)
    >>> assert(p.__dict__ == {'name': 'My position', 'x': 10, 'y': 20})
    >>> json2object('{"y":25}', p)
    >>> assert(p.__dict__ == {'name': 'My position', 'x': 10, 'y': 25})
    >>> json2object('{"z":3}', p)
    >>> assert(p.__dict__ == {'name': 'My position', 'x': 10, 'y': 25})

    Deserialize a JSON string to a dictionary:

    >>> expected = {'firstname': 'Tabby', 'lastname': 'Fischer'}
    >>> assert(json2object('{"firstname":"Tabby","lastname":"Fischer"}') == expected)
    """
    if something is None:
        return json.loads(json_string)
    for key, value in json.loads(json_string).items():
        if hasattr(something, key):
            setattr(something, key, value)
    #something.__dict__.update(loads(json)) <-- old implementation


def jsonfile2object(filename_or_file, something=None):
    u"""
    Loads and deserialize the JSON string stored in a file ``filename``  to attributes of
    ``something``.

    .. warning:: Current implementation does not handle recursion.

    **Example usage**:

    Define the sample class, instantiate it and serialize it to a file:

    >>> class Point(object):
    ...     def __init__(self, name=None, x=0, y=0):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    >>> p1 = Point(name='My point', x=10, y=-5)
    >>> open('test.json', 'w').write(object2json(p1, include_properties=False))

    Deserialize the freshly saved file to the attributes of another instance:

    >>> p2 = Point()
    >>> jsonfile2object('test.json', p2)
    >>> assert(p1.__dict__ == p2.__dict__)
    >>> jsonfile2object(open('test.json'), p2)
    >>> assert(p1.__dict__ == p2.__dict__)

    Deserialize the freshly saved file to a dictionary:

    >>> assert(jsonfile2object('test.json') == p1.__dict__)
    >>> assert(jsonfile2object(open('test.json')) == p1.__dict__)
    >>> os.remove('test.json')
    """
    if something is None:
        try:
            return json.load(open(filename_or_file))
        except TypeError:
            return json.load(filename_or_file)
    else:
        if isinstance(filename_or_file, string_types):
            json2object(open(filename_or_file).read(), something)
        else:
            json2object(filename_or_file.read(), something)


def object2json(something, include_properties):
    if not include_properties:
        return json.dumps(something, cls=SmartJSONEncoderV1)
    else:
        return json.dumps(something, cls=SmartJSONEncoderV2)


def sorted_dict(dictionary):
    return sorted(dictionary.items(), key=lambda x: x[0])


# LOGGING ------------------------------------------------------------------------------------------

def setup_logging(name='', reset=False, filename=None, console=False, level=logging.DEBUG,
                  fmt='%(asctime)s %(levelname)-8s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S'):
    u"""
    Setup logging (TODO).

    :param name: TODO
    :type name: str
    :param reset: Unregister all previously registered handlers ?
    :type reset: bool
    :param filename: TODO
    :type name: str
    :param console: Toggle console output (stdout)
    :type console: bool
    :param level: TODO
    :type level: int
    :param fmt: TODO
    :type fmt: str
    :param datefmt: TODO
    :type datefmt: str

    **Example usage**

    Setup a console output for logger with name *test*:

    >>> setup_logging(name='test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log = logging.getLogger('test')
    >>> log.info('this is my info')
    this is my info
    >>> log.debug('this is my debug')
    this is my debug
    >>> log.setLevel(logging.INFO)
    >>> log.debug('this is my hidden debug')
    >>> log.handlers = []  # Remove handlers manually: pas de bras, pas de chocolat !
    >>> log.debug('no handlers, no messages ;-)')

    Show how to reset handlers of the logger to avoid duplicated messages (e.g. in doctest):

    >>> setup_logging(name='test', console=True, fmt=None, datefmt=None)
    >>> setup_logging(name='test', console=True, fmt=None, datefmt=None)
    >>> log.info('double message')
    double message
    double message
    >>> setup_logging(name='test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('single message')
    single message
    """
    if reset:
        logging.getLogger(name).handlers = []
    if filename:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.FileHandler(filename)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
    if console:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)

UUID_ZERO = str(uuid.UUID('{00000000-0000-0000-0000-000000000000}'))


# RSYNC --------------------------------------------------------------------------------------------

def rsync(source, destination, makedest=False, archive=True, delete=False, exclude_vcs=False,
          progress=False, recursive=False, simulate=False, excludes=None, includes=None, fail=True,
          log=None):
    if makedest and not os.path.exists(destination):
        os.makedirs(destination)
    source = os.path.normpath(source) + (os.sep if os.path.isdir(source) else '')
    destination = os.path.normpath(destination) + (os.sep if os.path.isdir(destination) else '')
    command = ['rsync',
               '-a' if archive else None,
               '--delete' if delete else None,
               '--progress' if progress else None,
               '-r' if recursive else None,
               '--dry-run' if simulate else None]
    if excludes is not None:
        command.extend(['--exclude=%s' % e for e in excludes])
    if includes is not None:
        command.extend(['--include=%s' % i for i in includes])
    if exclude_vcs:
        command.extend(['--exclude=.svn', '--exclude=.git'])
    command.extend([source, destination])
    return cmd(filter(None, command), fail=fail, log=log)


# SCREEN -------------------------------------------------------------------------------------------

def screen_kill(name=None, fail=True, log=None):
    for name in screen_list(name=name, log=log):
        cmd(['screen', '-S', name, '-X', 'quit'], fail=fail, log=log)


def screen_launch(name, command, fail=True, log=None):
    return cmd(['screen', '-dmS', name] + (command if isinstance(command, list) else [command]),
               fail=fail, log=log)


def screen_list(name=None, log=None):
    u"""
    Returns a list containing all instances of screen. Can be filtered by ``name``.

    **Example usage**:

    >>> def log_it(line):
    ...     print(line)

    Launch some screens:

    >>> print(screen_launch('my_1st_screen', 'top', fail=False))['stderr']
    <BLANKLINE>
    >>> print(screen_launch('my_2nd_screen', 'top', fail=False))['stderr']
    <BLANKLINE>
    >>> print(screen_launch('my_2nd_screen', 'top', fail=False))['stderr']
    <BLANKLINE>

    List the launched screen sessions:

    >>> print(screen_list(name=r'my_1st_screen'))  # doctest: +ELLIPSIS
    ['....my_1st_screen']
    >>> print(screen_list(name=r'my_2nd_screen'))  # doctest: +ELLIPSIS
    ['....my_2nd_screen', '....my_2nd_screen']

    Cleanup:

    >>> screen_kill(name='my_1st_screen', log=log_it)  # doctest: +ELLIPSIS
    Execute ['screen', '-ls', 'my_1st_screen']
    Execute ['screen', '-S', '....my_1st_screen', '-X', 'quit']
    >>> screen_kill(name='my_2nd_screen', log=log_it)  # doctest: +ELLIPSIS
    Execute ['screen', '-ls', 'my_2nd_screen']
    Execute ['screen', '-S', '....my_2nd_screen', '-X', 'quit']
    Execute ['screen', '-S', '....my_2nd_screen', '-X', 'quit']
    """
    return re.findall(r'\s+(\d+.\S+)\s+\(.*\).*',
                      cmd(['screen', '-ls', name], fail=False, log=log)['stdout'])


# SERIALIZATION/DESERIALIZATION --------------------------------------------------------------------

class PickleableObject(object):
    u"""
    An :class:`object` serializable/deserializable by :mod:`pickle`.
    """
    @staticmethod
    def read(filename, store_filename=False):
        u"""
        Returns a deserialized instance of a pickleable object loaded from a file.
        """
        the_object = pickle.load(file(filename))
        if store_filename:
            the_object._pickle_filename = filename
        return the_object

    def write(self, filename=None):
        u"""
        Serialize ``self`` to a file, excluding the attribute ``_pickle_filename``.
        """
        if filename is None and hasattr(self, '_pickle_filename'):
            filename = self._pickle_filename
            delattr(self, '_pickle_filename')
            pickle.dump(self, file(filename, 'w'))
            self._pickle_filename = filename
        elif filename is not None:
            pickle.dump(self, file(filename, 'w'))
        else:
            raise ValueError('A filename must be specified')


# SUBPROCESS ---------------------------------------------------------------------------------------

def cmd(command, input=None, cli_input=None, shell=False, fail=True, log=None):
    u"""
    Calls the ``command`` and returns a dictionary with stdout, stderr, and the returncode.

    * Pipe some content to the command with ``input``.
    * Answer to interactive CLI questions with ``cli_input``.
    * Set ``fail`` to False to avoid the exception ``subprocess.CalledProcessError``.
    * Set ``shell`` to True to enable shell expension (dangerous ! See :mod:`subprocess`).
    * Set ``log`` to a method to log / print details about what is executed / any failure.

    **Example usage**:

    >>> import six
    >>> def print_it(str):
    ...     print('[DEBUG] %s' % str)
    >>> cmd(['echo', 'it seem to work'], log=print_it)  # doctest: +ELLIPSIS
    [DEBUG] Execute ['echo', 'it seem to work']
    ...
    >>> assert(cmd('cat missing_file', fail=False, log=print_it)['returncode'] != 0)
    [DEBUG] Execute cat missing_file
    >>> assert(cmd('my.funny.missing.script.sh', fail=False)['stderr'] != '')
    >>> result = cmd('cat %s' % __file__)
    >>> print(result['stdout'].splitlines()[0])
    #!/usr/bin/env python
    """
    if log is not None:
        log('Execute %s%s%s' % ('' if input is None else 'echo %s | ' % repr(input), command,
            '' if cli_input is None else ' < %s' % repr(cli_input)))
    args = filter(None, command if isinstance(command, list) else shlex.split(command))
    try:
        process = subprocess.Popen(args, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError as e:
        if fail:
            raise
        return {'stdout': '', 'stderr': e, 'returncode': 2}
    if cli_input is not None:
        process.stdin.write(cli_input)
    stdout, stderr = process.communicate(input=input)
    result = {'stdout': stdout, 'stderr': stderr, 'returncode': process.returncode}
    if fail and process.returncode != 0:
        if log is not None:
            log(result)
        raise subprocess.CalledProcessError(process.returncode, command, stderr)
    return result


# TEST / MOCK --------------------------------------------------------------------------------------

MOCK_SIDE_EFFECT_RETURNS = [Exception('you must set MOCK_SIDE_EFFECT_RETURNS'), {'title': 'second'}]


def mock_cmd(stdout='', stderr='', returncode=0):
    return Mock(return_value={'stdout': stdout, 'stderr': stderr, 'returncode': returncode})


def mock_side_effect(*args, **kwargs):
    u"""
    Pop and return values from MOCK_SIDE_EFFECT_RETURNS.

    from your own module, you need to set MOCK_SIDE_EFFECT_RETURNS before using this method::

        import pyutils.pyutils
        pyutils.pyutils.MOCK_SIDE_EFFECT_RETURNS = ['first', {'title': 'second'}, EOFError('last')]

    **example usage**:

    Set content (only required for this doctest, see previous remark):

    Pops return values with ``mock_side_effect``:

    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    Exception: you must set MOCK_SIDE_EFFECT_RETURNS
    >>> print(mock_side_effect())
    {'title': 'second'}
    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    IndexError: pop from empty list
    """
    global MOCK_SIDE_EFFECT_RETURNS
    result = MOCK_SIDE_EFFECT_RETURNS.pop(0)
    if isinstance(result, Exception):
        raise result
    return result


# VALIDATION ---------------------------------------------------------------------------------------

def valid_filename(filename):
    u"""
    Returns True if ``filename`` is a valid filename.

    **Example usage**:

    >>> valid_filename('my_file_without_extension')
    False
    >>> valid_filename('my_file_with_extension.mp4')
    True
    """
    try:
        return True if re.match(r'[^\.]+\.[^\.]+', filename) else False
    except:
        return False


def valid_ip(ip):
    u"""
    Returns True if ``ip`` is a valid IP address.

    **Example usage**:

    >>> valid_ip('123.0.0.')
    False
    >>> valid_ip('239.232.0.222')
    True
    """
    try:
        ip_address(ip)
        return True
    except:
        return False


def valid_mail(mail):
    u"""
    Returns True if ``mail`` is a valid e-mail address.

    **Example usage**:

    >>> valid_mail('Tabby@croquetes')
    False
    >>> valid_mail('Tabby@bernex.ch')
    True
    """
    try:
        return True if re.match(r'[^@]+@[^@]+\.[^@]+', mail) else False
    except:
        return False


def valid_port(port):
    u"""
    Returns True if ``port`` is a valid port.

    **Example usage**:

    >>> assert(not valid_port(-1))
    >>> assert(not valid_port('something not a port'))
    >>> assert(valid_port('80'))
    >>> valid_port(65535)
    True
    """
    try:
        return 0 <= int(port) < 2**16
    except:
        return False


def valid_secret(secret, none_allowed):
    u"""
    Returns True if ``secret`` is a valid secret.

    A valid secret contains at least 8 alpha-numeric characters.

    **Example usage**:

    >>> valid_secret('1234', False)
    False
    >>> valid_secret(None, True)
    True
    >>> valid_secret(None, False)
    False
    >>> valid_secret('my_password', False)
    True
    """
    if secret is None and none_allowed:
        return True
    try:
        return True if re.match(r'[A-Za-z0-9@#$%^&+=-_]{8,}', secret) else False
    except:
        return False


def valid_uuid(id, none_allowed):
    u"""
    Returns True if ``id`` is a valid UUID.

    **Example usage**:

    >>> valid_uuid('gaga-gogo-gaga-gogo', False)
    False
    >>> valid_uuid(None, True)
    True
    >>> valid_uuid(uuid.uuid4(), False)
    True
    """
    if id is None and none_allowed:
        return True
    try:
        uuid.UUID('{' + str(id) + '}')
    except ValueError:
        return False
    return True


# Main ---------------------------------------------------------------------------------------------

if __name__ == '__main__':

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    HELP_TRAVIS = 'Disable screen doctest for Travis CI'

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog='''Generate a unique identifier (UUID) and save it into pictures's tags (EXIFv2).''')
    parser.add_argument('-t', '--travis', help=HELP_TRAVIS, action='store_true')
    args = parser.parse_args()

    if args.travis:
        screen_kill.__doc__ = screen_launch.__doc__ = screen_list.__doc__ = ''

    print('Test pyutils with doctest')
    import doctest
    assert(doctest.testmod(verbose=True).failed == 0)

    print('Test PickleableObject outside of docstring')
    class MyPoint(PickleableObject):
        def __init__(self, name=None, x=0, y=0):
            self.name = name
            self.x = x
            self.y = y
    p1 = MyPoint(name='My point', x=6, y=-3)
    p1.write('test.pkl')
    p2 = MyPoint.read('test.pkl', store_filename=True)
    assert(p2.__dict__ == {'y': -3, 'x': 6, '_pickle_filename': 'test.pkl', 'name': 'My point'})
    p2.write()
    delattr(p2, '_pickle_filename')
    try:
        p2.write()
        raise ValueError('Must raise an AttributeError')
    except ValueError:
        pass
    finally:
        os.remove('test.pkl')
    print('OK')
