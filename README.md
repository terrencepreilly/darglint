# Darglint

A functional docstring linter which checks whether a docstring's
description matches the actual function/method implementation.
*Darglint* expects docstrings to be formatted using the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
or [Sphinx Style Guide](https://pythonhosted.org/an_example_pypi_project/sphinx.html#function-definitions).

Feel free to submit an issue/pull request if you spot a problem or
would like a feature in *darglint*.

**Table of Contents**:

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Sphinx](#sphinx)
- [Integrations](#integrations)
- [Roadmap](#roadmap)
- [Contribution](#development-and-contributions)


## Installation

To install *darglint*, use pip.

```bash
pip install darglint
```

Or, clone the repository, `cd` to the directory, and

```bash
pip install .
```

## Configuration

*darglint* can be configured using a configuration file.  The configuration
file must be named either *.darglint*, *setup.cfg*, or *tox.ini*.  It must
also have a section starting with the section header, `[darglint]`.
Finally, the configuration file must be located either in the directory
*darglint* is called from, or from a parent directory of that working
directory.

Currently, the configuration file allows us to ignore errors, to specify
message templates, and to specify the strictness of checks.

### Error Configuration

If we would like to ignore `ExcessRaiseError`s (because we know that
an underlying function will raise an exception), then we would add its
error code to a file named *.darglint*:

```ini
[darglint]
ignore=DAR402
```

We can ignore multiple errors by using a comma-separated list:

```ini
[darglint]
ignore=DAR402,DAR103
```

Instead of specifying error codes to ignore in general one can also specify a
regex to exclude certain function names from tests. For example, the following 
configuration would disable linting on all private methods.
```ini
[darglint]
ignore_regex=^_(.*)
```

### Message Template Configuration

If we would like to specify a message template, we may do so as
follows:

```ini
[darglint]
message_template={msg_id}@{path}:{line}
```

Which will produce a message such as `DAR102@driver.py:72`.

Finally, we can specify the docstring style type using `docstring_style`
("google" by default):

```ini
[darglint]
docstring_style=sphinx
```

### Strictness Configuration

Strictness determines how lax darglint will be when checking docstrings.
There are three levels of strictness available:

- short: One-line descriptions are acceptable; anything
more and the docstring will be fully checked.

- long: One-line descriptions and descriptions without
arguments/returns/yields/etc. sections will be allowed.  Anything more,
and the docstring will be fully checked.

- full: (Default) Docstrings will be fully checked.

For example, if we have the following function:

```python
def double(x):
    # <docstring>
    return x * 2
```

Then the following table describes which errors will be raised for
each of the docstrings (rows) when checked against each of the
configurations (columns):

```
┌──────────────────────────────┬──────────────────┬────────────────┬──────────────────┐
│ Docstring                    │  short           │  long          │  full            │
├──────────────────────────────┼──────────────────┼────────────────┼──────────────────┤
│ """Doubles the argument."""  │ None             │ None           │ Missing argument │
│                              │                  │                │ Missing return   │
│                              │                  │                │                  │
│                              │                  │                │                  │
├──────────────────────────────┼──────────────────┼────────────────┼──────────────────┤
│ """Doubles the argument.     │ Missing argument │ None           │ Missing argument │
│                              │ Missing return   │                │ Missing return   │
│ Not very pythonic.           │                  │                │                  │
│                              │                  │                │                  │
│ """                          │                  │                │                  │
│                              │                  │                │                  │
├──────────────────────────────┼──────────────────┼────────────────┼──────────────────┤
│ """Doubles the argument.     │ Missing return   │ Missing return │ Missing return   │
│                              │                  │                │                  │
│ Args:                        │                  │                │                  │
│     x: The number to double. │                  │                │                  │
│                              │                  │                │                  │
│ """                          │                  │                │                  │
└──────────────────────────────┴──────────────────┴────────────────┴──────────────────┘
```

In short, if you want to be able to have single-line docstrings, and check
all other docstrings against their described parameters, you would specify

```ini
[darglint]
strictness=short
```

In your configuration file.


## Usage


### Command Line use

Given a python source file, `serializers.py`, you would check the docstrings
as follows:

```bash
darglint serializers.py
```

You can give an optional verbosity setting to *darglint*.  For example,

```bash
darglint -v 2 *.py
```

Would give a description of the error along with information as to this
specific instance.  The default verbosity is 1, which gives the filename,
function name, line number, error code, and some general hints.

To use an arbitrary error format, you can pass a message template, which
is a python format string.  For example, if we pass the message
template

```bash
darglint -m "{path}:{line} -> {msg_id}" darglint/driver.py
```

Then we would get back error messages like

```
darglint/driver.py :61 -> DAR101
```

The following attributes can be passed to the format string:
- *line*: The line number,
- *msg*: The error message,
- *msg_id*: The error code,
- *obj*: The function/method name,
- *path*: The relative file path.

The message template can also be specified in the configuration file
as the value `message_template`.

*darglint* is particularly useful when combined with the utility, `find`.
This allows us to check all of the files in our project at once.  For example,
when eating my own dogfood (as I tend to do), I invoke *darglint* as follows:

```bash
find . -name "*.py" | xargs darglint
```

Where I'm searching all files ending in ".py" recursively from the
current directory, and calling *darglint* on each one in turn.

### Ignoring Errors in a Docstring

You can ignore specific errors in a particular docstring.  The syntax
is much like that of *pycodestyle*, etc.  It generally takes the from
of:

```python
# noqa: <error> <argument>
```

Where `<error>` is the particular error to ignore (`DAR402`, or `DAR201`
for example), and `<argument>` is what (if anything) the ignore
statement refers to (if nothing, then it is not specified).

Let us say that we want to ignore a missing return statement
in the following docstring:

```python
def we_dont_want_a_returns_section():
  """Return the value, 3.

  # noqa: DAR201

  """
  return 3
```

We put the `noqa` anywhere in the top level of the docstring.
However, this won't work if we are missing something more specific,
like a parameter.  We may not want to ignore all missing parameters,
either, just one particular one.  For example, we may be writing a
function that takes a class instance as self. (Say, in a bound *celery*
task.) Then we would do something like:

```python
def a_bound_function(self, arg1):
  """Do something interesting.

  Args:
    arg1: The first argument.

  # noqa: DAR101 arg1

  """
  arg1.execute(self)
```

So, the argument comes to the right of the error.

We may also want to mark excess documentation as being okay.  For example,
we may not want to explicitly catch and raise a `ZeroDivisionError`.  We
could do the following:

```python
def always_raises_exception(x):
    """Raise a zero division error or type error.o

    Args:
      x: The argument which could be a number or could not be.

    Raises:
      ZeroDivisionError: If x is a number.  # noqa: DAR402
      TypeError: If x is not a number.  # noqa: DAR402

    """
    x / 0
```

So, in this case, the argument for `noqa` is really all the way to
the left.  (Or whatever description we are parsing.)  We could also
have put it on its own line, as `# noqa: DAR402 ZeroDivisionError`.

### Error Codes

- *DAR001*: The docstring was not parsed correctly due to a syntax error.
- *DAR002*: An argument/exception lacks a description
- *DAR003*: A line is under-indented or over-indented.
- *DAR004*: The docstring contains an extra newline where it shouldn't.
- *DAR101*: The docstring is missing a parameter in the definition.
- *DAR102*: The docstring contains a parameter not in function.
- *DAR103*: The docstring parameter type doesn't match function.
- *DAR104*: (disabled) The docstring parameter has no type specified 
- *DAR201*: The docstring is missing a return from definition.
- *DAR202*: The docstring has a return not in definition.
- *DAR203*: The docstring parameter type doesn't match function.
- *DAR301*: The docstring is missing a yield present in definition.
- *DAR302*: The docstring has a yield not in definition.
- *DAR401*: The docstring is missing an exception raised.
- *DAR402*: The docstring describes an exception not explicitly raised.
- *DAR501*: The docstring describes a variable which is not defined.

The number in the hundreds narrows the error by location in the docstring:

- 000: Syntax, formatting, and style
- 100: Args section
- 200: Returns section
- 300: Yields section
- 400: Raises section
- 500: Variables section

You can enable disabled-by-default exceptions in the configuration file
using the `enable` option.  It accepts a comma-separated list of error
codes.

```ini
[darglint]
enable=DAR104
```


## Sphinx

Darglint can handle sphinx-style docstrings, but imposes some restrictions
on top of the Sphinx style. For example, all fields (such as `:returns:`)
must be the last items in the docstring.  They must be together, and all
indents should be four spaces.  These restrictions may be loosened at a
later date.

To analyze Sphinx-style docstrings, pass the style flag to the command:

```bash
darglint -s sphinx example.py
darglint --docsting-style sphinx example.py
```

Alternatively, you can specify the style in the configuration file using
the setting, "docstring\_style":

```ini
[darglint]
docstring_style=sphinx
```

## Integrations

### Flake8

Darglint can be used in conjunction with Flake8 as a plugin.  The only
setup necessary is to install Flake8 and Darglint in the same environment.
Darglint will pull its configuration from any configuration file present.
(So, if you would like to lint Sphinx-style comments, then you should have
that setting enabled in a configuration file in the project directory.)

### SublimeLinter

A plugin for SublimeLinter can be found [here](https://github.com/raddessi/SublimeLinter-contrib-darglint)


## Roadmap
The below list is the current roadmap for *darglint*.  For each
version number, it specifies which features will be added.
To see the most recently implemented features, see the *CHANGELOG*.


### 1.0
- [ ] Robust logging for errors caused/encountered by *darglint*.
- [ ] Add style errors and suggestions.  In particular, allow for multiple
levels of strictness, (lenient by default).  Then warn for no newline after
short description, and for excess whitespace between sections, etc.
- [ ] Add support for numpydoc style docstrings.



### Other features
I haven't decided when to add the below features.

- [ ] ALE support.
- [ ] Syntastic support. (Syntastic is not accepting new checkers until
their next API stabilizes, so this may take some time.)
- [ ] Check super classes of errors/exceptions raised to allow for more
general descriptions in the interface.

## Development and Contributions

### Development Setup

Install `darglint`. First, clone the repository:

```bash
git clone https://github.com/terrencepreilly/darglint.git
```

`cd` into the directory, create a virtual environment (optional), then setup:

```bash
cd darglint/
virtualenv -p python3.6 .env
source .env/bin/activate
pip install -e .
```

You can run the tests using

```bash
python setup.py test
```

Or, install `pytest` manually, `cd` to the project's root directory,
and run

```bash
pytest
```

This project tries to conform by the styles imposed by `pycodestyle`
and `pydocstyle`, as well as by `darglint` itself.


A dockerfile exists for testing with Python3.4.  Although it's not
officially supported (only 3.5+), it's nice to try to make minor
version numbers support it.  You would build the dockerfile and
test using something like

```bash
pushd docker-build
docker build -t darglint-34 -f Dockerfile.test34 .
popd
docker run -it --rm -v $(pwd):/code darglint-34 pytest
```

### Contribution

If you would like to tackle an issue or feature, email me or comment on the
issue to make sure it isn't already being worked on.  Contributions will
be accepted through pull requests.  New features should include unit tests,
and, of course, properly formatted documentation.
