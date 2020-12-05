from pytoolbox.validation import validate_list

from . import base


class TestValidation(base.TestCase):

    tags = ('validation', )

    def test_validate_list(self):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call(['my_var', recursive=False])"], regexes)

    def test_validate_list_fail_size(self):
        with self.raises(IndexError):
            validate_list([1, 2], [1, 2, 3])

    def test_validate_list_fail_value(self):
        with self.raises(ValueError):
            regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
            validate_list([10, "call(['my_var', recursive='error'])"], regexes)
