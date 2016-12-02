# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, inspect, json, os, pickle, shutil
from codecs import open  # pylint:disable=redefined-builtin

from . import module
from .encoding import string_types, text_type, to_bytes
from .private import ObjectId
from .types import get_slots

_all = module.All(globals())


# Data -> File ---------------------------------------------------------------------------------------------------------

def to_file(path, data=None, pickle_data=None, binary=False, safe=False, backup=False, makedirs=False):
    """
    Write some data to a file, can be safe (tmp file -> rename), may create a backup before any write operation.
    Return the name of the backup path or None.

    **Example usage**

    In-place write operation:

    >>> from pytoolbox.unittest import asserts
    >>> asserts.is_none(to_file('/tmp/to_file', data='bonjour'))
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'bonjour')

    No backup is created if the destination file does not exist:

    >>> from pytoolbox.filesystem import remove
    >>> _ = remove('/tmp/to_file')
    >>> asserts.is_none(to_file('/tmp/to_file', data='bonjour', backup=True))

    In-place write operation after having copied the file into a backup:

    >>> asserts.equal(to_file('/tmp/to_file', data='ça va ?', backup=True), '/tmp/to_file.bkp')
    >>> asserts.equal(open('/tmp/to_file.bkp', 'r', 'utf-8').read(), 'bonjour')
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'ça va ?')

    The most secure, do a backup, write into a temporary file, and rename the temporary file to the destination:

    >>> asserts.equal(to_file('/tmp/to_file', data='oui et toi ?', safe=True, backup=True), '/tmp/to_file.bkp')
    >>> asserts.equal(open('/tmp/to_file.bkp', 'r', 'utf-8').read(), 'ça va ?')
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'oui et toi ?')

    The content of the destination is not broken if the write operation fails:

    >>> asserts.raises(TypeError, to_file, '/tmp/to_file', data=asserts.equal, safe=True)
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'oui et toi ?')
    """
    if makedirs:
        makedirs(os.path.dirname(path))
    if backup:
        backup_path = '{0}.bkp'.format(path)
        try:
            shutil.copy2(path, backup_path)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            backup_path = None
    write_path = '{0}.tmp'.format(path) if safe else path
    with open(write_path, 'wb' if binary else 'w', None if binary else 'utf-8') as f:
        if data is not None:
            f.write(data)
        if pickle_data is not None:
            pickle.dump(pickle_data, f)
    if safe:
        os.rename(write_path, path)
    return backup_path if backup else None


# Object <-> Pickle file -----------------------------------------------------------------------------------------------

class PickleableObject(object):
    """An :class:`object` serializable/deserializable by :mod:`pickle`."""
    @classmethod
    def read(cls, path, store_path=False, create_if_error=False, **kwargs):
        """Return a deserialized instance of a pickleable object loaded from a file."""
        try:
            with open(path, 'rb') as f:
                the_object = pickle.load(f)
        except:
            if not create_if_error:
                raise
            the_object = cls(**kwargs)
            the_object.write(path, store_path=store_path)
        if store_path:
            the_object._pickle_path = path
        return the_object

    def write(self, path=None, store_path=False, safe=False, backup=False, makedirs=False):
        """Serialize `self` to a file, excluding the attribute `_pickle_path`."""
        pickle_path = getattr(self, '_pickle_path', None)
        path = path or pickle_path
        if path is None:
            raise ValueError(to_bytes('A path must be specified'))
        try:
            if pickle_path:
                del self._pickle_path
            to_file(path, pickle_data=self, binary=True, safe=safe, backup=backup, makedirs=makedirs)
        finally:
            if store_path:
                self._pickle_path = path
            elif pickle_path:
                self._pickle_path = pickle_path


# Object <-> JSON string -----------------------------------------------------------------------------------------------

## http://stackoverflow.com/questions/6255387/mongodb-object-serialized-as-json
class SmartJSONEncoderV1(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return text_type(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super(SmartJSONEncoderV1, self).default(obj)


class SmartJSONEncoderV2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return text_type(obj)
        attributes = {}
        for a in inspect.getmembers(obj):
            if inspect.isroutine(a[1]) or inspect.isbuiltin(a[1]) or a[0].startswith('__'):
                continue
            if hasattr(obj.__dict__, a[0]) and not isinstance(a[1], property):
                continue
            attributes[a[0]] = a[1]
        return attributes


def object_to_json(obj, include_properties, **kwargs):
    """
    Serialize an :class:`object` to a JSON string. Use one of the *smart* JSON encoder of this module.

    * Set include_properties to True to also include the properties of `obj`.
    * Set kwargs with any argument of the function :mod:`json`.dumps excepting cls.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class Point(object):
    ...     def __init__(self, x=0, y=0):
    ...         self.x = x
    ...         self.y = y
    ...     @property
    ...     def z(self):
    ...         return self.x + self.y
    >>> p1 = Point(x=16, y=-5)
    >>> asserts.equal(object_to_json(p1, include_properties=False, sort_keys=True), '{"x": 16, "y": -5}')
    >>> asserts.equal(object_to_json(p1, include_properties=True, sort_keys=True), '{"x": 16, "y": -5, "z": 11}')
    >>> print(object_to_json(p1, include_properties=True, sort_keys=True, indent=4)) # doctest: +NORMALIZE_WHITESPACE
    {
        "x": 16,
        "y": -5,
        "z": 11
    }
    """
    return json.dumps(obj, cls=(SmartJSONEncoderV2 if include_properties else SmartJSONEncoderV1), **kwargs)


def json_to_object(cls, json_string, inspect_constructor):
    """
    Deserialize the JSON string `json_string` to an instance of `cls`.

    Set `inspect_constructor` to True to filter input dictionary to avoid sending unexpected keyword arguments to the
    constructor (`__init__`) of `cls`.
    """
    return dict_to_object(cls, json.loads(json_string), inspect_constructor)


def jsonfile_to_object(cls, path_or_file, inspect_constructor):
    """
    Load and deserialize the JSON string stored in a file `path` to an instance of `cls`.

    .. warning::

        Class constructor is responsible of converting attributes to instances of classes with `dict_to_object`.

    **Example usage**

    Define the sample class, instantiate it and serialize it to a file:

    >>> import os
    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class Point(object):
    ...     def __init__(self, name=None, x=0, y=0):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    >>> p1 = Point(name='My point', x=10, y=-5)
    >>> open('test.json', 'w', encoding='utf-8').write(object_to_json(p1, include_properties=False))

    Deserialize the freshly saved file:

    >>> p2 = jsonfile_to_object(Point, 'test.json', inspect_constructor=False)
    >>> asserts.dict_equal(p1.__dict__, p2.__dict__)
    >>> p2 = jsonfile_to_object(Point, open('test.json', 'r', encoding='utf-8'), inspect_constructor=False)
    >>> asserts.dict_equal(p1.__dict__, p2.__dict__)
    >>> os.remove('test.json')
    """
    f = open(path_or_file, 'r', encoding='utf-8') if isinstance(path_or_file, string_types) else path_or_file
    return json_to_object(cls, f.read(), inspect_constructor)


class JsoneableObject(object):
    """
    An :class:`object` serializable/deserializable by :mod:`json`.

    .. warning::

        Class constructor is responsible of converting attributes to instances of classes with `dict_to_object`.

    Convert-back from JSON strings containing extra parameters:

    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class User(object):
    ...     def __init__(self, first_name, last_name):
    ...         self.first_name, self.last_name = first_name, last_name
    ...     @property
    ...     def name(self):
    ...         return '{0} {1}'.format(self.first_name, self.last_name)
    >>>
    >>> class Media(JsoneableObject):
    ...     def __init__(self, author, title):
    ...         self.author = dict_to_object(User, author, True) if isinstance(author, dict) else author
    ...         self.title = title

    Sounds good:

    >>> media = Media(User('Andrés', 'Revuelta'), 'Vacances à Phucket')
    >>> media_json = media.to_json(include_properties=False)
    >>> media_back = Media.from_json(media_json, inspect_constructor=True)
    >>> isinstance(media_back.author, User)
    True
    >>> asserts.dict_equal(media_back.author.__dict__, media.author.__dict__)

    A second example handling extra arguments by using ``**kwargs`` (a.k.a the dirty way):

    >>> class User(object):
    ...     def __init__(self, first_name, last_name, **kwargs):
    ...         self.first_name, self.last_name = first_name, last_name
    ...     @property
    ...     def name(self):
    ...         return '{0} {1}'.format(self.first_name, self.last_name)
    >>>
    >>> class Media(JsoneableObject):
    ...     def __init__(self, author, title, **kwargs):
    ...         self.author = User(**author) if isinstance(author, dict) else author
    ...         self.title = title

    Sounds good:

    >>> media = Media(User('Andrés', 'Revuelta'), 'Vacances à Phucket')
    >>> media_json = media.to_json(include_properties=True)
    >>> media_back = Media.from_json(media_json, inspect_constructor=False)
    >>> isinstance(media_back.author, User)
    True
    >>> asserts.dict_equal(media_back.author.__dict__, media.author.__dict__)
    """
    @classmethod
    def read(cls, path, store_path=False, inspect_constructor=True):
        """Return a deserialized instance of a jsoneable object loaded from a file."""
        with open(path, 'r', 'utf-8') as f:
            the_object = dict_to_object(cls, json.loads(f.read()), inspect_constructor)
            if store_path:
                the_object._json_path = path
            return the_object

    def write(self, path=None, include_properties=False, safe=False, backup=False, makedirs=False, **kwargs):
        """Serialize `self` to a file, excluding the attribute `_json_path`."""
        if path is None and hasattr(self, '_json_path'):
            path = self._json_path
            try:
                del self._json_path
                to_file(path, data=object_to_json(self, include_properties, **kwargs),
                        binary=False, safe=safe, backup=backup, makedirs=makedirs)
            finally:
                self._json_path = path
        elif path is not None:
            to_file(path, data=object_to_json(self, include_properties, **kwargs),
                    binary=False, safe=safe, backup=backup, makedirs=makedirs)
        else:
            raise ValueError('A path must be specified')

    def to_json(self, include_properties, **kwargs):
        """Serialize this instance to a JSON string."""
        return object_to_json(self, include_properties, **kwargs)

    @classmethod
    def from_json(cls, json_string, inspect_constructor):
        """Deserialize a JSON string to an instance of `JsoneableObject`."""
        return dict_to_object(cls, json.loads(json_string), inspect_constructor)


# Object <-> Dictionary ------------------------------------------------------------------------------------------------

def object_to_dict(obj, include_properties):
    """
    Convert an :class:`object` to a python dictionary.

    .. warning::

        Current implementation serialize `obj` to a JSON string and then deserialize this JSON string to an instance
        of :class:`dict`.

    **Example usage**

    Define the sample class and convert some instances to a dictionary:

    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class Point(object):
    ...     def __init__(self, name, x, y, p):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    ...         self.p = p
    ...     @property
    ...     def z(self):
    ...         return self.x - self.y
    >>>
    >>> p1_dict = {'y': 2, 'x': 5, 'name': 'p1', 'p': {'y': 4, 'x': 3, 'name': 'p2', 'p': None}}
    >>> asserts.dict_equal(
    ...     object_to_dict(Point('p1', 5, 2, Point('p2', 3, 4, None)), include_properties=False),
    ...     p1_dict
    ... )
    >>>
    >>> p2_dict = {'y': 4, 'p': None, 'z': -1, 'name': 'p2', 'x': 3}
    >>> p1_dict = {'y': 2, 'p': p2_dict, 'z': 3, 'name': 'p1', 'x': 5}
    >>> asserts.dict_equal(
    ...     object_to_dict(Point('p1', 5, 2, Point('p2', 3, 4, None)), include_properties=True),
    ...     p1_dict
    ... )
    >>>
    >>> p1, p2 = Point('p1', 5, 2, None), Point('p2', 3, 4, None)
    >>> p1.p, p2.p = p2, p1
    >>> print(object_to_dict(p1, True))
    Traceback (most recent call last):
        ...
    ValueError: Circular reference detected
    """
    return json_to_object(dict, object_to_json(obj, include_properties), inspect_constructor=False)


def object_to_dictV2(obj, remove_underscore):
    if isinstance(obj, dict):
        something_dict = {}
        for key, value in obj.iteritems():
            if remove_underscore and key[0] == '_':
                key = key[1:]
            something_dict[key] = object_to_dictV2(value, remove_underscore)
        return something_dict
    elif hasattr(obj, '__iter__'):
        return [object_to_dictV2(value, remove_underscore) for value in obj]
    elif hasattr(obj, '__dict__'):
        something_dict = {}
        for key, value in obj.__dict__.iteritems():
            if remove_underscore and key[0] == '_':
                key = key[1:]
            something_dict[key] = object_to_dictV2(value, remove_underscore)
        return something_dict
    return obj


def dict_to_object(cls, the_dict, inspect_constructor):
    """
    Convert a python dictionary to an instance of a class.

    Set `inspect_constructor` to True to filter input dictionary to avoid sending unexpected keyword arguments to the
    constructor (`__init__`) of `cls`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class User(object):
    ...     def __init__(self, first_name, last_name='Fischer'):
    ...         self.first_name, self.last_name = first_name, last_name
    ...     @property
    ...     def name(self):
    ...        return '{0} {1}'.format(self.first_name, self.last_name)
    ...
    >>> user_dict = {'first_name': 'Victor', 'last_name': 'Fischer', 'unexpected': 10}
    >>> dict_to_object(User, user_dict, inspect_constructor=False)
    Traceback (most recent call last):
        ...
    TypeError: __init__() got an unexpected keyword argument 'unexpected'
    >>> asserts.dict_equal(dict_to_object(User, user_dict, inspect_constructor=True).__dict__, {
    ...     'first_name': 'Victor', 'last_name': 'Fischer'
    ... })
    """
    if inspect_constructor:
        the_dict = {arg: the_dict.get(arg, None) for arg in inspect.getargspec(cls.__init__)[0] if arg != 'self'}
    return cls(**the_dict)


class SlotsToDictMixin(object):

    extra_slots = None

    def to_dict(self, extra_slots=True):
        self_dict = {}
        slots = set(s for s in get_slots(self) if s[0] != '_')
        if extra_slots:
            slots.update(self.__class__.extra_slots or [])
        for attribute in slots:
            value = getattr(self, attribute)
            if value is not None:
                self_dict[attribute] = value
        return self_dict

__all__ = _all.diff(globals())
