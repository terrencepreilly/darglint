Darglint
========

A functional docstring linter which checks whether a docstring's
description matches the actual function/method implementation.
*Darglint* expects docstrings to be formatted using the `Google Python
Style Guide <https://google.github.io/styleguide/pyguide.html>`__.

*Darglint* is still in an early stage, and may fail for some things. See
the **Roadmap** section for an idea of where the project is going.

Feel free to submit an issue/pull request if you spot a problem or would
like a feature in *darglint*.

Installation
------------

To install *darglint*, use pip.

::

    pip install darglint

Or, clone the repository, ``cd`` to the directory, and

::

    pip install .

Configuration
-------------

*darglint* can be configured using a configuration file. The
configuration file must be named either *.darglint*, *setup.cfg*, or
*tox.ini*. It must also have a section starting with the section header,
``[darglint]``. Finally, the configuration file must be located either
in the directory *darglint* is called from, or from a parent directory
of that working directory.

Currently, the configuration file only allows us to ignore errors. For
example, if we would like to ignore ``ExcessRaiseError``\ s (because we
know that an underlying function will raise an exception), then we would
add its error code to a file named *.darglint*:

::

    [darglint]
    ignore=I402

We can ignore multiple errors by using a comma-separated list:

::

    [darglint]
    ignore=I402,I103

Usage
-----

Command Line use
~~~~~~~~~~~~~~~~

Given a python source file, ``serializers.py``, you would check the
docstrings as follows:

::

    darglint serializers.py

You can give an optional verbosity setting to *darglint*. For example,

::

    darglint -v 2 *.py

Would give a description of the error along with information as to this
specific instance. The default verbosity is 1, which gives the filename,
function name, line number, error code, and some general hints.

*darglint* is particularly useful when combined with the utility,
``find``. This allows us to check all of the files in our project at
once. For example, when eating my own dogfood (as I tend to do), I
invoke *darglint* as follows:

::

    find . -name "*.py" -exec darglint {} \;

Where I'm searching all files ending in ".py" recursively from the
current directory, and calling *darglint* on each one in turn.

Ignoring Errors in a Docstring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can ignore specific errors in a particular docstring. The syntax is
much like that of *pycodestyle*, etc. It generally takes the from of:

::

    # noqa: <error> <argument>

Where ``<error>`` is the particular error to ignore (``I402``, or
``I201`` for example), and ``<argument>`` is what (if anything) the
ignore statement refers to (if nothing, then it is not specified).

Let us say that we want to ignore a missing return statement in the
following docstring:

::

    def we_dont_want_a_returns_section():
      """Returns the value, 3.

      # noqa: I201

      """
      return 3

We put the ``noqa`` anywhere in the top level of the docstring. However,
this won't work if we are missing something more specific, like a
parameter. We may not want to ignore all missing parameters, either,
just one particular one. For example, we may be writing a function that
takes a class instance as self. (Say, in a bound *celery* task.) Then we
would do something like:

::

    def a_bound_function(self, arg1):
      """Do something interesting.

      Args:
        arg1: The first argument.

      # noqa: I101 arg1

      """
      arg1.execute(self)

So, the argument comes to the right of the error.

We may also want to mark excess documentation as being okay. For
example, we may not want to explicitly catch and raise a
``ZeroDivisionError``. We could do the following:

::

    def always_raises_exception(x):
        """Raise a zero division error or type error.o

        Args:
          x: The argument which could be a number or could not be.

        Raises:
          ZeroDivisionError: If x is a number.  # noqa: I402
          TypeError: If x is not a number.  # noqa: I402

        """
        x / 0

So, in this case, the argument for ``noqa`` is really all the way to the
left. (Or whatever description we are parsing.) We could also have put
it on its own line, as ``# noqa: I402 ZeroDivisionError``.

Roadmap
-------

The below list is the current roadmap for *darglint*. For each version
number, it specifies which features will be added. To see the most
recently implemented features, see the *CHANGELOG*.

0.3
~~~

-  [ ] Take an argument which supports a formatting string for the error
   message. That way, anyone can specify their own format.

1.0
~~~

-  [ ] Robust logging for errors caused/encountered by *darglint*.
-  [ ] Add support for python versions earlier than 3.6.
-  [ ] Add more specific line numbers in error messages.
-  [ ] Add style errors and suggestions.

Other features
~~~~~~~~~~~~~~

I haven't decided when to add the below features.

-  [ ] ALE support.
-  [ ] Syntastic support. (Syntastic is not accepting new checkers until
   their next API stabilizes, so this may take some time.)
-  [ ] Check super classes of errors/exceptions raised to allow for more
   general descriptions in the interface.

Development and Contributions
-----------------------------

Development Setup
~~~~~~~~~~~~~~~~~

Install ``darglint``. First, clone the repository:

::

    git clone https://github.com/terrencepreilly/darglint.git

``cd`` into the directory, create a virtual environment (optional), then
setup:

::

    cd darglint/
    virtualenv -p python3.6 .env
    source .env/bin/activate
    pip install -e .

You can run the tests using

::

    python setup.py test

Or, install ``pytest`` manually, ``cd`` to the project's root directory,
and run

::

    pytest

This project tries to conform by the styles imposed by ``pycodestyle``
and ``pydocstyle``, as well as by ``darglint`` itself.

Contribution
~~~~~~~~~~~~

If you would like to tackle an issue or feature, email me or comment on
the issue to make sure it isn't already being worked on. Contributions
will be accepted through pull requests. New features should include unit
tests, and, of course, properly formatted documentation.
