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
    Any,
    Iterator,
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

    def __init__(self,
                 symbol,
                 lchild=None,
                 rchild=None,
                 value=None,
                 annotations=list()):
        # type: (str, Optional[CykNode], Optional[CykNode], Optional[Token], List[Any]) -> None  # noqa: E501
        self.symbol = symbol
        self.lchild = lchild
        self.rchild = rchild
        self.value = value
        self.annotations = annotations

    def __str__(self, indent=0):
        if self.value:
            ret = (
                ' ' * indent
                + str(self.value.token_type)
                + ': '
                + repr(self.value.value)
            )
        else:
            ret = ' ' * indent + self.symbol
        if self.annotations:
            ret += ': ' + ', '.join([str(x) for x in self.annotations])
        if self.lchild:
            ret += '\n' + self.lchild.__str__(indent + 2)
        if self.rchild:
            ret += '\n' + self.rchild.__str__(indent + 2)
        return ret

    # TODO: Make this imperative.
    def in_order_traverse(self):
        # type: () -> Iterator['CykNode']
        if self.lchild:
            yield from self.lchild.in_order_traverse()
        yield self
        if self.rchild:
            yield from self.rchild.in_order_traverse()

    def reconstruct_string(self, strictness=0):
        # type: (int) -> str
        """Reconstruct the docstring.

        This method should rebuild the docstring while fixing style
        errors.  The errors themselves determine how to fix the node
        they apply to.  (If there isn't a good fix, then it's just the
        identity function.)

        Args:
            strictness: How strictly we should correct.  If an error
                doesn't match the strictness, we won't correct for
                that error.

        Returns:
            The docstring, reconstructed.

        """
        ret = ''
        for node in self.in_order_traverse():
            if node.value:
                # TODO: Make this into a not-gross check.
                if ret and node.value.value != '\n':
                    ret += ' '
                ret += node.value.value
        return ret


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
                        annotations, B, C = derivation
                        b = lookup[B]
                        c = lookup[C]
                        lchild = P[p - 1][s - 1][b]
                        rchild = P[l - p - 1][s + p - 1][c]
                        if lchild and rchild:
                            P[l - 1][s - 1][a] = CykNode(
                                production.lhs,
                                lchild,
                                rchild,
                                annotations=annotations,
                            )
    return P[n - 1][0][lookup[grammar.start]]
