# Change Log

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [1.5.5]

### Fixed

- Permissions errors from searching for a config would previously
  crash darglint.  Fixed thanks to @pawamoy.
- Some code highlighting issues fixed thanks to @sobolevn.
- Documentation on installing test dependencies updated thanks to @mathieu.
- Finally/else blocks for try statements are now handled when analyzing
  whether an exception can be raised.

## [1.5.4]

### Added

- Added handling of positional-only arguments, and some tests for
  mixing with positional/keyword arguments and keyword-only arguments.

## [1.5.3]

### Added

- Allowed sphinx docstrings to raise an `IndentError` when a
  line is underindented in an item definition.  This makes
  troubleshooting incorrect indentation easier.  (Previously,
  it would have just failed to parse.)
- Configuration for log level.  By default, now, all assertions
  are logged at `ERROR`, and the default log level is `CRITICAL`.
  If darglint doesn't act as expeced, then, the user could pass
  the `--log-level` flag to rerun and see if an expectation was
  missed.

### Fixed

- Allowed `AssertionError` for functions which contain an `assert`
  statement.  Previously, this would result in an excess raises
  error.
- Allowed qualified names in tuple exception handlers.
- Removed legacy token for quotation mark, which could cause poor
  parsing in edge cases (due to the token not being used.)

## [1.5.2]

### Added

- A colon after an error in Numpy format is now reported
  as an empty type error.  Even though exception types are not a
  part of the function signature, and even though it's not a
  part of the numpy standard, this at least gives a hint to the
  user that a dangling colon should be removed.  Incidentally,
  exceptions could have different types, and it could be somewhat
  useful to know what those are.

### Fixed

- Typo in readme fixed thanks to cthoyt@.
- Underspecified types previously resulted in confusing error
  messages because dargint incorrectly matched types up with the
  arguments they describe.  This is now corrected.
- Ignoring style errors wasn't working.  Any error captured during
  the parsing phase was just being added without respecting the
  "ignore" configuration.

## [1.5.1]

### Fixed

- Make flake8 config use default config as a base configuration.
- Fix style being parsed for strictness in configuration parsing.

## [1.5.0]

### Added

- Settings can now be configured from flake8's configuration
  file, or from the flake8 command.  Thanks to @Harrison88 for
  the PR!

### Fixed

- Handle bare raise statement in multiple exception handlers.
- Handle bare raise statement in catch-all exception handler.

## [1.4.1]

### Fixed

- Handle reraising an error from a handler where the caught
  error(s) is a tuple.

## [1.4.0]

### Changed

- Private arguments (arguments with a leading underscore)
  are no longer required.  If present, they will still be
  subject to other checks. (For example, if the description
  is missing, an error will be reported.)

### Fixed

- Handled newlines after Google argument types.  Newlines
  were handled in most other situations (inside of types,
  after an untyped item, etc.) but this one slipped through.
- Handle parentheses inside parenthetical google types.
  Previously, darglint simply failed to parse those arguments.
  Now it will raise a ParameterMalformedError.

## [1.3.1]

### Changed

- Updated README to be more explicit about how Darglint
  handles types and style.

### Fixed

- Qualified exceptions in a raise section were not being
  handled correctly by the `FunctionDescription` class.
  So, if you had a catch statement like,

    def finish_me():
        try:
            raise requests.exceptions.ProxyError()
        except requests.exceptions.ProxyError:
            raise
 
  It wouldn't have been handled correctly.  That is, if
  you documented `requests.exceptions.ProxyError` in the
  docstring, darglint would throw an error.  This change
  resolves the situation, at lest somewhat.  It expects
  the documented exception and the caught exception to
  match exactly.
- Implicitly raised exceptions which are rethrown was
  also not handled. So, for example, if you had:

    def throwing_up():
        """Throws up.
    
        Raises:
            ProxyError: If failed to yarf.
    
        """
        try:
            proxy_puke()
        except ProxyError:
            raise
            
  Darglint would report an error.  It no longer reports
  an error in this case.  See Issue #88 and Issue #68.

## [1.3.0]

### Fixed

- A race condition in the integrity checker.  I had moved
  the function to be an instance variable, rather than a
  member of the class, but I had forgotten to do so with
  the docstring representation.  So, if the next docstring
  was fast enough to parse, it could override the previous
  docstring.  This didn't happen often because parsing
  is what takes the longest, and there is a high variability
  between the time it takes to parse each docstring.
- Handle newline after exception in raises section.  Rather
  than failing to parse the raises section, it now reports
  an indentation error.


## [1.2.3]

### Changed

- Made ordering of error messages more strict.  Error messages
  are grouped by function, then sorted alphabetically, then
  sorted in place by their line numbers within the function
  groups.

### Fixed

- Handle the else branch of try-except statements when searching
  for raise statements during analysis.
- Handle empty type in Google-style arguments (previously raised
  an exception, now it's a darglint error with a description.)
- Handle exceptions raised by the Python module, ast.
- Handle a bare raise statement within an exception handler.
  For example, if you have

    try:
        raise SyntaxError('Wrong!')
    except SyntaxError:
        raise

  Then you know that you really have to document a syntax
  error.

## [1.2.2]

### Fixed

- Certain versions of Python failed with in analysis,
  complaining of a missing 'id' attribute.

## [1.2.1]

### Added

- Merged in a configuration file for the pre-commit project.
  Thanks to @mikaelKvalvaer for the PR and @nioncode for
  pointing out the advantages of this configuration.

### Changed

- Made error analysis more robust.  Previously, errors were
  compared simply by looking a the name in the `raises` statement.
  Now analysis builds contexts around try-except blocks, and
  accounts for the catch-and-throw pattern.  Anything unusual
  will still raise an error, but it's more robust than previously.

### Fixed

- Fixed the handling of breaks in item descriptions.  Thanks to
  lvermue@ for the pull request and submitting the bug.

## [1.2.0]

### Added

- Added initial implementation for the numpy docstring format to
  darglint.  Support for this docstring format is not yet stable,
  and may have performance problems specific to the format.

## [1.1.3]

### Fixed

- Add error number to exceptions raised when using the flake8
  runner.  This allows flake8 to report the error without
  incorrectly unpacking the string.
- Fix sphinx return type annotation.  Previously, there was an
  inline return type which was accepted, in the format
  `:return x: Explanation.` where `x` is the type returned.
  However, this should really only be handled by the `:rtype:`
  section.  This incorrect return type was labelled using the
  same node name as the normal return type, leading to an
  assertion being raised.  The inline return type was removed.

## [1.1.2]

### Changed

- Allow for two-space indentation.
- Make the asterisk(s) in star arguments optional.

## [1.1.1]

### Added

- Added compatibility test for Darglint with flake8-docstrings and
  flake8-rst-docstrings.

## [1.1.0] - 2019-10-19

### Added
- Added `DAR104` which checks for the presence of types in the docstring.

### Fixed

- Updated the flake8 entry point to reflect the new error codes.

## [1.0.0] - 2019-10-19

### Changed

- Updated readme and error description list.
- Move debug- or test-only functions to utils file.  Probably this
  won't help much with load times or memory use, but it will at least
  reduce the risk of parse errors from that code.
- Removed the *google_types.py* target, since that is not used directly
  by any source code. (*google_types.bnf* is imported by other BNF files,
  only.)

### Fixed

- Fixed mypy errors in darglint.

## [1.0.0-alpha.2] - 2019-09-29

### Changed

- Changed the error code prefixes from "I" and "S" to "DAR".  This
  will prevent collisions with other utilities reported through flake8.
  See Issue #40.

### Fixed

- UTF-8 encoded source files were not working previously.  Rather than
  reading the string (and forcing an encoding on the data), we're now
  reading bytes and passing that along to the `ast` module. See Issue #46.

## [1.0.0-alpha.1] - 2019-09-28

### Changed

- Changed the long description format to text/markdown.

## [1.0.0-alpha] - 2019-09-28

### Added

- A *bin/* folder to hold various development utilities for darglint.
  Currently, it holds `bnf_to_cnf` (a utility to convert BNF grammars to
  CNF grammars), and `doc_extract` (a utility to extract docstrings from
  repositories, and annotate them for use in integration tests.)

- A (crappy) integration test framework.  Test fixtures are ignored in git,
  since the integration tests are only relevant for local development (and
  even then, mostly just release).  The integration tests are as follows:

  - *goldens.py*: Tests against goldens for individual docstrings.  This
  attempts to ensure that parsed docstrings always contain the expected
  sections after development.  Goldens are generated using the `doc_extract`
  utility in the *bin/* folder.

  - *grammar_size.py*: Tests that the grammar size doesn't increase
  significantly.  Larger grammars will result in longer parse times, and it
  could be relatively easy to accidentally introduce a much larger grammar.

  - *performance.py*: Tests performance of the parser against individual
  docstrings to make sure we don't introduce a performance regression.  Also
  tests performance for individual files in some repositories.

  - TODO: We still need to add some tests against multiple configurations,
  and against entire repositories.

### Changed

- Changed the recursive descent parser to a CYK parser.  This was a significant
  change.  It makes darglint much more flexible and extensible.  However, it
  also introduces a significant performance regression.  For that reason, this
  will be released first as an alpha, while I figure out how to handle the
  performance regression (or I determine whether or not it's even all that
  important of a problem.)

## [0.6.1] - 2019-08-11

### Fixed

- Incorrect configuration for flake8.  See Issue #35.

- Incorrect check for strictness options *long* and *full*.  See Issue #37.

Thanks to sobolevn for these fixes!

## [0.6.0] - 2019-08-10

### Added

- Minimum strictness configuration option.  You can now specify a minimum
  amount of strictness to have when checking docstrings.  Strictness does
  not affect whether the docstring will be checked or not; it only changes
  the amount of checking which is done.  For example, if your config file
  looks like

    [darglint]
    strictness=short

  Then the following would pass with no errors:

    def double(x):
        """Returns the number, multiplied by two."""
        return x * 2

  The following levels of strictness are available:

  - short: One-line descriptions are acceptable;
  anything more and the docstring will be fully checked.

  - long: One-line descriptions and descriptions
  without arguments/returns/yields/etc. sections will be
  allowed.  Anything more, and the docstring will be fully
  checked.

  - full: (Default) Docstrings will be fully
  checked.

## [0.5.8] - 2019-08-06

### Fixed

- Syntax error when logging about unusual raises description.
  (See Issue #34).

## [0.5.7] - 2019-07-20

### Fixed

- Handle async function definitions.  Previously they were simply skipped.
  Thanks to @zeebonk!

## [0.5.6] - 2019-06-03

### Fixed

- Erroneous I203 was being raised for return type when one of the
  type annotations was missing (it should only ever be raised when
  both type signatures are present.)  Thanks to @asford!

## [0.5.5] - 2019-05-19

### Fixed

- Try-block handlers were not included when tranversing the function
  ast.  This meant that return or yield statements in the except-block
  or else block would not register, and an exception would be raised.

- Allow indents in types. This lets us handle line continuation for
  type signatures.

- Fix appropriate noqas not hiding S001. (Because the docstring is never
  actually parsed when it's a syntax error.)

## [0.5.4] - 2019-04-03

### Fixed

- Fixed double reports from flake8.  These were occurring due to the two
  entry points listed in the setup file.  Currently, the fix just uses two
  temporary subclasses that filter the response from running Darglint.
  Ideally, flake8 would not run the same program twice -- a script may want
  to report more than one error code.  (As is the case here.)


## [0.5.3] - 2018-11-28

### Added

- The ability to read from stdin, which should make it easier to
  integrate darglint into other tools.

### Removed

- The restriction that a file must end in `.py`.


## [0.5.2] - 2018-11-23

### Changed

- Simplified the interface for the Docstring base class.  This should
  make modifications easier, and should ensure that the same value is
  returned consistently between Google and Sphinx styles.

  This comes at the cost of a slightly more complicated function signature
  for the functions which remain.  However, the single parameter which
  is passed to the functions (an enumeration named `Sections`), can
  (and should) be used everywhere the `NodeType` enumeration is currently
  used (outside of the actual parsing step.)  This will effectively create
  a firewall around the parsing step.

### Fixed

- Fix the parser failing on single-word return description.


## [0.5.1] - 2018-11-10

### Added

- Check for excess variable descriptions in Sphinx docstrings.  If the
  docstring contains `:var <name>:`, and the *name* doesn't exist in
  the actual function, an error will be issued.

### Fixed

- Parser exception being thrown when there is a whitespace-only line
  with indentation at the same level as an item within a compound section.
  (See Issue #7.)

## [0.5.0] - 2018-08-25

### Added

- Support for using Darglint as a Flake8 extension.  If Flake8 and Darglint
  are installed in the same environment, Darglint will issue warnings through
  Flake8.

## [0.4.0] - 2018-06-14

### Added

- Parser for sphinx-style docstrings.  This parser handles most
  sphinx-style docstrings, but adds certain restrictions.  For example,
  the fields such as `:returns:` must be the last items in the docstring,
  must be together, and any multiple lines must be indented with four spaces.
- Pipfile for setup with pipenv.

## [0.3.4] - 2018-05-22

### Added

- Previously, *darglint* always exited with status 0, even if errors
  were encountered.  Now, darglint exists with status 1 if docstring
  errors were encountered.
- Add description of errors to both the readme and the driver.
  The errors are each described on a single line to make it easy
  to search for errors from the command line.

### Fixed

- Fix regression in type hints: Deque was only available in Python3.6.


## [0.3.3] - 2018-05-13

### Changed

- Update the line numbers to be closer to the actual source of problems.

## [0.3.2] - 2018-05-05

### Changed

- Change the parser to a recursive descent parser.  This allows
  greater precision and flexibility.  It will also make it possible
  to capture and pass along line numbers.

## [0.3.1] - 2018-02-11

### Added

- Line numbers added to `Token`s.  The line numbers are added
  and incremented in the `lex()` function.

## [0.3.0] - 2018-02-11

### Added

- Message templates for error reports based on Pylint's syntax.
  The message template uses a normal Python format string with
  named arguments.  For example, the default format string
  for an error message is '{path}:{obj}:{line}: {msg_id}: {msg}'.

  This is passed to the linter by a command-line argument.
  For example, to get only the path, line number, and error code,
  we could pass something like the following:

```
darglint -m "{path}:{line} -> {msg_id}" *.py
```

  This value can also be specified in the configuration file
  as the value, `message_template`.  For example, the above
  template could have been specified in the configuration
  as

```
[darglint]
message_template={path}:{line} -> {msg_id}
```

## [0.2.0]

### Added

- Added support for Python3.5.  Probably earlier versions of Python
  can also be supported, but they need to be tested, first.

- Added *tox* script for running tests against all environments.
  To run the tests, make sure the test dependencies are installed,
  and run

```
tox
```

## [0.1.2]

### Added

- Allow global noqa statements in docstring.  If we have a docstring
  which we would like to ignore (say, because it has a different
  format), then we can ignore it either by adding "# noqa" or
  "# noqa: \*" to it.

  For example, the following program would raise an exception that
  there is a missing "Returns" section:

```
def is_palindrome(word):
    """True if the word is a palindrome.

    # noqa

    """
    return word == word[::-1]
```

  However, since there is a global noqa statement, all errors are
  ignored.

## [0.1.1]

### Added

- Added a mechanism for raising more specific style errors from the
  parser.  Unfortunately, the parser does not have access to the
  functions whose docstrings are being parsed.  (These two halves are
  put together in the `IntegrityChecker`.)  The parser cannot raise
  specific error messages, then, since it can't access the function.
  So, currently, the `ParserException` takes an optional, more
  specific error, which can be created by the `IntegrityChecker`.

### Fixed

- Fixed broken unit test.

## [0.1.0]

### Fixed

- Made error handling more robust.  If darglint is unable to parse, now,
  it will display an error message for that function.  This error message
  is taken from the assert statements in the parser, or is a general
  message.  This, at least, prevents an ugly stack trace and provides a
  model for how to handle style errors in the future.
- Fixed a couple of type errors.  Typing is either going to be removed
  or moved to a different format to allow for < Python3.6.
- Previously, returns in inner functions would raise errors for missing
  returns sections in the docstring, even if (for example), the parent
  function yielded values.  For example:
- Broken tests were fixed. (The `ast` module does not return functions
  in any particular order, but tests were relying on a specific order.)

```
def walk(root):
    """Walk the tree, yielding active nodes.

    Args:
        root: The root of the tree.

    Yields:
        Active nodes.

    """
    def skip(node):
        return node.inactive
    queue = deque()
    queue.append(root)
    while len(queue) > 0:
        curr = queue.pop()
        if skip(curr):
            continue
        yield curr
        queue.extend(curr.children)
```

  This function previously would have raised a missing return error
  (I201), and would have required a noqa.  That is no longer the case.

### Changed

- Renamed "darglint.py" to a more appropriate name: "function_description.py".

### Added

- `ParserException` is thrown if there is no colon after the type annotation
  or argument/exception in the description.

  For example, the following function would raise the `ParserException`:

```
def hello(name):
    """Say hello to the person.

    Args:
        name: The name of the person to
	whom we are saying hello.

    """
    print('hello, {}'.format(name))
```

- Added optional hint to the function `_expect_type` in `darglint/parse.py`.
  This will be displayed after the default message.  We'll have to add
  an option for hints in the configuration, and show or hide them accordingly.

- Added check to ensure that a description exists after an item in the
  argument descriptions or exception descriptions (or any multi-section).
  At some point, this should probably be optional, but it is currently
  raises a `ParserException` (which is too general to really want to
  exclude.)

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
      """Return the value, 3.

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
