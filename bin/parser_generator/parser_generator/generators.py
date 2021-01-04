import datetime
from copy import copy
from functools import (lru_cache, reduce)
from typing import (
    Any,
    Dict,
    List,
    Iterable,
    Optional,
    Set,
    Tuple,
    Union,
)
from itertools import (
    chain,
)

from bnf_to_cnf.parser import (  # type: ignore
    Parser,
    NodeType,
    Node,
)
from .production import Production
from .debug import RecurseDebug


def is_term(symbol: str) -> bool:
    return symbol.startswith('"') and symbol.endswith('"')


def gen_cache(max_iterator_depth=200):
    """A memoization wrapper for functions which return generators.

    The generator is evaluated at cache time, and a new generator
    is returned based on those results.  This means that the generator
    which is returned cannot be cyclic in nature, or caching it will
    loop forever.  For that reason, you can specify a max recursion depth
    for this cache.

    Args:
        max_iterator_depth: The maximum amount of items which can be pulled
            from the generator.

    Raises:
        Exception: If the maximum iterator depth has been exceeded.

    Returns:
        A decorator which caches the results from functions which return
        generators.

    """
    def _wrapper(fun):
        _cache = dict()

        def _inner(*args, **kwargs):
            key = (tuple(args), tuple(kwargs.items()))
            if key not in _cache:
                _cache[key] = list()
                counter = 0
                for value in fun(*args, **kwargs):
                    _cache[key].append(value)
                    counter += 1
                    if counter > max_iterator_depth:
                        raise Exception('Max iterator depth reached.')
            return (x for x in _cache[key])
        return _inner
    return _wrapper


class SubProduction:
    """Identifies a subset of a give production.

    A subset of a production is here given to be some
    ordered set of terminal and non-terminal symbols which
    occur on the RHS of some production P in G:

        ⟨s₁, s₂, ..., sₙ⟩

    """

    def __init__(self, symbols: List[str]):
        self.symbols = symbols

    def head(self) -> Tuple[Optional[str], 'SubProduction']:
        if self.symbols:
            return self.symbols[0], SubProduction(self.symbols[1:])
        return None, self

    def initial_terminals(self, k: int
                          ) -> Tuple['SubProduction', 'SubProduction']:
        if k == 0 and self.symbols and self.symbols[0] == 'ε':
            return SubProduction(['ε']), SubProduction([])
        i = 0
        while i < k and i < len(self.symbols) and (
                is_term(self.symbols[i]) or self.symbols[i] == 'ε'):
            i += 1
        return SubProduction(self.symbols[:i]), SubProduction(self.symbols[i:])

    def normalized(self) -> List[str]:
        if len(self) <= 1:
            return self.symbols
        return [x for x in self.symbols if x != 'ε']

    def __add__(self, other: 'SubProduction') -> 'SubProduction':
        return SubProduction(self.symbols + other.symbols)

    def __str__(self) -> str:
        return repr(self.symbols)

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self.symbols)

    def __len__(self) -> int:
        return len(self.symbols)

    def __key(self) -> Tuple[str, ...]:
        return tuple(self.symbols)

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SubProduction):
            return self.__key() == other.__key()
        return False

    def __getitem__(self, index: int) -> str:
        return self.symbols[index]


class FirstSet:

    def __init__(self, *sequences: SubProduction):
        self.sequences = list(sequences)

    def __len__(self) -> int:
        return len(self.sequences)

    def __mul__(self, other: 'FirstSet') -> 'FirstSet':
        result = FirstSet()
        for first_sequence in self.sequences:
            for second_sequence in other.sequences:
                if first_sequence == ['ε']:
                    result.sequences.append(second_sequence)
                elif second_sequence == ['ε']:
                    result.sequences.append(first_sequence)
                else:
                    result.sequences.append(first_sequence + second_sequence)
        return result

    def __bool__(self) -> bool:
        return bool(self.sequences)

    def __or__(self, other: 'FirstSet') -> 'FirstSet':
        return FirstSet(*self.sequences, *other.sequences)

    def __str__(self) -> str:
        return '{' + ', '.join(map(str, self.sequences)) + '}'

    def __repr__(self) -> str:
        return str(self)


class Grammar:
    def __init__(self, table: List[Production]):
        self.table = table

    def __getitem__(
        self,
        key: Union[int, str]
    ) -> Union[SubProduction, List[SubProduction]]:
        if isinstance(key, int):
            return SubProduction(self.table[key][1])
        elif isinstance(key, str):
            return [
                SubProduction(rhs) for lhs, rhs in self.table if lhs == key
            ]
        else:
            raise ValueError(
                'Grammar only indexed by production index '
                'or non-terminal symbol.'
            )


class LLTableGenerator:

    def __init__(self,
                 grammar: str,
                 lookahead: int = 1,
                 debug: bool = False
                 ) -> None:
        self.lookahead = lookahead
        self.bnf = Parser().parse(grammar)
        self._table = None  # type: Optional[List[Production]]
        self._adjacency_matrix = None  # type: Optional[Dict[str, List[List[str]]]]  # noqa
        self.start = next(self.bnf.filter(Node.is_start)).value
        self.debug = RecurseDebug('fi') if debug else None

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

    @gen_cache(max_iterator_depth=1000)
    def _kfirst(self,
                symbol: Union[str, SubProduction],
                k: int,
                allow_underflow: bool = True,
                parent_debug: Optional[str] = None,
                ) -> Iterable[FirstSet]:
        """Get the k-first lookup table.

        This method satisfies

            _kfirst(k) = ⋃ Fi(s0, n) ∀ n ∊ 1..k

        Where `s0` is a symbol in the grammar and

            Fi(s0, n) = ∀ p ∊ G, the set of all
                | ⟨x1⟩
                |   if p = s0 -> x1 where x1 is terminal or ε, and n = 1
                | ⟨x1, x2, ..., xn⟩
                |   if s0 -> x1 x2 ... xn, ... is in G
                |       where x1..xn are terminals
                | ⟨x1, x2, ..., xj⟩ × Fi(⟨s1, ...⟩, n - j)
                |   if s0 -> x1 x2 ... xj, s1, ..., where x1-xn are terminals,
                |   s1 is non-terminal, and Fi(s1, n - j) is defined.

        The symbol ε counts as length 1, and could be found in the
        middle of any of the subproductions in the yielded sets.
        These are valid, even if they're not of the correct length.

        Args:
            symbol: The lhs or rhs for which we should generate kfirst.
            k: The maximum number of symbols in the yielded firstset.
            allow_underflow: Whether we can yield firstsets of less than
                k length.

        Yields:
            Lists of terminal symbols.

        """
        debug_symbol = None
        if self.debug:
            debug_symbol = self.debug.add_call(
                [symbol, k],
                {'allow_underflow': allow_underflow},
                extra=[]
            )
        if parent_debug:
            self.debug.add_child(parent_debug, debug_symbol)

        G = Grammar(self.table)

        # Fi(S, k)
        if isinstance(symbol, str):
            for subproduction in G[symbol]:
                yield from self._kfirst(subproduction,
                                        k,
                                        allow_underflow=allow_underflow,
                                        parent_debug=debug_symbol)
            return

        assert isinstance(symbol, SubProduction)
        # Fi(<>, k)
        if not symbol:
            if self.debug:
                self.debug.add_result(debug_symbol, '<>')
            yield FirstSet()
            return

        # Fi(<s1, s2, ..., s_k>, k)
        terms, rest = symbol.initial_terminals(k)
        # There will be more than k terms if k = 0 and symbol contains ε.
        if len(terms) == 1 and terms[0] == 'ε' and k == 0:
            if self.debug:
                self.debug.add_result(debug_symbol, terms[0])
            yield FirstSet(terms)
            return
        if terms and len(terms) == k:
            if allow_underflow or len(rest) == 0:
                if self.debug:
                    self.debug.add_result(debug_symbol, terms)
                yield FirstSet(terms)
                return
        # len(terms) < k

        # Fi(<s1, s2, ..., s_(k - n)>, k), where n > 0
        # We can't build up to k symbols.
        if not rest:
            if self.debug:
                self.debug.add_result(debug_symbol, 'X')
            return

        # Fi(<S, s2, ...>, k)
        # The first symbol is non-terminal.
        if len(terms) == 0:
            head, rest = symbol.head()
            assert head is not None
            yield from self._kfirst(
                head,
                k,
                allow_underflow,
                parent_debug=debug_symbol
            )
            # At i = k, first_first will be _kfirst(head, 0)
            # This is meaningful if head has <ε>.
            for i in range(1, k + 1):
                for first_first in self._kfirst(
                    head,
                    k - i,
                    False,
                    parent_debug=debug_symbol
                ):
                    for second_first in self._kfirst(
                        rest,
                        i,
                        allow_underflow,
                        parent_debug=debug_symbol
                    ):
                        if self.debug:
                            self.debug.add_result(
                                debug_symbol,
                                first_first * second_first
                            )
                        yield first_first * second_first
            return

        # Fi(<s1, s2, ..., s_(k - n), S, ...>, k), where n > 0
        # There are < k terminals, followed by at least one non-terminal.
        rest_kfirst = self._kfirst(
            rest, k - len(terms), allow_underflow, parent_debug=debug_symbol)
        rest_kfirst = reduce(FirstSet.__or__, rest_kfirst, FirstSet())
        if self.debug:
            self.debug.add_result(debug_symbol, FirstSet(terms) * rest_kfirst)
        yield FirstSet(terms) * rest_kfirst

    def kfirst(self, k: int) -> Dict[str, Set[str]]:
        F = {x: set() for x, _ in self.table}
        for i in range(1, k + 1):
            for symbol in F.keys():
                first_set = reduce(
                    FirstSet.__or__,
                    self._kfirst(symbol, i),
                    FirstSet()
                )
                for subproduction in first_set.sequences:
                    normalized = subproduction.normalized()
                    if len(normalized) == 1:
                        F[symbol].add(normalized[0])
                    else:
                        F[symbol].add(tuple(normalized))
        return F

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

    # TODO: Change to handle multiple terminals
    # TODO: Change to be stored as an intermediate result of Fi, Fo
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
                # TODO: Should this ever happen?
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
