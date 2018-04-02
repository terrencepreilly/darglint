r"""
__EBNF for a google-style docstring__:

  <docstring> ::= <short-description>
                | <short-description><newline>
                    <long-description>*
                    <sections>*

  <short-description> ::= <word>[<word><colon><keyword>]*
  <long-description>  ::= <head-line>+
  <head-line> ::= <indent>
                    [<word><colon><indent>]
                    [<word><colon><indent><keyword>]*<newline>
  
  <sections> ::= <arguments-section>?
                   <raises-section>?
                   (<yields-section>|<returns-section>)?
               | <raises-section>?
                   <arguments-section>?
                   (yields-section>|<returns-section>)?

  <arguments-section> ::= <section-compound>
  <raises-section> ::= <section-compound>
  <yields-section> ::= <section-simple>
  <returns-section> ::= <section-simple>

  <section-simple> ::= <section-head><section-simple-body>
  <section-compound> ::= <section-head><section-compound-body>
  <section-head> ::= <indent><keyword><colon><newline>
  <section-simple-body> ::=
    <indent><type>?[<word><colon><indent><keyword>]*<newline>
    (<indent><line>)*
  <section-compound-body> ::= <indent>{2}<word><type>?<colon>
                               [<word><colon><keyword>]*<newline>
                               (<indent>{2}<line>)*
  <line> ::= <indent>
                [<word><colon><indent><keyword>]*<newline>
  <type> ::= "(" <word> ")"
           | <word><colon>

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
from typing import Set # noqa

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
    if value.startswith('('):
        Assert(
            value.endswith(')'),
            'Expected type to begin with "(" and end with ")"'
        )
        return Node(
            node_type=NodeType.TYPE,
            value=value[1:-1],
        )
    else:
        AssertNotEmpty(peaker, 'parse type')
        Assert(
            _is(TokenType.COLON, peaker.peak()),
            'Expected type to have "(" and ")" around it or '
            'end in colon.'
        )
        peaker.next() # Toss the colon
        return Node(
            node_type=NodeType.TYPE,
            value=value,
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

def parse_line(peaker, with_type=False):
    # type: (Peaker[Token], bool) -> Node
    AssertNotEmpty(peaker, 'parse line')
    children = [
        parse_indent(peaker)
    ]

    # Get the first node, which may be a type description.
    if with_type and _is(TokenType.WORD, peaker.peak()):
        next_value = peaker.next()
        if next_value.value.startswith('(') and next_value.value.endswith(')'):
            first_node = parse_type(
                Peaker((x for x in [next_value]))
            )
        elif _is(TokenType.COLON, peaker.peak()):
            first_node = parse_type(
                Peaker((x for x in [next_value, peaker.next()]))
            )
        else:
            first_node = parse_word(
                Peaker((x for x in [next_value]))
            )
        children.append(first_node)

    # Get the remaining nodes in the line, up to the newline.
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

# NOTE: If Peaker ever allows 2-constant look-ahead, then change
# this to call to the `parse_line(peaker)` function to prevent
# drift between these two functions.
def parse_line_with_type(peaker):
    # type: (Peaker[Token]) -> Node
    """Parse a line which begins with a type description.

    Such lines occur at the start of the yields and returns
    sections.

    Args:
        peaker: A stream of tokens.

    Returns:
        A line node.
    
    """
    AssertNotEmpty(peaker, 'parse line')
    children = [
        parse_indent(peaker),
        parse_indent(peaker)
    ]

    # Get the first node, which may be a type description.
    if _is(TokenType.WORD, peaker.peak()):
        next_value = peaker.next()
        if next_value.value.startswith('(') and next_value.value.endswith(')'):
            first_node = parse_type(
                Peaker((x for x in [next_value]))
            )
        elif _is(TokenType.COLON, peaker.peak()):
            first_node = parse_type(
                Peaker((x for x in [next_value, peaker.next()]))
            )
        else:
            first_node = parse_word(
                Peaker((x for x in [next_value]))
            )
        children.append(first_node)

    # Get the remaining nodes in the line, up to the newline.
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

def parse_section_head(peaker, expecting=set()):
    # type: (Peaker[Token], Set[str]) -> Node
    AssertNotEmpty(peaker, 'parse section head')
    Assert(
        _is(TokenType.INDENT, peaker.peak()),
        'Failed to parse section head: expected '
        '{} but encountered {}'.format(
            TokenType.INDENT,
            peaker.peak().token_type,
        )
    )
    children = [
        parse_indent(peaker),
    ]
    # TODO: This error message is too generic; try to make it more specific.
    Assert(
        peaker.peak().value in expecting,
        'Expected section head to start with one of {}'.format(
            expecting,
        )
    )
    children.append(parse_keyword(peaker))
    children.append(parse_colon(peaker))
    Assert(
        _is(TokenType.NEWLINE, peaker.peak()),
        'Failed to parse section head: expected '
        'it to end with {} but encountered {}'.format(
            TokenType.NEWLINE,
            peaker.peak().token_type,
        )
    )
    peaker.next()
    return Node(
        NodeType.SECTION_HEAD,
        children=children,
    )


def parse_section_simple_body(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse section body')
    children = [
        parse_line_with_type(peaker),
    ]
    while not _is(TokenType.NEWLINE, peaker.peak()):
        children.append(parse_line(peaker))
    return Node(
        NodeType.SECTION_SIMPLE_BODY,
        children=children,
    )

def parse_simple_section(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse section')
    children = [
        parse_section_head(peaker, expecting={'Returns', 'Yields'}),
        parse_section_simple_body(peaker),
    ]
    return Node(
        NodeType.SECTION,
        children=children,
    )
