from klayout_pyxs.pyxs3D_lib import XSectionGenerator


generator = XSectionGenerator(xs_run)
generator.set_output_parameters(filename=xs_out)
generator.run()
