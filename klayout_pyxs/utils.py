from __future__ import absolute_import
from __future__ import print_function
import math

VERBOSE = True
OFFSET = 0


def info(*s):
    """ Print information with offset.

    Parameters
    ----------
    s : str
        string to be printed
    """
    if VERBOSE:
        print(' ' * OFFSET, *s)


def print_info(v=True):
    """ Decorator to show / disable function output to the console.

    Parameters
    ----------
    v : bool
        it False, all info() inside the function will be disabled.

    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            global VERBOSE
            global OFFSET
            old_v = VERBOSE
            VERBOSE = v
            if v:
                OFFSET += 4
            info(f'{f.__name__}():')
            res = f(*args, **kwargs)
            info(f'end of {f.__name__}()\n')
            if v:
                OFFSET -= 4
            VERBOSE = old_v
            return res
        return wrapper
    return decorator


def int_floor(x):
    """ Floor a float value and return int

    Returns
    -------
    res : int
        int(math.floor(x))

    Examples
    --------
    >>> int_floor(1.5)
    1
    >>> int_floor(1.2)
    1
    >>> int_floor(1.8)
    1
    >>> int_floor(-1.2)
    -2
    >>> int_floor(-1.5)
    -2
    >>> int_floor(-1.8)
    -2
    """
    return int(math.floor(x))


def _check_type(instance, typ, caller=''):
    """Check type of an object

    Parameters
    ----------
    caller : str
        caller name. Used for more informative error messages.
    """

    if not isinstance(instance, typ):
        caller_str = f"'{caller}': " if caller != '' else ""
        raise TypeError(
            f"{caller_str}Argument must be an instance of {typ}. {type(instance)} is given"
        )


def make_iterable(v):
    return v if (v is None) or (type(v) in (list, tuple)) else [v]


def main():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    main()
