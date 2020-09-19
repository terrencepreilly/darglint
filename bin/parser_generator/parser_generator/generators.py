from copy import copy
from typing import (
    List,
    Iterable,
    Optional,
    Set,
    Tuple,
)
from itertools import (
    chain,
)

from bnf_to_cnf.parser import (
    Parser,
    NodeType,
    Node,
)
from bnf_to_cnf.translator import (
    Translator,
)
from bnf_to_cnf.validate import (
    Validator,
)

Production = Tuple[str, List[str]]


class LLTableGenerator:

    def __init__(self, grammar: str) -> None:
        self.bnf = Parser().parse(grammar)
        self._table = None  # type: Optional[List[Production]]

    @property
    def rules(self) -> List[Tuple[str, Node]]:
        """Return a list of rules.

        Returns:
            A list of rules.  Each rule is a tuple,
            containing the production and the RHS.

        """
        pass

    def _normalize_terminal_value(self, value: str) -> str:
        return value.replace('\\', '')

    @property
    def table(self) -> List[Production]:
        """Transform the grammar into an easier representation for parsing.

        Returns:
            The grammar, but as a list of productions.  For example,
            the grammar

                <S> ::= <A>
                    | <A> <B>
                <A> ::= "A"
                <B> ::= "B"

            would be represented as

                [ ('S', ['A'])
                , ('S', ['A', 'B'])
                , ('A', ['"A"'])
                , ('B', ['"B"'])
                ]

        """
        if self._table:
            return self._table
        self._table = list()
        for production in self.bnf.filter(
            lambda x: x.node_type == NodeType.PRODUCTION
        ):
            assert production.children[0].node_type == NodeType.SYMBOL
            lhs = production.children[0].value
            for expression in production.filter(
                lambda x: x.node_type == NodeType.EXPRESSION
            ):
                for sequence in expression.filter(
                    lambda x: x.node_type == NodeType.SEQUENCE,
                ):
                    rhs = list()  # type: List[str]
                    for child in sequence.children:
                        if child.node_type == NodeType.SYMBOL:
                            rhs.append(child.value)
                        elif child.node_type == NodeType.TERMINAL:
                            rhs.append(self._normalize_terminal_value(
                                child.value
                            ))
                    self._table.append((lhs, rhs))
        return self._table

    def _is_term(self, symbol: str) -> bool:
        return symbol.startswith('"') and symbol.endswith('"')

    def _eps(self, grammar: List[Production]) -> Iterable[Production]:
        for lhs, rhs in grammar:
            if len(rhs) == 1 and rhs[0] == 'ε':
                yield (lhs, rhs)

    def _terms(self, grammar: List[Production]) -> Iterable[Production]:
        for lhs, rhs in grammar:
            if len(rhs) > 0 and self._is_term(rhs[0]):
                yield (lhs, rhs)

    def _nonterms(self, grammar: List[Production]) -> Iterable[Production]:
        for lhs, rhs in grammar:
            if len(rhs) > 0 and not self._is_term(rhs[0]) and rhs[0] != 'ε':
                yield (lhs, rhs)

    def _after(self, needle: str, haystack: List[str]) -> Iterable[Production]:
        gen = (x for x in haystack)
        try:
            while True:
                symbol = next(gen)
                if symbol == needle:
                    s1 = next(gen)
                    try:
                        s2 = next(gen)
                    except StopIteration:
                        yield s1, None
                        break
                    yield s1, s2
        except StopIteration:
            pass

    def first(self):
        G = self.table
        F = {x: set() for x, _ in G}
        for lhs, rhs in chain(self._terms(G), self._eps(G)):
            F[lhs].add(rhs[0])
        changed = True
        i = 0
        while changed:
            changed = False
            for lhs, rhs in chain(self._nonterms(G), self._eps(G)):
                i += 1
                prev = copy(F[lhs])
                if rhs[0] == 'ε':
                    F[lhs].add('ε')
                elif 'ε' in F[rhs[0]]:
                    for lhs2, rhs2 in G:
                        for s1, s2 in self._after(rhs[0], rhs2):
                            if self._is_term(s1):
                                F[lhs].add(s1)
                            elif 'ε' in F[s1]:
                                F[lhs] |= (
                                    (F[s1] - {'ε'})
                                    | {s2} if self._is_term(s2) else F[s2]
                                )
                            else:
                                F[lhs] |= F[s1]
                else:
                    F[lhs] |= F[rhs[0]]
                changed |= prev != F[lhs]
        return F
