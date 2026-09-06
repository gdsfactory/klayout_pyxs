"""Compatibility tests using real KLayout modules and isolated GUI stubs."""

import importlib
import sys
import types
import unittest
from unittest import mock

import pya

import klayout_pyxs
from klayout_pyxs import pyxs_lib
from klayout_pyxs.compat import (
    get_active_cellview_index,
    get_application,
    get_main_window,
)

pyxs3D_lib = importlib.import_module("klayout_pyxs.pyxs3D_lib")


def load_fresh_library(module):
    # reload() retains old globals and can hide the very NameError we test.
    spec = importlib.util.spec_from_file_location(
        module.__name__ + "_probe", module.__file__
    )
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    return fresh


class CompatibilityTests(unittest.TestCase):
    def test_property_cellview_index(self):
        for index in (0, 2):
            with self.subTest(index=index):
                view = types.SimpleNamespace(active_cellview_index=index)
                self.assertEqual(get_active_cellview_index(view), index)

    def test_callable_cellview_index(self):
        method = mock.Mock(return_value=0)
        view = types.SimpleNamespace(active_cellview_index=method)
        self.assertEqual(get_active_cellview_index(view), 0)
        method.assert_called_once_with()

    def test_application_missing(self):
        with self.assertRaisesRegex(RuntimeError, "KLayout application runtime"):
            get_application(None)

    def test_application_instance_missing(self):
        application_type = types.SimpleNamespace(instance=lambda: None)
        with self.assertRaisesRegex(RuntimeError, "KLayout application runtime"):
            get_application(application_type)

    def test_main_window_missing(self):
        app = types.SimpleNamespace(main_window=lambda: None)
        application_type = types.SimpleNamespace(instance=lambda: app)
        with self.assertRaisesRegex(RuntimeError, "use -z"):
            get_main_window(application_type)

    def test_main_window_available(self):
        window = object()
        app = types.SimpleNamespace(main_window=lambda: window)
        application_type = types.SimpleNamespace(instance=lambda: app)
        self.assertIs(get_application(application_type), app)
        self.assertIs(get_main_window(application_type), window)

    def test_native_gui_imports_with_has_pya_false(self):
        # Reproduce the flag combination caused by an importable pip klayout.
        with mock.patch.object(klayout_pyxs, "HAS_PYA", False):
            for module in (pyxs_lib, pyxs3D_lib):
                fresh = load_fresh_library(module)
                self.assertIs(fresh.Application, pya.Application)
                self.assertIs(fresh.Action, pya.Action)

    def test_standalone_imports_and_gui_entry_points(self):
        # Retain real geometry bindings but remove the GUI-only pya names.
        with mock.patch.object(klayout_pyxs, "HAS_PYA", False):
            with mock.patch.dict(sys.modules, {"pya": types.ModuleType("pya")}):
                for module in (pyxs_lib, pyxs3D_lib):
                    fresh = load_fresh_library(module)
                    self.assertIsNone(fresh.Application)
                    self.assertIsNone(fresh.FileDialog)
                    self.assertIsNone(fresh.MessageBox)
                    with self.assertRaisesRegex(RuntimeError, "KLayout application"):
                        fresh.XSectionScriptEnvironment()
                    generator = fresh.XSectionGenerator("unused.pyxs")
                    with self.assertRaisesRegex(RuntimeError, "KLayout application"):
                        if module is pyxs_lib:
                            generator.run(pya.DPoint(0, 0), pya.DPoint(1, 0))
                        else:
                            generator.run()
