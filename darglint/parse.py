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


def _token_is_args(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Args', 'Arguments'])


def _token_is_return(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Returns'])


def _token_is_yield(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Yields'])


def _token_is_raises(token: Token) -> bool:
    return (token.token_type == TokenType.WORD
            and token.value in ['Raises'])


def _parse_argument(peaker: Peaker, indentation: int) -> str:
    """Return the name from a section with indentation, a name, and a colon.

    Args:
        peaker: Contains the tokens to parse.
        indentation: The number of INDENT tokens before each definition.
            This should be set by the first argument.

    Returns:
        The name of the argument.

    """
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

    Returns:
        A set of parameters to the function.

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

    Returns:
        A set containing the return node's string, or
        an empty set (if there is no return).

    """
    peaker = Peaker(tokens)
    peaker.take_while(_not(_token_is_return))
    if peaker.has_next():
        return {peaker.next().value}
    else:
        return set()


def parse_yield(tokens: Iterable[Token]) -> Set[str]:
    """Parse the stream of tokens in a docstring.

    Args:
        tokens: The tokens we want to parse.

    Returns:
        A set containing the return node's yield string,
        or an empty set (if there is no yield section.)

    """
    peaker = Peaker(tokens)
    peaker.take_while(_not(_token_is_yield))
    if peaker.has_next():
        return {peaker.next().value}
    else:
        return set()


def parse_raises(tokens: Iterable[Token]) -> Set[str]:
    """Parse the stream of tokens in a docstring for a Raises section.

    Args:
        tokens: The tokens we want to parse.

    Returns:
        A set containing "Raises", or an empty set (if there is
        no raises section.)

    """
    peaker = Peaker(tokens)
    peaker.take_while(_not(_token_is_raises))

    # There is no Raises section.
    if not peaker.has_next():
        return set()

    _expect_type(peaker, TokenType.WORD)  # Raises
    peaker.next()
    _expect_type(peaker, TokenType.COLON)
    peaker.next()
    _expect_type(peaker, TokenType.NEWLINE)
    peaker.next()

    raises = set()
    indents = peaker.take_while(_token_is(TokenType.INDENT))

    while peaker.has_next() and not _is_type(peaker, TokenType.NEWLINE):
        raises.add(_parse_argument(peaker, indentation=len(indents)))
    return raises
