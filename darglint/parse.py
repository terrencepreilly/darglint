r"""
__EBNF for a google-style docstring__:

  <docstring> ::= <short-description>
                | <short-description><newline><newline>
                    <long-description>*
                    <sections>*

  <short-description> ::= <word>[<hash><noqa><word><colon><keyword>]*
  <long-description>  ::= <head-line>+
  <head-line> ::= <indent>
                    [<word><colon><indent>]
                    [<word><colon><indent><keyword>]*
                    <noqa>?<newline>

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
  <section-head> ::= <keyword><colon><newline>
  <section-simple-body> ::=
    <indent><type>?[<word><colon><indent><keyword>]*<newline>
    (<indent><indent><line>)*
  <section-compound-body> ::= <item>+
  <item> ::= <indent><item-name><colon><item-definition>
  <item-name> ::= <word><type>?
  <item-definition> ::= <line>+
  <line> ::= [<word><hash><colon><indent><keyword>]*<noqa>?<newline>
  <type> ::= <lparen><word>+<rparen>
           | <word><colon>

  <noqa> ::= <noqa-head>(<colon><noqa-body>)?
  <noqa-head> ::= <hash><word>
  <noqa-body> ::= <word><list>?
  <list> ::= <word>["," <word>]*

  <hash> ::= "#"
  <lparen> ::= "("
  <rparen> ::= ")"
  <keyword> ::= "Args"
            | "Arguments"
            | "Returns
            | "Yields"
            | "Raises"
  <indent>  ::= " "{4}
  <word>    ::= [^\ \n\:\"\t]+
  <colon>   ::= ":"
  <newline> ::= "\n"

"""
from typing import (
    Any,
    List,
    Optional,
    Set,
    Tuple,
)  # noqa

from .peaker import Peaker  # noqa
from .token import Token, TokenType  # noqa
from .node import Node, NodeType
from .errors import (
    GenericSyntaxError,
    EmptyDescriptionError,
)

KEYWORDS = {
    'Args': NodeType.ARGUMENTS,
    'Arguments': NodeType.ARGUMENTS,
    'Returns': NodeType.RETURNS,
    'Yields': NodeType.YIELDS,
    'Raises': NodeType.RAISES,
}


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
        ),
        token=peaker.peak(),
    )
    Assert(
        peaker.peak().value in KEYWORDS,
        'Unable to parse keyword: "{}" is not a keyword'.format(
            peaker.peak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(KEYWORDS[token.value], value=token.value, token=token)


def parse_colon(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse colon')
    Assert(
        _is(TokenType.COLON, peaker.peak()),
        'Unable to parse colon: expected {} but received {}'.format(
            TokenType.COLON, peaker.peak().token_type
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
            TokenType.WORD, peaker.peak().token_type
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
            TokenType.HASH, peaker.peak().token_type
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
            TokenType.LPAREN, peaker.peak().token_type
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
            TokenType.RPAREN, peaker.peak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.RPAREN,
        value=token.value,
        token=token,
    )


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


def parse_indent(peaker):
    # type: (Peaker[Token]) -> Node
    AssertNotEmpty(peaker, 'parse indent')
    Assert(
        _is(TokenType.INDENT, peaker.peak()),
        'Unable to parse indent: expected {} but received {}'.format(
            TokenType.INDENT, peaker.peak().token_type
        ),
        token=peaker.peak(),
    )
    token = peaker.next()
    return Node(
        node_type=NodeType.INDENT,
        value=token.value,
        token=token,
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
    while peaker.has_next() and not peaker.peak().token_type == TokenType.NEWLINE:
        next_child = peaker.peak()
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker))
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
        AssertNotEmpty(peaker, 'parse line')
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
    while (peaker.has_next()
            and not peaker.peak().token_type == TokenType.NEWLINE):
        next_child = peaker.peak()
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker))
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
    Assert(
        peaker.peak().value in expecting,
        'Expected section head to start with one of {} but was {}'.format(
            expecting,
            repr(peaker.peak().value),
        ),
        token=peaker.peak(),
    )
    children.append(parse_keyword(peaker))
    children.append(parse_colon(peaker))
    # TODO: Allow a noqa here.
    Assert(
        _is(TokenType.NEWLINE, peaker.peak()),
        'Failed to parse section head: expected '
        'it to end with {} but encountered {}'.format(
            TokenType.NEWLINE,
            peaker.peak().token_type,
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
        token = peaker.peak(lookahead=i)
        return token is not None and _is(TokenType.INDENT, token)

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
    # type: (Peaker[Token]) -> Node
    children = [
        parse_indent(peaker),
        parse_item_name(peaker),
    ]

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
        children.append(parse_item(peaker))

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
        Assert(
            _is(TokenType.NEWLINE, peaker.peak()),
            'Expected {} after compound section but received {}'.format(
                TokenType.NEWLINE,
                peaker.peak().token_type
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
        if _is(TokenType.WORD, next_child) and next_child.value in KEYWORDS:
            children.append(parse_keyword(peaker))
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
    Assert(
        peaker.has_next() and peaker.peak().value not in KEYWORDS,
        'Expected long description to start with non-keyword but {}.'.format(
            'was empty.' if not peaker.has_next() else 'was {}'.format(
                peaker.peak().value
            )
        ),
        token=peaker.peak(),
    )
    children = [
        parse_line(peaker),
    ]
    while peaker.has_next() and peaker.peak().value not in KEYWORDS:
        children.append(parse_line(peaker))

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
        Assert(
            _is(TokenType.NEWLINE, peaker.peak()),
            'Expected blank line after short description, but '
            'found {}: {}.'.format(
                peaker.peak().token_type,
                repr(peaker.peak().value)
            ),
            token=peaker.peak(),
        )
        peaker.next()  # consume blank line.
    if peaker.has_next() and peaker.peak().value not in KEYWORDS:
        children.append(parse_long_description(peaker))
    return Node(
        node_type=NodeType.DESCRIPTION,
        children=children,
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


def parse_list(peaker):
    # type: (Peaker[Token]) -> Node
    prev = parse_word(peaker)
    children = [prev]
    while (prev.value.endswith(',')
            and peaker.has_next()
            and _is(TokenType.WORD, peaker.peak())):
        prev = parse_word(peaker)
        children.append(prev)
    return Node(
        node_type=NodeType.LIST,
        children=children
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
        next_value = peaker.peak().value
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
