"""Tests for the deprecation module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

import functools
import inspect
import warnings
from importlib import machinery
from typing import Any

import pytest

from pytoolbox import deprecation
from pytoolbox.compat import override


class Base:
    """A base whose ``old`` hook is renamed ``new``."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        deprecation.alias_renamed_methods(cls, {'old': 'new'})

    def new(self) -> list[str]:
        """Return the names of the overrides reached, none here."""
        return []


class Meta(type):
    """A metaclass creating its classes from its own frame, as Django's ``ModelBase`` does."""

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> Meta:
        return super().__new__(mcs, name, bases, namespace)


def test_an_override_of_the_old_name_is_reached_through_the_new_one_with_a_warning() -> None:
    """A subclass overriding the old name keeps working, and its warning names the new name."""
    with pytest.warns(DeprecationWarning) as record:

        class Legacy(Base):
            """Override the old name only."""

            def old(self) -> list[str]:
                """Return the base's names and this one."""
                return [*super().new(), 'legacy']

    assert len(record) == 1
    assert str(record[0].message) == (
        f'{Legacy.__qualname__}.old is deprecated; override new instead.'
    )
    assert record[0].filename == __file__
    assert record[0].lineno == Legacy.__dict__['old'].__code__.co_firstlineno
    assert Legacy().new() == ['legacy']
    assert Legacy().old() == ['legacy']


def test_an_override_of_the_new_name_is_reached_through_the_old_one_silently() -> None:
    """A caller still using the old name reads what the new override returns."""
    with warnings.catch_warnings():
        warnings.simplefilter('error')

        class Current(Base):
            """Override the new name only."""

            @override
            def new(self) -> list[str]:
                """Return the base's names and this one."""
                return [*super().new(), 'current']

    assert Current().old() == ['current']  # pylint:disable=no-member


def test_overrides_of_both_names_are_kept_as_written() -> None:
    """A class defining both names keeps each of its methods, without a warning."""
    with warnings.catch_warnings():
        warnings.simplefilter('error')

        class Both(Base):
            """Override both names, each with its own method."""

            def old(self) -> list[str]:
                """Return this method's name."""
                return ['old']

            @override
            def new(self) -> list[str]:
                """Return this method's name."""
                return ['new']

    assert Both().old() == ['old']
    assert Both().new() == ['new']


def test_a_subclass_of_a_legacy_class_emits_no_second_warning() -> None:
    """Only the creation of the class defining the old name emits a warning."""
    with pytest.warns(DeprecationWarning):

        class Legacy(Base):
            """Override the old name only."""

            def old(self) -> list[str]:
                """Return this class's name."""
                return ['legacy']

    with warnings.catch_warnings():
        warnings.simplefilter('error')

        class Child(Legacy):
            """Inherit the legacy override."""

    assert Child().new() == ['legacy']


def test_overrides_under_either_name_chain_through_super() -> None:
    """A mixin on the old name over a class on the new one: each override is reached once."""

    class Current(Base):
        """Override the new name only."""

        @override
        def new(self) -> list[str]:
            """Return the base's names and this one."""
            return [*super().new(), 'current']

    class LegacyMixin:
        """Override the old name only, outside the base's hierarchy."""

        def old(self) -> list[str]:
            """Return the next class's names and this one."""
            return [*super().old(), 'legacy']

    with pytest.warns(DeprecationWarning, match='LegacyMixin.old is deprecated'):

        class Combined(LegacyMixin, Current):
            """Stack the legacy mixin over the current override."""

    assert Combined().new() == ['current', 'legacy']
    assert Combined().old() == ['current', 'legacy']


def test_the_warning_points_at_the_method_of_a_class_built_by_a_metaclass() -> None:
    """The warning names the old method's definition, not the frame of the metaclass."""
    with pytest.warns(DeprecationWarning) as record:

        class Legacy(Base, metaclass=Meta):
            """Override the old name only, in a class built by a metaclass."""

            def old(self) -> list[str]:
                """Return this class's name."""
                return ['legacy']

    assert len(record) == 1
    assert record[0].filename == __file__
    assert record[0].lineno == Legacy.__dict__['old'].__code__.co_firstlineno
    assert Legacy().new() == ['legacy']


def test_a_classmethod_under_the_old_name_is_aliased_and_located() -> None:
    """A descriptor is bound under the new name as is, and the warning names its function."""

    class ClassBase:
        """A base whose ``old`` class method is renamed ``new``."""

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            deprecation.alias_renamed_methods(cls, {'old': 'new'})

    with pytest.warns(DeprecationWarning) as record:

        class Legacy(ClassBase):
            """Override the old name only, as a class method."""

            @classmethod
            def old(cls) -> str:
                """Return the class's name."""
                return cls.__name__

    assert len(record) == 1
    assert record[0].filename == __file__
    assert record[0].lineno == Legacy.__dict__['old'].__func__.__code__.co_firstlineno
    assert Legacy.new() == 'Legacy'  # pylint:disable=no-member


def test_a_property_under_the_old_name_is_located_at_its_getter() -> None:
    """A property's warning names its getter, also below a cooperative ``__init_subclass__``."""

    class Middle(Base):
        """Add a cooperative ``__init_subclass__`` between the base and its subclasses."""

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)

    with pytest.warns(DeprecationWarning) as record:

        class Legacy(Middle):
            """Override the old name only, as a property."""

            @property
            def old(self) -> str:
                """Return this class's name."""
                return 'legacy'

    assert len(record) == 1
    assert record[0].filename == __file__
    assert record[0].lineno == Legacy.__dict__['old'].fget.__code__.co_firstlineno
    # The alias replaces the base's method with the property.
    assert Legacy().new == 'legacy'  # pylint:disable=comparison-with-callable


def test_a_cached_property_under_the_old_name_is_located_at_its_function() -> None:
    """A cached property's warning names the function it caches."""
    with pytest.warns(DeprecationWarning) as record:

        class Legacy(Base):
            """Override the old name only, as a cached property."""

            @functools.cached_property
            def old(self) -> str:
                """Return this class's name."""
                return 'legacy'

    assert len(record) == 1
    assert record[0].filename == __file__
    assert record[0].lineno == Legacy.__dict__['old'].func.__code__.co_firstlineno
    # The alias replaces the base's method with the cached property.
    assert Legacy().new == 'legacy'  # pylint:disable=comparison-with-callable


def test_a_member_without_code_warns_at_the_base_alias_call() -> None:
    """A member with no Python code behind it warns at the base's call to the helper."""
    with pytest.warns(DeprecationWarning) as record:

        class Legacy(Base):
            """Override the old name only, with a builtin."""

            old = staticmethod(len)

    lines, first_line = inspect.getsourcelines(Base.__init_subclass__)
    assert len(record) == 1
    assert record[0].filename == __file__
    assert record[0].lineno == first_line + next(
        index for index, line in enumerate(lines) if 'alias_renamed_methods' in line
    )
    assert Legacy.new('abc') == 3


@pytest.mark.parametrize(
    'main_globals',
    [
        pytest.param({}, id='exec'),
        pytest.param({'__spec__': None}, id='no-loader'),
        pytest.param(
            {'__spec__': None, '__loader__': machinery.SourceFileLoader('__main__', __file__)},
            id='script',
        ),
        pytest.param({'__spec__': None, '__loader__': machinery.BuiltinImporter}, id='stdin'),
    ],
)
def test_a_class_defined_in_a_main_module_warns_once(main_globals: dict[str, Any]) -> None:
    """A subclass created by code run as ``__main__`` emits exactly one warning, at its method."""
    source = "class Legacy(Base):\n    def old(self):\n        return ['legacy']\n"
    namespace: dict[str, Any] = {'__name__': '__main__', 'Base': Base, **main_globals}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        exec(compile(source, '<legacy>', 'exec'), namespace)  # pylint:disable=exec-used

    assert [(str(w.message), w.filename, w.lineno) for w in caught] == [
        ('Legacy.old is deprecated; override new instead.', '<legacy>', 2),
    ]
    assert namespace['Legacy']().new() == ['legacy']


def test_deprecated_warns_at_the_function_with_its_guidelines() -> None:
    """A call to a deprecated function warns at its definition, naming it and the guidelines."""

    @deprecation.deprecated('Use new_function instead')
    def old_function(value: int) -> int:
        return value + 1

    with pytest.warns(DeprecationWarning) as record:
        assert old_function(5) == 6

    assert len(record) == 1
    assert str(record[0].message) == (
        f'{old_function.__qualname__} is deprecated: Use new_function instead.'
    )
    assert record[0].filename == __file__
    assert record[0].lineno == old_function.__wrapped__.__code__.co_firstlineno


def test_deprecated_without_guidelines() -> None:
    """A deprecated function without guidelines has no suffix after its name."""

    @deprecation.deprecated()
    def old_function() -> int:
        return 42

    with pytest.warns(DeprecationWarning) as record:
        assert old_function() == 42

    assert str(record[0].message) == f'{old_function.__qualname__} is deprecated.'
