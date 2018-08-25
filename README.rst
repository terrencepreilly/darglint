Darglint
========

Check out the `poster <./docs/poster.pdf>`__ about darglint which was
presented at pycon!

A functional docstring linter which checks whether a docstring’s
description matches the actual function/method implementation.
*Darglint* expects docstrings to be formatted using the `Google Python
Style Guide <https://google.github.io/styleguide/pyguide.html>`__.

*Darglint* is still in an early stage, and may fail for some things. See
the **Roadmap** section for an idea of where the project is going.

Feel free to submit an issue/pull request if you spot a problem or would
like a feature in *darglint*.

**Table of Contents**:

-  `Installation <#installation>`__
-  `Configuration <#configuration>`__
-  `Usage <#usage>`__
-  `Sphinx <#sphinx>`__
-  `Flake8 <#flake8>`__
-  `Roadmap <#roadmap>`__
-  `Contribution <#development-and-contributions>`__

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

Currently, the configuration file only allows us to ignore errors and
specify message templates. For example, if we would like to ignore
``ExcessRaiseError``\ s (because we know that an underlying function
will raise an exception), then we would add its error code to a file
named *.darglint*:

::

   [darglint]
   ignore=I402

We can ignore multiple errors by using a comma-separated list:

::

   [darglint]
   ignore=I402,I103

If we would like to specify a message template, we may do so as follows:

::

   [darglint]
   message_template={msg_id}@{path}:{line}

Which will produce a message such as ``I102@driver.py:72``.

Finally, we can specify the docstring style type using
``docstring_style`` (“google” by default):

::

   [darglint]
   docstring_style=sphinx

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

To use an arbitrary error format, you can pass a message template, which
is a python format string. For example, if we pass the message template

::

   darglint -m "{path}:{line} -> {msg_id}" darglint/driver.py

Then we would get back error messages like

::

   darglint/driver.py :61 -> I101

The following attributes can be passed to the format string: - *line*:
The line number, - *msg*: The error message, - *msg_id*: The error code,
- *obj*: The function/method name, - *path*: The relative file path.

The message template can also be specified in the configuration file as
the value ``message_template``.

*darglint* is particularly useful when combined with the utility,
``find``. This allows us to check all of the files in our project at
once. For example, when eating my own dogfood (as I tend to do), I
invoke *darglint* as follows:

::

   find . -name "*.py" | xargs darglint

Where I’m searching all files ending in “.py” recursively from the
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
     """Return the value, 3.

     # noqa: I201

     """
     return 3

We put the ``noqa`` anywhere in the top level of the docstring. However,
this won’t work if we are missing something more specific, like a
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

Error Codes
~~~~~~~~~~~

-  *I101*: The docstring is missing a parameter in the definition.
-  *I102*: The docstring contains a parameter not in function.
-  *I103*: The docstring parameter type doesn’t match function.
-  *I201*: The docstring is missing a return from definition.
-  *I202*: The docstring has a return not in definition.
-  *I203*: The docstring parameter type doesn’t match function.
-  *I301*: The docstring is missing a yield present in definition.
-  *I302*: The docstring has a yield not in definition.
-  *I401*: The docstring is missing an exception raised.
-  *I402*: The docstring describes an exception not explicitly raised.
-  *S001*: Describes that something went wrong in parsing the docstring.
-  *S002*: An argument/exception lacks a description.

The error code scheme is based on the errors from the pycodestyle
package. The first letter corresponds to the broad class of error:

-  I (Interface): Incorrect or incomplete documentation.
-  S (Style): Errors with documentation style/syntax.

The number in the hundreds narrows the error by location in the
docstring:

-  100: Args section
-  200: Returns section
-  300: Yields section
-  400: Raises section

Sphinx
------

Darglint can handle sphinx-style docstrings, but imposes some
restrictions on top of the Sphinx style. For example, all fields (such
as ``:returns:``) must be the last items in the docstring. They must be
together, and all indents should be four spaces. These restrictions may
be loosened at a later date.

To analyze Sphinx-style docstrings, pass the style flag to the command:

::

   darglint -s sphinx example.py
   darglint --docsting-style sphinx example.py

Alternatively, you can specify the style in the configuration file using
the setting, “docstring_style”:

::

   [darglint]
   docstring_style=sphinx

Flake8
------

Darglint can be used in conjunction with Flake8 as a plugin. The only
setup necessary is to install Flake8 and Darglint in the same
environment. Darglint will pull its configuration from any configuration
file present. (So, if you would like to lint Sphinx-style comments, then
you should have that setting enabled in a configuration file in the
project directory.)

Roadmap
-------

The below list is the current roadmap for *darglint*. For each version
number, it specifies which features will be added. To see the most
recently implemented features, see the *CHANGELOG*.

0.3
~~~

-  [x] Take an argument which supports a formatting string for the error
   message. That way, anyone can specify their own format.

.. _section-1:

1.0
~~~

-  [ ] Robust logging for errors caused/encountered by *darglint*.
-  [x] Add support for python versions earlier than 3.6.
-  [x] Add more specific line numbers in error messages.
-  [ ] Add style errors and suggestions.
-  [x] Support for Sphinx-style docstrings.

Other features
~~~~~~~~~~~~~~

I haven’t decided when to add the below features.

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

Or, install ``pytest`` manually, ``cd`` to the project’s root directory,
and run

::

   pytest

This project tries to conform by the styles imposed by ``pycodestyle``
and ``pydocstyle``, as well as by ``darglint`` itself.

Contribution
~~~~~~~~~~~~

If you would like to tackle an issue or feature, email me or comment on
the issue to make sure it isn’t already being worked on. Contributions
will be accepted through pull requests. New features should include unit
tests, and, of course, properly formatted documentation.
