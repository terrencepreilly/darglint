"""Defines a function for lexing a comment, `lex`."""

from typing import (
    Iterator,
    List,
    Optional,
)
from .custom_assert import Assert
from .peaker import Peaker
from .token import Token, TokenType
from .config import (
    get_config,
)

# These convenience functions take an optional string
# because the peaker could return None when at the end
# of the stream.


def _is_space(char):
    # type: (Optional[str]) -> bool
    return char == ' '


def _is_newline(char):
    # type: (Optional[str]) -> bool
    return char == '\n'


def _is_colon(char):
    # type: (Optional[str]) -> bool
    return char == ':'


def _is_hash(char):
    # type: (Optional[str]) -> bool
    return char == '#'


def _is_separator(char):
    # type: (Optional[str]) -> bool
    """Check whether if `char` is a separator other than newline or space.

    Args:
        char: The character to check.

    Returns:
        true if `char` is a separator other than newline or space.

    """
    if char is None:
        return False
    return char.isspace() and not (_is_space(char) or _is_newline(char))


def _is_lparen(char):
    # type: (Optional[str]) -> bool
    return char == '('


def _is_rparen(char):
    # type: (Optional[str]) -> bool
    return char == ')'


def _is_hyphen(char):
    # type: (Optional[str]) -> bool
    return char == '-'


def _is_word(char):
    # type: (str) -> bool
    return not any([
        _is_space(char),
        _is_newline(char),
        _is_colon(char),
        _is_separator(char),
        _is_hash(char),
        _is_lparen(char),
        _is_rparen(char),
    ])


def lex(program):
    # type: (str) -> Iterator[Token]
    """Create a stream of tokens from the string.

    Args:
        program: The program to lex, as a string.

    Yields:
        Tokens lexed from the string.

    """
    extra = ''  # Extra characters which are pulled but unused from a check.
    peaker = Peaker((x for x in program or []))  # the stream
    line_number = 0

    # Set the amount of spaces which count as an indent.
    config = get_config()

    while peaker.has_next():
        # Each of the following conditions must move the stream
        # forward and -- excepting separators -- yield a token.
        if _is_space(peaker.peak()):
            spaces = ''.join(peaker.take_while(_is_space))
            for _ in range(len(spaces) // config.indentation):
                yield Token(' ' * 4, TokenType.INDENT, line_number)
        elif _is_newline(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.NEWLINE, line_number)
            line_number += 1
        elif _is_colon(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.COLON, line_number)
        elif _is_separator(peaker.peak()):
            peaker.take_while(_is_separator)
        elif _is_hash(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.HASH, line_number)
        elif _is_lparen(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.LPAREN, line_number)
        elif _is_rparen(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.RPAREN, line_number)
        elif _is_hyphen(peaker.peak()):
            value = ''.join(peaker.take_while(_is_word))
            if value.count('-') == len(value):
                yield Token(value, TokenType.HEADER, line_number)
            else:
                yield Token(value, TokenType.WORD, line_number)
        else:
            value = ''.join(peaker.take_while(_is_word))
            if extra != '':
                value = extra + value
                extra = ''
            Assert(
                len(value) > 0,
                "There should be non-special characters.",
            )
            yield Token(value, TokenType.WORD, line_number)


KEYWORDS = {
    'Args': TokenType.ARGUMENTS,
    'Arguments': TokenType.ARGUMENTS,
    'Yields': TokenType.YIELDS,
    'Raises': TokenType.RAISES,
    'Returns': TokenType.RETURNS,
    'noqa': TokenType.NOQA,
    'param': TokenType.ARGUMENTS,
    'parameter': TokenType.ARGUMENTS,
    'Parameters': TokenType.ARGUMENTS,
    'arg': TokenType.ARGUMENTS,
    'argument': TokenType.ARGUMENTS,
    'key': TokenType.VARIABLES,
    'keyword': TokenType.VARIABLES,
    'var': TokenType.VARIABLES,
    'ivar': TokenType.VARIABLES,
    'cvar': TokenType.VARIABLES,
    'type': TokenType.ARGUMENT_TYPE,
    'vartype': TokenType.VARIABLE_TYPE,
    'raises': TokenType.RAISES,
    'yield': TokenType.YIELDS,
    'yields': TokenType.YIELDS,
    'ytype': TokenType.YIELD_TYPE,
    'return': TokenType.RETURNS,
    'returns': TokenType.RETURNS,
    'rtype': TokenType.RETURN_TYPE,
    'Other': TokenType.OTHER,
    'Receives': TokenType.RECEIVES,
    'Warns': TokenType.WARNS,
    'Warnings': TokenType.WARNS,
    'See': TokenType.SEE,
    'Also': TokenType.ALSO,
    'Notes': TokenType.NOTES,
    'Examples': TokenType.EXAMPLES,
    'References': TokenType.REFERENCES,
}


def condense(tokens):
    # type: (Iterator[Token]) -> List[Token]
    """Condense the stream of tokens into a list consumable by CYK.

    This servers two purposes:

    1. It minimizes the lookup table used in the CYK algorithm.
       (The CYK algorithm is a dynamic algorithm, with one dimension
       in the two-dimension lookup table being determined by the number
       of tokens.)

    2. It applies more discriminate token types to the tokens identified
       by lex.  Eventually, this will be moved into the lex function.

    Args:
        tokens: The stream of tokens from the lex function.

    Returns:
        A List of tokens which have been condensed into as small a
        representation as possible.

    """
    ret = list()  # type: List[Token]
    try:
        curr = next(tokens)
    except StopIteration:
        return ret

    if curr.value in KEYWORDS:
        curr.token_type = KEYWORDS[curr.value]

    encountered_noqa = False

    for token in tokens:
        if token.token_type == TokenType.WORD and token.value in KEYWORDS:
            ret.append(curr)
            if token.value == 'noqa':
                encountered_noqa = True
            curr = Token(
                token.value,
                KEYWORDS[token.value],
                token.line_number,
            )
        elif token.token_type == TokenType.WORD:
            if curr.token_type == TokenType.WORD and not encountered_noqa:
                curr.value += ' {}'.format(token.value)
            else:
                ret.append(curr)
                curr = token
        elif token.token_type == TokenType.NEWLINE:
            ret.append(curr)
            curr = token
            encountered_noqa = False
        else:
            ret.append(curr)
            curr = token

    ret.append(curr)

    return ret
