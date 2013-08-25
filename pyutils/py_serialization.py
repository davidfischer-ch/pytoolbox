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

import inspect, json, pickle
from bson.objectid import ObjectId
from codecs import open
from six import string_types


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
        if filename is None and hasattr(self, u'_pickle_filename'):
            filename = self._pickle_filename
            delattr(self, u'_pickle_filename')
            pickle.dump(self, file(filename, u'w'))
            self._pickle_filename = filename
        elif filename is not None:
            pickle.dump(self, file(filename, u'w'))
        else:
            raise ValueError(u'A filename must be specified')


class JsoneableObject(object):
    u"""
    An :class:`object` serializable/deserializable by :mod:`json`.

    .. note::

        Class constructor should have default value for all arguments !
    """
    def to_json(self, include_properties):
        return object2json(self, include_properties)

    @classmethod
    def from_json(cls, json):
        the_object = cls()
        json2object(json, the_object)
        return the_object


## http://stackoverflow.com/questions/6255387/mongodb-object-serialized-as-json
class SmartJSONEncoderV1(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return unicode(obj)
        if hasattr(obj, u'__dict__'):
            return obj.__dict__
        return super(SmartJSONEncoderV1, self).default(obj)


class SmartJSONEncoderV2(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return unicode(obj)
        attributes = {}
        for a in inspect.getmembers(obj):
            if inspect.isroutine(a[1]) or inspect.isbuiltin(a[1]) or a[0].startswith(u'__'):
                continue
            attributes[a[0]] = a[1]
        return attributes


def json2object(json_string, obj=None):
    u"""
    Deserialize the JSON string ``json_string`` to attributes of ``obj``.

    .. warning::

        This method does not handle conversion of ``obj``attributes from ``dict`` to instances of classes.

    **Example usage**:

    Define the sample class and deserialize a JSON string to attributes of a new instance:

    >>> class Point(object):
    ...     def __init__(self, name=None, x=0, y=0):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    >>> p = Point()
    >>> assert(p.__dict__ == {u'name': None, u'x': 0, u'y': 0})
    >>> json2object(u'{"x":10,"y":20,"name":"My position"}', p)
    >>> assert(p.__dict__ == {u'name': u'My position', u'x': 10, u'y': 20})
    >>> json2object(u'{"y":25}', p)
    >>> assert(p.__dict__ == {u'name': u'My position', u'x': 10, u'y': 25})
    >>> json2object(u'{"z":3}', p)
    >>> assert(p.__dict__ == {u'name': u'My position', u'x': 10, u'y': 25})

    Deserialize a JSON string to a dictionary:

    >>> expected = {u'firstname': u'Tabby', u'lastname': u'Fischer'}
    >>> assert(json2object('{"firstname":"Tabby","lastname":"Fischer"}') == expected)
    """
    if obj is None:
        return json.loads(json_string)
    for key, value in json.loads(json_string).items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    #obj.__dict__.update(loads(json)) <-- old implementation


def jsonfile2object(filename_or_file, obj=None):
    u"""
    Loads and deserialize the JSON string stored in a file ``filename``  to attributes of ``obj``.

    .. warning::

        This method does not handle conversion of ``obj``attributes from ``dict`` to instances of classes.

    **Example usage**:

    Define the sample class, instantiate it and serialize it to a file:

    >>> import os
    >>> class Point(object):
    ...     def __init__(self, name=None, x=0, y=0):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    >>> p1 = Point(name=u'My point', x=10, y=-5)
    >>> open(u'test.json', u'w', encoding=u'utf-8').write(object2json(p1, include_properties=False))

    Deserialize the freshly saved file to the attributes of another instance:

    >>> p2 = Point()
    >>> jsonfile2object(u'test.json', p2)
    >>> assert(p1.__dict__ == p2.__dict__)
    >>> jsonfile2object(open(u'test.json', u'r', encoding=u'utf-8'), p2)
    >>> assert(p1.__dict__ == p2.__dict__)

    Deserialize the freshly saved file to a dictionary:

    >>> assert(jsonfile2object(u'test.json') == p1.__dict__)
    >>> assert(jsonfile2object(open(u'test.json', u'r', encoding=u'utf-8')) == p1.__dict__)
    >>> os.remove(u'test.json')
    """
    if obj is None:
        try:
            return json.load(open(filename_or_file, u'r', encoding=u'utf-8'))
        except TypeError:
            return json.load(filename_or_file)
    else:
        if isinstance(filename_or_file, string_types):
            json2object(open(filename_or_file, u'r', encoding=u'utf-8').read(), obj)
        else:
            json2object(filename_or_file.read(), obj)


def object2json(obj, include_properties):
    if not include_properties:
        return json.dumps(obj, cls=SmartJSONEncoderV1)
    else:
        return json.dumps(obj, cls=SmartJSONEncoderV2)


def object2dict(obj, include_properties):
    u"""
    Convert an object to a python dictionary.

    .. warning::

        Current implementation serialize ``obj`` to a JSON string and then deserialize this JSON string to a ``dict``.

    **Example usage**:

    Define the sample class and convert some instances to a dictionary:

    >>> class Point(object):
    ...     def __init__(self, name, x, y, p):
    ...         self.name = name
    ...         self.x = x
    ...         self.y = y
    ...         self.p = p
    ...     @property
    ...     def z(self):
    ...         return self.x - self.y

    >>> p1_dict = {u'y': 2, u'x': 5, u'name': u'p1', u'p': {u'y': 4, u'x': 3, u'name': u'p2', u'p': None}}
    >>> assert(object2dict(Point('p1', 5, 2, Point('p2', 3, 4, None)), False) == p1_dict)

    >>> p2_dict = {u'y': 4, u'p': None, u'z': -1, u'name': u'p2', u'x': 3}
    >>> p1_dict = {u'y': 2, u'p': p2_dict, u'z': 3, u'name': u'p1', u'x': 5}
    >>> assert(object2dict(Point('p1', 5, 2, Point('p2', 3, 4, None)), True) == p1_dict)

    >>> p1, p2 = Point('p1', 5, 2, None), Point('p2', 3, 4, None)
    >>> p1.p, p2.p = p2, p1
    >>> print(object2dict(p1, True))
    Traceback (most recent call last):
        ...
    ValueError: Circular reference detected
    """
    return json2object(object2json(obj, include_properties))
