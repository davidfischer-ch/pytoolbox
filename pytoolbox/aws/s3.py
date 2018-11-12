import re, tempfile

from botocore.exceptions import ClientError


def copy_object(s3, bucket_name, source_key, target_key):
    return s3.copy_object(
        CopySource={'Bucket': bucket_name, 'Key': source_key},
        Bucket=bucket_name,
        Key=target_key)


def get_bucket_location(s3, bucket_name):
    return s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']


def get_object_url(bucket_name, location, key):
    return f'https://s3-{location}.amazonaws.com/{bucket_name}/{key}'


def list_objects(s3, bucket_name, prefix=''):
    if prefix and prefix[-1] != '/':
        prefix += '/'
    paginator = s3.get_paginator('list_objects').paginate(Bucket=bucket_name, Prefix=prefix)
    for page in paginator:
        try:
            yield from page['Contents']
        except KeyError:
            raise StopIteration


def load_object_meta(s3, bucket_name, path, fail=True):
    try:
        return s3.head_object(Bucket=bucket_name, Key=path)
    except ClientError as e:
        if 'Not Found' in str(e) and not fail:
            return None
        raise


def read_object(s3, bucket_name, path, file=None):
    if file:
        s3.download_fileobj(bucket_name, path, file)
        file.seek(0)
    else:
        with tempfile.TemporaryFile() as f:
            s3.download_fileobj(bucket_name, path, f)
            f.seek(0)
            return f.read()


def remove_objects(s3, bucket_name, prefix='', pattern=r'.*', simulate=False):
    """Remove objects matching pattern, by chunks of 1000 to be efficient."""
    pattern = re.compile(pattern)
    objects = []
    removed = []
    for obj in list_objects(s3, bucket_name, prefix):
        key = obj['Key']
        if pattern.match(key):
            objects.append({'Key': key})
            removed.append(obj)
            if len(objects) == 1000 and not simulate:
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                objects = []
    # Remove remaining objects
    if objects and not simulate:
        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
    return removed


def write_object(s3, bucket_name, path, file):
    s3.upload_fileobj(file, bucket_name, path)
