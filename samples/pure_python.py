import pathlib
from klayout_pyxs.pyxs_lib import XSectionGenerator


gdspath = pathlib.Path(__file__).parent.absolute() / "sample.gds"
xg = XSectionGenerator(file_name=gdspath)

lpoly = xg.layer("3/0")
lactive = xg.layer("2/0")
lfox = lactive.inverted()
lwn = xg.layer("1/0")
lcg = xg.layer("4/0")
m1 = xg.layer("6/0")
