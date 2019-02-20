# klayout_pyxs

This is a python port of the XSection project 
(https://github.com/klayoutmatthias/xsection). 

The goal of this project is to provide an add-on to KLayout (www.klayout.de) to 
create and visualize a realistic cross-section view for VLSI designs 
supporting a wide range of technology options.

## User Documentation

For the project description see [TODO: klayout-pyxs Project Home Page](https://klayoutmatthias.github.io/xsection).

For an introduction into writing PYXS files, see 
[TODO: Writing XS Files - an Introduction](https://klayoutmatthias.github.io/xsection/DocIntro).

For a reference of the elements of the PYXS scripts, see 
[TODO: XS File Reference](https://klayoutmatthias.github.io/xsection/DocIntro).

## Project Files

The basic structure is:

 * <tt>docs</tt> The documentation
 * <tt>samples</tt> Some sample files
 * <tt>klayout_pyxs</tt> The package sources
 * <tt>tests</tt> Test sources and golden data

The `docs` folder contain the MD file and images for the documentation pages.

The `samples` folder holds a few files for playing around.

TODO: The `klayout_pyxs` folder contains the package definition file 
(`grain.xml`), the `macros` folder with the actual package code 
(`xsection.lym`). The download URL for the package index is therefore the 
pseudo-SVN URL TODO: `https://github.com/klayoutmatthias/xsection.git/tags/x.y/src`.

The <tt>tests</tt> folder contains some regression tests for the package. 
To run the tests, make sure "klayout" is in your path and use

```sh
$ cd tests
$ ./run_tests.sh
```
