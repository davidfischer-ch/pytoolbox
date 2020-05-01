import fnmatch, re

from .itertools import chain

__all__ = [
    'TIME_REGEX_PARTS',
    'UUID_REGEX',
    'embed_in_regex',
    'findall_partial',
    'from_path_patterns'
]

TIME_REGEX_PARTS = ['[0-2]', '[0-9]', ':', '[0-5]', '[0-9]', ':', '[0-5]', '[0-9]']
UUID_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


def embed_in_regex(string, regex_parts, index, as_string=True):
    """
    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.equal(embed_in_regex('L', ['[a-z]', '[a-z]'], 0), (0, 'L[a-z]'))
    >>> asserts.equal(embed_in_regex('L', ['[a-z]', '[a-z]'], 1), (1, '[a-z]L'))
    >>> asserts.equal(embed_in_regex('L', ['[a-z]', '[a-z]'], 1, as_string=False), (1, ['[a-z]', 'L']))
    """
    regex = regex_parts[:]
    regex[index:index + len(string)] = string
    return index, ''.join(regex) if as_string else regex


def findall_partial(string, regex_parts):
    """
    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> result = [i for s, r, i in findall_partial(':', TIME_REGEX_PARTS)]
    >>> asserts.list_equal(result, [2, 5])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('12:15:2', TIME_REGEX_PARTS)]
    >>> asserts.list_equal(result, [(0, '12:15:2[0-9]')])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('18:2', TIME_REGEX_PARTS)]
    >>> asserts.list_equal(result, [(0, '18:2[0-9]:[0-5][0-9]'), (3, '[0-2][0-9]:18:2[0-9]')])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('59:1', TIME_REGEX_PARTS)]
    >>> asserts.list_equal(result, [(3, '[0-2][0-9]:59:1[0-9]')])
    """
    for index in range(0, len(regex_parts) - len(string) + 1):  # noqa
        regex = regex_parts[index:index + len(string)]
        match = re.search(''.join(regex), string)
        if match:
            yield string, regex_parts, index


def from_path_patterns(patterns, regex=False):
    """
    Return patterns compiled to regular expressions, if necessary.

    If `regex` is set to False, then any string pattern will be converted from the unix-style
    wildcard to the regular expression equivalent using :func:`fnatmch.translate`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns('*.txt')],
    ...     ['.*\\.txt\\Z(?ms)'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns(['text', 'something*'], '*.py')],
    ...     ['text\\Z(?ms)', 'something.*\\Z(?ms)'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns([re.compile('a?c'), 'fo?'])],
    ...     ['a?c', 'fo.\\Z(?ms)'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns([re.compile('a?c'), 'foo?'], regex=True)],
    ...     ['a?c', 'foo?'])
    """
    return [
        p if hasattr(p, 'match') else re.compile(p if regex else fnmatch.translate(p))
        for p in chain(patterns)
    ]
