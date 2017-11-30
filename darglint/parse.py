r"""Defines the parse function.

__EBNF for a google-style docstring__:

  <docstring> ::= <empty-short-description>
              | <full-short-description><long-description><docterm>
              | <full-short-description>
                  [<long-description>]
                  <section>+
                <docterm>
  <long-description> ::= <line>+<newline>
  <short-description> ::= <empty-short-description>|<full-short-description>
  <full-short-description> ::= <doc-term><line><newline>
  <empty-short-description> ::= <doc-term><nnline><doc-term>
  <section> ::= <single-section>|<multi-section>
  <multi-section> ::= <empty-headline>
                        (<full-headline>(<indent><line>)*)+
                        <newline>
  <single-section> ::= <emtpty-headline>(<indent><line>)+<newline>
     | <full-headline>(<indent><line>)*<newline>
  <headline> ::= <empty-headline>|<full-headline>
  <empty-headline> ::= <keyword><colon><newline>
  <full-headline> ::= <keyword><colon><space><line>
  <line> ::= <nnline><newline>
  <nnline> ::= (<word><space>+)*<word>
  <keyword> ::= "Args"
            | "Arguments"
            | "Returns
            | "Yields"
            | "Raises"
  <word> ::= <content>*
  <colon> ::= ":"
  <indent> ::= <space>{4}
  <space> ::= " "
  <newline> ::= "\n"
  <content> ::= A letter, special character, or number.
  <doc-term> ::= \"\"\"

"""

from itertools import chain
from typing import (
    Callable,
    Dict,
    Iterable,
    Tuple,
)

from .config import get_logger
from .token import Token, TokenType
from .peaker import Peaker

logger = get_logger()


class ParserException(BaseException):
    """The exception raised when there is a parsing problem."""

    pass


def _expect_type(peaker: Peaker[Token], expected_type: TokenType):
    """Raise an exception if peaker's next value isn't the given type.

    Args:
        peaker: The peaker to check.  Should have the given type next.
        expected_type: The type we expect to see next.

    Raises:
        ParserException: If the next token in the Peaker is not of the
            expected type.

    """
    actual_type = peaker.peak().token_type
    if actual_type != expected_type:
        msg = ''
        if actual_type == TokenType.WORD:
            msg = 'Exected type {}, but was {}: "{}"'.format(
                expected_type,
                actual_type,
                peaker.peak().value,
            )
        else:
            msg = 'Expected type {}, but was {}.'.format(
                expected_type,
                actual_type,
            )
        raise ParserException(msg)


def _is_type(peaker: Peaker[Token], token_type: TokenType) -> bool:
    """Tell if the next token in the Peaker is of the given type.

    Args:
        peaker: A peaker holding tokens.
        token_type: A TokenType we are looking for.

    Returns:
        True if the next token in the peaker is of the given type.

    """
    return peaker.peak().token_type == token_type


def _not(*fns) -> Callable:
    """Negates a function which returns a boolean.

    Args:
        *fns: Functions which returns a boolean.

    Returns:
        A function which returns fallse when any of the callables
        return true, and true will all of the callables return false.

    """
    def inner(*args, **kwargs):
        return not any([fn(*args, **kwargs) for fn in fns])
    return inner


def _token_is(token_type: TokenType) -> Callable:
    """Return a checker function for a token.

    Args:
        token_type: The type we wish to have a checker for.

    Returns:
        A function which returns a true if the when supplied
        a token of the given type.

    """
    def check_type(token: Token) -> bool:
        return token.token_type == token_type
    return check_type


class Docstring(object):
    """Represents a google - style docstring."""

    RETURNS = ('Returns',)
    ARGS = ('Args', 'Arguments')
    YIELDS = ('Yields',)
    RAISES = ('Raises',)
    keywords = tuple(chain(
        RETURNS,
        ARGS,
        YIELDS,
        RAISES
    ))

    def __init__(self, tokens: Iterable[Token]) -> None:
        """Create a new docstring from the stream of tokens.

        Attributes of the class either detail descriptions, or
        noqa statements (errors to ignore for a given detail.)

        For example, if we wish to ignore an extra member in the
        raises section, (say, a ZeroDivisionError, because we are
        doing some division, and we want to allow the error to
        propagate up), then we would have the key and item
        `('I402', ['ZeroDivisionError'])` in the noqa dictionary.

        If a noqa statement is for a global member of the docstring
        (such as the return statement or short description), then
        the item may be None.  For example, to ignore a missing
        return, we would have `('I201', None)` in the noqa dictionary.

        Noqa statements should appear either after the section/argument
        they reference, or at the end of the long description.

        Args:
            tokens: A stream of tokens.

        """
        self.short_description = ''
        self.long_description = ''
        self.arguments_descriptions = dict()  # type: Dict[str, str]
        self.argument_types = dict()  # type: Dict[str, str]
        self.returns_description = ''
        self.return_type = None  # type: str
        self.yields_description = ''
        self.raises_descriptions = dict()  # type: Dict[str, str]
        self.noqa = dict()  # type: Dict[str, str]

        self._peaker = Peaker(tokens)
        self._parse()

    def _dispatch(self, keyword: str):
        """Parse the section described by the keyword.

        Args:
            keyword: The word which starts this section.

        # noqa: I401 Exception

        """
        _expect_type(self._peaker, TokenType.COLON)
        self._peaker.next()

        if keyword in self.RETURNS:
            self._parse_return()
        elif keyword in self.YIELDS:
            self._parse_yield()
        elif keyword in self.ARGS:
            self._parse_arguments()
        elif keyword in self.RAISES:
            self._parse_raises()
        else:
            raise Exception('Unexpected section keyword "{}"'.format(
                keyword
            ))

    def _parse(self):
        if not self._peaker.has_next():
            return
        self._parse_short_description()

        if not self._peaker.has_next():
            return
        _expect_type(self._peaker, TokenType.NEWLINE)
        self._peaker.take_while(_token_is(TokenType.NEWLINE))
        # _expect_type(self._peaker, TokenType.WORD)

        is_keyword = self._peaker.peak().value in self.keywords
        if not is_keyword:
            self._parse_long_description()

        while self._peaker.has_next():
            is_keyword = self._peaker.peak().value in self.keywords
            is_hash = self._peaker.peak().token_type == TokenType.HASH
            is_newline = self._peaker.peak().token_type == TokenType.NEWLINE
            if is_keyword:
                keyword = self._peaker.next().value
                _expect_type(self._peaker, TokenType.COLON)
                self._dispatch(keyword)
            elif is_hash:
                self._parse_possible_noqa(None)
            elif is_newline:
                self._peaker.next()
            else:
                # ignore -- it's an uknown section type and not a noqa.
                self._parse_line(None)

    def _parse_short_description(self):
        self.short_description = self._parse_line(None)

    def _parse_long_description(self):
        while self._peaker.has_next():
            is_keyword = self._peaker.peak().value in self.keywords
            if is_keyword:
                return
            space = ' ' if self.long_description != '' else ''
            while not self._at_terminal():
                self.long_description += space + self._parse_line(None)
            self._peaker.take_while(_token_is(TokenType.NEWLINE))

    def _parse_multi_section(self) -> Dict[str, Tuple[str, str]]:
        """Parse a multi - section.

        Returns:
            A dictionary containing the headline as key and the
            type and description as a values (in a tuple).

        """
        _expect_type(self._peaker, TokenType.NEWLINE)
        self._peaker.next()
        _expect_type(self._peaker, TokenType.INDENT)

        descriptions = dict()
        indents_to_argument = len(self._peaker.take_while(
            _token_is(TokenType.INDENT)))

        # Parse the whole section
        while not _is_type(self._peaker, TokenType.NEWLINE):
            _expect_type(self._peaker, TokenType.WORD)
            word = self._peaker.next().value
            word_type = None
            if _is_type(self._peaker, TokenType.COLON):
                _expect_type(self._peaker, TokenType.COLON)
                self._peaker.next()
            elif _is_type(self._peaker, TokenType.WORD):
                word_type = self._peaker.next().value
                if not (word_type.startswith('(') and word_type.endswith(')')):
                    # Raise exception
                    pass
                word_type = word_type[1:-1]

            current_indents = indents_to_argument + 1
            word_description = ''

            # Parse the subsection
            while current_indents > indents_to_argument:
                word_description = self._parse_line(word)

                # If we're at the end of the docstring, finish the routine.
                if not self._peaker.has_next():
                    break

                self._peaker.next()
                current_indents = len(self._peaker.take_while(
                    _token_is(TokenType.INDENT)))
            descriptions[word] = (word_type, word_description)

            # If this is the last section, end the algorithm.
            if not self._peaker.has_next():
                break

        return descriptions

    def _parse_single_section(self) -> str:
        """Parse a single section.

        Returns:
            The string parsed, which represents a single section.

        """
        description = ''

        # The text is to the right of the heading.
        if _is_type(self._peaker, TokenType.WORD):
            description += self._parse_line(None)
            if not self._peaker.has_next():
                return description

        _expect_type(self._peaker, TokenType.NEWLINE)
        self._peaker.next()
        indents = None

        # We check for two newlines, because we could have a block below
        # this one.
        while not _is_type(self._peaker, TokenType.NEWLINE):
            new_indents = self._peaker.take_while(_token_is(TokenType.INDENT))
            if indents is None:
                indents = len(new_indents)
            else:
                # Assert that they should be equal, and display error
                pass
            description += self._parse_line(None)

            # If we're at the end of the docstring, finish the routine.
            if not self._peaker.has_next():
                break
            _expect_type(self._peaker, TokenType.NEWLINE)
            self._peaker.next()
        return description

    def _at_terminal(self) -> bool:
        """Return true if at line terminal: newline or empty.

        Returns:
            True if we are at a newline or there are more tokens;
                false otherwise.

        """
        is_empty = not self._peaker.has_next()
        if is_empty:
            return True
        newline_is_next = _is_type(self._peaker, TokenType.NEWLINE)
        if newline_is_next:
            return True

    def _parse_line(self, target) -> str:
        """Parse up to the newline, returning the string representation.

        Recursively gets the words in the line, up to (but not including)
        the newline.

        Args:
            target: If we are parsing an argument description or raises
                description, target is the argument/exception we are
                describing.

        Returns:
            Space-separated values of the tokens up to the newline.

        """
        if _is_type(self._peaker, TokenType.NEWLINE):
            return ''
        elif _is_type(self._peaker, TokenType.HASH):
            return self._parse_possible_noqa(target)

        word = self._peaker.next().value
        if self._at_terminal():
            return word
        else:
            return word + ' ' + self._parse_line(target)

    def _parse_possible_noqa(self, target) -> str:
        """Return the value if it's not noqa, otherwise return blank.

        This should be called when we encounter a hash mark.  If there
        is a valid noqa after the hash, then it will be added to the noqa
        dictionary, and a blank string will be returned.  Otherwise, the
        hash and whatever comes after it will be returned.

        Does not consume the newline.

        Args:
            target: None if we are at the global scope.  If we are in a
                section, then it should be the current parameter/error
                whose description we are parsing.

        Returns:
            A string which is either blank, or represents the tokens up to
            the newline.

        """
        def add_to_errors(error, item):
            # Target should be none only if it is always a global attribute.
            if item is None:
                self.noqa[error_to_ignore] = None
            else:
                if error_to_ignore not in self.noqa:
                    self.noqa[error_to_ignore] = list()
                self.noqa[error_to_ignore].append(item)

        _expect_type(self._peaker, TokenType.HASH)
        self._peaker.next()

        if not self._peaker.has_next():
            return '#'

        # If it's not a noqa statement, then return up to the newline.
        is_word = self._peaker.peak().token_type == TokenType.WORD
        is_noqa = False if not is_word else self._peaker.peak().value == 'noqa'
        if not (is_word and is_noqa):
            return '# ' + self._parse_line(target)

        self._peaker.next()
        _expect_type(self._peaker, TokenType.COLON)
        self._peaker.next()
        _expect_type(self._peaker, TokenType.WORD)
        error_to_ignore = self._peaker.next().value

        # If we're at the end of the line, add to errors and return
        if self._at_terminal():
            add_to_errors(error_to_ignore, target)
            return ''

        # Otherwise, we are specifying a target, so grab it, add and return.
        _expect_type(self._peaker, TokenType.WORD)
        target = self._peaker.next().value
        add_to_errors(error_to_ignore, target)
        return ''

    def _parse_arguments(self):
        descriptions = self._parse_multi_section()
        self.arguments_descriptions = {
            key: descriptions[key][1] for key in descriptions
        }
        self.argument_types = {
            key: descriptions[key][0] for key in descriptions
        }

    def _parse_yield(self):
        self.yields_description = self._parse_single_section()

    def _parse_return(self):
        self.returns_description = self._parse_single_section()

        if self.returns_description is None:
            logger.error(
                'Error while parsing returns section for docstring '
                'beginning "%s..."' % self.short_description[:30]
            )

        # Attempt to remove the return type, if any.
        try:
            colon_index = self.returns_description.index(':')
            up_to_colon = self.returns_description[:colon_index].strip()
            spaces = up_to_colon.count(' ')
            colon_after_first_word = spaces == 0
            if colon_after_first_word:
                self.return_type = up_to_colon
                self.returns_description = self.returns_description[
                    colon_index + 2:]
        except ValueError:
            # There was no colon, and, hence, no return type.
            pass

    def _parse_raises(self):
        self.raises_descriptions = {
            key: value[1] for key, value in self._parse_multi_section().items()
        }
