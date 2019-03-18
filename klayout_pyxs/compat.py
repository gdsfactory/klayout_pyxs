# coding: utf-8
"""klayout_pyxs.compat.py

This module imports functions necessary to ensure compatibility with
both 2.7 and 3.7 Python versions.

Copyright 2017-2019 Dima Pustakhod

"""
import sys

major, middle, minor, _, _ = sys.version_info

if major == 2:
    from six.moves import range
    from six.moces import zip
elif major == 3:
    range = range
    zip = zip
else:
    raise EnvironmentError('Unsupported python version')

__all__ = [
    'range',
    'zip',
]
