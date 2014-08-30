"""
Clipy video downloader utilities
"""


def take_first(values):
    if isinstance(values, str):
        return values

    if values is not None:
        for value in values:
            if value is not None and value != '':
                return value
