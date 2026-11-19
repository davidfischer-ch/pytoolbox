"""Tests for the aws.s3 module."""

from __future__ import annotations

import boto3
from botocore.stub import Stubber

from pytoolbox.aws import s3


def test_list_objects_yields_the_matching_objects_of_every_page() -> None:
    """Objects whose keys match the patterns are yielded from each page of the listing."""
    client = boto3.client(
        's3',
        aws_access_key_id='testing',
        aws_secret_access_key='testing',
        region_name='us-east-1',
    )
    with Stubber(client) as stubber:
        stubber.add_response(
            'list_objects_v2',
            {
                'Contents': [{'Key': 'media/a.mp4'}, {'Key': 'media/a.txt'}],
                'IsTruncated': True,
                'NextContinuationToken': 'page-2',
            },
            {'Bucket': 'bucket', 'Prefix': 'media/'},
        )
        stubber.add_response(
            'list_objects_v2',
            {'Contents': [{'Key': 'media/b.mp4'}], 'IsTruncated': False},
            {'Bucket': 'bucket', 'ContinuationToken': 'page-2', 'Prefix': 'media/'},
        )
        keys = [obj['Key'] for obj in s3.list_objects(client, 'bucket', 'media', '*.mp4')]
    assert keys == ['media/a.mp4', 'media/b.mp4']
