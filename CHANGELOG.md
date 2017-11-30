# Change Log

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.1.0]

### Fixed

- Fixed a couple of type errors.  Typing is either going to be removed
  or moved to a different format to allow for < Python3.6.

## [0.0.9]

### Added

- `GenericSyntaxError` for any `ParserException`s which are raised when
  parsing. Ideally, we would add the offset for the lines in the
  docstring so that we could get a more accurate indication of where the
  actual error occurred. (This would be useful for when we integrate with
  ALE or Syntastic or something.)
- `get_logger()` function to the config file.  This will help us to get a
  fully configured logger.  It'll also be a nice way to request a preconfigured
  logger (say, "darglint.parser" or something if we want to log from the
  parser.)  Then we could parse the same configuration to every logger.
- Added check for bare raises.  For example, if we had a function such as:

```
def do_something_dangerous():
    try:
        dangerous_action()
    except CertainDoom:
        raise
```

  This would previously caused an error.  Now, no checks are made for it.
  A "TODO" was left in the code as a reminder that we could handle this better
  in the future.

## [0.0.8]

### Added

- Added configuration files.  Configuration files use the normal Python
  `configparser` and TOML format.  Configuration files for *darglint*
  should have one of the following names:

  - `.darglint`
  - `setup.cfg`
  - `tox.ini`

  In addition, the settings for *darglint* must be in a section described
  by `[darglint]`.  The configuration takes a single key, `ignore`,
  and a list of error codes to ignore as a value.  For example, if we
  would like to ignore the errors "I101" and "I102", then we would
  could write the following section in our *tox.ini* file:

```
  [darglint]
  ignore=I101,I102
```

  *darglint* will look for a config file stating at the current directory
  and working its way up to the root directory.

## [0.0.7]

### Fixed

- Fixed star arguments not being treated correctly.

### Changed

- Simplified error messages.

  There are now only two verbosity levels, 1 and 2.  I've kept it as an
  integer argument so that, in the future, we can add other levels if
  necessary.  The default level, now, is 1.  At that level, the error
  message is something like:

    <filename>:<function>:<linenumber>: <error-code>: <message>

  Where message is an abbreviated version. (It uses symbols primarily.
  For example "- word" denotes a missing parameter in a docstring.  "+
  word" denotes an extra parameter in the docstring.

  Using a level 2 verbosity also prints out the general error message.
  (This describes what the error is.  So, if level 1 is too cryptic, we
  can switch to level 2.)  This will look like:

    <filename>:<function>:<linenumber>: <error-code>: <description>: <message>

  This gets pretty long, so that's why it's not the default.


## [0.0.6] -- 2017-10-15

### Added

- Verifies types specified in the docstring against type hints
  on the function.  Also added `noqa` for these errors.

  For example, if we have a function with a mismatched type,
  such as:

    ```
    def mismatched_type(x: int) -> str:
      """Return the string representation of the number.

      Args:
        x (float): The float to represent.

      Returns:
        str: The string representation of the number.

      """
      return str(x)
    ```

  Then it would raise a `TypeMismatchError`, since the parameter,
  `x`, has a type hint of `int`, while the docstring documents
  it as being of type `float`.  We could prevent this error
  by either adding `# noqa: I103` or `# noqa: I103 x`.

## [0.0.5] -- 2017-10-14

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

- We can now ignore certain errors using `noqa`.  The syntax for
  `noqa` is very similar to that used for *pycodestyle* and other
  linters, with the exception that `noqa`, here, can take an argument.

  Let us say that we want to ignore a missing return statement
  in the following docstring:

    ```
    def we_dont_want_a_returns_section():
      """Returns the value, 3.

      # noqa: I201

      """
      return 3
    ```

  We put the `noqa` anywhere in the top level of the docstring.
  However, this won't work if we are missing something more specific,
  like a parameter.  We may not want to ignore all missing parameters,
  either, just one particular one.  For example, we may be writing a
  function that takes a class instance as self. (Say, in a bound *celery*
  task.) Then we would do something like:

    ```
    def a_bound_function(self, arg1):
      """Do something interesting.

      Args:
        arg1: The first argument.

      # noqa: I101 arg1

      """
      arg1.execute(self)
    ```

  So, the argument comes to the right of the error.

  We may also want to mark excess documentation as being okay.  For example,
  we may not want to explicitly catch and raise a `ZeroDivisionError`.  We
  could do the following:

    ```
    def always_raises_exception(x):
        """Raise a zero division error or type error.o

        Args:
          x: The argument which could be a number or could not be.

        Raises:
          ZeroDivisionError: If x is a number.  # noqa: I402
          TypeError: If x is not a number.  # noqa: I402

        """
        x / 0
    ```

  So, in this case, the argument for `noqa` is really all the way to
  the left.  (Or whatever description we are parsing.)  We could also
  have put it on its own line, as `# noqa: I402 ZeroDivisionError`.

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
