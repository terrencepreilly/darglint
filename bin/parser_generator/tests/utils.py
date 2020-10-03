from collections import (
    deque,
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
)

class GrammarGenerator(object):
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
