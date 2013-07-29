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
    if something is None:
        try:
            return json.load(open(filename_or_file, u'r', encoding=u'utf-8'))
        except TypeError:
            return json.load(filename_or_file)
    else:
        if isinstance(filename_or_file, string_types):
            json2object(open(filename_or_file, u'r', encoding=u'utf-8').read(), something)
        else:
            json2object(filename_or_file.read(), something)


def object2json(something, include_properties):
    if not include_properties:
        return json.dumps(something, cls=SmartJSONEncoderV1)
    else:
        return json.dumps(something, cls=SmartJSONEncoderV2)
