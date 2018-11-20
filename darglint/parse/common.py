"""Common parsing utilities."""

from typing import (  # noqa: F401
    Any,
    Dict,
    Optional,
    Tuple,
)

from ..errors import (
    GenericSyntaxError,
)
from ..node import (
    Node,
    NodeType,
)
from ..peaker import (  # noqa: F401
    Peaker,
)
from ..token import (  # noqa: F401
    Token,
    TokenType,
)


def _is(expected_type, token):
    # type: (TokenType, Optional[Token]) -> bool
    assert token is not None
    return token.token_type == expected_type


class ParserException(BaseException):
    """The exception raised when there is a parsing problem."""

    def __init__(self,
                 msg='',
                 style_error=GenericSyntaxError,
                 line_numbers=None):
        # type: (str, Any, Tuple[int, int]) -> None
        """Create a new ParserException.

        Args:
            msg: The message this error should display.
            style_error: If style errors are supported, then this
                is the type of style error.
            line_numbers: Th eline number where this error occurred.

        """
        super(ParserException, self).__init__(msg)
        self.style_error = style_error
        self.line_numbers = line_numbers


def Assert(expr, msg, style_error=None, token=None):
    # type: (bool, str, Any, Token) -> None
    """Assert that the expression is True.

    Args:
        expr: The expression which we are evaluating.
        msg: The message which will be passed to the error
            if we are wrong.
        style_error: The error to pass into the ParserException
            if `expr` is false.
        token: The last token which was parsed before or at
            this check. (Used for passing along line numbers.)

    Raises:
        ParserException: If `expr` is not true and `style_error`
            is not specified.

    """
    if not expr:
        if token is not None:
            line_numbers = (token.line_number, token.line_number)  # type: Optional[Tuple[int, int]] # noqa
        else:
            line_numbers = None
        if style_error:
            raise ParserException(
                msg,
                style_error=style_error,
                line_numbers=line_numbers,
            )
        else:
            raise ParserException(
                msg,
                line_numbers=line_numbers,
            )


def AssertNotEmpty(peaker, context, style_error=None):
    # type: (Peaker, str, Any) -> None
    """Raise a parser exception if the next item is empty.

    Raises:
        ParserException: If the peaker is, in fact, empty.

    Args:
        peaker: The Peaker which should not be empty.
        context: A verb in the gerund form which describes
            our current actions.
        style_error: The style error passed with the
            ParserException if the Peaker is empty.

    """
    if not peaker.has_next():
        prev_line_numbers = None
        if peaker.prev and peaker.prev.line_number:
            line_no = peaker.prev.line_number
            prev_line_numbers = (line_no, line_no)
        if style_error:
            raise ParserException(
                'Unable to {}: stream was unexpectedly empty.'.format(
                    context
                ),
                style_error=style_error,
                line_numbers=prev_line_numbers,
            )
        else:
            raise ParserException(
                'Unable to {}: stream was unexpectedly empty.'.format(
                    context,
                ),
                line_numbers=prev_line_numbers,
            )


def parse_colon(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse colon')
    Assert(
        _is(TokenType.COLON, peaker.peak()),
        'Unable to parse colon: expected {} but received {}'.format(
            TokenType.COLON, peaker.rpeak().token_type
        ),
        token=peaker.peak()
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.COLON,
        value=token.value,
        token=token,
    )


def parse_word(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse word')
    Assert(
        _is(TokenType.WORD, peaker.peak()),
        'Unable to parse word: expected {} but received {}'.format(
            TokenType.WORD, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.WORD,
        value=token.value,
        token=token,
    )


def parse_hash(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse hash')
    Assert(
        _is(TokenType.HASH, peaker.peak()),
        'Unable to parse hash: expected {} but received {}'.format(
            TokenType.HASH, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.HASH,
        value=token.value,
        token=token,
    )


def parse_lparen(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse left parenthesis')
    Assert(
        _is(TokenType.LPAREN, peaker.peak()),
        'Unable to parse left parenthesis: expected {} '
        'but received {}'.format(
            TokenType.LPAREN, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.LPAREN,
        value=token.value,
        token=token,
    )


def parse_rparen(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse right parenthesis')
    Assert(
        _is(TokenType.RPAREN, peaker.peak()),
        'Unable to parse right parenthesis: expected {} '
        'but received {}'.format(
            TokenType.RPAREN, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.RPAREN,
        value=token.value,
        token=token,
    )


def parse_indent(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse indent')
    Assert(
        _is(TokenType.INDENT, peaker.peak()),
        'Unable to parse indent: expected {} but received {}'.format(
            TokenType.INDENT, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.INDENT,
        value=token.value,
        token=token,
    )


def parse_noqa_head(peaker):
    # type: (Peaker[Token]) -> Node
    children = [
        parse_hash(peaker),
    ]
    word = parse_word(peaker)
    Assert(
        word.value == 'noqa',
        'Failed to parse noqa statement. '
        'Expected "# noqa" but received "# {}"'.format(
            word.value,
        ),
        token=peaker.peak(),
    )
    children.append(word)
    return Node(
        node_type=NodeType.NOQA_HEAD,
        children=children,
    )


def parse_noqa_body(peaker):
    # type: (Peaker[Token]) -> Node
    children = [parse_word(peaker)]
    if peaker.has_next() and _is(TokenType.WORD, peaker.peak()):
        children.append(parse_list(peaker))
    return Node(
        node_type=NodeType.NOQA_BODY,
        children=children,
    )


def parse_list(peaker):
    # type: (Peaker[Token]) -> Node
    prev = parse_word(peaker)
    children = [prev]
    while ((prev.value or '').endswith(',')
            and peaker.has_next()
            and _is(TokenType.WORD, peaker.peak())):
        prev = parse_word(peaker)
        children.append(prev)
    return Node(
        node_type=NodeType.LIST,
        children=children
    )


def parse_noqa(peaker):
    # type: (Peaker[Token]) -> Node
    children = [
        parse_noqa_head(peaker),
    ]
    if peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        children.extend([
            parse_colon(peaker),
            parse_noqa_body(peaker),
        ])
    return Node(
        node_type=NodeType.NOQA,
        children=children,
    )


def parse_keyword(peaker, keywords=dict()):
    # type: (Peaker[Token], Dict[str, NodeType]) -> Node
    """Parse a keyword.

    Args:
        peaker: A stream of tokens from lexing a docstring.
        keywords: A map of keywords to their associated
            NodeTypes.

    Returns:
        A Node with Keyword NodeType.

    """
    AssertNotEmpty(peaker, 'parse keyword')
    Assert(
        _is(TokenType.WORD, peaker.peak()),
        'Unable to parse keyword: expected {} but received {}'.format(
            TokenType.WORD, peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    Assert(
        peaker.rpeak().value in keywords,
        'Unable to parse keyword: "{}" is not a keyword'.format(
            peaker.rpeak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(keywords[token.value], value=token.value, token=token)
