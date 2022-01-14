
import unicodedata
from string import punctuation


def clean(s, keep_accents=False, keep_punctuation=False):
    """
    Method who remove accents and punctuation from a string

    :type s: str
    :type keep_accents: bool
    :type keep_punctuation: bool
    :return: The cleaned string
    """
    if keep_accents is False:
        s = ''.join(
            x for x in unicodedata.normalize('NFKD', s) if unicodedata.category(x)[0] in ('L', 'Z', 'P')
        ).lower()
    if keep_punctuation is False:
        s = s.translate(str.maketrans('', '', punctuation))
    return s


def split(s, seps):
    """
    Method who split the given string to every character given in args
    :param s: The string to be split
    :param seps: An iterable containing all separators
    :return: The split string
    """
    start_index = end_index = 0
    split_str = []
    for char in s:
        if char in seps:
            before = s[start_index:end_index]
            if before:
                split_str.append(before)
            start_index = end_index + 1
        end_index += 1
    if not split_str:
        split_str = [s]
    return split_str
