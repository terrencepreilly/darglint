"""Defines the parse function."""

from typing import Callable, Iterable, Set

from .token import Token, TokenType
from .peaker import Peaker


class ParserException(BaseException):
    """The exception raised when there is a parsing problem."""

    pass

# Pseudocode
#
# A docstring is expected to be in the following format:
#
#    <docstring > ::= <doc-term><content><doc-term>
#        | <doc-term><explanation><newline>
#              (<explanation-section><newline>)?
#              <arguments-section>?
#              (<return-section>|<yield-section>)?
#          <doc-term>
#    <yield-section> ::= Yields: <explanation>+<newline>
#    <return-section> ::= Returns: <explanation>+<newline>
#    <arguments-section> ::= Args:<newline><argument>+
#    <argument> ::= <name>: <explanation>[<indent><explanation>]*
#    <name> ::= \w[\w\d\_]*
#    <explanation-section> ::= [explanation]+<newline>
#    <explanation> ::= [<content><newline>]+
#    <newline> ::= '\n'
#    <indent> ::= '    '
#    <content> ::= '\w', '\ ', or special characters
#    <doc-term > ::= """


def _expect_not_empty(peaker: Peaker[Token]):
    """Raise an exception if peaker is empty.

    Args:
        peaker: The peaker to check to see if it is empty.
    """
    if not peaker.has_next():
        raise ParserException('End of stream unexpectedly encountered')


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
    return peaker.peak().token_type == token_type


def _not(*fns) -> Callable:
    """Negates a function which returns a boolean.

    Args:
        fn: A function which returns a boolean.

    """
    def inner(*args, **kwargs):
        return not any([fn(*args, **kwargs) for fn in fns])
    return inner


def _token_is(token_type: TokenType) -> Callable:
    """Return a checker function for a token.

    Args:
        token_type: The type we wish to have a checker for.
    """
    def check_type(token: Token) -> bool:
        return token.token_type == token_type
    return check_type


def _token_is_args(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Args', 'Arguments'])


def _token_is_return(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Returns'])


def _parse_argument(peaker: Peaker, indentation: int) -> str:
    _expect_type(peaker, TokenType.WORD)
    arg = peaker.next()
    # get the type?
    # get the definition?
    peaker.take_while(_not(_token_is(TokenType.NEWLINE)))

    if not peaker.has_next():
        # We're at the end of the arguments, there is no return.
        return arg.value

    peaker.next()  # consume the newline.
    indents = peaker.take_while(_token_is(TokenType.INDENT))
    # While we are one indentation in on the Argument.
    while len(indents) >= indentation + 1:
        peaker.take_while(_not(_token_is(TokenType.NEWLINE)))
        if not peaker.has_next():
            # We're at the end of the arguments.
            break
        peaker.next()
        indents = peaker.take_while(_token_is(TokenType.INDENT))
    return arg.value


def parse_arguments(tokens: Iterable[Token]) -> Set[str]:
    """Parse the stream of tokens into a `Docstring`.

    Args:
        tokens: The tokens which we want to parse.

    """
    peaker = Peaker(tokens)

    # Toss away everything up to Args
    peaker.take_while(_not(_token_is_args))

    if not peaker.has_next():
        return set()

    peaker.next()
    _expect_type(peaker, TokenType.COLON)
    peaker.next()
    _expect_type(peaker, TokenType.NEWLINE)
    peaker.next()

    args = set()
    indents = peaker.take_while(_token_is(TokenType.INDENT))

    # Parse until there is a second newline.
    # (_parse_argument consumes the newline after the arg.)
    while peaker.has_next() and not _is_type(peaker, TokenType.NEWLINE):
        args.add(_parse_argument(peaker, indentation=len(indents)))
    return args


def parse_return(tokens: Iterable[Token]) -> Set[str]:
    """Parse the stream of tokens into a `Docstring`.

    Args:
        tokens: The tokens which we want to parse.

    """
    peaker = Peaker(tokens)
    peaker.take_while(_not(_token_is_return))
    if peaker.has_next():
        return set(peaker.next().value)
    else:
        return set()
