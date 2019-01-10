# -*- coding: utf-8 -*-
""" pyxs.geometry_2d.py

(C) 2017 Dima Pustakhod and contributors
"""
from random import random

from .misc import print_info, info
from .geometry_2d import EdgeProcessor, LayoutData



class LayerProcessor(EdgeProcessor):
    """ Class implementing operations on MaterialLayer lists
    """

    def normalize(self, layers):
        """
        Parameters
        ----------
        layers : list of MaterialLayer or empty list
            a list of non-sorted and / or overlapping layers

        Returns
        -------
        res : list of MaterialLayer
            a sorted list of non-overlapping layers
        """
        layers.sort()
        res = self.split_overlapping_z(layers)
        res = self.merge_layers_same_mask(res)

        return res

    @print_info(False)
    def split_overlapping_z(self, layers):
        """
        Parameters
        ----------
        layers : list of MaterialLayer
            a list of non-sorted and / or overlapping layers

        Returns
        -------
        res : list of MaterialLayer
            a sorted list of non-overlapping layers
        """
        info('    layers = {}'.format(layers))
        _check_layer_list_sorted(layers)

        res = []

        while layers:
            la = layers.pop(0)  # first element is the lowest in z
            info('    la = {}'.format(la))
            if not layers:  # la was the only element
                res += [la]
                continue

            lb = layers.pop(0)  # take next element
            info('    lb = {}'.format(lb))
            if la.is_lower(lb, levela='top', levelb='bottom'):
                # a is lower or touching
                # layers is sorted, la will not overlap with other lb
                res += [la]
                layers.insert(0, lb)
                info('    la top < lb btm, la is moved to result, lb is returned')
            elif la.bottom == lb.bottom:
                info('    la btm == lb btm')
                if la.top < lb.top:
                    lb_split = lb.split_by_layer(la)
                    o = MaterialLayer(la.mask.or_(lb_split[0].mask),
                                      la.bottom, la.thickness)
                    layers = [o] + layers

                    # top part of b is inserted to layers, ensuring sorted order
                    i = 0
                    while i < len(layers):
                        if lb_split[1].bottom < layers[i].bottom:
                            layers.insert(i, lb_split[1])
                            break
                        elif lb_split[1].bottom == layers[i].bottom:
                            if lb_split[1].top <= layers[i].top:
                                layers.insert(i, lb_split[1])
                                break
                        i += 1
                    else:
                        layers.append(lb_split[1])
                    info('    la top < lb top, o calculated, added to layers')
                else:
                    # la is the same height as lb
                    # perform OR operation on the LayoutData
                    o = MaterialLayer(la.mask.or_(lb.mask),
                                      la.bottom, la.thickness)
                    layers.insert(0, o)
                    info('    la top == lb top, o calculated, added to layers')
            else:
                info('    la btm < lb btm, lower part of la is result, rest added to layers')
                # lb bottom splits a somewhere (maybe lb top too)
                la_split = la.split_by_layer(lb)

                # bottom sublayer is not overlapping with lb and others
                res.append(la_split[0])
                layers = la_split[1:] + [lb] + layers

        info('    res = {}'.format(res))
        return res

    @print_info(False)
    def boolean_l2l(self, la, lb, mode, rh=True, mc=True):
        """
        Parameters
        ----------
        la : list of MaterialLayer or empty list
            sorted list. layers must not overlap with each other
        lb : list of MaterialLayer or empty list
            sorted list. layers must not overlap with each other
        mode: int
        rh : bool (optional)
            resolve_holes
        mc : bool (optional)
            min_coherence

        Returns
        -------
        list of MaterialLayer or []
        """
        n_la, n_lb = len(la), len(lb)  # number of polygons in pa and pb

        info('    n_la = {}, n_lb = {}, mode = {}'.format(n_la, n_lb, mode))

        ia, ib = 0, 0
        a = la[ia] if la else None
        b = lb[ib] if lb else None
        la_res, lb_res, oa, ob = [], [], [], []
        while a and b:
            info('    a = {}'.format(a))
            info('    b = {}'.format(b))
            if a.is_lower_s(b, 'bottom'):
                info('    a bottom is lower')
                top = min(a.top, b.bottom)
                info('    top = {}'.format(top))
                if top == a.top:  # no overlap
                    info('    a top is lower than b bottom, no overlap')
                    la_res += [a]
                    ia += 1
                    a = None if ia >= len(la) else la[ia]
                    continue
                else:
                    info('    a top is higher than b bottom, overlap')
                    # use part of a from a.bottom to top
                    la_res += [MaterialLayer(a.mask, a.bottom, top-a.bottom)]
                    # overlapping candidate a is a from top to a.top
                    a = MaterialLayer(a.mask, top, a.top-top)
                    continue
            elif b.is_lower_s(a, 'bottom'):
                info('    b is lower')
                top = min(b.top, a.bottom)
                if top == b.top:  # no overlap
                    lb_res += [b]
                    ib += 1
                    b = None if ib >= len(lb) else lb[ib]
                    continue
                else:
                    # use part of b from b.bottom to top
                    lb_res += [MaterialLayer(b.mask, b.bottom, top-b.bottom)]
                    # overlapping candidate b is b from top to b.top
                    b = MaterialLayer(b.mask, top, b.top-top)
                    continue
            else:
                assert a.bottom == b.bottom, 'bottoms must be equal here'
                info('    same bottom')
                if a.is_lower_s(b, 'top') or b.is_lower_s(a, 'top'):
                    top = min(a.top, b.top)
                    if top < b.top:  # a is in the overlap, b is higher
                        info('    b is higher')
                        oa += [a]
                        ob += [MaterialLayer(b.mask, b.bottom, top-b.bottom)]
                        b = MaterialLayer(b.mask, top, b.top-top)  # remaining top
                        ia += 1
                        a = None if ia >= len(la) else la[ia]
                        continue
                    elif top < a.top:  # b is in the overlap, a is higher
                        info('    a is higher')
                        ob += [b]
                        oa += [MaterialLayer(a.mask, a.bottom, top-a.bottom)]
                        a = MaterialLayer(a.mask, top, a.top-top)  # remaining top
                        ib += 1
                        b = None if ib >= len(lb) else lb[ib]
                        continue
                else:
                    assert a.top == b.top, 'tops must be equal here'
                    info('    same top')
                    oa += [a]
                    ob += [b]
                    ia += 1
                    a = None if ia >= len(la) else la[ia]
                    ib += 1
                    b = None if ib >= len(lb) else lb[ib]
                    continue

        if a:
            la_res += [a]
        if b:
            lb_res += [b]

        # add remaining a's and b's
        while ia < len(la) - 1:
            ia += 1
            la_res += [la[ia]]

        while ib < len(lb) - 1:
            ib += 1
            lb_res += [lb[ib]]

        lo_res = []
        for a, b in zip(oa, ob):
            o_polygons = self.boolean_p2p(a.mask.data, b.mask.data,
                                          mode, rh, mc)
            if o_polygons:
                lo_res += [MaterialLayer(LayoutData(o_polygons, a.mask._xs),
                    a.bottom, a.top-a.bottom)]

        info('    la_res = {}'.format(la_res))
        info('    lb_res = {}'.format(lb_res))
        info('    lo_res = {}'.format(lo_res))

        if mode == self.ModeAnd:  # either la and lb is empty, mode AND
            info('    mode AND')
            res = lo_res  # will be empty
        elif mode == self.ModeOr or mode == self.ModeXor:
            info('    mode OR/XOR')
            res = la_res + lo_res + lb_res
        elif mode == self.ModeANotB:
            info('    mode ANotB')
            res = la_res + lo_res
        elif mode == self.ModeBNotA:
            info('    mode BNotA')
            res = lo_res + lb_res
        else:
            res = []

        res = self.normalize(res)
        # res = self.merge_layers_same_z(res)
        # res = self.merge_layers_same_mask(res)
        # res.sort()
        info('    boolean_l2l().res = {}'.format(res))
        return res

    def split_layers_z(self, a, b):
        """ Split two layers if they overlap in z-direction

        Parameters
        ----------
        a : MaterialLayer
        b : MaterialLayer

        Return
        ------
        res : tuple of MaterialLayer
            ab, ao, at, bb, bo, bt. bottom, overlapping and top part of each
            initial layer.

        """
        if not a.is_z_overlapping(b):
            if a.is_lower(b):
                return a, None, None, None, None, b
            else:
                return None, None, a, b, None, None

        overlap_bottom, overlap_top = a.z_overlap(b)
        if a.bottom < overlap_bottom:
            ab_bottom, ab_top = a.bottom, overlap_bottom
        else:
            ab_bottom, ab_top = None, None

        if a.top > overlap_top:
            at_bottom, at_top = overlap_top, a.top
        else:
            at_bottom, at_top = None, None

        if b.bottom < overlap_bottom:
            bb_bottom, bb_top = b.bottom, overlap_bottom
        else:
            bb_bottom, bb_top = None, None

        if b.top > overlap_top:
            bt_bottom, bt_top = overlap_top, b.top
        else:
            bt_bottom, bt_top = None, None

        ab = MaterialLayer(a.mask, ab_bottom, ab_top-ab_bottom) if ab_bottom else None
        at = MaterialLayer(a.mask, at_bottom, at_top-at_bottom) if at_bottom else None
        ao = MaterialLayer(a.mask, overlap_bottom, overlap_top-overlap_bottom)

        bb = MaterialLayer(b.mask, bb_bottom, bb_top-bb_bottom) if bb_bottom else None
        bt = MaterialLayer(b.mask, bt_bottom, bt_top-bt_bottom) if bt_bottom else None
        bo = MaterialLayer(b.mask, overlap_bottom, overlap_top-overlap_bottom)

        return ab, ao, at, bb, bo, bt

    @print_info(False)
    def size_l2l(self, layers, dx, dy=0, dz=0, mode=2, rh=True, mc=True):
        """ Change mask size in each layer by dx and dy.

        Size in z-direction remains unchanged.

        Parameters
        ----------
        layers : list of MaterialLayer
        dx : int
            size increase in x-direction in [dbu]
        dy : int (optional)
            size increase in y-direction in [dbu]
        dz : int (optional)
            size increase in z-direction in [dbu]
        mode : int
        rh : boolean (optional)
        mc : boolean (optional)

        Returns
        -------
        res : layers : list of MaterialLayer
        """
        res = []
        for l in layers:
            sized_polys = self.size_p2p(l.mask.data, dx, dy, mode, rh, mc)
            res.append(MaterialLayer(LayoutData(sized_polys, l.mask._xs),
                                     l.bottom - dz, l.thickness + 2 * dz))

        # Join overlapping layers
        info('    res before normalize = {}'.format(res))
        res = self.normalize(res)
        info('    res after normalize = {}'.format(res))

        return res

    @print_info(False)
    def merge_layers_same_z(self, layers):
        """
        Parameters
        ----------
        layers : list of MaterialLayer

        Returns
        -------
        res : list of MaterialLayer
        """
        n_layers = len(layers)
        res_merged = []

        for i, li in enumerate(layers):
            merged = MaterialLayer(li.mask, li.bottom, li.thickness)
            for j in range(i+1, n_layers):
                lj = layers[j]
                if merged.is_z_same(lj):

                    # perform OR operation on the LayoutData
                    merged = MaterialLayer(merged.mask.or_(lj.mask),
                                           merged.bottom,
                                           merged.thickness)
                    info('    Merged layers b = {}, t = {}'
                         .format(merged.bottom, merged.top))
            res_merged.append(merged)
        return res_merged

    @print_info(False)
    def merge_layers_same_mask(self, layers):
        """
        Parameters
        ----------
        layers : list of MaterialLayer

        Returns
        -------
        res : list of MaterialLayer
        """
        _check_layer_list_sorted(layers)

        res_merged = []

        while layers:
            la = layers.pop(0)
            ib = 0
            while layers and (ib < len(layers)):
                lb = layers[ib]
                if la.top == lb.bottom:
                    if la.mask.data == lb.mask.data:
                        la = MaterialLayer(la.mask, la.bottom,
                                           lb.top - la.bottom)
                        info('    Merged layers ({},{}) and ({}, {})'
                             .format(la.bottom, la.top, lb.bottom, lb.top))
                        layers.pop(ib)
                elif la.top < lb.bottom:
                    # all following lb will be higher
                    res_merged.append(la)
                    break  # go to the next la
                ib += 1
            else:
                res_merged.append(la)
        return res_merged


class MaterialLayer(object):
    def __init__(self, mask, elevation, thickness):
        """
        Parameters
        ----------
        mask : LayoutData
        elevation : int
            z-coordinate of the layer bottom in [dbu]
        thickness : float
            thickness of the layer in [dbu]
        """
        self.mask = mask
        self._bottom = elevation
        self._top = self._bottom
        self.thickness = thickness

    def __lt__(self, other):
        """
        Parameters
        ----------
        other : MaterialLayer
        """
        if self._bottom < other.bottom:
            return True
        elif self._bottom > other.bottom:
            return False
        else:
            return self._top < other.top

    def __str__(self):
        n_edges = ''
        for poly in self.mask.data:
            n_edges += '{}, '.format(poly.num_points())

        s = '<MatLayer (n_polys={}, n_edges=({}), ' \
            'btm = {}, top = {})>'.format(self.mask.n_poly, n_edges[:-2],
                                          self._bottom, self._top)

        return s

    def __repr__(self):
        n_edges = ''
        for poly in self.mask.data:
            n_edges += '{}, '.format(poly.num_points())

        s = '<MatLayer (n_polys={}, n_edges=({}), ' \
            'btm = {}, top = {})>'.format(self.mask.n_poly, n_edges[:-2],
                                          self._bottom, self._top)

        return s

    @property
    def bottom(self):
        return self._bottom

    @property
    def top(self):
        return self._top

    @property
    def thickness(self):
        return self._top - self._bottom

    @thickness.setter
    def thickness(self, t):
        """
        Parameters
        ----------
        t : int
            thickness in [dbu]
        """
        if t <= 0:
            raise ValueError('Material layer thickness must be positive. '
                             '{} is given.'.format(t))
        else:
            self._top = self._bottom + t

    @print_info(False)
    def is_z_overlapping(self, other):
        """ Check two layers for overlap.

        Parameters
        ----------
        other : MaterialLayer

        Returns
        -------
        bool
        """
        info('   self.b, self.t, other.b, other.t = {} {} {} {}'
             .format(self.bottom, self.top, other.bottom, other.top))
        if (self._top <= other.bottom) or (self._bottom >= other.top):
            return False
        else:
            return True

    def is_z_same(self, other):
        return self._bottom == other.bottom and self._top == other.top

    def split(self, z_coords):
        """ Split layer into several layers.

        Parameters
        ----------
        z_coords : list of int

        Returns
        -------
        res : list of MaterialLayer
        """
        z_coords_all = [self.bottom] + z_coords + [self.top]
        res = []

        for b, t in zip(z_coords_all[:-1], z_coords_all[1:]):
            res += [MaterialLayer(self.mask, b, t-b)]

        return res

    def split_by_layer(self, other):

        z_split = []
        if self.bottom < other.bottom < self.top:
            z_split.append(other.bottom)

        if self.bottom < other.top < self.top:
            z_split.append(other.top)

        return self.split(z_split)

    def z_overlap(self, other):
        """ Return overlap points with the other layer.

        self and other must be overlapping.

        Parameters
        ----------
        other : MaterialLayer

        Return
        ------
        res : tuple
            bottom : int or None
            top : int  or None
        """
        bottom = max(self._bottom, other.bottom)
        top = min(self._top, other.top)
        return bottom, top

    def is_lower_s(self, other, levela='bottom', levelb=None):
        """ Compares the location of two layers strictly.

        Parameters
        ----------
        other : MaterialLayer
        levela : str
            'bottom|top'
        levelb : str or None
            'bottom|top'. If None, levela will be used

        Returns
        -------
        bool
        """
        if not levelb:
            levelb = levela

        if getattr(self, levela) < getattr(other, levelb):
            return True
        else:
            return False

    def is_lower(self, other, levela='bottom', levelb=None):
        """ Compares the location of two layers nonstrictly.

        Parameters
        ----------
        other : MaterialLayer
        levela : str
            'bottom|top'
        levelb : str or None
            'bottom|top'. If None, levela will be used

        Returns
        -------
        bool
        """
        if not levelb:
            levelb = levela

        if getattr(self, levela) <= getattr(other, levelb):
            return True
        else:
            return False

    def is_higher(self, other, levela='bottom', levelb=None):
        """ Compares the tops of two layers strictly.

        Parameters
        ----------
        other : MaterialLayer

        Returns
        -------
        bool
        """
        if not levelb:
            levelb = levela

        if getattr(self, levela) > getattr(other, levelb):
            return True
        else:
            return False


def _check_layer_list_sorted(layers):
    for la, lb in zip(layers[:-1], layers[1:]):
        if (la.bottom > lb.bottom) or (
                    (la.bottom == lb.bottom) and (la.top > lb.top)):
            raise ValueError('layers must be a sorted list of '
                             'MaterialLayer. Layers {} and {} are not '
                             'sorted.'.format(la, lb))

@print_info(False)
def layer_to_tech_str(layer_no_gds, layer, name='', color=None, filter=0.0,
                      metal=0, shortcut='', show=True):
    """
    Parameters
    ----------
    layer_no_gds : int
        layer number in the gds file
    layer : MaterialLayer
        layer to be exported
    name : str
        name to be displayed in the legend. If empty, layer number is used.
    color : tuple of float
        r, g, b components of the color in the range [0, 1] each
    filter : float
        layer transparency, from 0 to 1
    metal : float
        Not used at the moment
    shortcut : str
        A digit from 0 to 9. Defines a shortcut from 0 to 9 to toggle the layer
        visibility. Can be pre-pended with any combination of <Alt>, <Ctrl>,
        and <Shift> as modifiers (eg. '<Shift> 0')
    show : bool
        Whether to show layer during rendering

    Returns
    -------
    s : str
        A layer record for the tech file of GDS3D software.

    """
    if name:
        name = '{} ({})'.format(name, layer_no_gds)
    else:
        name = '-- ({})'.format(layer_no_gds)

    if (color is None) or (len(color) not in (3, 4)):
        r, g, b = random(), random(), random()
        a = filter
    elif len(color) == 3:
        r, g, b = color
        a = filter
    elif len(color) == 4:
        r, g, b, a = color

    if not(0 <= r <= 1 and 0 <= g <= 1 and 0 <= b <= 1):
        raise ValueError('Color components must be from 0 to 1. ({}, {}, {})'
                         ' is given'.format(r, g, b))

    if not(0 <= a <= 1):
        raise ValueError('Filter / transparency value must be from 0 to 1. '
                         '{} is given'.format(a))

    s = ''
    s += 'LayerStart: {}\n'.format(name)
    s += 'Layer: {}\n'.format(layer_no_gds)
    s += 'Height: {}\n'.format(layer.bottom)
    s += 'Thickness: {}\n'.format(layer.thickness)

    s += 'Red: {}\nGreen: {}\nBlue: {}\nFilter: {}\n'.format(r, g, b, a)
    s += 'Metal: {}\n'.format(metal)
    s += 'Shortkey: {}\n'.format(shortcut) if shortcut else ''
    s += 'Show: {}\n'.format(int(show))
    s += 'LayerEnd\n\n'
    return s

LP = LayerProcessor
lp = LayerProcessor()
