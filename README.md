# klayout_pyxs 0.1.12

[![docs](https://github.com/gdsfactory/klayout_pyxs/actions/workflows/pages.yml/badge.svg)](https://gdsfactory.github.io/klayout_pyxs/)
[![pypi](https://img.shields.io/pypi/v/klayout_pyxs)](https://pypi.org/project/klayout_pyxs/)
[![MIT](https://img.shields.io/github/license/gdsfactory/gdsfactory)](https://choosealicense.com/licenses/mit/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://pepy.tech/badge/klayout_pyxs)](https://pepy.tech/project/klayout_pyxs)
[![Downloads](https://pepy.tech/badge/klayout_pyxs/month)](https://pepy.tech/project/klayout_pyxs)
[![Downloads](https://pepy.tech/badge/klayout_pyxs/week)](https://pepy.tech/project/klayout_pyxs)

This is a python port of the XSection project
(https://github.com/klayoutmatthias/xsection).

The goal of this project is to provide an add-on to KLayout (www.klayout.de) to
create and visualize a realistic cross-section view for VLSI designs
supporting a wide range of technology options.

## User Documentation

For the project description see [klayout_pyxs Project Home Page](https://gdsfactory.github.io/klayout_pyxs).


## Project Files

The basic structure is:

 * `docs` The documentation
 * `klayout_pyxs` The python package sources
 * `pymacros` The python .lym macros files for KLayout
 * `samples` Some sample files
 * `tests` Test sources and golden data
 * `xs2pyxs` xs to pyxs conversion scripts

The `docs` folder contains the .rst files and images for the documentation
pages. See rendered version [here](https://klayout-pyxs.readthedocs.io/en/latest).

The `klayout_pyxs` folder contains the python package which includes
the cross-section generation engine.

The `pymacros` folder contains with the actual KLayout macros code,
`pyxs.lym`.

The `samples` folder holds a few files for playing around.

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

The `xs2pyxs` folder contains a shell script which helps converting
Ruby-based .xs scripts to .pyxs scripts. It performs necessary but not
sufficient string replacements. Depending on the .xs script complexity,
more changes are likely to be needed.


## Installation for users

You can install the module

```
pip install klayout_pyxs
```

And the klayout macro from klayout package manager.

![](https://i.imgur.com/0e1vAqW.png)

## Installation for developers

To run .pyxs scripts from the KLayout menu, klayout_pyxs package and
python macros file have to be installed to the KLayout folders.
According to [KLayout documentation](https://www.klayout.de/doc-qt4/about/macro_editor.html),
they should go to the "pymacros" and "python" folders in KLayout's user
specific application folder. In Windows, it is $USERPROFILE/KLayout.

If you are using Python 2.7 in your KLayout distribution, you need
`six` package installed.

### Windows

In Windows, do the following (the commands should be run from e.g.
git bash console). Tested on KLayout 0.25.3 and 0.25.7.

0. Check if $USERPROFILE/KLayout exists and is used by the KLayout to
store macros. Run

    ```bash
    $ ls $USERPROFILE/KLayout
    ```

    If no error reported, continue with 1. If there is an error, you need to
    find a location of KLayout's user specific application folder
    with pymacros, python folders and use it in further commands.

1. Clone klayout_pyxs repository into any source folder:

    ```bash
    $ git clone https://github.com/dimapu/klayout_pyxs.git klayout_pyxs_repo
    ```

2. Copy klayout_pyxs_repo/pymacros/pyxs.lym to $USERPROFILE/KLayout/pymacros/pyxs.lym

    ```bash
    $ cp klayout_pyxs_repo/pymacros/pyxs.lym $USERPROFILE/KLayout/pymacros/pyxs.lym
    ```

3. Copy klayout_pyxs_repo/klayout_pyxs/*.* to $USERPROFILE/KLayout/python/klayout_pyxs

    ```bash
    $ mkdir $USERPROFILE/KLayout/python/klayout_pyxs
    $ cp klayout_pyxs_repo/klayout_pyxs/*.py $USERPROFILE/KLayout/python/klayout_pyxs
    ```

Now, run Klayout. In the Tools menu, you should see pyxs > Load pyxs script.

### Linux / Mac OS

Run

```bash
$ make install
```

Now, run Klayout. In the Tools menu, you should see pyxs > Load pyxs script.
