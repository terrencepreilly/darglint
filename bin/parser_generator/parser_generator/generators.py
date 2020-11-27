import datetime
from copy import copy
from typing import (
    Dict,
    List,
    Iterable,
    Optional,
    Set,
    Tuple,
)
from itertools import (
    chain,
)

from bnf_to_cnf.parser import (  # type: ignore
    Parser,
    NodeType,
    Node,
)

Production = Tuple[str, List[str]]


class LLTableGenerator:

    def __init__(self, grammar: str) -> None:
        self.bnf = Parser().parse(grammar)
        self._table = None  # type: Optional[List[Production]]
        self._adjacency_matrix = None  # type: Optional[Dict[str, List[List[str]]]]  # noqa
        self.start = next(self.bnf.filter(Node.is_start)).value

    @property
    def terminals(self) -> Iterable[str]:
        for _, lhs in self.table:
            for term in lhs:
                if self._is_term(term):
                    yield term

    @property
    def nonterminals(self) -> Iterable[str]:
        for rhs, _ in self.table:
            yield rhs

    def _normalize_terminal_value(self, value: str) -> str:
        return value.replace('\\', '')

    @property
    def adjacency_matrix(self) -> Dict[str, List[List[str]]]:
        """Get the grammar as an adjacency matrix.

        Returns:
            An adjacency matrix, where each non-terminal points to
            the productions it creates.

        """
        if self._adjacency_matrix:
            return self._adjacency_matrix
        self._adjacency_matrix = dict()
        for rhs, lhs in self.table:
            if rhs not in self._adjacency_matrix:
                self._adjacency_matrix[rhs] = list()
            self._adjacency_matrix[rhs].append(lhs)
        return self._adjacency_matrix

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
        """Yield all of the non-terminal productions in the grammar.

        Args:
            grammar: The grammar to extract non-terminals from.

        Yields:
            Productions which are non-terminal.

        """
        for lhs, rhs in grammar:
            if len(rhs) > 0 and not self._is_term(rhs[0]) and rhs[0] != 'ε':
                yield (lhs, rhs)

    def _after(self, needle: str, haystack: List[str]) -> Iterable[Tuple[str, Optional[str]]]:
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

    def two_iter(self, rhs: List[str]) -> Iterable[Tuple[str, str]]:
        for i in range(len(rhs) - 1):
            yield rhs[i], rhs[i + 1]

    def reverse_nonterms(self, rhs: List[str],
                         first: Dict[str, Set[str]]
                         ) -> Iterable[str]:
        """Return production-end non-terminals.

        Args:
            rhs: The right-hand side.
            first: The first set.

        Yields:
            Non-terminals at the end of the production.  Yields
            starting at the last one, and continues until it reaches
            a non-ε terminal or non-terminal without ε in its first
            set.

        """
        for i in range(len(rhs))[::-1]:
            if self._is_term(rhs[i]):
                break
            elif rhs[i] == 'ε':
                continue
            else:
                if 'ε' not in first[rhs[i]]:
                    yield rhs[i]
                    break
                else:
                    yield rhs[i]

    def first(self) -> Dict[str, Set[str]]:
        """Calculate the first set for generating an LL(1) table.

        Returns:
            A mapping from non-terminal productions to the first terminal
            symbols (or ε), which can occur in them.

        """
        G = self.table
        F = {x: set() for x, _ in G}  # type: Dict[str, Set[str]]
        changed = True
        while changed:
            changed = False
            for lhs, rhs in G:
                prev = copy(F[lhs])
                if self._is_term(rhs[0]) or rhs[0] == 'ε':
                    F[lhs].add(rhs[0])
                for i in range(len(rhs)):
                    if self._is_term(rhs[i]) or rhs[i] == 'ε' or 'ε' not in F[rhs[i]]:
                        break
                    for lhs2, rhs2 in G:
                        for s1, s2 in self._after(rhs[i], rhs2):
                            if self._is_term(s1):
                                F[lhs].add(s1)
                            elif s2 and 'ε' in F[s1]:
                                F[lhs] |= (
                                    F[s1]
                                    | ({s2} if self._is_term(s2) else F[s2])
                                ) - {'ε'}
                            else:
                                F[lhs] |= F[s1]
                if not self._is_term(rhs[0]) and rhs[0] != 'ε' and F[rhs[0]] != 'ε':
                    F[lhs] |= F[rhs[0]] - {'ε'}
                changed |= prev != F[lhs]
        return F

    def follow(self, first: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Calculate the follow set for generating an LL(1) table.

        Args:
            first: The previously calculated first-set.

        Returns:
            A mapping from non-terminal productions to the first
            terminals which can follows them.

        """
        G = self.table
        F = {x: set() for x, _ in G}  # type: Dict[str, Set[str]]
        F[self.start] = {'$'}

        changed = True
        while changed:
            changed = False
            for lhs, rhs in G:
                for term1, term2 in self.two_iter(rhs):
                    if self._is_term(term1):
                        continue
                    if self._is_term(term2):
                        changed |= term2 not in F[term1]
                        F[term1].add(term2)
                    else:
                        for x in filter(self._is_term, first[term2]):
                            changed |= x not in F[term1]
                            F[term1].add(x)
                        if 'ε' in first[term2]:
                            changed |= bool(F[term2] - F[term1])
                            F[term1] |= F[term2]
                for term in self.reverse_nonterms(rhs, first):
                    changed |= bool(F[lhs] - F[term])
                    F[term] |= F[lhs]
        return F

    def goes_to(self,
                nonterm: str,
                term: str) -> bool:
        stack = [nonterm]
        encountered = set()
        while stack:
            curr = stack.pop()
            encountered.add(curr)
            for lhs in self.adjacency_matrix[curr]:
                assert len(lhs) > 0, 'Expected a non-empty LHS.'
                if self._is_term(lhs[0]):
                    if lhs[0] == term:
                        return True
                elif lhs[0] == 'ε':
                    continue
                elif lhs[0] not in encountered:
                    stack.append(lhs[0])
        return False

    def get_production_leading_to_terminal(self,
                                           nonterm: str,
                                           term: str
                                           ) -> Iterable[Production]:
        for lhs in self.adjacency_matrix[nonterm]:
            if self._is_term(lhs[0]) and lhs[0] == term:
                yield (nonterm, lhs)
            elif lhs[0] == 'ε' and lhs[0] == term:
                yield (nonterm, lhs)
            elif not self._is_term(lhs[0]) and lhs[0] != 'ε':
                if self.goes_to(lhs[0], term):
                    yield (nonterm, lhs)

    def generate_table(self,
                       first: Dict[str, Set[str]],
                       follow: Dict[str, Set[str]]
                       ) -> Dict[str, Dict[str, Production]]:
        table = {
            nonterm: dict()
            for nonterm in self.nonterminals
        }  # type: Dict[str, Dict[str, Production]]
        for nonterm, terms in first.items():
            for term in terms:
                productions = list(self.get_production_leading_to_terminal(
                    nonterm, term
                ))
                assert len(productions) == 1, 'Ambiguous grammar.'
                production = productions[0]
                if term == 'ε':
                    for term2 in follow[nonterm]:
                        table[nonterm][term2] = production
                else:
                    table[nonterm][term] = production
        return table


def normalize_for_table(symbol: str) -> str:
    if symbol.startswith('"') and symbol.endswith('"'):
        return symbol[1:-1]
    return repr(symbol)


PARSE_EXCEPTION = r'''
class ParseException(Exception):
    pass
'''

PARSE = r'''
    def parse(self):
        # type: () -> Optional[Node]
        root = Node(node_type={start_symbol})
        stack = deque([root])
        token = next(self.tokens)
        token_type = token.token_type
        while stack:
            curr = stack.popleft()
            if curr.node_type == 'ε':
                continue
            if isinstance(curr.node_type, TokenType):
                if curr.node_type == token_type:
                    curr.value = token
                    try:
                        token = next(self.tokens)
                        token_type = token.token_type
                    except StopIteration:
                        token = None
                        token_type = '$'
                    continue
                else:
                    raise ParseException(
                        'Expected token type {{}}, but got {{}}'.format(
                            token_type, curr.node_type
                        )
                    )
            if curr.node_type not in self.table:
                raise ParseException(
                    'Expected {{}} to be in grammar, but was not.'.format(
                        curr,
                    )
                )
            if token_type not in self.table[curr.node_type]:
                raise ParseException(
                    'Expected {{}} to be in a production '
                    'of {{}}, but was not.'.format(
                        token, curr
                    )
                )
            lhs, rhs = self.table[curr.node_type][token_type]

            # `extendleft` appends in reverse order,
            # so we have to reverse before extending.
            # Otherwise, right-recursive productions will
            # never finish parsing.
            children = [Node(x) for x in rhs]
            curr.children = children
            stack.extendleft(children[::-1])
        return root
'''


def generate_parser(grammar: str, imports: Optional[str]) -> str:
    generator = LLTableGenerator(grammar)
    first = generator.first()
    follow = generator.follow(first)
    table = generator.generate_table(first, follow)
    if imports:
        imports_or_blank = f'\n{imports}\n'
    else:
        imports_or_blank = ''

    parser = [
        f'# Generated on {datetime.datetime.now()}',
        '',
        'from collections import deque',
        'from typing import (Iterator, Optional)',
        imports_or_blank,
        PARSE_EXCEPTION,
        'class Parser(object):',
        '    table = {'
    ]
    for row_value, row in table.items():
        parser.append(' ' * 8 + f'{normalize_for_table(row_value)}: {{')
        for col_value, production in row.items():
            parser.append(' ' * 12 + f'{normalize_for_table(col_value)}: (')
            lhs, rhs = production
            parser.append(' ' * 16 + f'{normalize_for_table(lhs)},')
            parser.append(' ' * 16 + '[')
            for value in rhs:
                parser.append(' ' * 20 + f'{normalize_for_table(value)},')
            parser.append(' ' * 16 + ']')
            parser.append(' ' * 12 + '),')
        parser.append(' ' * 8 + '},')
    parser.append(' ' * 4 + '}')

    parser.append('')
    parser.append('    def __init__(self, tokens):')
    parser.append('        # type: (Iterator[Token]) -> None')
    parser.append('        self.tokens = tokens')
    parser.append('')
    parser.append(PARSE.strip('\n').format(start_symbol=repr(generator.start)))

    return '\n'.join(parser)
