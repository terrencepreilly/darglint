import inspect
from typing import (
    List,
)
from functools import (
    reduce,
)

from ..custom_assert import Assert
from ..token import (
    Token,
    TokenType,
    KEYWORDS,
)
from .cyk import (
    parse as cyk_parse,
)
from ..node import (
    CykNode,
)

from .combinator import (
    parser_combinator,
)
from .long_description import (
    parse as long_description_parse,
)

from .grammars.google_arguments_section import ArgumentsGrammar
from .grammars.google_raises_section import RaisesGrammar
from .grammars.google_returns_section import ReturnsGrammar
from .grammars.google_returns_section_without_type import (
    ReturnsWithoutTypeGrammar,
)
from .grammars.google_short_description import ShortDescriptionGrammar
from .grammars.google_yields_section import YieldsGrammar
from .grammars.google_yields_section_without_type import (
    YieldsWithoutTypeGrammar,
)


def _get_split_end_with_indents(tokens, i):
    # type: (List[Token], int) -> int
    """Return the index of the end of this split, or 0.

    Args:
        tokens: A list of tokens.
        i: The current index.

    Returns:
        If i is the start of a split, return the index of the
        token after the end of the split (or the last token, if
        it's the end of the docstring.)  If we're not at a split,
        return 0.

    """
    newline_count = 0
    newline_run = 0
    highest_newline_run = 0
    j = i
    while j < len(tokens):
        if tokens[j].token_type == TokenType.NEWLINE:
            newline_count += 1
            newline_run += 1
            if newline_run > highest_newline_run:
                highest_newline_run = newline_run
        elif tokens[j].token_type == TokenType.INDENT:
            newline_run = 0
        else:
            break
        j += 1

    # Back up so that we don't remove indents on the same line as
    # the encountered text.
    while (j < len(tokens)
            and j > 1
            and tokens[j - 1].token_type == TokenType.INDENT):
        j -= 1

    # TODO: Do we want to check for keywords before assuming a
    # new section?  If we have line-separated sections in args,
    # which do not have indents, then we will parse incorrectly.
    if newline_count < 2:
        return 0

    # If there are two newlines in a row, we have a break, no
    # matter what.
    if highest_newline_run > 1:
        return j

    # If there were not 2+ newlines in a row, (i.e. there were
    # indented lines in with these), then it's only a new section
    # if it starts with a keyword.
    if (j < len(tokens)
            and tokens[j].token_type in KEYWORDS
            and tokens[j - 1].token_type == TokenType.NEWLINE):
        return j

    return 0


def top_parse(tokens):
    # type: (List[Token]) -> List[List[Token]]
    all_sections = list()
    curr = 0
    # Strip leading newlines.
    while curr < len(tokens) and tokens[curr].token_type == TokenType.NEWLINE:
        curr += 1
    prev = curr

    while curr < len(tokens):
        split_end = _get_split_end_with_indents(tokens, curr)
        if split_end > curr:
            if tokens[prev:curr]:
                all_sections.append(
                    tokens[prev:curr]
                )
            curr = split_end
            prev = curr
        else:
            curr += 1
    last_section = tokens[prev:curr]
    if last_section:
        all_sections.append(last_section)
    return all_sections


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
            ReturnsWithoutTypeGrammar,
            long_description_parse,
        ],
        TokenType.ARGUMENTS: [
            ArgumentsGrammar,
            long_description_parse,
        ],
        TokenType.YIELDS: [
            YieldsGrammar,
            YieldsWithoutTypeGrammar,
            long_description_parse,
        ],
        TokenType.RAISES: [
            RaisesGrammar,
            long_description_parse,
        ],
    }
    return tt_lookup.get(token.token_type, [long_description_parse])


def lookup(section, section_index=-1):
    Assert(len(section) > 0, 'Expected non-empty section.')
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
            if inspect.isclass(grammar):
                yield lambda x: cyk_parse(grammar, x)
            else:
                yield grammar
    return parser_combinator(top_parse, mapped_lookup, combinator, tokens)
