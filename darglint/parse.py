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
)

from .token import Token, TokenType
from .peaker import Peaker


class ParserException(BaseException):
    """The exception raised when there is a parsing problem."""

    pass


def _expect_type(peaker: Peaker[Token], token_type: TokenType):
    """Raise an exception if peaker's next value isn't the given type.

    Args:
        peaker: The peaker to check.  Should have the given type next.
        token_type: The type we expect to see next.

    """
    if peaker.peak().token_type != token_type:
        raise ParserException('Expected type {}, but was {}.'.format(
            token_type,
            peaker.peak().token_type,
        ))


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
        fns: Functions which returns a boolean.

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

    def __init__(self, tokens: Iterable[Token]):
        """Create a new docstring from the stream of tokens.

        Args:
            tokens: A stream of tokens.

        """
        self.short_description = ''
        self.long_description = ''
        self.arguments_descriptions = dict()  # type: Dict[str, str]
        self.returns_description = ''
        self.yields_description = ''
        self.raises_descriptions = dict()  # type: Dict[str, str]

        self._peaker = Peaker(tokens)
        self._parse()

    def _dispatch(self, keyword: str):
        """Parse the section described by the keyword."""
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

    def _parse(self):
        if not self._peaker.has_next():
            return
        self._parse_short_description()

        if not self._peaker.has_next():
            return
        _expect_type(self._peaker, TokenType.NEWLINE)
        self._peaker.take_while(_token_is(TokenType.NEWLINE))
        # Expect two newlines
        _expect_type(self._peaker, TokenType.WORD)

        sections_started = False  # True once we encounter Args, Returns, etc.
        while self._peaker.has_next():

            # Could be long description (multiple lines), or section.
            if not sections_started:
                word = self._peaker.next().value
                is_colon = self._peaker.peak().token_type == TokenType.COLON
                if word in self.keywords and is_colon:
                    self._dispatch(word)
            else:
                _expect_type(self._peaker, TokenType.WORD)
                self.long_description += ' '.join([
                    x.value for x in self._peaker.take_while(
                        _not(_token_is(TokenType.NEWLINE))
                    )
                ])
            self._peaker.take_while(_token_is(TokenType.NEWLINE))

    def _parse_line(self) -> str:
        """Get all of the text in a line.

        Consumes the newline.

        """
        content = self._peaker.take_while(_not(_token_is(TokenType.NEWLINE)))
        _expect_type(self.peaker, TokenType.NEWLINE)
        self.peaker.next()
        return content

    def _parse_short_description(self):
        _expect_type(self._peaker, TokenType.WORD)
        self.short_description = ' '.join([
            x.value for x in self._peaker.take_while(_token_is(TokenType.WORD))
        ])

    def _parse_arguments(self):
        self.arguments_descriptions = self._parse_multi_section()

    def _parse_multi_section(self) -> Dict[str, str]:
        """Parse a multi - section.

        Returns:
            A dictionary containing the headline as key and the
            description as a value.

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
            _expect_type(self._peaker, TokenType.COLON)
            self._peaker.next()
            current_indents = indents_to_argument + 1
            word_description = ''

            # Parse the subsection
            while current_indents > indents_to_argument:
                word_description += ' '.join([
                    x.value for x in self._peaker.take_while(
                        _not(_token_is(TokenType.NEWLINE)))])

                # If we're at the end of the docstring, finish the routine.
                if not self._peaker.has_next():
                    break

                self._peaker.next()
                current_indents = len(self._peaker.take_while(
                    _token_is(TokenType.INDENT)))
            descriptions[word] = word_description

            # If this is the last section, end the algorithm.
            if not self._peaker.has_next():
                break

        return descriptions

    def _parse_single_section(self):
        """Parse a single section."""
        description = ''

        # The text is to the right of the heading.
        if _is_type(self._peaker, TokenType.WORD):
            line = self._peaker.take_while(
                _not(_token_is(TokenType.NEWLINE)))
            description += ' '.join([x.value for x in line])
            if not self._peaker.has_next():
                return

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
            line_tokens = self._peaker.take_while(_not(
                _token_is(TokenType.NEWLINE)))
            description += ' '.join([x.value for x in line_tokens])

            # If we're at the end of the docstring, finish the routine.
            if not self._peaker.has_next():
                break
            _expect_type(self._peaker, TokenType.NEWLINE)
            self._peaker.next()
        return description

    def _parse_yield(self):
        self.yields_description = self._parse_single_section()

    def _parse_return(self):
        self.returns_description = self._parse_single_section()

    def _parse_raises(self):
        self.raises_descriptions = self._parse_multi_section()
