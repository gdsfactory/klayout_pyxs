"""Run a unittest module in KLayout and propagate failures to the shell."""

import runpy
import traceback
import types
import unittest

import pya

try:
    module = types.ModuleType("pyxs_tests")
    module.__dict__.update(runpy.run_path(pyxs_test))
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if not suite.countTestCases():
        raise RuntimeError(f"No tests found in {pyxs_test}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    status = 0 if result.wasSuccessful() else 1
except BaseException:
    traceback.print_exc()
    status = 1

pya.Application.instance().exit(status)
