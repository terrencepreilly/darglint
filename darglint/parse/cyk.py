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


class CykNode(object):
    """A node for use in a cyk parse."""

    def __init__(self, symbol, lchild=None, rchild=None, value=None):
        self.symbol = symbol
        self.lchild = lchild
        self.rchild = rchild
        self.value = value


def build_lookup(grammar):
    lookup = dict()
    for i, symbol in enumerate(grammar.productions):
        lookup[symbol] = i
    return lookup


def parse(grammar, tokens):
    if not tokens:
        return False
    n = len(tokens)
    r = len(grammar.productions)
    P = [
        [[False for _ in range(r)] for _ in range(n)]
        for _ in range(n)
    ]
    lookup = build_lookup(grammar)
    for s in range(n):
        for v, symbol in enumerate(grammar.productions):
            derivations = grammar.productions[symbol]
            if tokens[s] in derivations:
                P[0][s][v] = CykNode(symbol, value=tokens[s])
    for l in range(2, n + 1):
        for s in range(n - l + 2):
            for p in range(l):
                for a, symbol in enumerate(grammar.productions):
                    derivations = grammar.productions[symbol]
                    for derivation in derivations:
                        is_terminal_derivation = isinstance(derivation, str)
                        if is_terminal_derivation:
                            continue
                        B, C = derivation
                        b = lookup[B]
                        c = lookup[C]
                        lchild = P[p - 1][s - 1][b]
                        rchild = P[l - p - 1][s + p - 1][c]
                        if lchild and rchild:
                            P[l - 1][s - 1][a] = CykNode(
                                symbol, lchild, rchild
                            )
    return P[n - 1][0][lookup[grammar.start]]


class SimpleKlingonGrammar(object):
    terminals = {
        "verb": ["SuS"],
    }

    non_terminals = {
        "sentence": [("verb",)],
    }
