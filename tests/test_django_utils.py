import unittest

from . import base


@unittest.skip('Django modules testing disabled')
class TestDjangoUtils(base.TestCase):

    tags = ('django', 'utils')

    def test_FieldsToValuesLookupDict(self):
        class File(object):
            pass

        class Media(object):
            pass

        class MediaForm(object):
            class Meta:
                model = Media

        from pytoolbox.django.utils import collections
        numbers = collections.FieldsToValuesLookupDict(
            'numbers', {'MediaForm.name': 1, 'Media.url': 2, 'url': 3})
        self.equal(numbers[(File, 'url')], 3)
        self.equal(numbers[(Media, 'url')], 2)
        self.equal(numbers[(MediaForm, 'url')], 2)
        self.equal(numbers[(MediaForm, 'name')], 1)
