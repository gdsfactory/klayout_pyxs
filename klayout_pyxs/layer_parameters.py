# -*- coding: utf-8 -*-
"""

Copyright 2017-2019 Dima Pustakhod


Changelog
---------
2019.10.01
    Fix imports from pya/klayout
    Add doctests
2017.xx.xx
    Initial commit
"""
from __future__ import absolute_import
import re

from klayout_pyxs import LayerInfo


def string_to_layer_info_params(layer_spec, return_None=False):
    """ Convert the layer specification into a LayerInfo parameters

    Parameters
    ----------
    layer_spec : str
        format: "l", "l/d", "n(l/d)" or "n".

    Returns
    -------
    res : tuple
        layer (int), data type (int), name (str)

    Examples
    --------
    >>> print(string_to_layer_info_params('1'))
    (1, 0)
    >>> print(string_to_layer_info_params('1/2'))
    (1, 2)
    >>> print(string_to_layer_info_params('a(1/2)'))
    (1, 2, 'a')
    >>> print(string_to_layer_info_params('a'))
    ('a',)
    """
    if re.match(r'^(\d+)$', layer_spec):
        match = re.match(r'^(\d+)$', layer_spec)
        ls = int(match[0]), 0
    elif re.match(r'^(\d+)/(\d+)$', layer_spec):
        match = re.match(r'^(\d+)/(\d+)$', layer_spec)
        ls = int(match[1]), int(match[2])
    elif re.match(r'^(.*)\s*\((\d+)/(\d+)\)$', layer_spec):
        match = re.match(r'^(.*)\s*\((\d+)/(\d+)\)$', layer_spec)
        ls = int(match[2]), int(match[3]), match[1]
    else:
        ls = (layer_spec, )

    if return_None:
        if len(ls) == 1:
            ls = (None, None, ls[0])
        elif len(ls) == 2:
            ls = (ls[0], ls[1], None)

    return ls


def string_to_layer_info(layer_spec):
    """ Convert the layer specification into a LayerInfo structure

    Parameters
    ----------
    layer_spec : str
        format: "l", "l/d", "n(l/d)" or "n".

    Returns
    -------
    ls : LayerInfo
        layer parameters are given by the `layer_spec`.

    Examples
    --------
    >>> string_to_layer_info('1')
    1/0
    >>> string_to_layer_info('1/2')
    1/2
    >>> string_to_layer_info('a(1/2)')
    a (1/2)
    >>> string_to_layer_info('a')
    a
    """
    ls_param = string_to_layer_info_params(layer_spec)
    return LayerInfo(*ls_param)


def main():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    main()
