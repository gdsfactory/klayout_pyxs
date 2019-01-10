# coding: utf-8
"""klayout_pyxs.__init__.py

Copyright 2017-2019 Dima Pustakhod

"""
from pya import Polygon

# from .misc import info
# reload(pyxs.misc)
# reload(pyxs.geometry_2d)
# reload(pyxs.geometry_3d)


def _poly_repr(self):
    """Return nice representation of the Polygon instance

    This is useful when printing a list of Polygons
    """
    return '{} pts: '.format(self.num_points()) + self.__str__()


Polygon.__repr__ = _poly_repr


# info('pyxs.__init__.py loaded')
