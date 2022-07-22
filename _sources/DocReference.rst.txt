.. _DocReference:

PYXS File Reference
===================


This document details the functions available in PYXS scripts. An
introduction is available as a separate document:
:doc:`DocIntro`.

In PYXS scripts, there are basically three kind of functions and
methods:

* Standalone functions which don't require an object. For example
  ``input()`` and ``deposit()``.
* Methods on original layout layers (and in some weaker sense on
  material data objects), i.e. ``invert()`` or ``not_()``.
* Methods on mask data objects, i.e. ``grow()`` and ``etch()``.

Functions
---------

The following standalone functions are available:

.. list-table::
    :widths: 15 70
    :header-rows: 1

    * - Function
      - Description
    * - ``all()``
      - Return a pseudo-mask, covering the whole wafer
    * - ``below(b)``
      - | Configure the lower height of the processing window for
        | backside processing (see below)
    * - ``bulk()``
      - Return a pseudo-material describing the wafer body
    * - ``delta(d)``
      - Configure the accuracy parameter (see ``below()``)
    * - | ``deposit(...)``
        | ``grow()``
        | ``diffuse()``
      - | Deposit material as a uniform sheet. Equivalent to
        | ``all().grow(...)``. Return a material data object
    * - ``depth(d)``
      - | Configure the depth of the processing window or the wafer
        | thickness for backside processing (see below)
    * - ``etch(...)``
      - Uniform etching. Equivalent to ``all.etch(...)``
    * - ``extend(x)``
      - Configure the computation margin (see below)
    * - ``flip()``
      - Start or end backside processing
    * - ``height(h)``
      - Configure the height of the processing window (see below)
    * - ``layer(layer_spec)``
      - | Fetche an input layer from the original layout. Return a
        | layer data object.
    * - ``layers_file(lyp_filename)``
      - | Configure a ``.lyp`` layer properties file to be used on the
        | cross-section layout
    * - ``mask(layout_data)``
      - | Designate the ``layout_data`` object as a litho pattern (mask).
        | This is the starting point for structured grow or etch
        | operations. Return a mask data object.
    * - ``output(layer_spec, material)``
      - Output a material object to the output layout
    * - ``planarize(...)``
      - Planarization

``all()`` method
^^^^^^^^^^^^^^^^

This method delivers a mask data object which covers the whole wafer.
It's used as seed for the global etch and grow function only.

``below()``, ``depth()`` and ``height()`` methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The material operations a performed in a limited processing window,
which extends a certain height over the wafer top surface (``height``),
covers the wafer with a certain depth (``depth``) and extends below the
wafer for backside processing (``below`` parameter). Material cannot grow
outside the space above or below the wafer. Etching cannot happen
deeper than ``depth``. For backside processing, ``depth`` also defines the
wafer thickness.

The parameters can be modified with the respective functions. All
functions accept a value in micrometer units. The default value is
2 micrometers.

``bulk()`` method
^^^^^^^^^^^^^^^^^

This methods returns a material data object which represents the wafer
at it's initial state. This object can be used to represent the
unmodified wafer substrate and can be target of etch operations. Every
call of ``bulk()`` will return a fresh object, so the object needs to be
stored in a variable for later use:

.. code-block:: python

    substrate = bulk()
    mask(layer).etch(0.5, into='substrate')
    output("1/0", substrate)

``delta()`` method
^^^^^^^^^^^^^^^^^^

Due to limitations of the underlying processor which cannot handle
infinitely thin polygons, there is an accuracy limit for the creation
or modification or geometrical regions. The delta parameter will
basically determine that accuracy level and in some cases, for example
the sheet thickness will only be accurate to that level. In addition,
healing or small gaps and slivers during the processing uses the delta
value as a dimension threshold, so shapes or gaps smaller than that
value cannot be produced.

The default value of ``delta`` is 10 database units. To modify the value,
call the ``delta()`` function with the desired delta value in micrometer
units. The minimum value recommended is 2 database unit. That implies
that the accuracy can be increased by using a smaller database unit for
the input layout.

``deposit()`` (``grow()``, ``diffuse()``) methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function will deposit material uniformly. ``grow()`` and ``diffuse()``
are just synonyms. It is equivalent to ``all.grow(...)``. For a
description of the parameters see the ``grow()`` method on the mask data
object.

The ``deposit()`` function will return a material object representing the
deposited material.

``etch()`` method
^^^^^^^^^^^^^^^^^

This function will perform a uniform etch and is equivalent to
``all().etch(...)``. For a description of the parameter see the
"etch()" function on the mask data object.

``extend()`` method
^^^^^^^^^^^^^^^^^^^

To reduce the likelihood of missing important features, the cross
section script will sample the layout in a window around the cut line.
The dimensions of that window are controlled by the ``extend`` parameter.
The window extends the specified value to the left, the right, the start
and end of the cut line.

The default value is 2 micrometers. To catch all relevant input data in
cases where positive sizing values larger than the extend parameter are
used, increase the extend value by calling ``extend(e)`` with the desired
value in micrometer units.

In addition, the ``extend`` parameter determines the extension of an
invisible part left and right of the cross section, which is included
in the processing to reduce border effects. If deposition or etching
happens with dimensions bigger than the extend value, artifacts start
to appear at the borders of the simulation window. The extend value can
then be increased to hide these effects.

``flip()`` method
^^^^^^^^^^^^^^^^^

This function will start backside processing. After this function,
modifications will be applied on the back side of the wafer. Calling
``flip()`` again, will continue processing on the front side.

``layer()`` method
^^^^^^^^^^^^^^^^^^

The layer method fetches a layout layer and prepares a layout data
object for further processing. The ``layer()`` function expects a single
string parameter which encodes the source of the layout data.

The function understands the following variants:

* ``layer("17")``: Layer 17, datatype 0
* ``layer("17/6")``: Layer 17, datatype 6
* ``layer("METAL1")``: layer "METAL1" for formats that support
  named layers (DXF, CIF)
* ``layer("METAL1 (17/0)")``: hybrid specification for GDS
  (layer 17, datatype 0) and "METAL1" for named-layer formats like DXF
  and CIF.

``layers_file()`` method
^^^^^^^^^^^^^^^^^^^^^^^^

This function specifies a layer properties file which will be loaded
when the cross section has been generated. This file specifies colors,
fill pattern and other parameters of the display:

.. code-block:: python

    layers_file("/home/matthias/xsection/lyp_files/cmos1.lyp")

``mask()`` method
^^^^^^^^^^^^^^^^^

The ``mask()`` function designates the given layout data object as a litho
mask. It returns a mask data object which is the starting point for
further ``etch()`` or ``grow()`` operations:

.. code-block:: python

    l1 = layer("1/0")
    metal = mask(l1).grow(0.3)
    output("1/0", metal)

``output()`` method
^^^^^^^^^^^^^^^^^^^

The ``output()`` function will write the given material to the output
layout. The function expects two parameters: an output layer
specification and a material object:

.. code-block:: python

    output("1/0", metal)

The layer specifications follow the same rules than for the ``layer()``
function described above.

``planarize()`` method
^^^^^^^^^^^^^^^^^^^^^^

The ``planarize()`` function removes material of the given kind (``into``
argument) down to a certain level. The level can be determined
numerically or by a stop layer.

The function takes a couple of keyword parameters in the Python notation
(``name=value``), for example:

.. code-block:: python

    planarize(downto=substrate, into=metal)
    planarize(less=0.5, into=[metal, substrate])

The keyword parameters are:

.. list-table::
    :widths: 10 70
    :header-rows: 1

    * - Name
      - Description
    * - ``into``
      - | (mandatory) A single material or an array or materials. The
        | planarization will remove these materials selectively.
    * - ``downto``
      - | Value is a material. Planarization stops at the topmost point
        | of that material. Cannot be used together with ``less`` or ``to``.
    * - ``less``
      - | Value is a micrometer distance. Planarization will remove a
        | horizontal alice of the given material, stopping ``less``
        | micrometers measured from the topmost point of that material
        | before the planarization. Cannot be used together with ``downto``
        | or ``to``.
    * - ``to``
      - | Value is micrometer z value. Planarization stops when reaching
        | that value. The z value is measured from the initial wafer
        | surface. Cannot be used together with ``downto`` or ``less``.


Methods on original layout layers or material data objects
----------------------------------------------------------

The following methods are available for these objects:

.. list-table::
    :widths: 15 60
    :header-rows: 1

    * - Method
      - Description
    * - ``size(s)`` or ``size(x, y)``
      - Isotropic or anisotropic sizing
    * - ``sized(s)`` or ``sized(x, y)``
      - Out-of-place version of ``size()``
    * - ``invert()``
      - Invert a layer
    * - ``inverted()``
      - Out-of-place version of ``invert()``
    * - ``or_(other)``
      - Boolean OR (merging) with another layer
    * - ``and_(other)``
      - Boolean AND (intersection) with another layer
    * - ``xor(other)``
      - Boolean XOR (symmetric difference) with another layer
    * - ``not_(other)``
      - Boolean NOT (difference) with another layer

``size()`` method
^^^^^^^^^^^^^^^^^^^^^^

This method will apply a bias to the layout data. A bias is applied by
shifting the edges to the outside (for positive bias) or the inside
(for negative bias) of the figure.

Applying a bias will increase or reduce the dimension of a figure by
twice the value.

Two versions are available: isotropic or anisotropic sizing. The first
version takes one single value in micrometer units and applies this value
in x and y direction. The second version takes two values for x and y
direction.

The ``size()`` method will modify the layer object (in-place). A
non-modifying version (out-of-place) is ``sized()``.

.. code-block:: python

    l1 = layer("1/0")
    l1.size(0.3)
    metal = mask(l1).grow(0.3)

``sized()`` method
^^^^^^^^^^^^^^^^^^

Same as ``size()``, but returns a new layout data object rather than
modifying it:

.. code-block:: python

    l1 = layer("1/0")
    l1_sized = l1.sized(0.3)
    metal = mask(l1_sized).grow(0.3)
    # l1 can still be used in the original form

``invert()`` method
^^^^^^^^^^^^^^^^^^^

Inverts a layer (creates layout where nothing is drawn and vice versa).
This method modifies the layout data object (in-place):

.. code-block:: python

    l1 = layer("1/0")
    l1.invert()
    metal = mask(l1).grow(0.3)

A non-modifying version (out-of-place) is ``inverted()``.

``inverted()`` method
^^^^^^^^^^^^^^^^^^^^^

Returns a new layout data object representing the inverted source
layout:

.. code-block:: python

    l1 = layer("1/0")
    l1_inv = l1.inverted()
    metal = mask(l1_inv).grow(0.3)
    # l1 can still be used in the original form

``or_()``, ``and_()``, ``xor()``, ``not_()`` methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods perform boolean operations. Their notation is somewhat
unusual but follows the method notation of Python:

.. code-block:: python

    l1 = layer("1/0")
    l2 = layer("2/0")
    one_of_them = l1.xor(l2)

Here is the output of the operations:

.. list-table::
    :widths: 10 10 15 15 15 15
    :header-rows: 1

    * - layer ``a``
      - layer ``b``
      - ``a.or_(b)``
      - ``a.and_(b)``
      - ``a.xor(b)``
      - ``a.not_(b)``
    * - clear
      - clear
      - clear
      - clear
      - clear
      - clear
    * - drawn
      - clear
      - drawn
      - clear
      - drawn
      - drawn
    * - clear
      - drawn
      - drawn
      - clear
      - drawn
      - clear
    * - drawn
      - drawn
      - drawn
      - drawn
      - clear
      - clear


Methods on mask data objects: ``grow()`` and ``etch()``
-------------------------------------------------------

The following methods are available for mask data objects:

.. list-table::
    :widths: 15 60
    :header-rows: 1

    * - Method
      - Description
    * - ``grow(...)``
      - Deposition of material where this mask is present
    * - ``etch(...)``
      - Removal of material where this mask is present

``grow()`` method
^^^^^^^^^^^^^^^^^

This method is important and has a rich parameter set, so it is
described in an individual document here: :doc:`DocGrow`.

``etch()`` method
^^^^^^^^^^^^^^^^^

This method is important and has a rich parameter set, so it is
described in an individual document here: :doc:`DocEtch`.
