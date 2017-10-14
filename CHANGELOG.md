# Change Log

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.0.5] -- Unreleased

### Added

- Checks for a "Yields" section added.  If a function contains
  either the `yield` or `yield from` keywords, *darglint* will
  expect to find a "Yields" section in the docstring.
- Checks for a "Raises" section added.  If a function raises an
  exception, then the raises section should document the exact
  exception or error raised.  Will also warn if the raises
  section documents exceptions not explicitly raised in the function
  or method.  (This feature will be disabled by default.)

  It may be possible to check the super classes of a given error,
  to make more general descriptions in the raises section.  That would
  prevent the interface from leaking implementation details.  However,
  that would entail a good deal more work.  This may be implemented
  at a later date, but for now, if you're doing that, then you should
  just disable the checks for exception/error raising.
- A `Docstring` class. This class now handles all of the parsing for
  docstrings, and stores the attributes found from the docstring.  It
  is the docstring corollary `FunctionDescription`.

  It's attributes are either strings (`Docstring.returns_description`,
  `Docstring.yields_description`, `Docstring.short_description`,
  `Docstring.long_description`), or dictionaries containing
  arguments/exceptions and their descriptions (
  `Docstring.arguments_descriptions`, `Docstring.raises_descriptions`).

## [0.0.4] -- 2017-10-06

### Fixed

- Setup script was removing the *README.rst* file, which could not
  be referenced in the setup script.  So, it wasn't showing up as
  the long description on pypi.  This should fix that.

## [0.0.3]

### Added

- Command line interface.  There is currently only a single option,
  verbosity, and a single multi-value argument, files.  Help for
  the command can be accessed using

    ```
      darglint -h
    ```

  Example Usage:

    ```
      darglint -v 3 darglint/*.py
    ```

    This runs a documentation check on all of the internal modules
    for darglint, with a verbosity level of 3 (the highest.)


## [0.0.2]

### Added

- Changelog.

- Handling for methods.  Checks for whether the method is a static
  method or a class method.  Doesn't prompt for documentation for
  "self", or "cls" when not appropriate.

- Change format for error messages to be less verbose.
  The format is now:
    ```
    <function/method name>
      - <missing argument>
      + <extraneous argument>
    ```

### Changed

- Removed dependency on Red Baron.  This allows us to use line
  numbers, and to parse python which contains type hints.

### Fixed

- Handle functions/methods without docstrings by ignoring them.
  `darglint` should only care about whether a docstring is up to
  date, not whether it is present or not.


## [0.0.1] - 2017-09-18

Began project.  Added check of function definitions.  Buggy and
doesn't handle many options.
