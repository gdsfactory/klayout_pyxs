# coding: utf-8
"""klayout_pyxs.__init__.py

Copyright 2017-2019 Dima Pustakhod

"""
try:
    import klayout as klayout

    from klayout.db import Box
    from klayout.db import Edge
    from klayout.db import EdgeProcessor as EP_
    from klayout.db import LayerInfo
    from klayout.db import Point
    from klayout.db import Polygon
    from klayout.db import Trans


    HAS_KLAYOUT = True
    print('Found klayout module')
except:
    try:
        import pya as klayout

        from pya import Box
        from pya import Edge
        from pya import EdgeProcessor as EP_
        from pya import LayerInfo
        from pya import Point
        from pya import Polygon
        from pya import Trans

        # For plugin only
        from pya import Action
        from pya import Application
        from pya import FileDialog
        from pya import MessageBox

        HAS_PYA = True
        print('Found pya module')
    except:
        raise ModuleNotFoundError(
            'Neither pya nor klayout module are not '
            'installed in the current python distribution'
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
