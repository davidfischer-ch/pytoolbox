# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
try:
    from collections import abc
except ImportError:
    import collections as abc
import itertools

from . import module
from .encoding import binary_type, string_types

_all = module.All(globals())


def get_arguments_names(function):
    specs = inspect.getargspec(function)
    all_names = specs.args[:]
    for names in specs.varargs, specs.keywords:
        if names:
            all_names.extend(names if isinstance(names, list) else [names])
    return all_names


def get_properties(obj):
    return (
        (n, getattr(obj, n))
        for n, p in inspect.getmembers(obj.__class__, lambda m: isinstance(m, property))
    )


def get_slots(obj):
    """Return a set with the `__slots__` of the `obj` including all parent classes `__slots__`."""
    return set(itertools.chain.from_iterable(
        getattr(cls, '__slots__', ()) for cls in obj.__class__.__mro__)
    )


def get_subclasses(obj, nested=True):
    """
    Walk the inheritance tree of ``obj``. Yield tuples with (class, subclasses).

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>>
    >>> class Root(object):
    ...     pass
    ...
    >>> class NodeA(Root):
    ...     pass
    ...
    >>> class NodeB(Root):
    ...     pass
    ...
    >>> class NodeC(NodeA):
    ...     pass
    ...
    >>> class NodeD(NodeA):
    ...     pass
    ...
    >>> class NodeE(NodeD):
    ...     pass
    ...
    >>> asserts.list_equal([(c, bool(s)) for c, s in get_subclasses(Root)], [
    ...     (NodeA, True), (NodeC, False), (NodeD, True), (NodeE, False), (NodeB, False)
    ... ])
    >>> asserts.list_equal([(c, bool(s)) for c, s in get_subclasses(Root, nested=False)], [
    ...     (NodeA, True), (NodeB, False)
    ... ])
    >>> asserts.list_equal([(c, bool(s)) for c, s in get_subclasses(NodeB)], [])
    >>> asserts.list_equal([(c, bool(s)) for c, s in get_subclasses(NodeD)], [(NodeE, False)])
    """
    for subclass in obj.__subclasses__():
        yield subclass, subclass.__subclasses__()
        if nested:
            for subclass in get_subclasses(subclass, nested):
                yield subclass


def isiterable(obj, blacklist=(binary_type, string_types)):
    """
    Return ``True`` if the object is an iterable, but ``False`` for any class in `blacklist`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> for obj in 'text', b'binary', u'unicode', 42:
    ...     asserts.false(isiterable(obj), obj)
    >>> for obj in [], (), set(), {}.iteritems():
    ...     asserts.true(isiterable(obj), obj)
    >>> asserts.false(isiterable({}, dict))
    """
    return isinstance(obj, abc.Iterable) and not isinstance(obj, blacklist)


def merge_bases_attribute(cls, attr_name, init, default, merge_func=lambda a, b: a + b):
    """
    Merge all values of attribute defined in all bases classes (using `__mro__`).
    Return resulting value. Use default every time a class does not have given attribute.

    Be careful, `merge_func` must be a pure function.
    """
    value = init
    for base in cls.__mro__:
        value = merge_func(value, getattr(base, attr_name, default))
    return value


class DummyObject(object):
    """
    Easy way to generate a dynamic object with the attributes defined at instantiation.

    **Example usage**

    >>> obj = DummyObject(foo=42, bar=None)
    >>> obj.foo
    42
    >>> obj.bar is None
    True
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class EchoObject(object):
    """
    Object that return any missing attribute as an instance of :class:`EchoObject` with the name set
    to the Python expression used to access it. Also implements __getitem__. Some examples are worth
    hundred words...

    **Example usage**

    >>> from pytoolbox.encoding import text_type
    >>> from pytoolbox.unittest import asserts
    >>> something = EchoObject('something', language='Python')
    >>> asserts.equal(something._name, 'something')
    >>> asserts.equal(something.language, 'Python')
    >>> asserts.true(hasattr(something, 'everything'))
    >>> asserts.is_instance(something.user.email, EchoObject)
    >>> asserts.equal(text_type(something.user.first_name), 'something.user.first_name')
    >>> asserts.equal(text_type(something[0][None]['bar']).replace("[u'", "['"), "something[0][None]['bar']")
    >>> asserts.equal(text_type(something[0].node['foo'].x).replace("[u'", "['"), "something[0].node['foo'].x")
    >>> asserts.equal(text_type(something), 'something')

    You can also define the class for the generated attributes:

    >>> something.attr_class = list
    >>> asserts.is_instance(something.cool, list)

    This class handles sub-classing appropriately:

    >>> class MyEchoObject(EchoObject):
    ...     pass
    >>>
    >>> asserts.is_instance(MyEchoObject('name').x.y.z, MyEchoObject)
    """
    attr_class = None

    def __init__(self, name, **attrs):
        assert '_name' not in attrs
        self.__dict__.update(attrs)
        self._name = name

    def __getattr__(self, name):
        return (self.attr_class or self.__class__)('{0._name}.{1}'.format(self, name))

    def __getitem__(self, key):
        return (self.attr_class or self.__class__)('{0._name}[{1}]'.format(self, repr(key)))

    def __unicode__(self):
        return self._name


class EchoDict(dict):
    """
    Dictionary that return any missing item as an instance of :class:`EchoObject` with the name set
    to the Python expression used to access it. Some examples are worth hundred words...

    **Example usage**

    >>> from pytoolbox.encoding import text_type
    >>> from pytoolbox.unittest import asserts
    >>> context = EchoDict('context', language='Python')
    >>> asserts.equal(context._name, 'context')
    >>> asserts.equal(context['language'], 'Python')
    >>> asserts.true('anything' in context)
    >>> asserts.equal(text_type(context['user'].first_name).replace("[u'", "['"), "context['user'].first_name")
    >>> asserts.equal(text_type(context[0][None]['bar']).replace("[u'", "['"), "context[0][None]['bar']")
    >>> asserts.equal(text_type(context[0].node['foo'].x).replace("[u'", "['"), "context[0].node['foo'].x")

    You can also define the class for the generated items:

    >>> context.item_class = set
    >>> asserts.is_instance(context['jet'], set)
    """
    item_class = EchoObject

    def __init__(self, name, **items):
        assert '_name' not in items
        super(EchoDict, self).__init__(**items)
        self._name = name

    def __contains__(self, key):
        """Always return True because missing items are generated."""
        return True

    def __getitem__(self, key):
        try:
            return super(EchoDict, self).__getitem__(key)
        except KeyError:
            return self.item_class('{0._name}[{1}]'.format(self, repr(key)))


class MissingType(object):

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __nonzero__(self):
        return False

    def __repr__(self):
        return 'Missing'


Missing = MissingType()

__all__ = _all.diff(globals())
