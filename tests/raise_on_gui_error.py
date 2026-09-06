"""Turn modal PyXS errors into failing exceptions during hidden-GUI tests."""

import types

import pya

from klayout_pyxs import pyxs3D_lib, pyxs_lib


def critical(title, message, *args):
    raise RuntimeError(f"{title}: {message}")


message_box = types.SimpleNamespace(critical=critical, b_ok=pya.MessageBox.b_ok)
pyxs_lib.MessageBox = message_box
pyxs3D_lib.MessageBox = message_box
