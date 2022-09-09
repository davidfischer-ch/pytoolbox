import inspect, itertools
from collections import abc

from . import module
from .collections import merge_dicts

_all = module.All(globals())


def get_arguments_names(function):
    """
    Return a list with arguments names.

    >>> from pytoolbox import types
    >>>
    >>> get_arguments_names(get_arguments_names)
    ['function']
    >>>
    >>> def my_func(directory, a=1, *args, b, c=None, **kwargs):
    ...     pass
    ...
    >>> get_arguments_names(my_func)
    ['directory', 'a', 'args', 'b', 'c', 'kwargs']
    >>>
    >>> get_arguments_names(types.get_subclasses)
    ['obj', 'nested']
    >>> get_arguments_names(types.merge_bases_attribute)
    ['cls', 'attr_name', 'init', 'default', 'merge_func']
    """
    return list(inspect.signature(function).parameters.keys())


def get_properties(obj):
    return (
        (n, getattr(obj, n))
        for n, p in inspect.getmembers(obj.__class__, lambda m: isinstance(m, property))
    )


def get_slots(obj):
    """Return a set with the `__slots__` of the `obj` including all parent classes `__slots__`."""
    return set(itertools.chain.from_iterable(
        getattr(cls, '__slots__', ())
        for cls in obj.__class__.__mro__)
    )


def get_subclasses(obj, nested=True):
    """
    Walk the inheritance tree of ``obj``. Yield tuples with (class, subclasses).

    **Example usage**

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
    >>> [(c.__name__, bool(s)) for c, s in get_subclasses(Root)]
    [('NodeA', True), ('NodeC', False), ('NodeD', True), ('NodeE', False), ('NodeB', False)]
    >>> [(c.__name__, bool(s)) for c, s in get_subclasses(Root, nested=False)]
    [('NodeA', True), ('NodeB', False)]
    >>> [(c.__name__, bool(s)) for c, s in get_subclasses(NodeB)]
    []
    >>> [(c.__name__, bool(s)) for c, s in get_subclasses(NodeD)]
    [('NodeE', False)]
    """
    for subclass in obj.__subclasses__():
        yield subclass, subclass.__subclasses__()
        if nested:
            for sub_subclass in get_subclasses(subclass, nested):
                yield sub_subclass


def isiterable(obj, blacklist=(bytes, str)):
    """
    Return ``True`` if the object is an iterable, but ``False`` for any class in `blacklist`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> for obj in b'binary', 'unicode', 42:
    ...     asserts.false(isiterable(obj), obj)
    >>> for obj in [], (), set(), iter({}.items()):
    ...     asserts.true(isiterable(obj), obj)
    >>> isiterable({}, dict)
    False
    """
    return isinstance(obj, abc.Iterable) and not isinstance(obj, blacklist)


def merge_annotations(cls: type):
    """
    Merge annotations defined in all bases classes (using `__mro__`) into given `cls`.

    Can be used as a decorator.

    **Example usage**

    >>> class Point2D(object):
    ...     x: int
    ...     y: int
    ...
    >>> class Point3D(Point2D):
    ...     z: int
    ...
    >>> class Point4D(Point3D, Point2D):
    ...     w: int
    ...
    >>> @merge_annotations
    ... class Point4X(Point4D):
    ...     x: float
    ...     other: str
    ...
    >>> assert Point2D.__annotations__ == {'x': int, 'y': int}
    >>> assert Point3D.__annotations__ == {'z': int}
    >>> assert Point4D.__annotations__ == {'w': int}
    >>> assert Point4X.__annotations__ == {'x': float, 'y': int, 'z': int, 'w': int, 'other': str}
    """
    cls.__annotations__ = merge_dicts(*[
        getattr(base, '__annotations__', {})
        for base in reversed(cls.__mro__)
    ])
    return cls


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

    >>> from pytoolbox.unittest import asserts
    >>> something = EchoObject('something', language='Python')
    >>> something._name
    'something'
    >>> something.language
    'Python'
    >>> hasattr(something, 'everything')
    True
    >>> type(something.user.email)
    <class 'pytoolbox.types.EchoObject'>
    >>> str(something.user.first_name)
    'something.user.first_name'
    >>> str(something[0][None]['bar'])
    "something[0][None]['bar']"
    >>> str(something[0].node['foo'].x)
    "something[0].node['foo'].x"
    >>> str(something)
    'something'

    You can also define the class for the generated attributes:

    >>> something.attr_class = list
    >>> type(something.cool)
    <class 'list'>

    This class handles sub-classing appropriately:

    >>> class MyEchoObject(EchoObject):
    ...     pass
    >>>
    >>> type(MyEchoObject('name').x.y.z)
    <class 'pytoolbox.types.MyEchoObject'>
    """
    attr_class = None

    def __init__(self, name, **attrs):
        assert '_name' not in attrs
        self.__dict__.update(attrs)
        self._name = name

    def __getattr__(self, name):
        return (self.attr_class or self.__class__)(f'{self._name}.{name}')

    def __getitem__(self, key):
        return (self.attr_class or self.__class__)(f'{self._name}[{repr(key)}]')

    def __str__(self):
        return self._name


class EchoDict(dict):
    """
    Dictionary that return any missing item as an instance of :class:`EchoObject` with the name set
    to the Python expression used to access it. Some examples are worth hundred words...

    **Example usage**

    >>> context = EchoDict('context', language='Python')
    >>> context._name
    'context'
    >>> context['language']
    'Python'
    >>> 'anything' in context
    True
    >>> str(context['user'].first_name)
    "context['user'].first_name"
    >>> str(context[0][None]['bar'])
    "context[0][None]['bar']"
    >>> str(context[0].node['foo'].x)
    "context[0].node['foo'].x"

    You can also define the class for the generated items:

    >>> context.item_class = set
    >>> type(context['jet'])
    <class 'set'>
    """
    item_class = EchoObject

    def __init__(self, name, **items):
        assert '_name' not in items
        super().__init__(**items)
        self._name = name

    def __contains__(self, key):
        """Always return True because missing items are generated."""
        return True

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.item_class(f'{self._name}[{repr(key)}]')


class MissingType(object):

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __bool__(self):
        return False

    def __repr__(self):
        return 'Missing'


Missing = MissingType()

__all__ = _all.diff(globals())
