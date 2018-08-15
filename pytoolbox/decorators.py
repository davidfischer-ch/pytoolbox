# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import functools, os, warnings

from . import module
from .console import confirm
from .subprocess import cmd

_all = module.All(globals())


class cached_property(object):
    """
    Decorator that converts a method with a single self argument into a property cached on the instance.

    Optional ``name`` argument allows you to make cached properties of other methods.
    For example ``url=cached_property(get_absolute_url, name='url')``.

    Copyright: Django Project.
    """
    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__

    def __get__(self, instance, type=None):  # pylint:disable=redefined-builtin
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res


def deprecated(func):
    """
    Decorator that can be used to mark functions as deprecated. It will result in a warning being emitted when the
    function is used. Credits: https://wiki.python.org/moin/PythonDecoratorLibrary.
    """
    @functools.wraps(func)
    def _deprecated(*args, **kwargs):
        warnings.warn_explicit('Call to deprecated function {0.__name__}.'.format(func), category=DeprecationWarning,
                               filename=func.func_code.co_filename, lineno=func.func_code.co_firstlineno + 1)
        return func(*args, **kwargs)
    return _deprecated


class hybridmethod(object):
    """
    Decorator that allows a method to be both used as a class method and an instance method.

    Credits: http://stackoverflow.com/questions/18078744/python-hybrid-between-regular-method-and-classmethod#18078819

    **Example usage**

    >>> class Hybrid(object):
    ...     value = 10
    ...
    ...     def __init__(self):
    ...         self.value = 20
    ...
    ...     @hybridmethod
    ...     def get_value(receiver):
    ...         return receiver.value
    >>> Hybrid.get_value()
    10
    >>> Hybrid().get_value()
    20
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        context = obj if obj is not None else cls

        @functools.wraps(self.func)
        def hybrid(*args, **kwargs):
            return self.func(context, *args, **kwargs)

        # optional, mimic methods some more
        hybrid.__func__ = hybrid.im_func = self.func
        hybrid.__self__ = hybrid.im_self = context
        return hybrid


def confirm_it(message, default=False, abort_message='Operation aborted by the user'):
    """Ask for confirmation before calling the decorated function."""
    def _confirm_it(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if confirm(message, default=default):
                return f(*args, **kwargs)
            print(abort_message)
        return wrapper
    return _confirm_it


def disable_iptables(f):
    """
    Stop the iptables service if necessary, execute the decorated function and then reactivate iptables if it was
    previously stopped.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            try:
                cmd('sudo service iptables stop', shell=True)
                print('Disable iptables')
                has_iptables = True
            except:
                has_iptables = False
            return f(*args, **kwargs)
        finally:
            if has_iptables:
                print('Enable iptables')
                cmd('sudo service iptables start', shell=True)
    return wrapper


def root_required(error_message='This script must be run as root.'):
    """Raise an exception if the current user is not root."""
    def _root_required(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if not os.geteuid() == 0:
                raise RuntimeError(error_message)
            return f(*args, **kwargs)
        return wrapper
    return _root_required


def run_once(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.executed:
            result = f(*args, **kwargs)
            wrapper.executed = True
            return result
    wrapper.executed = False
    return wrapper


__all__ = _all.diff(globals())
