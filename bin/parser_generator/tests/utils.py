from collections import (
    deque,
)
from dataclasses import (
    dataclass,
    field,
)
from random import (
    paretovariate,
    randint,
    choice,
    random,
)
import string
from typing import (
    Iterable,
    Iterator,
    Callable,
    Optional,
    List,
    Set,
    Tuple,
    TypeVar,
    Generic,
)
from parser_generator.generators import (
    Grammar,
    is_term,
)


def is_epsilon(symbol: str) -> bool:
    return symbol == 'ε'


def is_nonterm(symbol: str) -> bool:
    return not (is_term(symbol) or is_epsilon(symbol))


T = TypeVar('T')


def count(test: Callable[[T], bool], items: Iterable[T]) -> int:
    total = 0
    for item in items:
        if test(item):
            total += 1
    return total


def rfind(test: Callable[[T], bool], items: List[T]) -> Optional[int]:
    if not items:
        return
    i = len(items) - 1
    while i >= 0:
        if test(items[i]):
            return i
        i -= 1


@dataclass
class Sequence(Generic[T]):

    start: Optional[int] = None
    end: Optional[int] = None
    sequence: List[T] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.start is not None and bool(self.sequence)

    def __len__(self) -> int:
        return len(self.sequence)


def longest_sequence(test: Callable[[T], bool],
                     items: List[T],
                     index: int = 0) -> Sequence[T]:
    seq = list()
    i = index

    # Move the pointer to the first passing item.
    while i < len(items) and not test(items[i]):
        i += 1

    if i == len(items):
        return Sequence()
    start = i

    # Move the pointer forward while it passes.
    while i < len(items) and test(items[i]):
        seq.append(items[i])
        i += 1

    return Sequence(start=start, end=i, sequence=seq)


class FollowSetGenerator:
    """Generates k-follow strings from a grammar.

    Given a grammar G, which accepts languages L, and
    given a production P -> R, this class does a random
    search for strings of length k which occur in L, immediately
    following strings produced by P.

    For example, if we have the grammar

        S -> A B
        A -> a S
           | B
        B -> b
           | c A

    Then some of the k = 1 items returned from this generator
    would include

        ('A', ['b'])
        ('B', ['b'])
        ('A', ['c'])

    In any particular order.  Some k = 2 items would include

        ('A', ['b', 'b'])
        ('A', ['b', 'c'])
        ('A', ['c', 'a'])

    """

    def __init__(self, grammar: Grammar, start_symbol: str, k: int):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.encountered = set()  # type: Set[Tuple[str, Tuple[str, ...]]]
        self._language = []
        self._new_language_count = dict()  # type: Dict[str, int]
        self._new_language()
        self.k = k
        self.final_guard = 200

    def _new_language(self):
        old_language = ''.join(self._language)
        if old_language not in self._new_language_count:
            self._new_language_count[old_language] = 0
        self._new_language_count[old_language] += 1
        # The maximum number of steps for generating this language.
        self._length = randint(1, 2000)
        self._count = 0
        self._language = [self.start_symbol]  # type: List[str]
        self._next_queue = []  # type: List[Tuple[str, Tuple[str, ...]]]

    def __iter__(self) -> Iterator[Tuple[str, Tuple[str, ...]]]:
        return self

    def __next__(self) -> Tuple[str, Tuple[str, ...]]:
        while not self._next_queue:
            self.final_guard -= 1
            if not self.final_guard:
                raise StopIteration
            self._step()
            if any([x > 5 for x in self._new_language_count.values()]):
                raise StopIteration
        return self._next_queue.pop()

    def _step(self):
        if self._count >= self._length:
            self._new_language()

        nonterm_indices = {
            index: nonterm
            for index, nonterm in enumerate(self._language)
            if is_nonterm(nonterm)
        }
        if not nonterm_indices:
            self._new_language()
            return

        nonterm_index = choice(list(nonterm_indices.keys()))
        nonterm = nonterm_indices[nonterm_index]
        productions = self.grammar[nonterm]
        assert isinstance(productions, list)
        # If it's pointing at nothing ...
        if not productions:
            return

        production = choice(productions)
        self._language = (
            self._language[:nonterm_index] +
            list(production) +
            self._language[nonterm_index + 1:]
        )

        # Find any new followsets produced.
        index = rfind(is_nonterm, self._language[:nonterm_index])
        under_consideration = self._language[index:nonterm_index + len(production)]
        if index:
            sequence = longest_sequence(is_term, under_consideration, index)
            loop_guard = 1000
            while sequence:
                loop_guard -= 1
                if not loop_guard:
                    raise Exception('Failed loop guard.')
                if len(sequence) >= self.k:
                    self._next_queue.append(
                        (self._language[index], sequence.sequence[:self.k])
                    )
                index = sequence.end
                sequence = longest_sequence(is_term, under_consideration, index)


class GrammarGenerator:
    """A generator of grammars, for fuzzing."""

    def __init__(self):
        # An ordered set of symbols.
        self.symbols = list()
        self.terminals = set()

    def generate_symbols(self) -> Iterable[str]:
        while True:
            next_symbol = ''
            while next_symbol == '' or next_symbol in self.symbols:
                # Choose the next symbol at random, prefering smaller symbols
                # to large ones.
                next_symbol = ''.join([
                    choice(string.ascii_uppercase)
                    for _ in range(min(5, round(paretovariate(1))))
                ])
            self.symbols.append(next_symbol)
            yield next_symbol

    def generate_terminal(self):
        while True:
            next_term = ''
            while next_term == '' or next_term in self.terminals:
                next_term = '"' + ''.join([
                    choice(string.ascii_lowercase)
                    for _ in range(randint(1, 10))
                ]) + '"'
            self.terminals.add(next_term)
            yield next_term

    def generate_rhs(self):
        if len(self.symbols) > 1 and random() < 0.1:
            yield choice(self.symbols)
        else:
            yield next(self.generate_symbols())

    def generate_lhs(self, exclude=None):
        lhs = list()
        for _ in range(min(4, round(paretovariate(1)))):
            if len(self.symbols) > 1 and random() < 0.5:
                next_symbol = choice(self.symbols)
                while exclude and next_symbol == exclude:
                    next_symbol = choice(self.symbols)
                lhs.append(next_symbol)
            elif self.terminals and random() < 0.5:
                lhs.append(choice(list(self.terminals)))
            else:
                lhs.append(next(self.generate_terminal()))
        yield lhs

    def generate_productions(self):
        while True:
            yield (next(self.generate_rhs()), next(self.generate_lhs()))

    def get_depth(self, adjacency_graph, root):
        visited = set()
        stack = deque([(root, 1)])
        max_depth = 0
        while stack:
            curr, curr_depth = stack.pop()
            visited.add(curr)
            max_depth = max(max_depth, curr_depth)
            for child in adjacency_graph.get(curr, []):
                if child not in visited and not child.startswith('"'):
                    stack.append((child, curr_depth + 1))
        return max_depth

    def to_dot(self, productions):
        ret = ['digraph G {']
        nodes = list()
        nodes_represented = set()
        relations = list()
        for lhs, rhs in productions:
            if lhs not in nodes_represented:
                nodes.append(f'  {lhs} [shape="rect"];')
                nodes_represented.add(lhs)
            for r in rhs:
                if r not in nodes_represented:
                    if r.startswith('"'):
                        nodes.append(f'  term_{r[1:-1]} [label="{r[1:-1]}", shape="oval"];')
                        rnode = f'term_{r[1:-1]}'
                    else:
                        nodes.append(f'  {r} [shape="rect"];')
                        rnode = r
                relations.append(
                    f'  {lhs} -> {rnode};'
                )
        ret = ret + ['\n'] + nodes + ['\n'] + relations + ['}']
        return '\n'.join(ret)


    def generate_ll1_grammar(self):
        # Generate some productions.
        gen = self.generate_productions()
        productions = [next(gen) for _ in range(randint(1, 10))]

        # Build an adjacency graph
        graph = dict()
        for lhs, rhs in productions:
            if lhs not in graph:
                graph[lhs] = set()
            graph[lhs] |= set(rhs)

        # then try three different
        # symbols to find the longest run.
        root = choice(self.symbols)
        max_length = self.get_depth(graph, root)
        for _ in range(3):
            other_root = choice(self.symbols)
            other_max_length = self.get_depth(graph, other_root)
            if other_max_length > max_length:
                root = other_root
                max_length = other_max_length

        def _partition(prods, symbol):
            left, right = list(), list()
            for lhs, rhs in prods:
                if lhs == symbol:
                    left.append((lhs, rhs))
                else:
                    right.append((lhs, rhs))
            return left, right

        # Trim the productions to only those in the tree
        # rooted at root.
        productions, old_productions = list(), productions
        visited = set()
        stack = deque([root])
        leaves = set()
        while stack:
            curr = stack.pop()
            visited.add(curr)
            to_add, old_productions = _partition(old_productions, curr)
            for _, rhs in to_add:
                for symbol in rhs:
                    if not symbol.startswith('"') and symbol not in visited:
                        stack.append(symbol)
            if to_add:
                productions.extend(to_add)
            else:
                leaves.add(curr)

        term_gen = self.generate_terminal()
        for leaf in leaves:
            productions.append((leaf, [next(term_gen)]))

        productions.insert(0, ('start', [root]))
        return productions

    def to_grammar(self, productions):
        ret = list()
        rules = dict()
        for lhs, rhs in productions:
            if lhs == 'start':
                ret.append(f'start: <{rhs[0]}>\n')
                continue

            if lhs not in rules:
                rules[lhs] = list()
            rules[lhs].append(' '.join([
                f'{r}' if r.startswith('"') else f'<{r}>'
                for r in rhs
            ]))
        for rhs in rules:
            for i, lhs in enumerate(rules[rhs]):
                if i == 0:
                    ret.append(f'<{rhs}> ::= {lhs}')
                else:
                    ret.append(f'  | {lhs}')
        return '\n'.join(ret)
