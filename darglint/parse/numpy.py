import inspect
from typing import (
    List,
    Optional,
    Callable,
    Union,
    Dict,
)
from functools import (
    reduce,
)
from ..token import (
    Token,
    TokenType,
)
from ..node import (
    CykNode,
)
from ..custom_assert import Assert
from .cyk import (
    parse as cyk_parse,
)
from .grammars.numpy_arguments_section import (
    ArgumentsGrammar,
)
from .grammars.numpy_other_arguments_section import (
    OtherArgumentsGrammar,
)
from .grammars.numpy_raises_section import (
    RaisesGrammar,
)
from .grammars.numpy_receives_section import (
    ReceivesGrammar,
)
from .grammars.numpy_returns_section import (
    ReturnsGrammar,
)
from .grammars.numpy_short_description import (
    ShortDescriptionGrammar,
)
from .grammars.numpy_warns_section import (
    WarnsGrammar,
)
from .grammars.numpy_yields_section import (
    YieldsGrammar,
)
from .grammar import (
    BaseGrammar,
)
from .combinator import (
    parser_combinator,
)
from ..token import (
    KEYWORDS,
)
from .long_description import (
    parse as long_description_parse,
)


def top_parse(tokens):
    # type: (List[Token]) -> List[List[Token]]
    """Split the docstring into sections.

    Each section will be parsed individually, according
    to the combinator.

    Args:
        tokens: The tokens representing the entire docstring.

    Returns:
        The docstring, split into sections.

    """
    def at_section_boundary(i):
        # type: (int) -> int
        """Return the number of tokens which start this new section.

        Args:
            i: The current pointer in the token list.

        Returns:
            The number of tokens which start this new section.
            If 0, then this is not a new section.

        """
        if i >= len(tokens):
            return 0
        if tokens[i].token_type == TokenType.OTHER:
            if (
                i + 3 < len(tokens) and
                tokens[i + 1].token_type == TokenType.ARGUMENTS and
                tokens[i + 2].token_type == TokenType.NEWLINE and
                tokens[i + 3].token_type == TokenType.HEADER
            ):
                return 4
            else:
                return 0
        elif tokens[i].token_type == TokenType.SEE:
            if (
                i + 3 < len(tokens) and
                tokens[i + 1].token_type == TokenType.ALSO and
                tokens[i + 2].token_type == TokenType.NEWLINE and
                tokens[i + 3].token_type == TokenType.HEADER
            ):
                return 4
            else:
                return 0
        elif tokens[i].token_type in KEYWORDS:
            if (
                i + 2 < len(tokens) and
                tokens[i + 1].token_type == TokenType.NEWLINE and
                tokens[i + 2].token_type == TokenType.HEADER
            ):
                return 3
            else:
                return 0
        else:
            return 0

    # Handle an empty docstring.
    if not tokens:
        return list()

    curr = list()  # type: List[Token]
    overall = list()  # type: List[List[Token]]
    i = 0
    while i < len(tokens) and tokens[i].token_type != TokenType.NEWLINE:
        i += 1
    while i < len(tokens) and tokens[i].token_type == TokenType.NEWLINE:
        i += 1
    overall = [tokens[:i]]
    while i < len(tokens):
        beginning_tokens = at_section_boundary(i)
        if beginning_tokens and curr:
            overall.append(curr)
            curr = list()
            curr.extend(tokens[i:i + beginning_tokens + 1])
            i += beginning_tokens + 1
        else:
            curr.append(tokens[i])
            i += 1
    if curr:
        overall.append(curr)
    return overall


def _match(token):
    # type: (Token) -> List[Union[Callable, BaseGrammar]]
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
            long_description_parse,
        ],
        TokenType.ARGUMENTS: [
            ArgumentsGrammar,
            long_description_parse,
        ],
        TokenType.YIELDS: [
            YieldsGrammar,
            long_description_parse,
        ],
        TokenType.RAISES: [
            RaisesGrammar,
            long_description_parse,
        ],
        TokenType.WARNS: [
            WarnsGrammar,
            long_description_parse,
        ],
        TokenType.RECEIVES: [
            ReceivesGrammar,
            long_description_parse,
        ],
        TokenType.OTHER: [
            OtherArgumentsGrammar,
            long_description_parse,
        ],
        # Discard these two sections -- there's nothing
        # to check against the function description.
        TokenType.SEE: [
            long_description_parse,
        ],
        TokenType.NOTES: [
            long_description_parse,
        ],
        TokenType.EXAMPLES: [
            long_description_parse,
        ],
    }  # type: Dict[TokenType, List[Union[BaseGrammar, Callable]]]  # noqa: E501
    return tt_lookup.get(token.token_type, [long_description_parse])


def lookup(section, section_index=-1):
    Assert(len(section) > 0, 'Expected a non-empty section.')
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
    # type: (List[Token]) -> Optional[CykNode]
    def mapped_lookup(section, section_index=-1):
        for grammar in lookup(section, section_index):
            if inspect.isclass(grammar):
                yield lambda x: cyk_parse(grammar, x)
            else:
                yield grammar
    return parser_combinator(top_parse, mapped_lookup, combinator, tokens)
