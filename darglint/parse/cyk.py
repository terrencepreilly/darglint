"""An implementation of the CYK algorithm.

The CYK algorithm was chosen because the Google
docstring format allows for ambiguous representations,
which CYK can handle without devolving into a terrible
complexity. (It has a worst case of O(n^3).

There are faster, on average, algorithms, which might
be better suited to the average task of Darglint.
However, CYK is relatively simple, and is well documented.
(Others, like chart parsing, are much more difficult
to find examples of.)

This representation was based directly on the wikipedia
article, https://en.wikipedia.org/wiki/CYK_algorithm.

"""

from typing import (
    Optional,
    List,
)

from .grammar import (  # noqa: F401
    BaseGrammar,
    Derivation,
    Production,
)
from ..token import (
    Token,
    BaseTokenType,
)


class CykNode(object):
    """A node for use in a cyk parse."""

    # TODO: Change symbol's type to NodeType.
    def __init__(self, symbol, lchild=None, rchild=None, value=None):
        # type: (str, Optional[CykNode], Optional[CykNode], Optional[Token]) -> None  # noqa: E501
        self.symbol = symbol
        self.lchild = lchild
        self.rchild = rchild
        self.value = value


def parse(grammar, tokens):
    # type: (BaseGrammar, List[Token]) -> Optional[CykNode]
    if not tokens:
        return None
    n = len(tokens)
    r = len(grammar.productions)
    P = [
        [[None for _ in range(r)] for _ in range(n)]
        for _ in range(n)
    ]  # type: List[List[List[Optional[CykNode]]]]
    lookup = grammar.get_symbol_lookup()
    for s, token in enumerate(tokens):
        for v, production in enumerate(grammar.productions):
            if token.token_type in production.rhs:
                P[0][s][v] = CykNode(production.lhs, value=token)
    for l in range(2, n + 1):
        for s in range(n - l + 2):
            for p in range(l):
                for a, production in enumerate(grammar.productions):
                    for derivation in production.rhs:
                        is_terminal_derivation = isinstance(
                            derivation, BaseTokenType
                        )
                        if is_terminal_derivation:
                            continue
                        B, C = derivation
                        b = lookup[B]
                        c = lookup[C]
                        lchild = P[p - 1][s - 1][b]
                        rchild = P[l - p - 1][s + p - 1][c]
                        if lchild and rchild:
                            P[l - 1][s - 1][a] = CykNode(
                                production.lhs, lchild, rchild
                            )
    return P[n - 1][0][lookup[grammar.start]]
