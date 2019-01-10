# -*- coding: utf-8 -*-
""" pyxs.__init__.py

(C) 2017 Dima Pustakhod and contributors


"""

from pya import Polygon
# from .misc import info
# reload(pyxs.misc)
# reload(pyxs.geometry_2d)
# reload(pyxs.geometry_3d)


def _poly_repr(self):
    return '{} pts: '.format(self.num_points()) + self.__str__()

# Print Polygon coordinates when displayed as a list element
Polygon.__repr__ = _poly_repr

# info('pyxs.__init__.py loaded')
