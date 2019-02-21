# klayout_pyxs

This is a python port of the XSection project 
(https://github.com/klayoutmatthias/xsection). 

The goal of this project is to provide an add-on to KLayout (www.klayout.de) to 
create and visualize a realistic cross-section view for VLSI designs 
supporting a wide range of technology options.

## User Documentation

For the project description see [klayout_pyxs Project Home Page](https://github.com/dimapu/klayout_pyxs).

For an introduction into writing PYXS files, see 
[Writing PYXS Files - an Introduction](https://klayout-pyxs.readthedocs.io/en/latest/DocIntro.html).

For a reference of the elements of the PYXS scripts, see 
[PYXS File Reference](https://klayout-pyxs.readthedocs.io/en/latest/DocReference.html).

## Project Files

The basic structure is:

 * `docs` The documentation
 * `samples` Some sample files
 * `klayout_pyxs` The package sources
 * `tests` Test sources and golden data

The `docs` folder contain the .rst files and images for the documentation 
pages. See rendered version [here](https://klayout-pyxs.readthedocs.io/en/latest). 

The `samples` folder holds a few files for playing around.

The `klayout_pyxs` folder contains the python package, and `pymacros` 
folder with the actual KLayout package code (`pyxs.lym`). 

The `tests` folder contains some regression tests for the package. 
To run the tests, make sure "klayout" or "klayout_app" (in Windows) 
is in your path and use

```sh
$ cd tests
$ ./run_tests.sh
```

or (from e.g. git bash console on Windows) 

```bash
$ cd tests
$ bash run_tests_windows.sh
```
