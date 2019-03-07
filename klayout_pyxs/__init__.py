# coding: utf-8
"""klayout_pyxs.__init__.py

Copyright 2017-2019 Dima Pustakhod

"""

from __future__ import absolute_import
from __future__ import print_function


DEBUG = False
HAS_KLAYOUT = False
HAS_PYA = False

try:
    if DEBUG:
        print('Trying to import klayout module... ', end='')
    import importlib

    importlib.import_module('klayout')
    HAS_KLAYOUT = True

    from klayout.db import Box
    from klayout.db import Edge
    from klayout.db import EdgeProcessor as EP_
    from klayout.db import LayerInfo
    from klayout.db import Point, DPoint
    from klayout.db import Polygon
    from klayout.db import Trans
    from klayout.db import Edges
    from klayout.db import Region
    from klayout.db import SimplePolygon

    if DEBUG:
        print('found!')
except:
    if DEBUG:
        print('not found!')
    try:
        if DEBUG:
            print('Trying to import pya module... ', end='')
        import pya as klayout

        from pya import Box
        from pya import Edge
        from pya import EdgeProcessor as EP_
        from pya import LayerInfo
        from pya import Point, DPoint
        from pya import Polygon
        from pya import Trans
        from pya import Edges
        from pya import Region
        from pya import SimplePolygon

        # For plugin only
        from pya import Action
        from pya import Application
        from pya import FileDialog
        from pya import MessageBox

        HAS_PYA = True
        if DEBUG:
            print('found!')
    except:
        if DEBUG:
            print('not found!')
        raise ModuleNotFoundError(
            'Neither pya nor klayout module are not '
            'installed in the current python distribution.'
        )


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

from klayout_pyxs.pyxs_lib import XSectionScriptEnvironment

__all__ = [
    'XSectionScriptEnvironment'
]
