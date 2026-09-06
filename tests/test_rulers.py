"""Integration checks for single-cut PyXS rulers in the real KLayout GUI API."""

import types
import unittest
from unittest import mock

import pya

import klayout_pyxs.pyxs_lib as pyxs_lib


class RulerTests(unittest.TestCase):
    def setUp(self):
        self.window = pya.Application.instance().main_window()
        self.window.select_view(0)
        self.view = self.window.current_view()
        self.view.clear_annotations()
        self.environment = pyxs_lib.XSectionScriptEnvironment("pyxs-ruler-test")

    def tearDown(self):
        self.window.select_view(0)
        self.view.clear_annotations()

    def add_ruler(self, category="", p1=None, p2=None, points=None, text=None):
        ruler = pya.Annotation()
        ruler.category = category
        if points is None:
            ruler.p1 = p1 if p1 is not None else pya.DPoint(-1, 0)
            ruler.p2 = p2 if p2 is not None else pya.DPoint(1, 0)
        else:
            ruler.points = points
        if text is not None:
            ruler.fmt = text
        self.view.insert_annotation(ruler)
        return ruler

    def capture_jobs(self):
        return mock.patch.object(pyxs_lib, "XSectionGenerator")

    def test_programmatic_cut_and_name(self):
        p1, p2 = pya.DPoint(-1, 0), pya.DPoint(1, 0)
        with self.capture_jobs() as generator:
            result = self.environment.run_script("unused.pyxs", p1, p2)
            generator.return_value.run.assert_called_once_with(p1, p2, "")
            self.assertEqual(result, [generator.return_value.run.return_value])

    def test_ordinary_rulers_remain_supported(self):
        self.add_ruler(text="ordinary.cut")
        with self.capture_jobs() as generator:
            self.environment.run_script("unused.pyxs")
            generator.return_value.run.assert_called_once_with(
                pya.DPoint(-1, 0), pya.DPoint(1, 0), "ordinary"
            )

    def test_xsection_ruler_takes_precedence(self):
        self.add_ruler(text="measurement")
        self.add_ruler(
            pyxs_lib._XSECTION_RULER_CATEGORY,
            pya.DPoint(-1, 0.2),
            pya.DPoint(1, 0.2),
            text="section",
        )
        with self.capture_jobs() as generator:
            self.environment.run_script("unused.pyxs")
            generator.return_value.run.assert_called_once_with(
                pya.DPoint(-1, 0.2), pya.DPoint(1, 0.2), "section"
            )

    def test_multiple_single_rulers(self):
        self.add_ruler(pyxs_lib._XSECTION_RULER_CATEGORY, text="first.cut")
        self.add_ruler(
            pyxs_lib._XSECTION_RULER_CATEGORY,
            pya.DPoint(-1, 0.2),
            pya.DPoint(1, 0.2),
            text="second.cut",
        )
        with self.capture_jobs() as generator:
            result = self.environment.run_script("unused.pyxs")
            self.assertEqual(len(result), 2)
            self.assertEqual(
                generator.return_value.run.call_args_list,
                [
                    mock.call(pya.DPoint(-1, 0), pya.DPoint(1, 0), "first"),
                    mock.call(pya.DPoint(-1, 0.2), pya.DPoint(1, 0.2), "second"),
                ],
            )

    def test_unnamed_ruler_fallback(self):
        self.add_ruler(pyxs_lib._XSECTION_RULER_CATEGORY, text="")
        with self.capture_jobs() as generator:
            self.environment.run_script("unused.pyxs")
            self.assertEqual(generator.return_value.run.call_args[0][2], "R01")

    def test_multi_ruler_is_skipped(self):
        self.add_ruler(
            pyxs_lib._XSECTION_RULER_CATEGORY,
            points=[pya.DPoint(-1, 0), pya.DPoint(0, 0), pya.DPoint(1, 0)],
            text="multi",
        )
        self.add_ruler(pyxs_lib._XSECTION_RULER_CATEGORY, text="valid")
        with self.capture_jobs() as generator:
            self.environment.run_script("unused.pyxs")
            generator.return_value.run.assert_called_once_with(
                pya.DPoint(-1, 0), pya.DPoint(1, 0), "valid"
            )

    def test_no_rulers_or_only_multi_rulers(self):
        dialog = types.SimpleNamespace(critical=mock.Mock(), b_ok=lambda: 1)
        for multi in (False, True):
            with self.subTest(multi=multi):
                if multi:
                    self.add_ruler(
                        pyxs_lib._XSECTION_RULER_CATEGORY,
                        points=[pya.DPoint(-1, 0), pya.DPoint(0, 0), pya.DPoint(1, 0)],
                    )
                with mock.patch.object(pyxs_lib, "MessageBox", dialog):
                    with self.capture_jobs() as generator:
                        self.assertIsNone(self.environment.run_script("unused.pyxs"))
                        generator.assert_not_called()
        self.assertEqual(dialog.critical.call_count, 2)

    def test_template_registration_is_idempotent(self):
        for _ in range(3):
            self.environment._register_xsection_ruler_template()
        templates = pyxs_lib._annotation_value(self.view, "annotation_templates")
        matching = [
            template
            for template in templates
            if pyxs_lib._annotation_value(template[0], "category")
            == pyxs_lib._XSECTION_RULER_CATEGORY
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0][2], pya.Annotation.RulerModeNormal)

    def test_source_view_zero_is_restored_after_error(self):
        self.add_ruler(pyxs_lib._XSECTION_RULER_CATEGORY)

        def fail_after_opening_output(*args):
            self.window.create_layout(1)
            raise RuntimeError("intentional recipe failure")

        with self.capture_jobs() as generator:
            generator.return_value.run.side_effect = fail_after_opening_output
            with self.assertRaisesRegex(RuntimeError, "intentional recipe failure"):
                self.environment.run_script("unused.pyxs")
        self.assertEqual(self.window.current_view_index, 0)

    def test_failed_target_is_not_returned(self):
        self.add_ruler(pyxs_lib._XSECTION_RULER_CATEGORY)
        with self.capture_jobs() as generator:
            generator.return_value.run.return_value = None
            self.assertEqual(self.environment.run_script("unused.pyxs"), [])
        self.assertEqual(self.window.current_view_index, 0)

    def assert_grow1_geometry(self, target, cell_name):
        actual = target.active_cellview().layout()
        reference = pya.Layout()
        reference.read("au/xs_grow1.gds")
        self.assertEqual(actual.top_cell().name, cell_name)
        self.assertEqual(actual.dbu, reference.dbu)
        self.assertEqual(
            {str(actual.get_info(index)) for index in actual.layer_indices()},
            {str(reference.get_info(index)) for index in reference.layer_indices()},
        )
        for index in reference.layer_indices():
            actual_index = actual.find_layer(reference.get_info(index))
            actual_region = pya.Region(actual.top_cell().begin_shapes_rec(actual_index))
            expected = pya.Region(reference.top_cell().begin_shapes_rec(index))
            self.assertTrue((actual_region ^ expected).is_empty())

    def test_real_programmatic_geometry(self):
        targets = self.environment.run_script(
            "xs_grow1.pyxs", pya.DPoint(-1, 0), pya.DPoint(1, 0)
        )
        self.assertEqual(len(targets), 1)
        self.assert_grow1_geometry(targets[0], "XSECTION")

    def test_real_multiple_sections_use_original_view(self):
        for name, y in (("first", 0), ("second", 0.2)):
            self.add_ruler(
                pyxs_lib._XSECTION_RULER_CATEGORY,
                pya.DPoint(-1, y),
                pya.DPoint(1, y),
                text=name,
            )
        targets = self.environment.run_script("xs_grow1.pyxs")
        self.assertEqual(len(targets), 2)
        self.assert_grow1_geometry(targets[0], "PYXS: first")
        self.assert_grow1_geometry(targets[1], "PYXS: second")
        self.assertEqual(self.window.current_view_index, 0)
