"""klayout_pyxs.compat.py

This module imports functions necessary to ensure compatibility with
both 2.7 and 3.7 Python versions.

Copyright 2017-2019 Dima Pustakhod

"""
import sys

major, middle, minor, _, _ = sys.version_info

if major == 2:
    from six.moces import zip
    from six.moves import range
elif major == 3:
    range = range
    zip = zip
else:
    raise OSError("Unsupported python version")


def get_active_cellview_index(view):
    """Read the active cell-view index across KLayout API versions."""
    index = view.active_cellview_index
    return index() if callable(index) else index


def get_application(application_type):
    """Require the application runtime without making module imports GUI-only."""
    application = application_type.instance() if application_type is not None else None
    if application is None:
        raise RuntimeError(
            "PyXS GUI operations require the KLayout application runtime; "
            "the standalone Python package does not provide it."
        )
    return application


def get_main_window(application_type):
    """Require a main window, also available in KLayout's hidden GUI mode (-z)."""
    window = get_application(application_type).main_window()
    if window is None:
        raise RuntimeError(
            "PyXS cross-section generation requires a KLayout main window; "
            "use -z for hidden GUI execution instead of batch mode (-b)."
        )
    return window


__all__ = [
    "range",
    "zip",
    "get_active_cellview_index",
    "get_application",
    "get_main_window",
]
