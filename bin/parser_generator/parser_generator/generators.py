import datetime
from collections import (
    defaultdict,
    deque,
)
from copy import copy
from functools import (lru_cache, reduce)
from typing import (
    Any,
    Deque,
    Dict,
    List,
    Iterable,
    Iterator,
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
from .utils import (
    Sequence,
    longest_sequence,
)


def is_term(symbol: str) -> bool:
    return symbol.startswith('"') and symbol.endswith('"')


def is_epsilon(symbol: str) -> bool:
    return symbol == 'ε'


def is_nonterm(symbol: str) -> bool:
    return not (is_term(symbol) or is_epsilon(symbol))


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
        self.__index = 0

    @staticmethod
    def from_sequence(sequence: Sequence) -> 'SubProduction':
        return SubProduction(sequence.sequence)

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

    def __getitem__(self,
                    index: Union[int, slice]
                    ) -> Union[str, 'SubProduction']:
        if isinstance(index, int):
            return self.symbols[index]
        else:
            return SubProduction(self.symbols.__getitem__(index))

    # Although __getitem__ makes it possible to pass this
    # into a list, mypy wants to know that this is an iterator.
    def __iter__(self) -> Iterator[str]:
        self.__index = 0
        return self

    def __next__(self) -> str:
        if self.__index >= len(self):
            raise StopIteration
        ret = self[self.__index]
        self.__index += 1
        assert isinstance(ret, str)
        return ret


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
    def __init__(self, table: List[Production], start: Optional[str] = None):
        self.table = table
        self.start = start

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

    def __iter__(self) -> Iterator[Tuple[str, SubProduction]]:
        return (
            (lhs, SubProduction(rhs))
            for lhs, rhs in self.table
        )

    def __str__(self) -> str:
        if self.start:
            lines = [f'start: <{self.start}>\n']
        else:
            lines = []
        prev = None
        for lhs, rhs in self.table:
            if lhs == prev:
                line = f'  | '
            else:
                line = f'<{lhs}> ::='
            for symbol in rhs:
                if is_epsilon(symbol):
                    line += f' {symbol}'
                elif is_nonterm(symbol):
                    line += f' <{symbol}>'
                else:
                    line += f' {symbol}'
            prev = lhs
            lines.append(line)
        return '\n'.join(lines)

    def __repr__(self) -> str:
        return str(self)

    def get_exact(self, start: str, k: int) -> Iterable[SubProduction]:
        """Get a derivation of a symbol, which is of an exact length.

        Args:
            start: The symbol at which we should begin the derivation.
            k: The exact length we are hoping to obtain.

        Yields:
            SubProductions of length k which are derived from the given
                symbol, start.

        """
        if is_term(start):
            if k == 1:
                yield SubProduction([start])
            return

        queue = [(SubProduction([]), SubProduction([start]))]
        while queue:
            curr, rem = queue.pop()
            if not rem:
                if len(curr) == k:
                    yield curr
                continue
            head, rest = rem[0], rem[1:]
            assert isinstance(head, str), "Integer index didn't result in str"
            for prod in self[head]:
                if len(prod) == 1 and prod[0] == 'ε':
                    assert isinstance(rest, SubProduction)
                    queue.append((curr, rest))
                    continue
                first_nonterm = 0
                while (first_nonterm < len(prod)
                        and is_term(prod[first_nonterm])):
                    first_nonterm += 1
                if len(curr) + first_nonterm > k:
                    continue
                prod_before_first_nonterm = prod[first_nonterm:]
                assert isinstance(prod_before_first_nonterm, SubProduction)
                prod_after_first_nonterm = prod[:first_nonterm]
                assert isinstance(prod_after_first_nonterm, SubProduction)

                assert isinstance(rest, SubProduction)
                queue.append((
                    curr + prod_after_first_nonterm,
                    prod_before_first_nonterm + rest
                ))

    def _has_infinite_left_recursion(self, start: str) -> Optional[Set[str]]:
        """Return the set of encountered symbols from this start symbol.

        Args:
            start: The symbol where we should start.

        Returns:
            The set of encountered symbols, if we did not encounter infinite
            recursion.  Otherwise, None.

        """
        encountered = set()
        queue = deque([start])  # type: Deque[Union[str, SubProduction]]
        while queue:
            curr = queue.pop()
            if isinstance(curr, str):
                key = curr
                rest = SubProduction([])
            elif isinstance(curr, SubProduction):
                key = curr[0]
                rest = curr[1:]
            else:
                raise Exception('Expected only strings and subproductions.')

            if key in encountered:
                return None

            encountered.add(key)

            for production in self[key]:
                assert isinstance(production, SubProduction)
                if is_nonterm(production[0]):
                    # We have to continue the search with nonterminals.
                    # If this production is only nonterminals, we have to
                    # continue with the rest of the current search, as well.
                    # Otherwise, we know that a fruitful production would
                    # occur in between, and we could just consider this
                    # next set of nonterminals.
                    sequence = longest_sequence(is_nonterm, production, 0)
                    if len(sequence) == len(production):
                        queue.appendleft(
                            SubProduction.from_sequence(sequence) +
                                rest
                        )
                    else:
                        queue.appendleft(
                            SubProduction.from_sequence(sequence)
                        )
                elif is_term(production[0]):
                    # Since it's a terminal, we can stop looking -- it
                    # was fruitful.
                    pass
                elif is_epsilon(production[0]):
                    # The symbols after whatever this is replacing
                    # could result in an infinite recursion. So we
                    # have to check them, if they exist.
                    #
                    # We assume epsilons only occur on their own in a RHS.
                    if rest:
                        queue.appendleft(rest)
        return encountered

    def has_infinite_left_recursion(self) -> bool:
        """Return whether this grammar contains infinite left recursion."""
        symbols = {lhs for lhs, rhs in self}
        while symbols:
            symbol = list(symbols)[0]
            encountered = self._has_infinite_left_recursion(symbol)
            if encountered:
                symbols -= encountered
            else:
                return True
        return False


class FollowSet:
    """Represents a complete or partial follow set.

    Can be iterated over to find the solutions so far.

    """

    def __init__(self,
                 partials: List[SubProduction],
                 complete: List[SubProduction],
                 follow: str,
                 k: int,
                 ):
        """Create a new FollowSet.

        Args:
            partials: Partial solutions, if this is a partial followset.
            complete: Complete solutions, if this is a complete followset.
            follow: The symbol which occurred on the LHS of the production
                under consideration.
            k: The lookahead we are aiming for.

        """
        self.partials = partials
        self.completes = complete
        self.follow = follow
        self.changed = False
        self.k = k
        self.is_complete = bool(complete)
        self.additional = set()  # type: Set[SubProduction]

    @staticmethod
    def complete(subproductions: List[SubProduction],
                 follow: str,
                 k: int) -> 'FollowSet':
        return FollowSet([], subproductions, follow, k)

    @staticmethod
    def empty(follow: str, k: int) -> 'FollowSet':
        """Create an null-value followset.

        This followset shouldn't be used as a value itself.  It should only
        be used as a basis for constructing further followsets.  (Say,
        through a fold/reduce/etc.)  For that reason, it is complete.

        Args:
            follow: The lhs of the production where this symbol occurs.
            k: The production length we're aiming for.

        """
        f = FollowSet([], [], follow, k)
        f.is_complete = True
        return f

    @staticmethod
    def partial(partials: List[SubProduction],
                follow: str,
                k: int,
                ) -> 'FollowSet':
        return FollowSet(
            partials,
            [],
            follow,
            k,
        )

    def append(self, followset: 'FollowSet'):
        """Append the followset of the lhs to this one's solutions.

        Args:
            followset: The followset of the lhs of a production.

        """
        def _add(partial, sub, remaining):
            if len(sub) >= remaining:
                new_complete = (partial + sub)[:self.k]
                if new_complete not in self.additional:
                    self.changed = True
                    self.additional.add(new_complete)

        assert not self.is_complete, 'Complete followsets are immutable.'

        for partial in self.partials:
            remaining = self.k - len(partial)
            if followset.is_complete:
                for complete in followset.completes:
                    _add(partial, complete, remaining)
            else:
                for other_partial in followset.partials:
                    _add(partial, other_partial, remaining)
                for complete in followset.additional:
                    _add(partial, complete, remaining)

    def upgrade(self, followset: 'FollowSet'):
        """Upgrade the lookahead, k, of the followset by absorbing another.

        In this way, you can go through a grammar, and calculate from i = 0..n
        the followset, upgrading the followsets for a particular symbol along
        the way.

        Args:
            followset: The basis for the upgrade (should contain a partial or
               complete solution.)

        Returns:
            The upgraded followset instance.

        """
        assert self.follow == followset.follow, (
            'Can only upgrade to the same follow type.  '
            'This ensures that the fixpoint solution will be found correctly.'
        )
        # I'm not sure if this is valid. But it shouldn't be problematic, if
        # we're only calling this method after the fixpoint solution.
        self.partials.extend(followset.partials)
        self.completes.extend(followset.completes)
        self.k = max(self.k, followset.k)
        self.additional |= followset.additional
        self.is_complete = self.is_complete and followset.is_complete
        return self

    def __iter__(self) -> Iterator[SubProduction]:
        """Return an iterator over the completed subproductions.

        Returns:
            An iterator over the completed subproductions.

        """
        return (x for x in self.additional)

    def __str__(self) -> str:
        return (
            f'<FollowSet {self.follow} {self.partials} '
            f'{self.completes} {self.additional}>'
        )

    def __repr__(self) -> str:
        return str(self)


class LLTableGenerator:

    def __init__(self,
                 grammar: str,
                 lookahead: int = 1,
                 debug: Set[str] = set()
                 ) -> None:
        self.lookahead = lookahead
        self.bnf = Parser().parse(grammar)
        self._table = None  # type: Optional[List[Production]]
        self._adjacency_matrix = None  # type: Optional[Dict[str, List[List[str]]]]  # noqa
        self.start = next(self.bnf.filter(Node.is_start)).value
        self.fi_debug = RecurseDebug('fi') if 'kfirst' in debug else None
        self.fo_debug = RecurseDebug('fo') if 'kfollow' in debug else None

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
            parent_debug: A debug argument which allows us to capture calls
                to this algorithm, and from which, we can print out a
                graphviz graph.

        Yields:
            Lists of terminal symbols.

        """
        debug_symbol = None
        if self.fi_debug:
            debug_symbol = self.fi_debug.add_call(
                [symbol, k],
                {'allow_underflow': allow_underflow},
                extra=[]
            )
        if debug_symbol and parent_debug and self.fi_debug:
            self.fi_debug.add_child(parent_debug, debug_symbol)

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
            if self.fi_debug and debug_symbol:
                self.fi_debug.add_result(debug_symbol, '<>')
            yield FirstSet()
            return

        # Fi(<s1, s2, ..., s_k>, k)
        terms, rest = symbol.initial_terminals(k)
        # There will be more than k terms if k = 0 and symbol contains ε.
        if len(terms) == 1 and terms[0] == 'ε' and k == 0:
            if self.fi_debug and debug_symbol:
                self.fi_debug.add_result(debug_symbol, terms[0])
            yield FirstSet(terms)
            return
        if terms and len(terms) == k:
            if allow_underflow or len(rest) == 0:
                if self.fi_debug and debug_symbol:
                    self.fi_debug.add_result(debug_symbol, terms)
                yield FirstSet(terms)
                return
        # len(terms) < k

        # Fi(<s1, s2, ..., s_(k - n)>, k), where n > 0
        # We can't build up to k symbols.
        if not rest:
            if self.fi_debug and debug_symbol:
                self.fi_debug.add_result(debug_symbol, 'X')
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
                        if self.fi_debug and debug_symbol:
                            self.fi_debug.add_result(
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
        if debug_symbol and self.fi_debug:
            self.fi_debug.add_result(debug_symbol, FirstSet(terms) * rest_kfirst)
        yield FirstSet(terms) * rest_kfirst

    def kfirst(self, k: int) -> Dict[str, Set[Union[str, Tuple[str, ...]]]]:
        F = {x: set() for x, _ in self.table}  # type: Dict[str, Set[Union[str, Tuple[str, ...]]]]
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
                        # If the subproductions were just epsilons, add an
                        # epsilon.
                        if not normalized:
                            F[symbol].add('ε')
                        else:
                            F[symbol].add(tuple(normalized))
        return F

    def first(self) -> Dict[str, Set[str]]:
        """Calculate the first set for generating an LL(1) table.

        Returns:
            A mapping from non-terminal productions to the first terminal
            symbols (or ε), which can occur in them.

        """
        return {
            key: {x for x in value if isinstance(x, str)}
            for key, value in self.kfirst(1).items()
        }

    def _kfollow_resolve_permutation(self,
                                     production: Production,
                                     base_index: int,
                                     current_permutation: Tuple[int, ...],
                                     allow_firstset: bool = True,
                                     parent_debug: Optional[str] = None,
                                     ) -> Iterable[SubProduction]:
        """Get all derivations from this subproduction of the exact lengths.

        Args:
            production: The production from which we will take derivations.
            base_index: How far into the rhs the derivations should start.
                That is, our derivation will be for production[1][base_index:].
            current_permutation: The exact lengths we are searching for.  For
                example, if current_permutation is [1, 0, 2], our production
                is ('A', ['a', 'B', 'C', 'D']), and the base index is 1, then
                we are seeking all derivations of ['B', 'C', 'D'] such that the
                derivation of 'B' is of length 1, the derivation of 'C' is a
                epsilon, and the derivation of 'D' is of length 2.
            allow_firstset: If true, then we should allow the returned
                subproductions to include values taken from the firstset of a
                production.
            parent_debug: If we're debugging the algorithm, the debug
                information of the parent call.

        Yields:
            SubProductions which follow the given permutation's length
            requirements.

        """
        debug = None
        if self.fo_debug and parent_debug:
            debug = self.fo_debug.add_call(
                [production, base_index, current_permutation],
                dict(),
                ['_kfollow_resolve_permutations']
            )
            self.fo_debug.add_child(parent_debug, debug)
        lhs, rhs = production
        assert base_index < len(rhs), (
            f'The permutation should have some symbols, but it starts '
            f'at {base_index} for {rhs}'
        )


        last_nonzero = len(current_permutation) - 1
        while last_nonzero >= 0 and current_permutation[last_nonzero] == 0:
            last_nonzero -= 1

        # Build up all possible productions of the length given in
        # the permutation.
        G = Grammar(self.table)
        unzipped_permutations = list()
        for i in range(len(current_permutation)):
            symbol = rhs[i + base_index]

            # If the symbol is a terminal, _kfirst won't return anything.
            # (Although, it should really return that symbol, if we have
            # a k of 1.)  So, instead, we get the exact length production,
            # which will return the symbol. (If it's a k of 1.)
            #
            # We should only allow adding a firstset to the result if the
            # result will be used in a _completed_ followset.  Otherwise, the
            # partial firstset could be appended to during the fixpoint solution.
            if i == last_nonzero and not is_term(symbol) and allow_firstset:
                all_exact_length_productions = list()
                for item in self._kfirst(
                    symbol,
                    current_permutation[i],
                    True,
                    debug
                ):
                    for subproduction in item.sequences:
                        if len(subproduction) == 1 and subproduction[0] == 'ε':
                            continue
                        all_exact_length_productions.append(subproduction)
            else:
                # Get all productions of the exact length specified.
                # If it's not possible, abort.
                all_exact_length_productions = list(
                    G.get_exact(symbol, current_permutation[i])
                )

            if not all_exact_length_productions:
                return
            unzipped_permutations.append(all_exact_length_productions)

        # Zip up the productions of exact length to form the permutations.
        stack = [(SubProduction([]), 0)]
        while stack:
            curr, i = stack.pop()
            if i == len(unzipped_permutations):
                if debug and self.fo_debug:
                    self.fo_debug.add_result(
                        debug,
                        curr,
                    )
                yield curr
                continue
            for terminal in unzipped_permutations[i]:
                stack.append((curr + terminal, i + 1))

    def _kfollow_permutations(self,
                              production: Production,
                              base_index: int,
                              k: int,
                              parent_debug: Optional[str] = None,
                              ) -> Iterable[FollowSet]:
        debug = None
        if self.fo_debug and parent_debug:
            debug = self.fo_debug.add_call([production, base_index, k], dict(), ['_kfollow_permutations'])
            self.fo_debug.add_child(parent_debug, debug)

        lhs, rhs = production
        # If the symbol occurred at the end of the RHS, then we have
        # no permutations -- it'll be composed of the LHS followset.
        if base_index == len(rhs):
            yield FollowSet.partial([SubProduction([])], lhs, k)
            return

        queue = [(i,) for i in range(k + 1)]  # type: List[Tuple[int, ...]]
        guard = 500
        while queue:
            if not guard:
                raise Exception('Reached max iteration.')
            guard -= 1

            current_permutation = queue.pop()
            if debug and self.fo_debug:
                new_debug = self.fo_debug.add_call(
                    [current_permutation],
                    dict(),
                    ['_kfollow_permutations', f'iteration {500 - guard}'],
                )
                self.fo_debug.add_child(debug, new_debug)
                debug = new_debug
            at_max_k = sum(current_permutation) == k
            assigned_each_symbol_value = (len(rhs) - base_index) <= len(
                current_permutation)
            if at_max_k:
                ret = FollowSet.complete(
                    list(self._kfollow_resolve_permutation(
                        production,
                        base_index,
                        current_permutation,
                        allow_firstset=True,
                        parent_debug=debug,
                    )),
                    lhs,
                    k
                )
                if debug and self.fo_debug:
                    self.fo_debug.add_result(debug, ret)
                yield ret
            elif assigned_each_symbol_value:
                # This means we have a partial solution, which will need to
                # be resolved during the fixpoint phase.
                ret = FollowSet.partial(
                    list(self._kfollow_resolve_permutation(
                        production,
                        base_index,
                        current_permutation,
                        allow_firstset=False,
                        parent_debug=debug,
                    )),
                    lhs,
                    k
                )
                if debug and self.fo_debug:
                    self.fo_debug.add_result(debug, ret)
                yield ret
            else:
                for i in range(k - sum(current_permutation) + 1):
                    queue.append(current_permutation + (i,))

    def _kfollow(self, symbol, k: int, parent_debug: Optional[str] = None) -> Iterable[FollowSet]:
        debug = None
        if self.fo_debug and parent_debug:
            debug = self.fo_debug.add_call([symbol, k], dict(), ['_kfollow'])
            self.fo_debug.add_child(parent_debug, debug)

        G = Grammar(self.table)
        for lhs, rhs in G:
            for i in [i for i, s in enumerate(rhs) if s == symbol]:
                yield from self._kfollow_permutations(
                    (lhs, list(rhs)), i + 1, k, parent_debug=debug
                )

    def _kfollow_fixpoint_solution(self,
                                   followset_lookup: Dict[str, List[FollowSet]],
                                   parent_debug: Optional[str] = None,
                                   ) -> Dict[str, List[FollowSet]]:
        """Resolve partial followsets into complete followsets.

        Args:
            followsets: A dictionary containing the non-terminal symbols
                and their complete/partial followsets.  Assumes that all
                non-terminal symbols present are keys in this dictionary,
                and that all followsets have the same k value.

        Returns:
            The dict of followsets, but completed.

        """
        debug = None
        if self.fo_debug and parent_debug:
            debug = self.fo_debug.add_call(
                [followset_lookup],
                dict(),
                ['_kfollow_fixpoint_solution']
            )
            self.fo_debug.add_child(parent_debug, debug)

        iteration_guard = 500
        changed = True
        while changed:
            changed = False

            if not iteration_guard:
                raise Exception(
                    'Reached iteration limit during fixpoint solution.'
                )
            iteration_guard -= 1

            for followsets in followset_lookup.values():
                for followset in followsets:
                    followset.changed = False
                    if followset.is_complete:
                        continue
                    for other in followset_lookup[followset.follow]:
                        followset.append(other)
                changed |= any([x.changed for x in followsets])

        if debug and self.fo_debug:
            self.fo_debug.add_result(debug, followset_lookup)

        return followset_lookup

    def kfollow(self,
                k: int
                ) -> Dict[str, Set[Union[str, Tuple[str, ...]]]]:
        # Track debugging information.
        debug = None
        if self.fo_debug:
            debug = self.fo_debug.add_call([k], dict(), ['kfollow'])

        F = {x: [] for x, _ in self.table}  # type: Dict[str, List[FollowSet]]
        initial_start = FollowSet.complete(
            [SubProduction(['$'])],
            self.start,
            1
        )
        F[self.start].append(initial_start)
        for i in range(1, k + 1):
            for symbol in F.keys():
                for followset in self._kfollow(symbol, i, parent_debug=debug):
                    F[symbol].append(followset)
            F = self._kfollow_fixpoint_solution(F, parent_debug=debug)
        ret = defaultdict(lambda: set())  # type: Dict[str, Set[Union[str, Tuple[str, ...]]]]  # noqa: E501
        for symbol, followsets in F.items():
            for follow in {followset.follow for followset in followsets}:
                # TODO: This could probably be improved, performance-wise.
                followset = reduce(
                    FollowSet.upgrade,
                    [
                        followset
                        for followset in followsets
                        if followset.follow == follow
                    ]
                )
                for subproduction in (
                    followset.additional | set(followset.completes)
                ):
                    if len(subproduction) == 1:
                        item = subproduction[0]
                        assert isinstance(item, str)
                        ret[symbol].add(item)
                    else:
                        ret[symbol].add(tuple(subproduction))

        if debug and self.fo_debug:
            self.fo_debug.add_result(debug, ret)

        return dict(ret)

    def follow(self, first: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """Calculate the follow set for generating an LL(1) table.

        Args:
            first: The previously calculated first-set.

        Returns:
            A mapping from non-terminal productions to the first
            terminals which can follows them.

        """
        return {
            key: {x for x in value if isinstance(x, str)}
            for key, value in self.kfollow(1).items()
        }

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
