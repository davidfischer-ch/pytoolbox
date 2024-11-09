from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Literal
import datetime
import re

from pytoolbox import decorators, exceptions
from pytoolbox.datetime import str_to_datetime, str_to_time

from .brand import Brand

__all__ = ['Tag', 'TagSet']


class Tag(object):

    brand_class = Brand
    date_formats = ['%Y%m%d %H%M%S', '%Y%m%d']
    date_clean_regex = re.compile(r'[:-]')
    group_to_brand_blacklist = frozenset(['aux', 'crs', 'exifEX', 'Image', 'Photo'])
    type_to_hook = {
        datetime.datetime: 'tag_string',  # clean method will convert to a date-time
        datetime.time: 'tag_string',  # clean method will convert to a time
        Fraction: 'exif_tag_rational',
        int: 'tag_long',
        list: 'tag_multiple',
        str: 'tag_string'
    }
    type_to_python = {
        'Ascii': str,
        'Byte': bytes,
        'Comment': str,
        'Date': datetime.datetime,
        'LangAlt': str,
        'Long': int,
        'Rational': Fraction,
        'SRational': Fraction,
        'SLong': int,
        'Short': int,
        'SShort': int,
        'String': str,
        'Time': datetime.time,
        'Undefined': bytes,
        'XmpBag': list,
        'XmpSeq': list,
        'XmpText': str
    }

    def __init__(self, metadata, key):
        self.metadata = metadata
        self.key = key

    def __repr__(self):
        return f'<{type(self).__name__} {self.key}: {str(self.data)[:20]}>'

    @property
    def data(self):
        if self.data_bytes is None:
            return None
        if type_hook := self.get_type_hook(mode='get'):
            try:
                return self.clean(type_hook(self.key))
            except UnicodeDecodeError as ex:
                return ex
        return self.data_bytes

    @property
    def data_bytes(self):
        tag_raw = self.metadata.exiv2.try_get_tag_raw(self.key)
        return tag_raw.get_data() if tag_raw else None

    @decorators.cached_property
    def description(self) -> str:
        return self.metadata.exiv2.get_tag_description(self.key)

    @property
    def brand(self) -> Brand | None:
        if self.group in self.group_to_brand_blacklist:
            return None
        return self.brand_class(self.group)

    @property
    def group(self) -> str:
        return self.key.split('.')[-2]

    @decorators.cached_property
    def label(self) -> str:
        return self.metadata.exiv2.try_get_tag_label(self.key) or self.key.split('.')[-1]

    @property
    def size(self) -> int:
        raw = self.metadata.exiv2.try_get_tag_raw(self.key)
        return raw.get_size() if raw else 0

    @decorators.cached_property
    def type(self) -> type:
        tag_type = self.metadata.exiv2.try_get_tag_type(self.key)
        try:
            return self.type_to_python[tag_type]
        except KeyError as ex:
            if tag_type:
                raise KeyError(f'Unknow tag type {tag_type}') from ex
        return bytes

    def clean(self, data):
        if isinstance(data, str):
            data = data.strip()
        if self.type == datetime.time:
            return str_to_time(data)
        if self.type == datetime.datetime or isinstance(data, str):
            cleaned_data = self.date_clean_regex.sub('', data)
            for date_format in self.date_formats:
                if date := str_to_datetime(cleaned_data, fmt=date_format, fail=False):
                    return date
        if self.type == Fraction and isinstance(data, tuple):
            try:
                return Fraction(*data)
            except ZeroDivisionError:
                # Special case were type is _ResultTuple(nom=0, den=0)
                return None
        if data is None or isinstance(data, self.type):
            return data
        raise exceptions.WrongExifTagDataTypeError(
            key=self.key,
            type=self.type.__name__,
            data_type=type(data).__name__,
            data_repr=repr(data))

    def get_type_hook(self, *, mode: Literal['get', 'set']) -> Callable | None:
        name = self.type_to_hook.get(self.type)
        return getattr(self.metadata.exiv2, f'try_{mode}_{name}') if name else None


class TagSet(object):  # pylint:disable=too-few-public-methods

    def __init__(self, metadata):
        self.metadata = metadata

    @staticmethod
    def clean_number(number) -> int | Fraction | None:
        return number if number and number > 0 else None
