r"""
__EBNF for a google-style docstring__:

  <docstring> ::= <short-description>
                | <short-description><newline>
                    <long-description>*
                    <section>*

  <short-description> ::= <word>[<word><colon><keyword>]*
  <long-description>  ::= <head-line>+
  <head-line> ::= <indent>
                    [<word><colon><indent>]
                    [<word><colon><indent><keyword>]*<newline>
  <section> ::= <indent><keyword><colon><newline>
                (<indent><line>)+
              | <indent><keyword><colon><newline>
                    <indent>{2}<word><type>?<colon>
                    [<word><colon><keyword>]*<newline>
                    (<indent>{2}<line>)*
  <line> ::= <indent>
                [<word><colon><indent><keyword>]*<newline>
  <type> ::= "(" <word> ")"

  <keyword> ::= "Args"
            | "Arguments"
            | "Returns
            | "Yields"
            | "Raises"
  <indent>  ::= " "{4}
  <word>    ::= [^\ \n\:\"\#\t]+
  <colon>   ::= ":"
  <newline> ::= "\n"

"""

from .parse import ParserException
from .peaker import Peaker  # noqa
from .token import Token, TokenType  # noqa
from .node import Node, NodeType

KEYWORDS = {
    'Args': NodeType.ARGUMENTS,
    'Arguments': NodeType.ARGUMENTS,
    'Returns': NodeType.RETURNS,
    'Yields': NodeType.YIELDS,
    'Raises': NodeType.RAISES,
}

def Assert(expr, msg):
    # type: (bool, str) -> None
    """Assert that the expression is True."""
    if not expr:
        raise ParserException(msg)


def AssertNotEmpty(peaker, context):
    # type: (Peaker, str) -> None
    """Raise a parser exception if the next item is empty.

    Args:
        peaker: The Peaker which should not be empty.
        context: A verb in the gerund form which describes
            our current actions.

    """
    if not peaker.has_next():
        raise ParserException(
            'Unable to {}: stream was unexpectedly empty.'.format(
                context
            )     
        )

def _is(expected_type, token):
    # type: (TokenType, Token) -> bool
    return token.token_type == expected_type


def parse_keyword(peaker):
    # type: (Peaker[Token]) -> Node
    """Parse a keyword.

    Args:
        peaker: A stream of tokens from lexing a docstring.

    Returns:
        A Node with Keyword NodeType.
    
    """
    AssertNotEmpty(peaker, 'parse keyword')
    Assert(
        _is(TokenType.WORD, peaker.peak()),
        'Unable to parse keyword: expected {} but received {}'.format(
            TokenType.WORD, peaker.peak().token_type
        )
    )
    Assert(
        peaker.peak().value in KEYWORDS,
        'Unable to parse keyword: "{}" is not a keyword'.format(
            peaker.peak().token_type
        ),
    )
    token = peaker.next()
    return Node(KEYWORDS[token.value], value=token.value)

def parse_colon(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse colon')
    Assert(
        _is(TokenType.COLON, peaker.peak()),
        'Unable to parse colon: expected {} but received {}'.format(
            TokenType.COLON, peaker.peak().token_type
        )
    )
    return Node(
        node_type=NodeType.COLON,
        value=peaker.next().value
    )

def parse_word(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse word')
    Assert(
        _is(TokenType.WORD, peaker.peak()),
        'Unable to parse word: expected {} but received {}'.format(
            TokenType.WORD, peaker.peak().token_type
        )
    )
    return Node(
        node_type=NodeType.WORD,
        value=peaker.next().value
    )

def parse_type(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse type')
    Assert(
        _is(TokenType.WORD, peaker.peak()),
        'Unable to parse type: expected {} but received {}'.format(
            TokenType.WORD, peaker.peak().token_type
        )
    )
    value = peaker.next().value
    Assert(
        value.startswith('(') and value.endswith(')'),
        'Expected type to begin with "(" and end with ")"'
    )
    return Node(
        node_type=NodeType.TYPE,
        value = value,
    )


def parse_indent(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse indent')
    Assert(
        _is(TokenType.INDENT, peaker.peak()),
        'Unable to parse indent: expected {} but received {}'.format(
            TokenType.INDENT, peaker.peak().token_type
        )
    )
    return Node(
        node_type=NodeType.INDENT,
        value=peaker.next().value,
    )

def parse_line(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse line')
    children = [
        parse_indent(peaker)
    ]
    while not peaker.peak().token_type == TokenType.NEWLINE:
        next_child = peaker.peak()
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker))
        elif _is(TokenType.WORD, next_child):
            children.append(parse_word(peaker))
        elif _is(TokenType.INDENT, next_child):
            children.append(parse_indent(peaker))
        elif _is(TokenType.COLON, next_child):
            children.append(parse_colon(peaker))
        else:
            raise Exception(
                'Failed to parse line: invalid token type {}'.format(
                    next_child.token_type
                )
            )
    AssertNotEmpty(peaker, 'parse line end')
    peaker.next() # Throw away newline.
    return Node(
        NodeType.LINE,
        children=children,
    )
