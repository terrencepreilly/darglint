# Darglint

A limited docstring linter which checks that function/method parameters
are defined in their docstrings.  *Darglint* expects docstrings to be
formatted using the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

*Darglint* is in a very early stage, and fails for a lot of things.
Certain features, such as a robust command-line interface, still
do not exist.

## Installation

To install *darglint*, use pip.

```
pip install darglint
```

Or, clone the repository, `cd` to the directory, and

```
pip install .
```


## Usage

Given a python source file, `serializers.py`, you would check the docstrings
as follows:

```
darglint serializers.py
```

## Features planned and implemented

The below list is all that defines the current roadmap for *darglint*.
It is roughly sorted in order of importance.

- [x] Function definitions can be checked.
- [x] Methods definitions of top-level class can be checked.
- [x] Line number printout for function/method definition.
- [ ] Add parsing of "Returns" section, and warn if differing from
function definition.
- [ ] Add command line interface.
- [ ] Add multiple options for output.
- [ ] Add type hint integration.  If an argument has a type hint, then
the description of the argument, if it has a type, should match that.
- [ ] Add support for python versions earlier than 3.6.
- [ ] Syntastic support. (Syntastic is not accepting new checkers until
their next API stabilizes, so this may take some time.)

## Development

Install `darglint`. First, clone the repository:

```
git clone https://github.com/terrencepreilly/darglint.git
```

`cd` into the directory, create a virtual environment (optional), then setup:

```
cd darglint/
virtualenv -p python3.6 .env
source .env/bin/activate
pip install -e .
```

You can run the tests using

```
python setup.py test
```

Or, install `pytest` manually, `cd` to the project's root directory,
and run

```
pytest
```

Contributions welcome.
