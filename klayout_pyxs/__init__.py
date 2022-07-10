"""klayout_pyxs.__init__.py

Copyright 2017-2019 Dima Pustakhod

"""
from ._version import __version__

DEBUG = False
HAS_KLAYOUT = False
HAS_PYA = False

try:
    if DEBUG:
        print("Trying to import klayout module... ", end="")
    import importlib

    importlib.import_module("klayout")
    HAS_KLAYOUT = True

    from klayout.db import Box, DPoint, Edge
    from klayout.db import EdgeProcessor as EP_
    from klayout.db import (
        Edges,
        LayerInfo,
        Point,
        Polygon,
        Region,
        SimplePolygon,
        Trans,
    )

    if DEBUG:
        print("found!")
except:
    if DEBUG:
        print("not found!")
    try:
        if DEBUG:
            print("Trying to import pya module... ", end="")
        import pya as klayout

        # For plugin only
        from pya import Action, Application, Box, DPoint, Edge
        from pya import EdgeProcessor as EP_
        from pya import (
            Edges,
            FileDialog,
            LayerInfo,
            MessageBox,
            Point,
            Polygon,
            Region,
            SimplePolygon,
            Trans,
        )

        HAS_PYA = True
        if DEBUG:
            print("found!")
    except:
        if DEBUG:
            print("not found!")
        raise ModuleNotFoundError(
            "Neither pya nor klayout module are not "
            "installed in the current python distribution."
        )


# from .misc import info
# reload(pyxs.misc)
# reload(pyxs.geometry_2d)
# reload(pyxs.geometry_3d)


def _poly_repr(self):
    """Return nice representation of the Polygon instance

    This is useful when printing a list of Polygons
    """
    return f"{self.num_points()} pts: {self.__str__()}"


Polygon.__repr__ = _poly_repr

# info('pyxs.__init__.py loaded')

from klayout_pyxs.pyxs_lib import XSectionScriptEnvironment

__all__ = [
    "XSectionScriptEnvironment",
    "__version__",
]
