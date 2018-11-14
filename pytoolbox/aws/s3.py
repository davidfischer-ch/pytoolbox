from io import BytesIO

from botocore.exceptions import ClientError

from pytoolbox.regex import from_path_patterns


def copy_object(s3, bucket_name, source_key, target_key):
    return s3.copy_object(
        CopySource={'Bucket': bucket_name, 'Key': source_key},
        Bucket=bucket_name,
        Key=target_key)


def get_bucket_location(s3, bucket_name):
    return s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']


def get_object_url(bucket_name, location, key):
    return 'https://s3-{1}.amazonaws.com/{0}/{2}'.format(bucket_name, location, key)


def list_objects(s3, bucket_name, prefix='', patterns='*', unix_wildcards=True):
    if prefix and prefix[-1] != '/':
        prefix += '/'
    patterns = from_path_patterns(patterns, unix_wildcards=unix_wildcards)
    for page in s3.get_paginator('list_objects').paginate(Bucket=bucket_name, Prefix=prefix):
        try:
            objects = page['Contents']
        except KeyError:
            raise StopIteration
        for obj in objects:
            key = obj['Key']
            if any(p.match(key) for p in patterns):
                yield obj


def load_object_meta(s3, bucket_name, path, fail=True):
    try:
        return s3.head_object(Bucket=bucket_name, Key=path)
    except ClientError as e:
        if 'Not Found' in str(e) and not fail:
            return None
        raise


def read_object(s3, bucket_name, path, file=None, fail=True):
    try:
        if file is None:
            with BytesIO() as f:
                s3.download_fileobj(bucket_name, path, f)
                return f.getvalue()
        else:
            s3.download_fileobj(bucket_name, path, file)
            file.seek(0)
            return file
    except ClientError as e:
        if 'Not Found' in str(e) and not fail:
            return None
        raise


def remove_objects(s3, bucket_name, prefix='', patterns=r'*', callback=lambda obj: True,
                   simulate=False, unix_wildcards=True):
    """
    Remove objects matching pattern, by chunks of 1000 to be efficient.

    * Set `callback` to a function returning True if given object has to be removed.
    """
    objects = []
    for obj in list_objects(s3, bucket_name, prefix, patterns, unix_wildcards=unix_wildcards):
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


def write_object(s3, bucket_name, path, file):
    s3.upload_fileobj(file, bucket_name, path)
