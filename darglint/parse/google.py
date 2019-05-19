r"""
__EBNF for a google-style docstring__:

  docstring = short-description
              | short-description
                  , newline
                  , newline
                  , {long-description}
                  , [sections];

  short-description = word, {hash | noqa | word | colon | keyword}
  long-description  = head-line, {head-line}
  head-line = indent
                  , [word | colon | indent]
                  , {word | colon | indent | keyword}
                  , [noqa]
                  , newline

  sections = [arguments-section]
                  , [raises-section]
                  , [yields-section | returns-section]
              | [raises-section]
                  , [arguments-section]
                  , [yields-section | returns-section]

  arguments-section = section-compound
  raises-section = section-compound
  yields-section = section-simple
  returns-section = section-simple

  section-simple = section-head, section-simple-body
  section-compound = section-head, section-compound-body
  section-head = keyword, colon, newline
  section-simple-body =
    indent, [type], {word | colon | indent | keyword}, newline
    {indent, indent, line}
  section-compound-body = item, {item}
  item = indent, item-name, colon, item-definition
  item-name = word, [type]
  item-definition = line, {line}
  line = { word
         | hash
         | colon
         | indent
         | keyword
         }, [noqa] newline
  type = lparen, word, {word}, rparen
           | word, colon

  noqa      = noqa-head, [colon, noqa-body]
  noqa-head = hash, word
  noqa-body = word, [list]
  list      = word, {"," word}

  hash    = "#"
  lparen  = "("
  rparen  = ")"
  keyword = "Args"
            | "Arguments"
            | "Returns
            | "Yields"
            | "Raises"
  indent  = " "{4}
  word    = [^\ \n\:\"\t]+
  colon   = ":"
  newline = "\n"

"""
from typing import (  # noqa: F401
    List,
    Optional,
    Set,
)

from ..peaker import Peaker  # noqa: F401
from ..token import Token, TokenType  # noqa: F401
from ..node import Node, NodeType
from ..errors import (
    EmptyDescriptionError,
)
from .common import (
    Assert,
    AssertNotEmpty,
    ParserException,
    parse_colon,
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


def _is(expected_type, token):
    # type: (TokenType, Optional[Token]) -> bool
    if token is None:
        return False
    return token.token_type == expected_type


def parse_parenthetical_type(peaker):
    # type: (Peaker[Token]) -> Node
    children = [parse_lparen(peaker)]
    parentheses_count = 1
    encountered_word = False
    while peaker.has_next() and parentheses_count > 0:
        Assert(
            peaker.has_next(),
            'Encountered end of stream while parsing '
            'parenthetical type. Ended with {}'.format(
                [x.value for x in children]
            ),
            token=peaker.peak(),
        )
        if _is(TokenType.LPAREN, peaker.peak()):
            parentheses_count += 1
            children.append(parse_lparen(peaker))
        elif _is(TokenType.RPAREN, peaker.peak()):
            parentheses_count -= 1
            children.append(parse_rparen(peaker))
        elif _is(TokenType.COLON, peaker.peak()):
            children.append(parse_colon(peaker))
        elif _is(TokenType.INDENT, peaker.peak()):
            parse_indent(peaker)
        else:
            encountered_word = True
            children.append(parse_word(peaker))
    Assert(
        parentheses_count == 0,
        'Mismatched parentheses in parenthetical type.',
        token=peaker.peak(),
    )
    Assert(
        encountered_word,
        'Parenthetical type must contain at least one word.',
        token=peaker.peak(),
    )
    return Node(
        node_type=NodeType.TYPE,
        children=children,
    )


def parse_type(peaker):
    # type: (Peaker[Token]) -> Node
    if _is(TokenType.LPAREN, peaker.peak()):
        return parse_parenthetical_type(peaker)

    AssertNotEmpty(peaker, 'parse type')
    node = parse_word(peaker)
    Assert(
        _is(TokenType.COLON, peaker.peak()),
        'Expected type, "{}", to have "(" and ")" around it or '
        'end in colon.'.format(
            node.value
        ),
        token=peaker.peak(),
    )
    peaker.next()  # Toss the colon
    return Node(
        node_type=NodeType.TYPE,
        children=[node],
    )


def parse_line(peaker, with_type=False):
    # type: (Peaker[Token], bool) -> Node
    AssertNotEmpty(peaker, 'parse line')
    children = list()

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
    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        next_child = peaker.peak()
        assert next_child is not None
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker, KEYWORDS))
        elif _is(TokenType.WORD, next_child):
            children.append(parse_word(peaker))
        elif _is(TokenType.INDENT, next_child):
            children.append(parse_indent(peaker))
        elif _is(TokenType.COLON, next_child):
            children.append(parse_colon(peaker))
        elif _is(TokenType.LPAREN, next_child):
            children.append(parse_lparen(peaker))
        elif _is(TokenType.RPAREN, next_child):
            children.append(parse_rparen(peaker))
        elif _is(TokenType.HASH, next_child):
            children.append(parse_noqa(peaker))
        else:
            raise ParserException(
                'Failed to parse line: invalid token type {}'.format(
                    next_child.token_type
                ),
                line_numbers=(
                    next_child.line_number,
                    next_child.line_number,
                )
            )

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

    Raises:
        ParserException: If there was any problem with parsing
            the line.

    Returns:
        A line node.

    """
    AssertNotEmpty(peaker, 'parse line')
    children = [
        parse_indent(peaker),
    ]

    # Get the first node, which may be a type description.
    if _is(TokenType.WORD, peaker.peak()):
        next_value = peaker.next()
        if next_value.value.startswith('(') and next_value.value.endswith(')'):
            AssertNotEmpty(peaker, 'parse line')
            first_node = parse_type(
                Peaker((x for x in [next_value]))
            )
        elif _is(TokenType.COLON, peaker.peak()):
            AssertNotEmpty(peaker, 'parse line')
            first_node = parse_type(
                Peaker((x for x in [next_value, peaker.next()]))
            )
        else:
            first_node = parse_word(
                Peaker((x for x in [next_value]))
            )
        children.append(first_node)

    # Get the remaining nodes in the line, up to the newline.
    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        next_child = peaker.peak()
        assert next_child is not None, 'Make the type checker happy.'
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker, KEYWORDS))
        elif _is(TokenType.WORD, next_child):
            children.append(parse_word(peaker))
        elif _is(TokenType.INDENT, next_child):
            children.append(parse_indent(peaker))
        elif _is(TokenType.COLON, next_child):
            children.append(parse_colon(peaker))
        elif _is(TokenType.LPAREN, next_child):
            children.append(parse_lparen(peaker))
        elif _is(TokenType.RPAREN, next_child):
            children.append(parse_rparen(peaker))
        else:
            raise ParserException(
                'Failed to parse line: invalid token type {}'.format(
                    next_child.token_type
                )
            )
    return Node(
        NodeType.LINE,
        children=children,
    )


def parse_section_head(peaker, expecting=set()):
    # type: (Peaker[Token], Set[str]) -> Node
    AssertNotEmpty(peaker, 'parse section head')
    children = list()  # type: List[Node]
    # TODO: This error message is too generic; try to make it more specific.
    child = peaker.peak()
    assert child is not None
    Assert(
        child.value in expecting,
        'Expected section head to start with one of {} but was {}'.format(
            expecting,
            repr(child.value),
        ),
        token=peaker.peak(),
    )
    children.append(parse_keyword(peaker, KEYWORDS))
    children.append(parse_colon(peaker))
    # TODO: Allow a noqa here.
    node = peaker.peak()
    Assert(
        _is(TokenType.NEWLINE, node),
        'Failed to parse section head: expected '
        'it to end with {} but encountered {}'.format(
            TokenType.NEWLINE,
            'None' if node is None else node.token_type,
        ),
        token=peaker.peak(),
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
    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        children.append(parse_indent(peaker))
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
    if peaker.has_next():
        Assert(
            _is(TokenType.NEWLINE, peaker.peak()),
            'Expected newline after section.',
            token=peaker.peak(),
        )
        peaker.next()  # Discard newline.
    return Node(
        NodeType.SECTION,
        children=children,
    )


def parse_yields(peaker):
    # type: (Peaker[Token]) -> Node
    node = parse_simple_section(peaker)
    node.node_type = NodeType.YIELDS_SECTION
    return node


def parse_returns(peaker):
    # type: (Peaker[Token]) -> Node
    node = parse_simple_section(peaker)
    node.node_type = NodeType.RETURNS_SECTION
    return node


def parse_item_name(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse item')
    children = [
        parse_word(peaker),
    ]
    if peaker.has_next() and not _is(TokenType.COLON, peaker.peak()):
        children.append(parse_type(peaker))
    return Node(
        NodeType.ITEM_NAME,
        children=children,
    )


def parse_item_definition(peaker, prev_line_number=None):
    # type: (Peaker[Token], Optional[int]) -> Node

    def _is_indent(i):
        return _is(TokenType.INDENT, peaker.peak(lookahead=i))

    AssertNotEmpty(
        peaker,
        'parse item definition',
        style_error=EmptyDescriptionError
    )
    Assert(
        not _is(TokenType.NEWLINE, peaker.peak()),
        'Unable to parse item definition: stream was unexpectedly empty.',
        token=peaker.peak(),
    )
    children = [
        parse_line(peaker),
    ]
    while _is_indent(1) and _is_indent(2):
        children.append(parse_line(peaker))
    return Node(
        NodeType.ITEM_DEFINITION,
        children=children,
    )


def parse_item(peaker):
    # type: (Peaker[Token]) -> Optional[Node]
    children = [
        parse_indent(peaker),
    ]

    excess_whitespace = False
    while _is(TokenType.INDENT, peaker.peak()):
        excess_whitespace = True
        peaker.next()
    if _is(TokenType.NEWLINE, peaker.peak()):
        return None
    Assert(
        not excess_whitespace,
        'Expected item but encountered extra whitespace.',
    )

    children.append(
        parse_item_name(peaker),
    )

    if _is(TokenType.LPAREN, peaker.peak()):
        children.append(parse_type(peaker))

    children.extend([
        parse_colon(peaker),
        parse_item_definition(peaker),
    ])
    return Node(
        NodeType.ITEM,
        children=children,
    )


def parse_section_compound_body(peaker):
    children = [
        parse_item(peaker),
    ]
    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        item = parse_item(peaker)
        whitespace_only_line = item is None
        if whitespace_only_line:
            continue
        children.append(item)

    return Node(
        node_type=NodeType.SECTION_COMPOUND_BODY,
        children=children,
    )


def parse_compound_section(peaker):
    # type: (Peaker[Token]) -> Node
    children = [
        parse_section_head(peaker, expecting={'Args', 'Arguments', 'Raises'}),
        parse_section_compound_body(peaker),
    ]
    if peaker.has_next():
        node = peaker.peak()
        assert node is not None
        Assert(
            _is(TokenType.NEWLINE, node),
            'Expected {} after compound section but received {}'.format(
                TokenType.NEWLINE,
                node.token_type
            ),
            token=peaker.peak(),
        )
        peaker.next()  # discard newline.

    return Node(
        node_type=NodeType.SECTION,
        children=children,
    )


def parse_args(peaker):
    # type: (Peaker[Token]) -> Node
    node = parse_compound_section(peaker)
    node.node_type = NodeType.ARGS_SECTION
    return node


def parse_raises(peaker):
    # type: (Peaker[Token]) -> Node
    node = parse_compound_section(peaker)
    node.node_type = NodeType.RAISES_SECTION
    return node


def parse_short_description(peaker):
    # type: (Peaker[Token]) -> Node
    children = list()
    while peaker.has_next() and not _is(TokenType.NEWLINE, peaker.peak()):
        next_child = peaker.peak()
        assert next_child is not None
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker, KEYWORDS))
        elif _is(TokenType.WORD, next_child):
            children.append(parse_word(peaker))
        elif _is(TokenType.INDENT, next_child):
            children.append(parse_indent(peaker))
        elif _is(TokenType.COLON, next_child):
            children.append(parse_colon(peaker))
        elif _is(TokenType.LPAREN, next_child):
            children.append(parse_lparen(peaker))
        elif _is(TokenType.RPAREN, next_child):
            children.append(parse_rparen(peaker))
        elif _is(TokenType.HASH, next_child):
            children.append(parse_noqa(peaker))
        else:
            raise ParserException(
                'Failed to parse line: invalid token type {}'.format(
                    next_child.token_type
                )
            )
    if peaker.has_next() and _is(TokenType.NEWLINE, peaker.peak()):
        peaker.next()  # Eat the newline.
    return Node(
        node_type=NodeType.SHORT_DESCRIPTION,
        children=children,
    )


def parse_long_description(peaker):
    # type: (Peaker[Token]) -> Node
    node = peaker.peak()
    Assert(
        node is not None and node.value not in KEYWORDS,
        'Expected long description to start with non-keyword but {}.'.format(
            'was empty.' if not peaker.has_next() else 'was {}'.format(
                'None' if node is None else node.value
            )
        ),
        token=peaker.peak(),
    )
    children = [
        parse_line(peaker),
    ]
    node = peaker.peak()
    while node is not None and node.value not in KEYWORDS:
        children.append(parse_line(peaker))
        node = peaker.peak()

    return Node(
        node_type=NodeType.LONG_DESCRIPTION,
        children=children,
    )


def parse_description(peaker):
    # type: (Peaker[Token]) -> Node
    children = [
        parse_short_description(peaker),
    ]
    if peaker.has_next():
        node = peaker.peak()
        assert node is not None
        Assert(
            _is(TokenType.NEWLINE, node),
            'Expected blank line after short description, but '
            'found {}: {}.'.format(
                node.token_type,
                repr(node.value)
            ),
            token=peaker.peak(),
        )
        peaker.next()  # consume blank line.
    node = peaker.peak()
    if node is not None and node.value not in KEYWORDS:
        children.append(parse_long_description(peaker))
    return Node(
        node_type=NodeType.DESCRIPTION,
        children=children,
    )


def parse(peaker):
    # type: (Peaker[Token]) -> Node
    """Parse the docstring.

    Args:
        peaker: A Peaker filled with the lexed tokens of the
            docstring.

    Raises:
        ParserException: If there is anything malformed with
            the docstring, or if anything goes wrong with parsing. # noqa

    Returns:
        The parsed docstring as an AST.

    """
    keyword_parse_lookup = {
        'Args': parse_args,
        'Arguments': parse_args,
        'Returns': parse_returns,
        'Yields': parse_yields,
        'Raises': parse_raises,
    }
    children = [
        parse_description(peaker)
    ]
    while peaker.has_next():
        node = peaker.peak()
        assert node is not None
        next_value = node.value
        if next_value in keyword_parse_lookup:
            children.append(
                keyword_parse_lookup[next_value](peaker)
            )
        else:
            children.append(
                parse_long_description(peaker)
            )
    return Node(
        node_type=NodeType.DOCSTRING,
        children=children,
    )
