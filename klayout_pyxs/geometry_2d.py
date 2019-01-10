# -*- coding: utf-8 -*-
""" pyxs.geometry_2d.py

(C) 2017 Dima Pustakhod and contributors
"""

from klayout_pyxs import pya_EP
from klayout_pyxs import Polygon
from klayout_pyxs.layer_parameters import string_to_layer_info
from klayout_pyxs.misc import info, print_info, int_floor, make_iterable


class EdgeProcessor(pya_EP):
    """
    Problems: empty polygon arrays produce errors with boolean_to_polygon
    because RBA does not recognize the empty array as an array of polygons
    and then there is an ambiguity between the edge-input and polygon input
    variants. Thus this extension which checks for empty input and performs
    some default operation
    """
    def boolean_p2p(self, pa, pb, mode, rh=True, mc=True):
        """ Boolean operation for a set of given polygons, creating polygons

        This method computes the result for the given boolean operation on
        two sets of polygons. This method produces polygons on output and
        allows to fine-tune the parameters for that purpose.

        This is a convenience method that bundles filling of the edges,
        processing with a Boolean operator and puts the result into an output
        vector.

        Parameters
        ----------
        pa : list of Polygon
            the input polygons (first operand)
        pb : list of Polygon
            the input polygons (second operand)
        mode : int
            one of self.ModeANotB, self.ModeAnd, self.ModeBNotA,
            self.ModeOr, self.ModeXor
        rh : bool (optional)
            True, if holes should be resolved into the hull
        mc : bool (optional)
            True, if touching corners should be resolved into less connected
            contours

        Returns
        -------
        res : list of Polygon
            The output polygons

        """
        return super().boolean_p2p(pa, pb, mode, rh, mc)

    def safe_boolean_to_polygon(self, pa, pb, mode, rh=True, mc=True):
        """ Applies boolean operation to two lists of polygons.

        Use of this method is deprecated. Use boolean_p2p instead

        Works safe in case any of input arrays is empty.

        Parameters
        ----------
        pa : list of Polygon
        pb : list of Polygon
        mode : int
        rh : bool (optional)
            resolve_holes
        mc : bool (optional)
            min_coherence

        Returns
        -------
        list of Polygon or []
        """
        n_pa, n_pb = len(pa), len(pb)  # number of polygons in pa and pb

        if n_pa > 0 and n_pb > 0:  # both pa and pb are not empty
            return self.boolean_to_polygon(pa, pb, mode, rh, mc)
        elif mode == self.ModeAnd:  # either pa and pb is empty, mode AND
            return []  # will be empty
        elif mode == self.ModeOr:
            if n_pa > 0:
                return pa
            else:
                return pb
        elif mode == self.ModeXor:
            if n_pa > 0:
                return pa
            else:
                return pb
        elif mode == self.ModeANotB:
            return pa
        elif mode == self.ModeBNotA:
            return pb
        else:
            return []

    def size_to_polygon(self, polygons, dx, dy, mode=2, rh=True, mc=True):
        """ Size the given polygons into polygons

        Use of this method is deprecated. Use size_p2p instead
        """
        return super().size_to_polygon(polygons, dx, dy, mode, rh, mc)

    @print_info(False)
    def size_p2p(self, polygons, dx, dy=0, mode=2, rh=True, mc=True):
        """ Size the given polygons into polygons

        Parameters
        ----------
        polygons : list of Polygon
            The input polygons
        dx : int
            The sizing value in x direction in dbu
        dy : int (optional)
            The sizing value in y direction in dbu
        mode : int (optional)
            The sizing mode. Allowed values from 1 to 5
        rh : bool (optional)
            True, if holes should be resolved into the hull
        mc : bool (optional)
            True, if touching corners should be resolved into less connected
            contours

        Returns
        -------
        res : list of Polygon
            The output polygons

        """
        info('    polys  = {}'.format(polygons))
        info('    dx = {}, dy = {}'.format(dx, dy))
        res = super().size_p2p(polygons, dx, dy, mode, rh, mc)
        info('    EP.size_p2p().res = {}'.format(res))
        return res


EP = EdgeProcessor
ep = EdgeProcessor()


def parse_grow_etch_args(method, into=[], through=[], on=[],
                         mode='square', material_cls=None):
    """
    Parameters
    ----------
    method : str
        'etch|grow'
    into : None or list (optional)
    on : None or list (optional)
    through : None or list (optional)
    mode : str (optional)
        'square|round|octagon'
    material_cls : type (optional)
        into, through, and on lists must contain instances of this type.

    Returns
    -------
    res : tuple
        into : None or list
        through : None or list
        on : None or list
        mode : str
            'square|round|octagon'

    """
    if into:
        into = make_iterable(into)
        for i in into:
            # should be MaterialData @@@
            if not isinstance(i, material_cls):
                raise TypeError("'{}' method: 'into' expects a material "
                                "parameter or an array of such. {} is given"
                                .format(method, type(i)))
    if on:
        on = make_iterable(on)
        for i in on:
            # should be MaterialData @@@
            if not isinstance(i, material_cls):
                raise TypeError("'{}' method: 'on' expects a material "
                                "parameter or an array of such".format(method))
    if through:
        through = make_iterable(through)
        for i in through:
            # should be MaterialData @@@
            if not isinstance(i, material_cls):
                raise TypeError("'{}' method: 'through' expects a material "
                                "parameter or an array of such".format(method))

    if on and (through or into):
        raise ValueError("'on' option cannot be combined with 'into' or "
                         "'through' option")

    if mode not in ('round', 'square', 'octagon'):
        raise ValueError("'{}' method: 'mode' should be 'round', 'square' or "
                         "'octagon'".format(method))

    return into, through, on, mode


class LayoutData(object):
    """ Class to manipulate masks, which is a 2d view.

    Layout data is a list of polygons.

    Attributes
    ----------
    self._polygons : list of Polygon
        In case of XSectionGenerator.layer() object, self._polygons
        contains shapes touching the ruler, top view of the mask
    """
    def __init__(self, polygons, xs):
        """ LayoutData constructor.

        Parameters
        ----------
        polygons : list of Polygon
            list of shapes contained in this LayoutData
        xs : XSectionGenerator

        """
        self._polygons = polygons
        self._xs = xs
        self._ep = ep

    def __str__(self):
        n_poly = self.n_poly

        s = 'LayoutData (n_polygons = {})'.format(n_poly)

        if n_poly > 0:
            s += ':'

        for pi in range(min(2, n_poly)):
            s += '\n    {}'.format(self._polygons[pi])
        return s

    def __repr__(self):
        s = '<LayoutData (n_polygons = {})>'.format(self.n_poly)
        return s

    @property
    def data(self):
        """
        Return
        ------
        data: list of Polygon
            polygons which constitute the mask
        """
        return self._polygons

    @data.setter
    def data(self, polygons):
        """
        Parameters
        ----------
        polygons: list of Polygon
            polygons to be saved in the mask
        """
        self._polygons = polygons

    def add(self, other):
        """ Add more polygons to the layout (OR).

        Parameters
        ----------
        other : LayoutData or list of Polygon

        """
        other_polygons = self._get_polygons(other)
        self._polygons = self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeOr)

    def and_(self, other):
        """ Calculate overlap of the mask with a list of polygons (AND).

        Parameters
        ----------
        other : LayoutData or list of Polygon

        Returns
        -------
        ld : LayoutData
        """
        other_polygons = self._get_polygons(other)
        return LayoutData(self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeAnd),
                          self._xs)

    def inverted(self):
        """ Calculate inversion of the mask.

        Total region is determined by self._xs.background().

        Returns
        -------
        ld : LayoutData
        """
        return LayoutData(self._ep.boolean_p2p(
                self._polygons, [Polygon(self._xs.background())], EP.ModeXor),
            self._xs)

    @print_info(False)
    def load(self, layout, cell, box, layer_spec):
        """ Load all shapes from the layer into self._polygons.

        The shapes are collected from layer defined by layer_spec. Only
        shapes touching the box are loaded. Box is effectively a ruler region.

        Parameters
        ----------
        layout : Layout
            layout
        cell : int
            cell's index
        box : Box
            The box of the ruler, enlarged in both directions.
            Only shapes touching this box will be collected
        layer_spec : str
            layer to be used
        """
        info('LD.load(..., box={}, layer_spec={})'.format(box, layer_spec))

        ls = string_to_layer_info(layer_spec)

        # look up the layer index with a given layer_spec in the current layout
        layer_index = None
        for li in layout.layer_indices():
            info("    li = {}".format(li))
            if layout.get_info(li).is_equivalent(ls):
                info("        layer_index = {}".format(li))
                layer_index = li
                break

        # collect polygons from the specified layer
        # all the shapes from the layout will be saved in self._polygons
        if layer_index is not None:
            info("    iterations:")
            shape_iter = layout.begin_shapes_touching(cell, layer_index, box)
            while not shape_iter.at_end():
                shape = shape_iter.shape()
                if shape.is_polygon() or shape.is_path() or shape.is_box():
                    self._polygons.append(
                            shape.polygon.transformed_cplx(shape_iter.itrans()))
                shape_iter.next()

        n_poly = self.n_poly
        info('    loaded polygon count: {}'.format(n_poly))
        if n_poly > 0:
            info('    loaded polygons:')
        for pi in range(min(2, n_poly)):
            info('        {}'.format(self._polygons[pi]))

        info('LD.load()\n')

    def mask(self, other):
        """ Mask current layout with external list of polygons (AND).

        Parameters
        ----------
        other : LayoutData or list of Polygon

        """
        other_polygons = self._get_polygons(other)
        self._polygons = self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeAnd)

    @property
    def n_poly(self):
        """
        Returns
        -------
        n_poly : int
            number of polygons contained in the mask

        """
        return len(self._polygons)

    def not_(self, other):
        """ Calculate difference with another list of polygons.

        Parameters
        ----------
        other : LayoutData or list of Polygon

        Returns
        -------
        ld : LayoutData
        """
        other_polygons = self._get_polygons(other)
        return LayoutData(self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeANotB),
                          self._xs)

    def or_(self, other):
        """ Calculate sum with another list of polygons (OR).
        Parameters
        ----------
        other : LayoutData or list of Polygon

        Returns
        -------
        ld : LayoutData
        """
        other_polygons = self._get_polygons(other)
        return LayoutData(self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeOr),
                          self._xs)

    def sized(self, dx, dy=None):
        """ Calculate a sized mask.

        Parameters
        ----------
        dx : float
            size change in x-direction in [um]
        dy : float (optional)
            size change in y-direction in [um]. Equals to dx by default.

        Returns
        -------
        ld : LayoutData
        """
        dy = dx if dy is None else dy
        ld = LayoutData(self._ep.size_p2p(self._polygons,
                                          int_floor(dx / self._xs.dbu + 0.5),
                                          int_floor(dy / self._xs.dbu + 0.5)),
                        self._xs)
        return ld

    def sub(self, other):
        """ Substract another list of polygons.

        Parameters
        ----------
        other : LayoutData or list of Polygon

        """
        other_polygons = self._get_polygons(other)
        self._polygons = self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeANotB)

    def transform(self, t):
        """ Transform mask with a transformation.

        Parameters
        ----------
        t : Trans
            transformation to be applied
        """
        self._polygons = [p.transformed(t) for p in self._polygons]

    def xor(self, other):
        """ Calculate XOR with another list of polygons.

        Parameters
        ----------
        other : LayoutData or list of Polygon

        Returns
        -------
        ld : LayoutData
        """
        other_polygons = self._get_polygons(other)
        return LayoutData(self._ep.boolean_p2p(
                self._polygons, other_polygons, EP.ModeXor),
                          self._xs)

    def close_gaps(self):
        """ Close gaps in self._polygons.

        Increase size of all polygons by 1 dbu in all directions.
        """
        sz = 1
        d = self._polygons
        d = self._ep.size_p2p(d, 0, sz)
        d = self._ep.size_p2p(d, 0, -sz)
        d = self._ep.size_p2p(d, sz, 0)
        d = self._ep.size_p2p(d, -sz, 0)
        self._polygons = d

    def remove_slivers(self):
        """ Remove slivers in self._polygons.
        """
        sz = 1
        d = self._polygons
        d = self._ep.size_p2p(d, 0, -sz)
        d = self._ep.size_p2p(d, 0, sz)
        d = self._ep.size_p2p(d, -sz, 0)
        d = self._ep.size_p2p(d, sz, 0)
        self._polygons = d

    @staticmethod
    def _get_polygons(l):
        if isinstance(l, LayoutData):
            return l.data
        elif isinstance(l, (tuple, list)):
            return l
        else:
            raise TypeError('l should be either an instance of LayoutData or '
                            'a list of Polygon. {} is given.'
                            .format(type(l)))