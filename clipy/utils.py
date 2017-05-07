"""
Clipy video downloader utilities
"""
import urllib


_traditional = [
    (1024 ** 5, 'P'),
    (1024 ** 4, 'T'),
    (1024 ** 3, 'G'),
    (1024 ** 2, 'M'),
    (1024 ** 1, 'K'),
    (1024 ** 0, 'B'),
]


def size(bytes, system=_traditional):
    """Human-readable file size

    Using the traditional system, where a factor of 1024 is used::

    >>> size(10)
    '10B'
    >>> size(100)
    '100B'
    >>> size(1000)
    '1000B'
    >>> size(2000)
    '1K'
    >>> size(10000)
    '9K'
    >>> size(20000)
    '19K'
    >>> size(100000)
    '97K'
    >>> size(200000)
    '195K'
    >>> size(1000000)
    '976K'
    >>> size(2000000)
    '1M'

    Taken from  Martijn Faassen's hurry.filesize
    https://pypi.python.org/pypi/hurry.filesize/
    """
    for factor, suffix in system:
        if bytes >= factor:
            break

    amount = int(bytes / factor)

    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple

    return str(amount) + suffix


def progress_bar(done, total, length=10, bar='#', sep='-'):
    """
    Return a string indicating graphically the percentage of the first argument
    to the second

    >>> progress_bar(3, 6)
    "#####-----"
    """
    fraction = float(done) / total
    bars = int(fraction * length)

    return '{}{}'.format(
        str(bar) * bars,
        str(sep) * (length - bars))


def list_properties(obj):
    """
    Return a list of the object's properties

    .. note:: Does not include callable or private attributes
    """
    return [
        '{}: {}'.format(p, getattr(obj, p, ''))
        for p in dir(obj)
        if not p.startswith('_') and not hasattr(getattr(obj, p, None), '__call__')
    ]


def take_first(values):
    if isinstance(values, str):
        return values

    if values is not None:
        for value in values:
            if value is not None and value != '':
                return value


def get_video_id(video):
    if '/watch' in video:
        parts = urllib.parse.urlsplit(video)
        info = urllib.parse.parse_qs(parts.query)
        vid = take_first(info.get('v'))
        return vid

    return video
