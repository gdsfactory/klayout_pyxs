#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#

# A feasibility study for a cross section generation using
# boolean operations. See "cmos.pyxs" for a brief description of the
# commands available and some examples.

# TODO: use a much smaller dbu for the simulation to have a really small delta
# the paths used for generating the masks are somewhat too thick
# TODO: the left and right areas are not treated correctly

from __future__ import absolute_import
import math
import os
import re

import klayout_pyxs
from klayout_pyxs.compat import range
from klayout_pyxs.compat import zip

# from importlib import reload
# try:
#     reload(klayout_pyxs.misc)
#     reload(klayout_pyxs.geometry_2d)
#     reload(klayout_pyxs.geometry_3d)
# except:
#     pass

from klayout_pyxs import Application
from klayout_pyxs import MessageBox
from klayout_pyxs import Action
from klayout_pyxs import FileDialog

from klayout_pyxs import Box
from klayout_pyxs import LayerInfo
from klayout_pyxs import Point
from klayout_pyxs import Polygon
from klayout_pyxs import Trans

from klayout_pyxs.utils import print_info, int_floor, make_iterable, info
from klayout_pyxs.geometry_2d import EP, LayoutData, parse_grow_etch_args
from klayout_pyxs.layer_parameters import string_to_layer_info_params
from klayout_pyxs.layer_parameters import string_to_layer_info
from klayout_pyxs.geometry_3d import MaterialLayer, LP, lp, layer_to_tech_str

info('Module pyxs3D_lib.py reloaded')
MIN_EXPORT_LAYER_THICKNESS = 5


class MaterialData3D(object):
    """ Class to operate 3D materials.

    3D material is described by its top view (mask), vertical
    position (elevation), and thickness.

    """
    def __init__(self, layers, xs, delta):
        """
        Parameters
        ----------
        layers : list of geometry_3d.MaterialLayer

        xs: XSectionGenerator
        delta : float
            the intrinsic height (required for mask data because there
            cannot be an infinitely small mask layer (in database units)
        """
        self._layers = []
        self.data= layers
        self._delta = delta
        self._xs = xs
        self._lp = lp

    def __str__(self):
        n_layers = self.n_layers

        s = 'MaterialData3D (n_layers = {}, delta = {})'.format(
            n_layers, self._delta)

        if n_layers > 0:
            s += ':'

        for li in range(min(5, n_layers)):
            s += '\n    {}'.format(str(self._layers[li]))
        return s

    @property
    def data(self):
        """
        Return
        ------
        data: list of MaterialLayer
            layers which constitute the material
        """
        return self._layers

    @data.setter
    def data(self, layers):
        """
        Parameters
        ----------
        layers: list of MaterialLayer
            layers to be saved in the material
        """
        for la, lb in zip(layers[:-1], layers[1:]):
            if la.top > lb.bottom:
                raise ValueError('layers must be a sorted list of non-'
                                 'overlapping layers. layers {} and {} are not '
                                 'sorted and/or overlap.'.format(la, lb))
        self._layers = layers

    def add(self, other):
        """ Add more material layers to the current one (OR).

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        """
        other_layers = self._get_layers(other)
        self._layers = self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeOr)

    def and_(self, other):
        """ Calculate overlap of the material with another material (AND).

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        Returns
        -------
        res : MaterialData33D
        """
        other_layers = self._get_layers(other)
        return MaterialData3D(self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeAnd),
            self._xs, self._delta)

    def inverted(self):
        """ Calculate inversion of the material.

        Total region is determined by self._xs.background().

        Returns
        -------
        res : MaterialData3D
        """
        return MaterialData3D(self._lp.boolean_l2l(
            self._layers,
            [MaterialLayer(
                LayoutData([Polygon(self._xs.background())], self._xs),
                - (self._xs.depth_dbu + self._xs.below_dbu),
                self._xs.depth_dbu + self._xs.below_dbu + self._xs.height_dbu)],
            EP.ModeXor),
            self._xs, self._delta)

    def mask(self, other):
        """ Mask material with another material (AND).

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        """
        other_layers = self._get_layers(other)
        self._layers = self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeAnd)

    @property
    def n_layers(self):
        """
        Returns
        -------
        n_layers : int
            number of layers contained in the material

        """
        return len(self._layers)

    def not_(self, other):
        """ Calculate difference with another material.

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        Returns
        -------
        res : MaterialData3D
        """
        other_layers = self._get_layers(other)
        return MaterialData3D(self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeANotB), self._xs, self._delta)

    def or_(self, other):
        """ Calculate sum with another material (OR).

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        Returns
        -------
        res : MaterialData3D
        """
        other_layers = self._get_layers(other)
        return MaterialData3D(self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeOr), self._xs, self._delta)

    def sized(self, dx, dy=None):
        """ Calculate material with a sized masks.

        Parameters
        ----------
        dx : float
            size change in x-direction in [um]
        dy : float (optional)
            size change in y-direction in [um]. Equals to dx by default.

        Returns
        -------
        res : MaterialData3D
        """
        dy = dx if dy is None else dy

        new_layers = []
        for l in self._layers:
            ld = l.mask.sized(dx, dy)
            new_layers.append(MaterialLayer(ld, l.bottom, l.thickness))

        return MaterialData3D(new_layers, self._xs, self._delta)

    def sub(self, other):
        """ Substract another material.

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        """
        other_layers = self._get_layers(other)
        self._layers = self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeANotB)

    def transform(self, t):
        """ Transform material masks with a transformation.

        Parameters
        ----------
        t : Trans
            transformation to be applied
        """
        for l in self._layers:
            l.mask.data = [p.transformed(t) for p in l.mask.data]

    def xor(self, other):
        """ Calculate XOR with another material.

        Parameters
        ----------
        other : MaterialData3D or list of MaterialLayer

        Returns
        -------
        res : MaterialData3D
        """
        other_layers = self._get_layers(other)
        return MaterialData3D(self._lp.boolean_l2l(
            self._layers, other_layers, LP.ModeXor), self._xs, self._delta)

    def close_gaps(self):
        """ Close gaps in the polygons of the masks.

        Increase size of all polygons by 1 dbu in all directions.
        """
        sz = 1

        for l in self._layers:
            d = l.mask.data
            d = self._lp.size_p2p(d, 0, sz)
            d = self._lp.size_p2p(d, 0, -sz)
            d = self._lp.size_p2p(d, sz, 0)
            d = self._lp.size_p2p(d, -sz, 0)
            l.mask.data = d

    def remove_slivers(self):
        """ Remove slivers in the polygons of the masks.
        """
        sz = 1
        for l in self._layers:
            d = l.mask.data
            d = self._lp.size_p2p(d, 0, -sz)
            d = self._lp.size_p2p(d, 0, sz)
            d = self._lp.size_p2p(d, -sz, 0)
            d = self._lp.size_p2p(d, sz, 0)
            l.mask.data = d

    def grow(self, z, xy=0.0, into=[], on=[], through=[],
             mode='square', buried=None, taper=None, bias=None):
        """
        Parameters
        ----------
        z : float
            grow height in [um]
        xy : float
            mask extension in [um]
        mode : str
            'round|square|octagon'. The profile mode.
        taper : float
            The taper angle. This option specifies tapered mode and cannot
            be combined with :mode.
        bias : float
            Adjusts the profile by shifting it to the interior of the figure.
            Positive values will reduce the line width by twice the value.
        on : list of MaterialData3D (optional)
            A material or an array of materials onto which the material is
            deposited (selective grow). The default is "all". This option
            cannot be combined with ":into". With ":into", ":through" has the
            same effect than ":on".
        into : list of MaterialData3D (optional)
            Specifies a material or an array of materials that the new
            material should consume instead of growing upwards. This will
            make "grow" a "conversion" process like an implant step.
        through : list of MaterialData3D (optional)
            To be used together with ":into". Specifies a material or an array
            of materials to be used for selecting grow. Grow will happen
            starting on the interface of that material with air, pass
            through the "through" material (hence the name) and consume and
            convert the ":into" material below.
        buried : float
            Applies the conversion of material at the given depth below the
            mask level. This is intended to be used together with :into
            and allows modeling of deep implants. The value is the depth
            below the surface.

        Returns
        -------
        res : MaterialData3D
            grown material
        """

        # parse the arguments
        into, through, on, mode = parse_grow_etch_args(
            'grow', MaterialData3D,
            into=into, on=on, through=through, mode=mode)

        # produce the geometry of the new material
        layers = self.produce_geom('grow', xy, z,
                                   into, through, on,
                                   taper, bias, mode, buried)

        # prepare the result
        res = MaterialData3D(layers, self._xs, self._delta)

        # consume material
        if into:
            for i in into:  # i is MaterialData3D
                i.sub(res)
                i.remove_slivers()
        else:
            self._xs.air().sub(res)  # self._xs.air() is MaterialData3D
            self._xs.air().remove_slivers()
        return res

    def etch(self, z, xy=0.0, into=[], through=[], mode='square',
             taper=None, bias=None, buried=None):
        """

        Parameters
        ----------
        z : float
            etch depth in [um]
        xy : float (optional)
            mask extension, lateral in [um]
        mode : str
            'round|square|octagon'. The profile mode.
        taper :	float
            The taper angle. This option specifies tapered mode and cannot
            be combined with mode.
        bias : float
            Adjusts the profile by shifting it to the interior of the
            figure. Positive values will reduce the line width by twice
            the value.
        into :	list of MaterialData3D (optional)
            A material or an array of materials into which the etch is
            performed. This specification is mandatory.
        through : list of MaterialData3D (optional)
            A material or an array of materials which form the selective
            material of the etch. The etch will happen only where this
            material interfaces with air and pass through this material
            (hence the name).
        buried : float
            Applies the etching at the given depth below the surface. This
            option allows to create cavities. It specifies the vertical
            displacement of the etch seed and there may be more applications
            for this feature.

        """
        # parse the arguments
        into, through, on, mode = parse_grow_etch_args(
            'etch', MaterialData3D,
            into=into, through=through, on=None, mode=mode)

        if not into:
            raise ValueError("'etch' method: requires an 'into' specification")

        # prepare the result
        layers = self.produce_geom('etch', xy, z,
                                   into, through, on,
                                   taper, bias, mode, buried)

        # produce the geometry of the etched material
        res = MaterialData3D(layers, self._xs, self._delta)

        # consume material and add to air
        if into:
            for i in into:  # i is MaterialData3D
                i.sub(res)
                i.remove_slivers()

        self._xs.air().add(res)  # self._xs.air() is MaterialData3D
        self._xs.air().close_gaps()

    @print_info(True)
    def produce_geom(self, method, xy, z,
                     into, through, on,
                     taper, bias, mode, buried):
        """

        method : str
        xy : float
            mask extension, lateral in [um]
        z : float
            vertical material size in [um]
        into : list of MaterialData3D
        through : list of MaterialData3D
        on : list of MaterialData3D
        taper : float
        bias : float
        mode : str
            'round|square|octagon'
        buried : float

        Returns
        -------
        layers : list of MaterialLayer
        """
        info('    method={}, xy={}, z={}, \n'
             '    into={}, through={}, on={}, \n'
             '    taper={}, bias={}, mode={}, buried={})'
             .format(method, xy, z, into, through, on, taper, bias, mode,
                     buried))

        prebias = bias or 0.0

        if xy < 0.0:
            xy = -xy
            prebias += xy

        '''
        if taper:
            d = z * math.tan(math.pi / 180.0 * taper)
            prebias += d - xy
            xy = d
        '''
        # determine the "into" material by joining the layers of all "into"
        # materials or taking air's layers if required.
        # Finally we get a into_layers : list of MaterialLayer
        if into:
            into_layers = []
            for i in into:
                info('    i = {}'.format(i))
                if len(into_layers) == 0:
                    into_layers = i.data
                else:
                    into_layers = self._lp.boolean_l2l(
                        i.data, into_layers, LP.ModeOr)
        else:
            # when deposit or grow is selected, into_layers is self._xs.air()
            into_layers = self._xs.air().data

        info('    into_layers = {}'.format(into_layers))

        # determine the "through" material by joining the layers of all
        # "through" materials
        # Finally we get a thru_layers : list of MaterialLayer
        if through:
            thru_layers = []
            for t in through:
                if len(thru_layers) == 0:
                    thru_layers = t.data
                else:
                    thru_layers = self._lp.boolean_l2l(
                        t.data, thru_layers, LP.ModeOr)
            info('    thru_layers = {}'.format(thru_layers))

        # determine the "on" material by joining the data of all "on" materials
        # Finally we get an on_layers : list of MaterialLayer
        if on:
            on_layers = []
            for o in on:
                if len(on_layers) == 0:
                    on_layers = o.data
                else:
                    on_layers = self._lp.boolean_l2l(
                        o.data, on_layers, LP.ModeOr)
            info('    on_layers = {}'.format(on_layers))

        offset = self._delta
        layers = self._layers
        info('    Seed material to be grown: {}'.format(self))

        '''
        if abs(buried or 0.0) > 1e-6:
            t = Trans(Point(
                    0, -_int_floor(buried / self._xs.dbu + 0.5)))
            d = [p.transformed(t) for p in d]
        '''

        # in the "into" case determine the interface region between
        # self and into
        if into or through or on:
            # apply an artificial sizing to create an overlap before
            if offset == 0:
                offset = self._xs.delta_dbu / 2
                layers = self._lp.size_l2l(layers, 0, dz=offset)

            if on:
                layers = self._lp.boolean_l2l(layers, on_layers, EP.ModeAnd)
            elif through:
                layers = self._lp.boolean_l2l(layers, thru_layers, EP.ModeAnd)
            else:
                layers = self._lp.boolean_l2l(layers, into_layers, EP.ModeAnd)
        info('    overlap layers = {}'.format(layers))

        pi = int_floor(prebias / self._xs.dbu + 0.5)
        info('    pi = {}'.format(pi))
        if pi < 0:
            layers = self._lp.size_l2l(layers, -pi, dy=-pi, dz=0)
        elif pi > 0:
            raise NotImplementedError('pi > 0 not implemented yet')
            # apply a positive prebias by filtering with a sized box
            dd = []
            for p in d:
                box = p.bbox()
                if box.width > 2 * pi:
                    box = Box(box.left + pi, box.bottom,
                                  box.right - pi, box.top)

                    for pp in self._ep.boolean_p2p([Polygon(box)], [p],
                                                   EP.ModeAnd):
                        dd.append(pp)
            d = dd

        xyi = int_floor(xy / self._xs.dbu + 0.5)  # size change in [dbu]
        zi = int_floor(z / self._xs.dbu + 0.5) - offset  # height in [dbu]
        info('    xyi = {}, zi = {}'.format(xyi, zi))

        if taper:
            raise NotImplementedError('taper option is not supported yet')
            # d = self._ep.size_p2p(d, xyi, zi, 0)
        elif xyi <= 0:
            layers = self._lp.size_l2l(layers, 0, dy=0, dz=zi)
            # d = self._ep.size_p2p(d, 0, zi)
        elif mode == 'round':
            # same as square for now
            layers = self._lp.size_l2l(layers, xyi, dy=xyi, dz=zi)

            # raise NotImplementedError('round option is not supported yet')
            # emulate "rounding" of corners by performing soft-edged sizes
            # d = self._ep.size_p2p(d, xyi / 3, zi / 3, 1)
            # d = self._ep.size_p2p(d, xyi / 3, zi / 3, 0)
            # d = self._ep.size_p2p(d, xyi - 2 * (xyi / 3), zi - 2 * (zi / 3), 0)
        elif mode == 'square':
            layers = self._lp.size_l2l(layers, xyi, dy=xyi, dz=zi)
        elif mode == 'octagon':
            raise NotImplementedError('octagon option is not supported yet')
            # d = self._ep.size_p2p(d, xyi, zi, 1)

        if through:
            layers = self._lp.boolean_l2l(layers, thru_layers, LP.ModeANotB)

        info('    layers before and with into:'.format(layers))
        layers = self._lp.boolean_l2l(layers, into_layers, LP.ModeAnd)
        info('    layers after and with into:'.format(layers))

        info('    final layers = {}'.format(layers))
        if None:
            # remove small features
            # Hint: this is done separately in x and y direction since that is
            # more robust against snapping distortions
            layers = self._lp.size_p2p(layers, 0, self._xs.delta_dbu / 2)
            layers = self._lp.size_p2p(layers, 0, -self._xs.delta_dbu)
            layers = self._lp.size_p2p(layers, 0, self._xs.delta_dbu / 2)
            layers = self._lp.size_p2p(layers, self._xs.delta_dbu / 2, 0)
            layers = self._lp.size_p2p(layers, -self._xs.delta_dbu, 0)
            layers = self._lp.size_p2p(layers, self._xs.delta_dbu / 2, 0)

        return layers

    @staticmethod
    def _get_layers(m):
        if isinstance(m, MaterialData3D):
            return m.data
        elif isinstance(m, (tuple, list)):
            return m
        else:
            raise TypeError('m should be either an instance of MaterialData3D'
                            ' or a list of MaterialLayer. {} is given.'
                            .format(type(m)))


class XSectionGenerator(object):
    """ The main class that creates a cross-section file

    Attributes
    ----------
    _lp : LayerProcessor

    """
    def __init__(self, file_path):
        """
        Parameters
        ----------
        file_path : str
        """
        # TODO: adjust this path:
        self._file_path = file_path
        self._lyp_file = None
        self._lp = lp
        self._flipped = False
        self._box_dbu = None  # pya.Box
        self._air, self._air_below = None, None
        self._delta, self._extend = 1, None
        self._height, self._depth, self._below = None, None, None
        self._thickness_scale_factor = 1
        self._target_gds_file_name = ''
        self._target_tech_file_name = ''
        self._tech_str = ''

        self.set_output_parameters(filename="3d_xs.gds")

    def layer(self, layer_spec):
        """ Fetches an input layer from the original layout.

        Parameters
        ----------
        layer_spec : str

        Returns
        -------
        ld : LayerData
        """
        ld = LayoutData([], self)  # empty

        # collect shapes from the corresponding layer touching
        # extended self._box_dbu into ld._polygons
        ld.load(self._layout, self._cell,
                self._box_dbu.enlarged(Point(self._extend, self._extend)),
                layer_spec)

        return ld

    @print_info(True)
    def mask(self, layer_data):
        """ Designates the layout_data object as a litho pattern (mask).

        This is the starting point for structured grow or etch operations.

        Parameters
        ----------
        layer_data : LayoutData

        Returns
        -------
        MaskData
        """
        info('    layer_data = {}'.format(layer_data))
        mask = layer_data.and_([Polygon(self._box_dbu)])
        info('    mask = {}'.format(mask))
        return self._mask_to_seed_material(mask)

    # @property
    def air(self):
        """ Return a material describing the air above

        Return
        ------
        air : MaterialData3D
        """
        return self._air

    # @property
    def bulk(self):
        """ Return a material describing the wafer body

        Return
        ------
        bulk : MaterialData3D
        """
        return MaterialData3D(self._bulk.data, self, self._delta)

    @print_info(True)
    def output(self, layer_spec, material, color=None):
        """ Outputs a material object to the output layout

        Parameters
        ----------
        layer_spec : str
            layer specification
        material : MaterialData3D
        """
        if not isinstance(material, MaterialData3D):
            raise TypeError("'output' method: second parameter must be "
                            "a material object (MaterialData3D). {} is given"
                            .format(type(material)))

        # confine the shapes to the region of interest
        # info('    roi = {}'.format(self._roi))
        # info('    material = {}'.format(material))
        export_layers = self._lp.boolean_l2l(self._roi, material.data,
                                             LP.ModeAnd)
        info('    layers to export = {}'.format(export_layers))
        l, data_type, name = string_to_layer_info_params(layer_spec, True)
        # info('{}, {}, {}'.format(l, data_type, name))

        name = name if name else ''

        for i, layer in enumerate(export_layers):
            layer_not_empty = False
            layer_no = l + i
            if layer.thickness < MIN_EXPORT_LAYER_THICKNESS:
                continue  # next layer in the material

            ls = LayerInfo(layer_no, data_type, '{} ({}-{})'
                           .format(name, layer.bottom, layer.top))
            li = self._target_layout.insert_layer(ls)
            shapes = self._target_layout.cell(self._target_cell).shapes(li)
            for polygon in layer.mask.data:
                # info('S = {}, S_box = {}'
                #      .format(polygon.area(), polygon.bbox().area()))
                if polygon.area() > 0.001 * polygon.bbox().area():
                    layer_not_empty = True
                    shapes.insert(polygon)

            if layer_not_empty:
                self._tech_str += layer_to_tech_str(layer_no, layer,
                                                    name=name, color=color)

        # info('    {}'.format(self._tech_str[0:150]))

    @print_info(True)
    def all(self):
        """ A pseudo-mask, covering the whole wafer

        Return
        ------
        res : MaterialData3D
        """
        res = self._mask_to_seed_material(
            LayoutData([Polygon(self._box_dbu)], self))
        info('    result: {}'.format(res))
        return res

    def flip(self):
        """ Start or end backside processing

        """
        self._air, self._air_below = self._air_below, self._air
        self._flipped = not self._flipped

    def diffuse(self, *args, **kwargs):
        """ Same as deposit()
        """
        return self.all().grow(*args, **kwargs)

    def deposit(self, *args, **kwargs):
        """ Deposits material as a uniform sheet.

        Equivalent to all.grow(...)

        Return
        ------
        res : MaterialData3D
        """
        return self.all().grow(*args, **kwargs)

    def grow(self, *args, **kwargs):
        """ Same as deposit()
        """
        return self.all().grow(*args, **kwargs)

    def etch(self, *args, **kwargs):
        """ Uniform etching

        Equivalent to all.etch(...)

        """
        return self.all().etch(*args, **kwargs)

    def planarize(self, into=[], downto=[], less=None, to=None, **kwargs):
        """Planarization
        """

        if not into:
            raise ValueError("'planarize' requires an 'into' argument")

        into = make_iterable(into)
        for i in into:
            # should be MaterialData @@@
            if not isinstance(i, MaterialData3D):
                raise TypeError("'planarize' method: 'into' expects "
                                "a material parameter or an array "
                                "of such")

        downto = make_iterable(downto)
        for i in downto:
            # should be MaterialData @@@
            if not isinstance(i, MaterialData3D):
                raise TypeError("'planarize' method: 'downto' expects "
                                "a material parameter or an array "
                                "of such")

        if less is not None:
            less = int_floor(0.5 + float(less) / self.dbu)

        if to is not None:
            to = int_floor(0.5 + float(to) / self.dbu)

        if downto:
            downto_data = []
            for d in downto:
                if len(downto_data) == 0:
                    downto_data = d.data
                else:
                    downto_data = self._lp.boolean_p2p(
                            d.data, downto_data, LP.ModeOr)

            # determine upper bound of material
            if downto_data:
                raise NotImplementedError('downto not implemented yet')
                for p in downto_data:
                    yt = p.bbox().top
                    yb = p.bbox().bottom
                    to = to or yt
                    if not self._flipped:
                        to = max([to, yt, yb])
                    else:
                        to = min([to, yt, yb])

        elif into and not to:
            raise NotImplementedError('into and not to not implemented yet')
            # determine upper bound of our material
            for i in into:

                for p in i.data:
                    yt = p.bbox().top
                    yb = p.bbox().bottom
                    to = to or yt
                    if not self._flipped:
                        to = max([to, yt, yb])
                    else:
                        to = min([to, yt, yb])

        if to:
            less = less or 0
            if self._flipped:
                removed_box = MaterialLayer(
                    LayoutData(
                        [Polygon(self._box_dbu.enlarged(Point(self._extend,
                                                     self._extend)))], self),
                    - (self.depth_dbu + self.below_dbu),
                    (to + less) + self.depth_dbu + self.below_dbu)

            else:
                removed_box = MaterialLayer(
                    LayoutData(
                        [Polygon(self._box_dbu.enlarged(Point(self._extend,
                                                     self._extend)))], self),
                    to - less, self.height_dbu - (to - less))

            rem = MaterialData3D([], self, self._delta)
            for i in into:
                rem.add(i.and_([removed_box]))
                i.sub([removed_box])

            self.air().add(rem)
            self.air().close_gaps()

    def set_thickness_scale_factor(self, factor):
        """Configures layer thickness scale factor to have better proportions

        Parameters
        ----------
        factor : float
        """
        self._thickness_scale_factor = factor

    def set_output_parameters(self, filename=None, format=None):
        if filename:
            self._target_gds_file_name = filename
            self._target_tech_file_name = filename + "_tech"

    def set_delta(self, x):
        """Configures the accuracy parameter
        """
        self._delta = int_floor(x / self._dbu + 0.5)
        info('XSG._delta set to {}'.format(self._delta))

    @property
    def delta_dbu(self):
        return self._delta

    def set_height(self, x):
        """ Configures the height of the processing window

        Parameters
        ----------
        x : float
            height in [um]

        """
        self._height = int_floor(x / self._dbu + 0.5)
        info('XSG._height set to {}'.format(self._height))
        self._update_basic_regions()

    @property
    def height_dbu(self):
        return self._height

    def set_depth(self, x):
        """ Configures the depth of the processing window
        or the wafer thickness for backside processing (see `below`)

        Parameters
        ----------
        x : float
            depth of the wafer in [um]
        """
        self._depth = int_floor(x / self._dbu + 0.5)
        info('XSG._depth set to {}'.format(self._depth))
        self._update_basic_regions()

    @property
    def depth_dbu(self):
        return self._depth

    def set_below(self, x):
        """ Configures the lower height of the processing window for backside processing

        Parameters
        ----------
        x : float
            depth below the wafer in [um]

        """
        self._below = int_floor(x / self._dbu + 0.5)
        info('XSG._below set to {}'.format(self._below))
        self._update_basic_regions()

    @property
    def below_dbu(self):
        return self._below

    def set_extend(self, x):
        """ Set the extend of the computation region

        Parameters
        ----------
        x : float
            extend in [um]
        """
        self._extend = int_floor(x / self._dbu + 0.5)
        self._update_basic_regions()

    @property
    def extend_dbu(self):
        return self._extend

    @property
    def width_dbu(self):
        """ Box size along the major flat (x-direction).

        Returns
        -------
        width : int
        """
        return self._box_dbu.width()

    @property
    def breadth_dbu(self):
        """ Box size perpendicular to major flat (y-direction)

        Returns
        -------
        breadth : int
        """
        return self._box_dbu.height()

    def background(self):
        """ This is used in inverted() method.

        Returns
        -------
        res : Box
            The extended box including the ruler.
        """
        # x1, y1 = self._line_dbu.p1.x, self._line_dbu.p1.y
        # x2, y2 = self._line_dbu.p2.x, self._line_dbu.p2.y
        # if x2 < x1:
        #     x1, x2 = x2, x1

        # if y2 < y1:
        #     y1, y2 = y2, y1

        # x1 -= self._extend
        # y1 -= self._extend
        # x2 += self._extend
        # y2 += self._extend
        # return pya.Box(pya.Point(x1 - self._delta * 5, y1 - self._delta * 5),
        #                pya.Point(x2 + self._delta * 5, y2 + self._delta * 5))

        # Since we will be inverting only masks, we can simply return a box
        # to be exported to 3D.
        return self._box_dbu  # TODO: return an extended box

    @property
    def dbu(self):
        """
        Returns
        -------
        dbu : float
            Database unit
        """
        return self._dbu

    def layers_file(self, lyp_file):
        """Configures a .lyp layer properties file to be used on the
        cross-section layout

        Parameters
        ----------
        lyp_file : str
            path to the lyp file
        """
        self._lyp_file = lyp_file

    @print_info(False)
    def run(self):
        """ The basic generation method
        """

        if not self._setup():
            return None

        self._update_basic_regions()

        text = None
        with open(self._file_path) as file:
            text = file.read()

        if not text:
            MessageBox.critical("Error",
                                "Error reading file #{self._file_path}",
                                MessageBox.b_ok())
            return None

        # prepare variables to be visible in the script
        locals_ = dir(self)
        locals_dict = {}
        for attr in locals_:
            if attr[0] != '_':
                locals_dict.update({attr: getattr(self, attr)})

        try:
            exec(text, locals_dict)
        except Exception as e:
            # For development
            # print(e.__traceback__.)
            # print(dir(e))
            MessageBox.critical("Error", str(e), MessageBox.b_ok())
            # pass
            return None

        Application.instance().main_window().cm_lv_add_missing()  # @@@
        if self._lyp_file:
            self._target_view.load_layer_props(self._lyp_file)
        self._target_view.zoom_fit()
        self._target_layout.write(self._target_gds_file_name)

        info('    len(bulk.data) = {}'.format(len(self._bulk.data)))
        self._tech_str = '# This file was generated automatically by pyxs.\n\n'\
                         + layer_to_tech_str(255, self._bulk.data[0],
                                             'Substrate') + self._tech_str
        with open(self._target_tech_file_name, 'w') as f:
            f.write(self._tech_str)

        return None

    @print_info(True)
    def _mask_to_seed_material(self, mask):
        """ Convert mask to a seed material for growth / etch operations.

        Parameters
        ----------
        mask: LayoutData
            top view of the region to be grown / etched

        Return
        ------
        seed : MaterialData3D
            Thin seed material to be used in geometry generation.
        """
        info('    mask = {}'.format(mask))

        mask_material = [MaterialLayer(mask, -(self._depth + self._below),
                                       self._depth + self._below + self._height)]
        info('    mask material = {}'.format(mask))

        air = self._air.data
        info('    air =        {}'.format(air))

        air_sized = self._lp.size_l2l(air, 0, 0, self._delta)
        info('    air sized =  {}'.format(air_sized))

        # extended air minus air
        air_border = self._lp.boolean_l2l(air_sized, air, LP.ModeANotB)
        info('    air_border = {}'.format(air_border))

        # overlap of air border and mask layer
        seed_layers = self._lp.boolean_l2l(air_border, mask_material,
                                           EP.ModeAnd)

        info('    seed_layers= {}'.format(seed_layers))

        seed = MaterialData3D(seed_layers, self, self._delta)

        return seed

    @print_info(False)
    def _update_basic_regions(self):

        h = self._height  # height above the wafer
        d = self._depth  # thickness of the wafer
        b = self._below  # distance below the wafer

        # w = self._line_dbu.length()  # length of the ruler
        e = self._extend  # extend to the sides

        # TODO: add extend to the basic regions
        self._area = [MaterialLayer(LayoutData([Polygon(self._box_dbu)], self),
                                   -(b+d), (b+d+h))]  # Box(-e, -(d+b), w+e, h)
        self._roi = [MaterialLayer(LayoutData([Polygon(self._box_dbu)], self),
                                   -(b+d), (b+d+h))]  # Box(0, -(d + b), w, h)

        self._air = MaterialData3D(
            [MaterialLayer(LayoutData([Polygon(self._box_dbu)], self), 0, h)],
            self, 0)
        self._air_below = MaterialData3D(
            [MaterialLayer(LayoutData([Polygon(self._box_dbu)], self),
                           -(d + b), b)],
            self, 0)

        self._bulk = MaterialData3D(
            [MaterialLayer(LayoutData([Polygon(self._box_dbu)], self), -d, d)],
            self, 0)

        info('    XSG._area:      {}'.format(self._area))
        info('    XSG._roi:       {}'.format(self._roi))
        info('    XSG._air:       {}'.format(self._air))
        info('    XSG._bulk:      {}'.format(self._bulk))
        info('    XSG._air_below: {}'.format(self._air_below))

    @print_info(True)
    def _setup(self):

        # locate the layout
        app = Application.instance()
        view = app.main_window().current_view()  # LayoutView
        if not view:
            MessageBox.critical(
                    "Error", "No view open for creating the cross "
                    "section from", MessageBox.b_ok())
            return False

        # locate the (single) ruler
        rulers = []
        n_rulers = 0
        for a in view.each_annotation():
            # Use only rulers with "plain line" style
            # print(a.style)
            # print(Annotation.StyleLine)
            # if a.style == Annotation.StyleLine:
            rulers.append(a)
            n_rulers += 1

        # if n_rulers == 0 or n_rulers >= 2:
        #     MessageBox.info("No rulers",
        #                         "Number of rulers is not equal to one. "
        #                         "Will be exporting the whole layout",
        #                         pya.MessageBox.b_ok())

        # if n_rulers == 1:
        #     MessageBox.info(
        #             "Box export", "One ruler is present for the cross "
        #             "section line. Will be exporting only shapes in the box",
        #             pya.MessageBox.b_ok())

        cv = view.cellview(view.active_cellview_index())  # CellView
        if not cv.is_valid():
            MessageBox.critical("Error",
                                "The selected layout is not valid",
                                MessageBox.b_ok())
            return False

        self._cv = cv  # CellView
        self._layout = cv.layout()  # Layout
        self._dbu = self._layout.dbu
        self._cell = cv.cell_index  # int

        if n_rulers == 1:
            # get the start and end points in database units and micron
            p1_dbu = Point.from_dpoint(rulers[0].p1 * (1.0 / self._dbu))
            p2_dbu = Point.from_dpoint(rulers[0].p2 * (1.0 / self._dbu))
            self._box_dbu = Box(p1_dbu, p2_dbu)  # box describing the ruler
        else:
            # TODO: choose current cell, not top cell
            top_cell = self._layout.top_cell()
            p1_dbu = (top_cell.bbox().p1 * (1.0 / self._dbu)).dup()
            p1_dbu = top_cell.bbox().p1.dup()
            p2_dbu = (top_cell.bbox().p2 * (1.0 / self._dbu)).dup()
            p2_dbu = top_cell.bbox().p2.dup()
            self._box_dbu = Box(p1_dbu, p2_dbu)  # box describing the top cell

        info('XSG._box_dbu to be used is: {}'.format(self._box_dbu))

        # create a new layout for the output
        cv = app.main_window().create_layout(1)
        cell = cv.layout().add_cell("XSECTION")
        self._target_view = app.main_window().current_view()
        self._target_view.select_cell(cell, 0)
        self._target_layout = cv.layout()
        self._target_layout.dbu = self._dbu
        self._target_cell = cell

        # initialize height and depth
        self._extend = int_floor(2.0 / self._dbu + 0.5)  # 2 um in dbu
        self._delta = 10
        self._height = int_floor(2.0 / self._dbu + 0.5)  # 2 um in dbu
        self._depth = int_floor(2.0 / self._dbu + 0.5)  # 2 um in dbu
        self._below = int_floor(2.0 / self._dbu + 0.5)  # 2 um in dbu

        info('    XSG._dbu is:    {}'.format(self._dbu))
        info('    XSG._extend is: {}'.format(self._extend))
        info('    XSG._delta is:  {}'.format(self._delta))
        info('    XSG._height is: {}'.format(self._height))
        info('    XSG._depth is:  {}'.format(self._depth))
        info('    XSG._below is:  {}'.format(self._below))

        return True


# MENU AND ACTIONS
# ----------------
N_PYXS_SCRIPTS_MAX = 4

pyxs_script_load_menuhandler = None
pyxs_scripts = None


class MenuHandler(Action):
    """ Handler for the load .xs file action
    """
    def __init__(self, title, action, shortcut=None, icon=None):
        """
        Parameters
        ----------
        title : str
        action : callable
        shortcut : str
        icon : str
        """
        self.title = title
        self._action = action
        if shortcut:
            self.shortcut = shortcut
        if icon:
            self.icon = icon

    def triggered(self):
        self._action()


class XSectionMRUAction(Action):
    """ A special action to implement the cross section MRU menu item
    """

    def __init__(self, action):
        """
        Parameters
        ----------
        action : callable
        """
        self._action = action
        self._script = None

    def triggered(self):
        self._action(self.script)

    @property
    def script(self):
        return self._script

    @script.setter
    def script(self, s):
        self._script = s
        self.visible = (s is not None)
        if s:
            self.title = os.path.basename(s)


class XSectionScriptEnvironment(object):
    """ The cross section script environment
    """
    def __init__(self):
        app = Application.instance()
        mw = app.main_window()

        def _on_triggered_callback():
            """ Load pyxs script menu action.

            Load new .pyxs file and run it.
            """
            view = Application.instance().main_window().current_view()
            if not view:
                raise UserWarning("No view open for running the pyxs script")

            filename = FileDialog.get_open_file_name(
                    "Select cross-section script", "",
                    "XSection Scripts (*.pyxs);;All Files (*)")

            # run the script and save it
            if filename.has_value():
                self.run_script(filename.value())
                self.make_mru(filename.value())

        def _XSectionMRUAction_callback(script):
            """ *.pyxs menu action

            Load selected .pyxs file and run it.

            Parameters
            ----------
            script : str
            """
            self.run_script(script)
            self.make_mru(script)

        # Create pyxs submenu in Tools
        menu = mw.menu()
        if not menu.is_valid("tools_menu.pyxs3D_script_group"):
            menu.insert_separator("tools_menu.end", "pyxs3D_script_group")
            menu.insert_menu("tools_menu.end", "pyxs3D_script_submenu", "pyxs3D")

        # Create Load XSectionpy Script item in XSection (py)
        global pyxs_script_load_menuhandler
        pyxs_script_load_menuhandler = MenuHandler(
                "Load pyxs script", _on_triggered_callback)
        menu.insert_item("tools_menu.pyxs3D_script_submenu.end",
                         "pyxs3D_script_load", pyxs_script_load_menuhandler)
        menu.insert_separator("tools_menu.pyxs3D_script_submenu.end.end",
                              "pyxs3D_script_mru_group")

        # Create list of existing pyxs scripts item in pyxs
        self._mru_actions = []
        for i in range(N_PYXS_SCRIPTS_MAX):
            a = XSectionMRUAction(_XSectionMRUAction_callback)
            self._mru_actions.append(a)
            menu.insert_item("tools_menu.pyxs3D_script_submenu.end",
                             "pyxs3D_script_mru{}".format(i), a)
            a.script = None

        # try to save the MRU list to $HOME/.klayout-processing-mru
        i = 0
        home = os.getenv("HOME", None) or os.getenv("HOMESHARE", None)
        global pyxs_scripts
        if pyxs_scripts:
            for i, script in enumerate(pyxs_scripts.split(":")):
                if i < len(self._mru_actions):
                    self._mru_actions[i].script = script
        elif home:
            fn = home + "\\.klayout-pyxs-scripts"
            try:
                with open(fn, "r") as file:
                    for line in file.readlines():
                        match = re.match('<mru>(.*)<\/mru>', line)
                        if match:
                            if i < len(self._mru_actions):
                                self._mru_actions[i].script = match.group(1)
                            i += 1
            except:
                pass

    def run_script(self, filename):
        """ Run .pyxs script

        filename : str
            path to the .pyxs script
        """
        view = Application.instance().main_window().current_view()
        if not view:
            raise UserWarning("No view open for running the pyxs script")

        # cv = view.cellview(view.active_cellview_index())

        XSectionGenerator(filename).run()
        # try:
        #     # print('XSectionGenerator(filename).run()')
        #     XSectionGenerator(filename).run()
        # except Exception as e:
        #     MessageBox.critical("Script failed", str(e),
        #                             MessageBox.b_ok())

    def make_mru(self, script):
        """ Save list of scripts

        script : str
            path to the script to be saved
        """
        # Don't maintain MRU if an external list is provided
        global pyxs_scripts
        if pyxs_scripts:
            return

        # Make a new script list. New script goes first, ...
        scripts = [script]
        # ... the rest are taken from the existing list
        for a in self._mru_actions:
            if a.script != script:
                scripts.append(a.script)

        # make sure the list is filled to the same length
        while len(scripts) < len(self._mru_actions):
            scripts.append(None)

        # update list of actions
        for i in range(len(self._mru_actions)):
            self._mru_actions[i].script = scripts[i]

        # try to save the MRU list to $HOME/.klayout-xsection
        home = os.getenv("HOME", None) or os.getenv("HOMESHARE", None)
        if home:
            fn = home + "\\.klayout-pyxs-scripts"
            with open(fn, "w") as file:
                file.write("<pyxs>\n")
                for a in self._mru_actions:
                    if a.script:
                        file.write("<mru>{}</mru>\n".format(a.script))
                file.write("</pyxs>\n")


if __name__ == '__main__':
    import doctest
    doctest.testmod()
