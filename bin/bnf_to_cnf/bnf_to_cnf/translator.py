from collections import (
    defaultdict,
    deque,
)
import re
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Set,
    Tuple,
)

from .parser import (
    Parser,
)
from .node import (
    Node,
    NodeType,
)


END_DIGIT = re.compile(r'\d+$')


def is_symbol(x: Node) -> bool:
    return x.node_type == NodeType.SYMBOL


def is_terminal(x: Node) -> bool:
    return x.node_type == NodeType.TERMINAL


def is_production(x: Node) -> bool:
    return x.node_type == NodeType.PRODUCTION


def is_sequence(x: Node) -> bool:
    return x.node_type == NodeType.SEQUENCE


def is_expression(x: Node) -> bool:
    return x.node_type == NodeType.EXPRESSION


def has_symbol(x: str) -> Callable[['Node'], bool]:
    def _inner(y: Node) -> bool:
        return exists(y.filter(lambda z: is_symbol(z) and z.value == x))
    return _inner


def exists(it: Iterator) -> bool:
    try:
        next(it)
    except StopIteration:
        return False
    return True


def _and(*args: Callable[[Node], bool]) -> Callable[[Node], bool]:
    def _inner(x: Node) -> bool:
        for fn in args:
            if not fn(x):
                return False
        return True
    return _inner


def _or(*args: Callable[[Node], bool]) -> Callable[[Node], bool]:
    def _inner(x: Node) -> bool:
        for fn in args:
            if fn(x):
                return True
        return False
    return _inner


def _not(fn: Callable[[Node], bool]) -> Callable[[Node], bool]:
    def _inner(x: Node) -> bool:
        return not fn(x)
    return _inner


def to_symbol(value: str, count: int = None) -> str:
    """Given a terminal value, produce an adquate symbol.

    Args:
        value: The value of the terminal.
        count: A number to append to the terminal symbol name,
            if non-null, otherwise nothing is added to the name.

    Returns:
        An adequate symbol name.

    """
    ret = value
    for not_allowed, allowed in [
        ('\\"', 'Q'),
        ('"', ''),
        ('*', 'A'),
        ('.', 'P'),
        (':', 'C'),
        ('^', 'E'),
        ('(', 'LP'),
        (')', 'RP'),
        ('\\', 'B'),
    ]:
        ret = ret.replace(not_allowed, allowed)
    return ret + (
        str(count) if count is not None
        else ''
    )


class Translator(object):
    """Transforms a BNF tree to CNF."""

    def _reassign_start(self, tree: Node):
        """Factor out the start symbol from the RHS.

        Args:
            tree: The tree to transform.

        """
        def is_start_node(x):
            return (
                x.node_type == NodeType.SYMBOL
                and x.value.startswith('start')
            )

        def is_start_production(x):
            return (
                x.node_type == NodeType.PRODUCTION
                and len(x.children) > 1
                and hasattr(x.children[0], 'value')
                and x.children[0].value == 'start'
            )

        # Gather all the symbols that start with "start",
        # so we can avoid collisions.
        start_versions = set()  # type: Set[str]
        for node in tree.filter(is_start_node):
            assert node.value is not None
            start_versions.add(node.value)

        # There are no "start" symbols at all, so they can't be
        # on the right-hand side to begin with.
        if not start_versions:
            return

        # Do a linear probe.  There won't be more than one or
        # two, if even that.
        start_suffix = 0
        while f'start{start_suffix}' in start_versions:
            start_suffix += 1

        # Rename the "start" symbol on the LHS.
        for production in tree.filter(is_start_production):
            symbol = production.children[0]
            symbol.value = f'start{start_suffix}'

        # Rename the "start" symbols on the RHS.
        for seq in tree.filter(lambda x: x.node_type == NodeType.SEQUENCE):
            for symbol in tree.filter(is_start_node):
                symbol.value = f'start{start_suffix}'

        new_production = Parser().parse_production(
            f'<start> ::= <start{start_suffix}>'
        )
        tree.prepend(new_production)

    def _reassign_nonsolitary_terminals(self, tree: Node):
        def contains_nonsolitary_terminal(x):
            return (
                is_sequence(x)
                and exists(x.filter(is_symbol))
                and exists(x.filter(is_terminal))
            )

        def defines_terminal(x):
            if not is_production(x):
                return False

            if len(x.children) < 2:
                return False

            lhs = x.children[0]
            if lhs.node_type != NodeType.SYMBOL:
                return False

            expression = x.children[1]
            return (
                exists(expression.filter(
                    lambda y: y.node_type == NodeType.TERMINAL
                ))
                and not exists(expression.filter(
                    lambda y: y.node_type == NodeType.SYMBOL
                ))
            )

        terminal_symbol_lookup = {
            x.children[1].value: x.children[0].value
            for x in tree.filter(defines_terminal)
        }

        # Find non-solitary terminals.
        for sequence in tree.filter(contains_nonsolitary_terminal):
            for terminal in sequence.filter(is_terminal):
                replacement = None
                if terminal.value in terminal_symbol_lookup:
                    replacement = terminal_symbol_lookup[terminal.value]
                else:
                    assert terminal.value is not None
                    replacement = to_symbol(terminal.value)
                    i = 0
                    while tree.defines(replacement):
                        replacement = to_symbol(terminal.value, i)
                        i += 1
                    tree.append(
                        Parser().parse_production(
                            f'<{replacement}> ::= {terminal.value}'
                        )
                    )
                terminal.value = replacement
                terminal.node_type = NodeType.SYMBOL

    def _get_name_end_digit(self, value: str) -> Tuple[str, int]:
        instances = END_DIGIT.findall(value)
        if instances:
            end_digit = instances[0]
            name = value[:-1 * len(end_digit)]
            return name, int(instances[0])
        else:
            return value, 0

    def _break_sequences_up(self, grammar: Node, production: Node):
        assert production.children[0].value is not None
        assert is_production(production)
        name, i = self._get_name_end_digit(production.children[0].value)
        for sequence in production.filter(is_sequence):
            if len(sequence.children) <= 2:
                continue
            while grammar.defines(f'{name}{i}'):
                i += 1
            new_children = [
                sequence.children[0],
                Node(
                    NodeType.SYMBOL,
                    value=f'{name}{i}'
                )
            ]
            old_children = sequence.children[1:]
            sequence.children = new_children
            new_sequence = Node(
                NodeType.EXPRESSION,
                children=[
                    Node(
                        NodeType.SEQUENCE,
                        children=old_children,
                    )
                ]
            )
            new_production = Node(
                NodeType.PRODUCTION,
                children=[
                    Node(
                        NodeType.SYMBOL,
                        value=f'{name}{i}'
                    ),
                    new_sequence
                ]
            )
            grammar.append(new_production)

            # We call recursively, because there may have been
            # more than three symbols on the RHS.
            self._break_sequences_up(grammar, new_production)

    def _eliminate_rhs_with_3plus_symbols(self, tree: Node):
        # We capture all productions before the transformation:
        # since the breaking up is recursive, we don't have to
        # worry about new productions.
        #
        # Productions which do not have RHSs which are too
        # long won't be affected.
        productions = list(tree.filter(is_production))
        for i, production in enumerate(productions):
            self._break_sequences_up(tree, production)

    def _prune(self, tree: Node):
        def _sequence_is_empty(x: Node) -> bool:
            return is_sequence(x) and not x.children

        def _expression_is_empty(x: Node) -> bool:
            return is_expression(x) and not x.children

        def _production_is_empty(x: Node) -> bool:
            return is_production(x) and _expression_is_empty(x.children[1])

        # This could be far more efficient by doing a BFS,
        # and only iterating over the children.
        tree.remove(_sequence_is_empty)
        tree.remove(_production_is_empty)

    def _get_symbol_production_lookup(self,
                                      tree: Node
                                      ) -> Dict[str, List[Node]]:
        lookup = dict()  # type: Dict[str, List[Node]]
        for production in tree.filter(is_production):
            for symbol in production.filter(is_symbol):
                assert symbol.value is not None
                key = symbol.value
                if key not in lookup:
                    lookup[key] = list()
                lookup[key].append(production)
        return lookup

    def _permute_sequence(self, sequence: Node, symbol: str) -> Iterator[Node]:
        """Yield all sequences resulting from an optional symbol.

        Args:
            sequence: The sequence to mutate.
            symbol: The symbol which may be present, or may not be present.

        Yields:
            All permutations of the symbol being present and absent,
            including the original sequence.

        """
        def from_bitmask(mask: int) -> Node:
            i = len(sequence.children) - 1
            mask_index = 0
            new_sequence = sequence.clone()
            while i >= 0:
                matches = new_sequence.children[i].value == symbol
                if matches:
                    include = (mask >> mask_index) & 1
                    if not include:
                        new_sequence.children.pop(i)
                    mask_index += 1
                i -= 1

            # Re-add an epsilon if it's otherwise empty.
            is_empty = len(new_sequence.children) == 0
            if is_empty:
                new_sequence.children.append(Node(
                    node_type=NodeType.SYMBOL,
                    value='ε',
                ))

            return new_sequence

        occurrences = len([x for x in sequence.children if x.value == symbol])
        for mask in range(2**occurrences - 1):
            yield from_bitmask(mask)

    def _eliminate_epsilon_productions(self, tree: Node) -> bool:
        """Eliminate all current epsilon rules.

        Args:
            tree: The root of the grammar.

        Returns:
            Whether the grammar was updated or not.

        """
        def is_epsilon_rule(x: Node) -> bool:
            return exists(x.filter(lambda y: y.value == 'ε'))

        updated = False

        replacement_candidates = set()  # Set[str]

        for production in tree.filter(_and(is_production, is_epsilon_rule)):
            updated = True

            # Remove the epsilon sequence
            production.children[1].remove(_and(is_sequence, is_epsilon_rule))

            # Register to replace the symbol, or remove the production
            # entirely. (It is either empty, or represents optional values.)
            symbol = production.children[0].value
            assert symbol is not None
            has_nonempty_expression = production.children[1].children
            if has_nonempty_expression:
                replacement_candidates.add(symbol)
            else:
                # TODO: Remove symbol from all sequences?
                tree.remove(_and(
                    is_production, lambda x: x.children[0].value == symbol
                ))

        production_lookup = self._get_symbol_production_lookup(tree)

        # Add each permutation of the symbol's presence. (For each
        # occurrence, it could be present, or it could be absent.)
        for symbol in replacement_candidates:
            for production in production_lookup[symbol]:
                for sequence in production.filter(_and(
                    is_sequence, has_symbol(symbol)
                )):
                    for new_sequence in self._permute_sequence(
                        sequence, symbol
                    ):
                        production.children[1].children.append(new_sequence)

        # Remove any productions which have empty expressions.
        self._prune(tree)

        return updated

    def _expand_reachability(self,
                             graph: Dict[str, Set[str]]
                             ) -> Dict[str, Set[str]]:
        """Get a lookup of nodes to reachable nodes.

        Args:
            graph: A directed graph represented as an adjacency matrix.

        Returns:
            A lookup from node to the reachable set of nodes.

        """
        def _bfs(node: str) -> Set[str]:
            queue = deque([node])
            encountered = set()
            while queue:
                curr = queue.pop()
                encountered.add(curr)
                for child in graph[curr]:
                    if child in encountered:
                        continue
                    queue.appendleft(child)
            return encountered - {node}

        return {
            node: _bfs(node)
            for node in list(graph.keys())
        }

    def _get_definition_lookup(self, tree: Node) -> Dict[str, Node]:
        return {
            node.children[0].value or '': node
            for node in tree.filter(is_production)
        }

    def _eliminate_unit_productions(self, tree: Node):
        def is_unit_sequence(x: Node) -> bool:
            return (
                is_sequence(x)
                and len(x.children) == 1
                and x.children[0].node_type == NodeType.SYMBOL
            )

        # Partition into unit, non-unit productions.
        non_unit_productions = defaultdict(
            lambda: set()
        )  # type: Dict[str, Set[str]]
        for production in tree.filter(is_production):
            for sequence in production.filter(is_unit_sequence):
                production_symbol = production.children[0].value
                assert production_symbol is not None
                sequence_symbol = sequence.children[0].value
                assert sequence_symbol is not None
                non_unit_productions[production_symbol].add(
                    sequence_symbol
                )

        tree.remove(is_unit_sequence)

        # Determine which sequences are reachable from each node.
        reachability_graph = self._expand_reachability(non_unit_productions)
        definition_lookup = self._get_definition_lookup(tree)

        # Appropriate all reachable terminals.
        for symbol, reachables in reachability_graph.items():
            production = definition_lookup[symbol]
            # Sorting the list of reachable productions makes the result
            # deterministic (and so, easier to test.)
            for reachable in sorted(list(reachables)):
                reachable_production = definition_lookup.get(reachable, None)
                if not reachable_production:
                    continue
                for sequence in reachable_production.filter(is_sequence):
                    if not any([
                        x.equals(sequence)
                        for x in production.children[1].children
                    ]):
                        production.children[1].children.append(
                            sequence.clone()
                        )

    def translate(self, tree: Node):
        self._reassign_start(tree)
        self._reassign_nonsolitary_terminals(tree)
        self._eliminate_rhs_with_3plus_symbols(tree)

        # Repeat the process until all epsilons are gone.
        max_iterations = 100
        while max_iterations and self._eliminate_epsilon_productions(tree):
            max_iterations -= 1

        self._eliminate_unit_productions(tree)

        return tree
