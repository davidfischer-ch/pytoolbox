"""
Helpers for interacting with Amazon S3 via :mod:`botocore`.
"""
from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from typing import Any, IO
import collections.abc

from botocore.exceptions import ClientError

from pytoolbox.regex import from_path_patterns


def copy_object(s3: Any, bucket_name: str, source_key: str, target_key: str) -> dict:
    """Copy an object within the same bucket."""
    return s3.copy_object(
        CopySource={'Bucket': bucket_name, 'Key': source_key},
        Bucket=bucket_name,
        Key=target_key)


def get_bucket_location(s3: Any, bucket_name: str) -> str | None:
    """Return the location constraint of a bucket."""
    return s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']


def get_object_url(bucket_name: str, location: str, key: str) -> str:
    """Build the public URL for an S3 object."""
    return f'https://s3-{location}.amazonaws.com/{bucket_name}/{key}'


def list_objects(
        s3: Any,
        bucket_name: str,
        prefix: str = '',
        patterns: str = '*',
        *,
        regex: bool = False) -> Iterator[dict]:
    """Yield objects in a bucket whose keys match the given patterns."""
    if prefix and prefix[-1] != '/':
        prefix += '/'
    patterns = from_path_patterns(patterns, regex=regex)
    for page in s3.get_paginator('list_objects').paginate(Bucket=bucket_name, Prefix=prefix):
        try:
            objects = page['Contents']
        except KeyError:
            return
        for obj in objects:
            key = obj['Key']
            if any(p.match(key) for p in patterns):
                yield obj


def load_object_meta(s3: Any, bucket_name: str, path: str, *, fail: bool = True) -> dict | None:
    """Return the HEAD metadata of an object, or ``None`` if not found."""
    try:
        return s3.head_object(Bucket=bucket_name, Key=path)
    except ClientError as ex:
        if 'Not Found' in str(ex) and not fail:
            return None
        raise


def read_object(
        s3: Any,
        bucket_name: str,
        path: str,
        file: IO | None = None,
        *,
        fail: bool = True) -> bytes | IO | None:
    """Download an object's content into memory or into an open file."""
    try:
        if file is None:
            with BytesIO() as f:
                s3.download_fileobj(bucket_name, path, f)
                return f.getvalue()
        else:
            s3.download_fileobj(bucket_name, path, file)
            file.seek(0)
            return file
    except ClientError as ex:
        if 'Not Found' in str(ex) and not fail:
            return None
        raise


def remove_objects(
    s3: Any,
    bucket_name: str,
    prefix: str = '',
    patterns: str = r'*',
    *,
    callback: collections.abc.Callable[[dict], bool] = lambda obj: True,
    regex: bool = False,
    simulate: bool = False
) -> Iterator[dict]:
    """
    Remove objects matching pattern, by chunks of 1000 to be efficient.

    * Set `callback` to a function returning True if given object has to be removed.
    """
    objects = []
    for obj in list_objects(s3, bucket_name, prefix, patterns, regex=regex):
        if callback(obj):
            key = obj['Key']
            objects.append({'Key': key})
            yield obj
            if len(objects) == 1000 and not simulate:
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                objects = []
    # Remove remaining objects
    if objects and not simulate:
        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})


def write_object(s3: Any, bucket_name: str, path: str, file: IO) -> None:
    """Upload a file object to an S3 bucket."""
    s3.upload_fileobj(file, bucket_name, path)
