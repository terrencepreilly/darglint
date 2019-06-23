from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    List,
    Tuple,
)
from functools import (
    reduce,
)

from ..token import (
    Token,
    TokenType,
)
from .cyk import (
    CykNode,
    parse as cyk_parse,
)

from .combinator import (
    parser_combinator,
)

from .grammars.google_arguments_section import ArgumentsGrammar
from .grammars.google_long_description import LongDescriptionGrammar
from .grammars.google_raises_section import RaisesGrammar
from .grammars.google_returns_section import ReturnsGrammar
from .grammars.google_short_description import ShortDescriptionGrammar
from .grammars.google_yields_section import YieldsGrammar


def top_parse(tokens):
    # type: (List[Token]) -> List[List[Token]]
    ret = list()
    curr = list()  # type: List[Token]
    i = 0

    # Consume initial newlines.
    while i < len(tokens) and tokens[i].token_type == TokenType.NEWLINE:
        i += 1

    if i >= len(tokens):
        return list()

    assert tokens[i].token_type != TokenType.NEWLINE, (
        'i points at a non-newline token.'
    )
    while i < len(tokens):
        curr.append(tokens[i])
        j = i + 1
        while j < len(tokens) and tokens[j].token_type == TokenType.NEWLINE:
            j += 1
        if j > len(tokens):
            break

        assert j == len(tokens) or tokens[j].token_type != TokenType.NEWLINE, (
            'j points at a non-newline token'
        )
        assert j > i
        if j - i == 1:
            i += 1
        elif j - i == 2:
            # There was one newline: it's a part of this section.
            i += 1
        else:
            # There were 2+ newlines: we're in a new section.
            ret.append(curr)
            curr = list()
            i = j

    if curr:
        ret.append(curr)

    return ret


def _match(token):
    """Match the given token from the given section to a set of grammars.

    Args:
        token: The token to match.  This should hint at what sections
            could possibly be here.

    Returns:
        A list of grammars to be tried in order.

    """
    tt_lookup = {
        TokenType.RETURNS: [
            ReturnsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.ARGUMENTS: [
            ArgumentsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.YIELDS: [
            YieldsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.RAISES: [
            RaisesGrammar,
            LongDescriptionGrammar,
        ],
    }
    return tt_lookup.get(token.token_type, [LongDescriptionGrammar])


def lookup(section, section_index=-1):
    assert len(section) > 0
    grammars = _match(section[0])
    if section_index == 0:
        return [ShortDescriptionGrammar] + grammars
    return grammars


def combinator(*args):
    def inner(*nodes):
        if len(nodes) == 1:
            return CykNode(
                symbol='docstring',
                lchild=nodes[0],
            )
        elif len(nodes) == 2:
            return CykNode(
                symbol='docstring',
                lchild=nodes[0],
                rchild=nodes[1],
            )
    if args:
        return reduce(inner, args)
    else:
        # The arguments are empty, so we return an
        # empty docstring.
        return CykNode(symbol='docstring')


def parse(tokens):
    def mapped_lookup(section, section_index=-1):
        for grammar in lookup(section, section_index):
            yield lambda x: cyk_parse(grammar, x)
    return parser_combinator(top_parse, mapped_lookup, combinator, tokens)
