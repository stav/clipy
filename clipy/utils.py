"""
Clipy video downloader utilities
"""
from __future__ import absolute_import, division, print_function, unicode_literals


def take_first(values):
    if values is not None:
        for value in values:
            if value is not None and value != '':
                return value
