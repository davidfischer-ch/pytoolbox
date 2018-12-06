# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, inspect, json, os, pickle, shutil
from codecs import open  # pylint:disable=redefined-builtin

from . import filesystem, module
from .encoding import string_types, text_type, to_bytes
from .private import ObjectId
from .types import get_slots, isiterable

_all = module.All(globals())


# Data -> File -------------------------------------------------------------------------------------

def to_file(path, data=None, pickle_data=None, binary=False, safe=False, backup=False,
            makedirs=False):
    """
    Write some data to a file, can be safe (tmp file -> rename), may create a backup before any
    write operation. Return the name of the backup path or None.

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

    The most secure, do a backup, write into a temporary file, and rename the temporary file to the
    destination:

    >>> asserts.equal(
    ...     to_file('/tmp/to_file', data='oui et toi ?', safe=True, backup=True),
    ...     '/tmp/to_file.bkp')
    >>> asserts.equal(open('/tmp/to_file.bkp', 'r', 'utf-8').read(), 'ça va ?')
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'oui et toi ?')

    The content of the destination is not broken if the write operation fails:

    >>> asserts.raises(TypeError, to_file, '/tmp/to_file', data=asserts.equal, safe=True)
    >>> asserts.equal(open('/tmp/to_file', 'r', 'utf-8').read(), 'oui et toi ?')
    """
    if makedirs:
        filesystem.makedirs(os.path.dirname(path))
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


# Object <-> Pickle file ---------------------------------------------------------------------------

class PickleableObject(object):
    """An :class:`object` serializable/deserializable by :mod:`pickle`."""
    @classmethod
    def read(cls, path, store_path=False, create_if_error=False, **kwargs):
        """Return a deserialized instance of a pickleable object loaded from a file."""
        try:
            with open(path, 'rb') as f:
                the_object = pickle.load(f)
        except Exception:
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
            to_file(
                path, pickle_data=self, binary=True, safe=safe, backup=backup, makedirs=makedirs)
        finally:
            if store_path:
                self._pickle_path = path
            elif pickle_path:
                self._pickle_path = pickle_path


# Object <-> JSON string ---------------------------------------------------------------------------

# http://stackoverflow.com/questions/6255387/mongodb-object-serialized-as-json
class SmartJSONEncoderV1(json.JSONEncoder):
    def default(self, obj):
        if ObjectId is not None and isinstance(obj, ObjectId):
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
    Serialize an :class:`object` to a JSON string.
    Use one of the *smart* JSON encoder of this module.

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
    return json.dumps(
        obj, cls=(SmartJSONEncoderV2 if include_properties else SmartJSONEncoderV1), **kwargs)


def json_to_object(cls, json_string, inspect_constructor):
    """
    Deserialize the JSON string `json_string` to an instance of `cls`.

    Set `inspect_constructor` to True to filter input dictionary to avoid sending unexpected keyword
    arguments to the constructor (`__init__`) of `cls`.
    """
    return dict_to_object(cls, json.loads(json_string), inspect_constructor)


def jsonfile_to_object(cls, path_or_file, inspect_constructor):
    """
    Load and deserialize the JSON string stored in a file `path` to an instance of `cls`.

    .. warning::

        Class constructor is responsible of converting attributes to instances of classes with
        `dict_to_object`.

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
    >>> p2 = jsonfile_to_object(
    ...     Point, open('test.json', 'r', encoding='utf-8'), inspect_constructor=False)
    >>> asserts.dict_equal(p1.__dict__, p2.__dict__)
    >>> os.remove('test.json')
    """
    if isinstance(path_or_file, string_types):
        f = open(path_or_file, 'r', encoding='utf-8')
    else:
        f = path_or_file
    return json_to_object(cls, f.read(), inspect_constructor)


class JsoneableObject(object):
    """
    An :class:`object` serializable/deserializable by :mod:`json`.

    .. warning::

        Class constructor is responsible of converting attributes to instances of classes with
        `dict_to_object`.

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
    ...         self.author = dict_to_object(
    ...             User, author, True) if isinstance(author, dict) else author
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

    def write(self, path=None, include_properties=False, safe=False, backup=False, makedirs=False,
              **kwargs):
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


# Object <-> Dictionary ----------------------------------------------------------------------------

def object_to_dict(
    obj, schema, depth=0,
    callback=lambda o, s, d: (o, s),
    iterable_callback=lambda o, s, d: list
):
    """
    Convert an :class:`object` to nested python lists and dictionaries to follow given schema.

    * Schema callback makes it possible to dynamically tweak obj and schema!
    * Iterable callback makes it possible to dynamically tweak iterable objects container type!

    **Example usage**

    Define the sample class and convert some instances to a nested structure:

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

    Simple example:

    >>> SCHEMA = {
    ...     'name': 'name',
    ...     'x': 'x',
    ...     'zed': 'z',
    ...     'p': [{
    ...         'name': 'name',
    ...         'stuff': lambda p: 42,
    ...         'p': {
    ...             'name': 'name'
    ...         }
    ...     }]
    ... }
    >>> asserts.dict_equal(
    ...     object_to_dict(
    ...         Point('p1', 5, 2, [
    ...             Point('p2', 3, 4, None),
    ...             Point('p3', 7, 0, Point('p4', 0, 0, None))
    ...         ]), SCHEMA),
    ...     {
    ...         'name': 'p1', 'x': 5, 'zed': 3, 'p': [
    ...             {'name': 'p2', 'stuff': 42, 'p': None},
    ...             {'name': 'p3', 'stuff': 42, 'p': {'name': 'p4'}}
    ...         ]
    ...     }
    ... )

    This serializer can optionally adapt container type and do a lot more:

    >>> SCHEMA = {
    ...     'name': 'name',
    ...     'x': 'x',
    ...     'zed': 'z',
    ...     'p': [{
    ...         '_container': tuple,
    ...         'name': 'name',
    ...         'stuff': lambda p: 42,
    ...         'p': [{
    ...             '_container': tuple,
    ...             'name': 'name'
    ...         }]
    ...     }]
    ... }
    ...
    >>> def use_container_defined_in_schema(obj, schema, depth):
    ...    return schema.get('_container', list)
    ...
    >>> def ignore_private_schema_keys(obj, schema, depth):
    ...     return obj, {k: v for k, v in schema.items() if k[0] != '_'}
    ...
    >>> asserts.dict_equal(
    ...     object_to_dict(
    ...         Point('p1', 5, 2, {
    ...             Point('p2', 3, 4, []),
    ...             Point('p3', 7, 0, [
    ...                 Point('p4', 0, 0, None),
    ...                 Point('p5', 0, 0, None)
    ...             ])
    ...         }),
    ...         schema=SCHEMA,
    ...         callback=ignore_private_schema_keys,
    ...         iterable_callback=use_container_defined_in_schema),
    ...     {
    ...         'name': 'p1', 'x': 5, 'zed': 3, 'p': (
    ...             {'name': 'p2', 'stuff': 42, 'p': ()},
    ...             {
    ...                 'name': 'p3', 'stuff': 42, 'p': (
    ...                     {'name': 'p4'},
    ...                     {'name': 'p5'}
    ...                 )
    ...             }
    ...         )
    ...     }
    ... )

    This serializer can optionally adapt schema to objects:

    >>> SCHEMA = [{
    ...     'n': 'name',
    ...     'p': {
    ...         'n': 'name',
    ...         'p': {
    ...             'n': 'name'
    ...         }
    ...     }
    ... }]
    ...
    >>> seen = set()
    >>> def reduce_seen(obj, schema, depth):
    ...     if obj in seen:
    ...         return obj, {'r': 'name'}
    ...     seen.add(obj)
    ...     return obj, schema
    ...
    >>> p1 = Point('p1', 0, 0, None)
    >>> asserts.list_equal(
    ...     object_to_dict([
    ...         p1,
    ...         Point('p2', 5, 2, Point('p3', 3, 4, p1)),
    ...         Point('p4', 5, 2, Point('p5', 3, 4, p1)),
    ...         Point('p6', 5, 2, p1)
    ...     ], SCHEMA, callback=reduce_seen),
    ...     [
    ...         {'n': 'p1', 'p': None},
    ...         {'n': 'p2', 'p': {'n': 'p3', 'p': {'r': 'p1'}}},
    ...         {'n': 'p4', 'p': {'n': 'p5', 'p': {'r': 'p1'}}},
    ...         {'n': 'p6', 'p': {'r': 'p1'}}
    ...     ]
    ... )
    """
    if isinstance(schema, list):
        count = len(schema)
        if count != 1:
            raise NotImplementedError('List containing {0} items.'.format(count))
        schema = schema[0]
        container_type = iterable_callback(obj, schema, depth)
        return container_type(
            _object_to_dict_item(i, schema, depth, callback, iterable_callback)
            for i in obj
        )
    return _object_to_dict_item(obj, schema, depth, callback, iterable_callback)


def _object_to_dict_item(
    obj, schema, depth=0,
    callback=lambda o, s, d: (o, s),
    iterable_callback=lambda o, s, d: list
):
    if obj is None:
        return None
    obj_dict = {}
    obj, schema = callback(obj, schema, depth)
    for key, value in schema.items():
        # Direct access to object
        if isinstance(value, string_types):
            obj_dict[key] = getattr(obj, value)
        elif callable(value):
            obj_dict[key] = value(obj)
        # Nested object(s)
        elif isinstance(value, (dict, list)):
            obj_dict[key] = object_to_dict(
                getattr(obj, key),
                schema[key],
                depth + 1,
                callback,
                iterable_callback)
        else:
            raise NotImplementedError('Key {0} with value {1}'.format(repr(key), repr(value)))
    return obj_dict


def dict_to_object(cls, the_dict, inspect_constructor):
    """
    Convert a python dictionary to an instance of a class.

    Set `inspect_constructor` to True to filter input dictionary to avoid sending unexpected keyword
    arguments to the constructor (`__init__`) of `cls`.

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
        the_dict = {
            arg: the_dict.get(arg, None)
            for arg in inspect.getargspec(cls.__init__)[0] if arg != 'self'
        }
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
