r"""A parser for Sphinx-style docstrings.

The EBNF for the parser is as follows:

  docstring = short-description, [long-description];
            | short-description
                , [long-description]
                , item
                , {[newline], item}
                , newline;

  short-description = unline
                    | line, newline;
  long-description = line, {line}, newline;

  item = indent, item-name, item-definition;
  section-name = colon, keyword, [word], colon;
  item-definition = line, {line};
  line = unline, newline
  unline = { word
           , hash
           , colon
           , indent
           , keyword
           , lparen
           , rparen
           }, [noqa];

  noqa = noqa-head, [colon, list]
  noqa-head = hash, noqa-keyword
  list = word {"," word}

  keyword = "arg"
          | "argument"
          | "param"
          | "parameter"
          | "key"
          | "keyword"
          | "raises"
          | "raise"
          | "except"
          | "exception"
          | "var"
          | "ivar"
          | "cvar"
          | "returns"
          | "return"
          | "yield"
          | "yields"
          | "type"
          | "vartype"
          | "rtype"
          | "ytype";

  indent  = " " * 4;
  word    = ? r/[^\ \n\:\"\t]+/ ?;
  noqa-keyword = "noqa"
  hash = "#"
  lparen = "("
  rparen = ")"
  colon   = ":";
  newline = "\n";

"""

from itertools import chain
from typing import (  # noqa
    Dict,
    List,
)

from ..node import (
    Node,
    NodeType,
)
from ..peaker import Peaker  # noqa
from ..token import (  # noqa
    Token,
    TokenType,
)
from .common import (
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
    'arg': NodeType.ARGUMENTS,
    'argument': NodeType.ARGUMENTS,
    'param': NodeType.ARGUMENTS,
    'parameter': NodeType.ARGUMENTS,
    'key': NodeType.ARGUMENTS,
    'keyword': NodeType.ARGUMENTS,
    'type': NodeType.TYPE,
    'raises': NodeType.RAISES,
    'raise': NodeType.RAISES,
    'except': NodeType.RAISES,
    'exception': NodeType.RAISES,
    'var': NodeType.VARIABLES,
    'ivar': NodeType.VARIABLES,
    'cvar': NodeType.VARIABLES,
    'vartype': NodeType.TYPE,
    'returns': NodeType.RETURNS,
    'return': NodeType.RETURNS,
    'rtype': NodeType.TYPE,
    'yield': NodeType.YIELDS,
    'yields': NodeType.YIELDS,
    'ytype': NodeType.TYPE,
}

_KEYWORD_TO_SECTION = {
    NodeType.ARGUMENTS: NodeType.ARGS_SECTION,
    NodeType.RAISES: NodeType.RAISES_SECTION,
    NodeType.VARIABLES: NodeType.VARIABLES_SECTION,
    NodeType.RETURNS: NodeType.RETURNS_SECTION,
    NodeType.YIELDS: NodeType.YIELDS_SECTION,
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
            children.append(parse_keyword(peaker, KEYWORDS))
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
    AssertNotEmpty(peaker, 'parse short description')
    Assert(
        not _is(TokenType.NEWLINE, peaker),
        'Must have short description in docstring.'
    )
    return Node(
        NodeType.SHORT_DESCRIPTION,
        children=[parse_line(peaker)],
    )


def _at_item(peaker):
    # type: (Peaker[Token]) -> bool
    token = peaker.peak(lookahead=2)
    if token is None:
        return False
    return (_is(TokenType.COLON, peaker)
            and token.value in KEYWORDS)


def parse_long_description(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse long description')
    children = list()  # type: List[Node]
    while peaker.has_next() and not _at_item(peaker):
        children.append(parse_line(peaker))

    return Node(
        node_type=NodeType.LONG_DESCRIPTION,
        children=children,
    )


def parse_item_definition(peaker):
    # type: (Peaker[Token]) -> Node
    children = [parse_line(peaker)]
    while _is(TokenType.INDENT, peaker):
        children.append(parse_line(peaker))
    return Node(
        node_type=NodeType.ITEM_DEFINITION,
        children=children,
    )


def parse_item_head_with_argument(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse item')
    children = list()  # type: List[Node]

    token = peaker.peak()
    assert token is not None
    Assert(
        _is(TokenType.COLON, peaker),
        'Expected item to start with {} but was {}: {}'.format(
            TokenType.COLON, token.token_type, token.value
        ),
    )
    children.append(parse_colon(peaker))

    AssertNotEmpty(peaker, 'parse item')
    token = peaker.peak()
    assert token is not None
    Assert(
        _in_keywords(peaker),
        'Expected a keyword (e.g. "arg", "returns", etc.) but was {}'.format(
            token.value
        )
    )
    keyword = parse_keyword(peaker, KEYWORDS)
    children.append(keyword)

    Assert(
        not _is(TokenType.COLON, peaker),
        'Expected argument in {} section.'.format(
            children[-1].value
        ),
    )

    #           1     2  3
    # :param <type> <arg>:
    if not _is(TokenType.COLON, peaker, offset=2):
        _type = parse_word(peaker)
        children.append(Node(
            node_type=NodeType.TYPE,
            children=[_type],
        ))
    children.append(parse_word(peaker))

    AssertNotEmpty(peaker, 'parse item head end')
    token = peaker.peak()
    assert token is not None
    Assert(
        _is(TokenType.COLON, peaker),
        'Expected item head to end with {} but was {} {}'.format(
            TokenType.COLON,
            token.token_type,
            repr(token.value),
        ),
    )
    children.append(parse_colon(peaker))
    return Node(
        node_type=NodeType.ITEM_NAME,
        children=children,
    )


def parse_item_head_without_argument(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse item')
    children = list()  # type: List[Node]

    token = peaker.peak()
    assert token is not None
    Assert(
        _is(TokenType.COLON, peaker),
        'Expected item to start with {} but was {}: {}'.format(
            TokenType.COLON, token.token_type, token.value,
        ),
    )
    children.append(parse_colon(peaker))

    AssertNotEmpty(peaker, 'parse item')
    token = peaker.peak()
    assert token is not None
    Assert(
        token.value in {
            'returns', 'return', 'yields', 'yield', 'rtype', 'ytype'
        },
        'Expected section which doesn\'t take an argument '
        '({}) but was {}'.format(
            'returns, return, yields or yield', token.value
        )
    )
    keyword = parse_keyword(peaker, KEYWORDS)
    children.append(keyword)

    if not _is(TokenType.COLON, peaker):
        _type = parse_word(peaker)
        children.append(Node(
            node_type=NodeType.TYPE,
            children=[_type],
        ))

    AssertNotEmpty(peaker, 'parse item head end')
    token = peaker.peak()
    assert token is not None
    Assert(
        _is(TokenType.COLON, peaker),
        'Expected item head to end with {} but was {} {}'.format(
            TokenType.COLON,
            token.token_type,
            repr(token.value),
        ),
    )
    children.append(parse_colon(peaker))
    return Node(
        node_type=NodeType.ITEM_NAME,
        children=children,
    )


def parse_item_head(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse item')

    colon_token = peaker.peak()
    assert colon_token is not None
    Assert(
        _is(TokenType.COLON, peaker),
        'Expected item to start with {} but was {}: "{}". '
        'Are your indents four spaces?'.format(
            TokenType.COLON, colon_token.token_type, colon_token.value,
        ),
    )

    section_token = peaker.peak(lookahead=2)
    Assert(
        section_token is not None,
        'Stream unexpectedly empty while parsing item head.'
    )
    assert section_token is not None
    Assert(
        section_token.value in KEYWORDS,
        'Expected a keyword (e.g. "arg", "returns", etc.) but was {}'.format(
            section_token.value
        )
    )

    if section_token.value in {
            'returns', 'return', 'yield', 'yields', 'rtype', 'ytype'
    }:
        return parse_item_head_without_argument(peaker)
    else:
        return parse_item_head_with_argument(peaker)


def parse_item(peaker):
    # type: (Peaker[Token]) -> Node
    head = parse_item_head(peaker)

    keyword = head.children[1]

    if keyword.node_type == NodeType.TYPE:
        allowable_types = ['type', 'rtype', 'vartype', 'ytype']
        Assert(
            keyword.value in allowable_types,
            'Unable to determine section type from keyword {}: '
            'expected one of {}'.format(
                keyword.value,
                str(allowable_types),
            )
        )
        if keyword.value == 'rtype':
            section_type = NodeType.RETURNS_SECTION
        elif keyword.value == 'vartype':
            section_type = NodeType.VARIABLES_SECTION
        elif keyword.value == 'type':
            section_type = NodeType.ARGS_SECTION
        elif keyword.value == 'ytype':
            section_type = NodeType.YIELDS_SECTION
    else:
        section_type = _KEYWORD_TO_SECTION[keyword.node_type]

    children = [
        head,
        parse_item_definition(peaker),
    ]

    return Node(
        node_type=section_type,
        children=[Node(
            node_type=NodeType.ITEM,
            children=children,
        )]
    )


def parse_description(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse description')
    children = [
        parse_short_description(peaker),
    ]
    long_descriptions = list()  # type: List[Node]
    while peaker.has_next() and not _at_item(peaker):
        long_descriptions.append(
            parse_long_description(peaker)
        )

    # Consolidate all long descriptions into one.
    if long_descriptions:
        desc = [x.children for x in long_descriptions]
        children.append(
            Node(
                node_type=NodeType.LONG_DESCRIPTION,
                children=list(chain(*desc))
            )
        )

    return Node(
        node_type=NodeType.DESCRIPTION,
        children=children
    )


def parse(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse docstring')
    children = [
        parse_description(peaker)
    ]

    while peaker.has_next():
        children.append(parse_item(peaker))

        # Consume extra newlines.
        while _is(TokenType.NEWLINE, peaker):
            peaker.next()

    return Node(
        node_type=NodeType.DOCSTRING,
        children=children,
    )

    # TODO: In the parse function, parse everything,
    # then run over it and conglomerate the sections.
    # that will allow us to treat the tree the same as we
    # treat the Google tree.
