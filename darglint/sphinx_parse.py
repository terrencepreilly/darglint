from typing import List

from .node import (
    Node,
    NodeType,
)
from .peaker import Peaker
from .token import (
    Token,
    TokenType,
)
from .parse import (
    Assert,
    AssertNotEmpty,
    ParserException,
    parse_colon,
    parse_hash,
    parse_indent,
    parse_keyword,
    parse_lparen,
    parse_noqa,
    parse_rparen,
    parse_word,
)

KEYWORDS = {
    'Args': NodeType.ARGUMENTS,
    'Arguments': NodeType.ARGUMENTS,
    'Returns': NodeType.RETURNS,
    'Yields': NodeType.YIELDS,
    'Raises': NodeType.RAISES,
}


def _in_keywords(peaker, offset=1):
    # type: (Peaker[Token], int) -> bool
    token = peaker.peak(offset)
    if token is None:
        return False
    return token.value in KEYWORDS


def _is(expected_type, peaker, offset=1):
    # type: (TokenType, Peaker[Token], int) -> bool
    """Check if the peaker's next value is the given type.

    Args:
        expected_type: The type we're checking.
        peaker: The peaker.
        offset: The lookahead to use.  (Most of the time, this
            will be 1 -- the current token.)

    Returns:
        True if the next token is the given type, false
        otherwise. (Including if there are no more tokens.)

    """
    token = peaker.peak(offset)
    if token is not None:
        return token.token_type == expected_type
    return False


def parse_line(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'Parsing line.')
    children = []  # type: List[Node]

    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker):
        if _is(TokenType.WORD, peaker) and _in_keywords(peaker):
            children.append(parse_keyword(peaker))
        elif _is(TokenType.WORD, peaker):
            children.append(parse_word(peaker))
        elif _is(TokenType.COLON, peaker):
            children.append(parse_colon(peaker))
        elif _is(TokenType.INDENT, peaker):
            children.append(parse_indent(peaker))
        elif _is(TokenType.LPAREN, peaker):
            children.append(parse_lparen(peaker))
        elif _is(TokenType.RPAREN, peaker):
            children.append(parse_rparen(peaker))
        elif _is(TokenType.HASH, peaker):
            token = peaker.peak(lookahead=2)
            if token is not None and token.value == 'noqa':
                children.append(parse_noqa(peaker))
            else:
                children.append(parse_hash(peaker))
        else:
            token = peaker.peak()
            assert token is not None
            raise ParserException('Unexpected type {} in line.'.format(
                token.token_type
            ))

    # It is possible that there are no children at this point, in
    # which case there is likely just the newline.  In this case,
    # we try to set the token so that the line can have a line
    # number.
    token = None
    if peaker.has_next():
        if not children:
            token = peaker.next()
        else:
            peaker.next()  # Throw away newline.
    return Node(
        NodeType.LINE,
        children=children,
        token=token,
    )


def parse_short_description(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse line')
    Assert(
        not _is(TokenType.NEWLINE, peaker),
        'Must have short description in docstring.'
    )
    return Node(
        NodeType.SHORT_DESCRIPTION,
        children=[parse_line(peaker)],
    )
