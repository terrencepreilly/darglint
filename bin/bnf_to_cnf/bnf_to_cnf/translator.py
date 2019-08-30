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
    Optional,
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
from .functools import (
    exists,
    and_,
    or_,
)


END_DIGIT = re.compile(r'\d+$')


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

    def _reassign_start(self, tree: Node, start_symbol: Optional[Node]):
        """Factor out the start symbol from the RHS.

        If start is annotated, that annotation moves to the new start.

        Args:
            tree: The tree to transform.
            start_symbol: The start symbol, if there is one.

        """
        if not start_symbol:
            return
        start_value = start_symbol.value

        def is_start_node(x):
            return (
                x.node_type == NodeType.SYMBOL
                and x.value.startswith(start_value)
            )

        def is_start_production(x):
            return (
                x.node_type == NodeType.PRODUCTION
                and exists(x.filter(Node.has_value(start_value)))
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
        while f'{start_value}{start_suffix}' in start_versions:
            start_suffix += 1

        # Rename the "start" symbol on the LHS.
        annotations = list()  # type: List[Node]
        for production in tree.filter(is_start_production):
            if Node.has_annotation(production):
                parent = production.children.pop(0)
                annotations.extend(parent.children)
            symbol = production.children[0]
            symbol.value = f'{start_value}{start_suffix}'

        # Rename the "start" symbols on the RHS.
        for seq in tree.filter(lambda x: x.node_type == NodeType.SEQUENCE):
            for symbol in seq.filter(is_start_node):
                symbol.value = f'{start_value}{start_suffix}'

        new_production = Parser().parse_production(
            f'<{start_value}> ::= <{start_value}{start_suffix}>'
        )
        if annotations:
            new_production.prepend(Node(
                node_type=NodeType.ANNOTATIONS,
                children=annotations,
            ))
        tree.prepend(new_production)

    def _reassign_nonsolitary_terminals(self, tree: Node):
        def contains_nonsolitary_terminal(x):
            return (
                Node.is_sequence(x)
                and exists(x.filter(Node.is_symbol))
                and exists(x.filter(Node.is_terminal))
            )

        def defines_terminal(x):
            if not Node.is_production(x):
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
            for terminal in sequence.filter(Node.is_terminal):
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
        has_annotation = (
            len(production.children) > 0
            and Node.is_annotations(production.children[0])
        )
        assert (
            (has_annotation and production.children[1].value is not None)
            or production.children[0].value is not None
        )
        assert Node.is_production(production)
        if has_annotation:
            symbol = production.children[1]
        else:
            symbol = production.children[0]
        name, i = self._get_name_end_digit(symbol.value)
        for sequence in production.filter(Node.is_sequence):
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
        productions = list(tree.filter(Node.is_production))
        for i, production in enumerate(productions):
            self._break_sequences_up(tree, production)

    def _prune(self, tree: Node):
        def _sequence_is_empty(x: Node) -> bool:
            return Node.is_sequence(x) and not x.children

        def _expression_is_empty(x: Node) -> bool:
            return Node.is_expression(x) and not x.children

        def _production_is_empty(x: Node) -> bool:
            return (
                Node.is_production(x)
                and all([
                    _expression_is_empty(expression)
                    for expression in x.filter(Node.is_expression)
                ])
            )

        # This could be far more efficient by doing a BFS,
        # and only iterating over the children.
        tree.remove(_sequence_is_empty)
        tree.remove(_production_is_empty)

    def _get_symbol_production_lookup(self,
                                      tree: Node
                                      ) -> Dict[str, List[Node]]:
        lookup = dict()  # type: Dict[str, List[Node]]
        for production in tree.filter(Node.is_production):
            for symbol in production.filter(Node.is_symbol):
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

            # FIXME This results in a never-ending list if
            # a symbol is self-referencing with optional symbol.
            # That is, if there are two productions,
            #
            #    <A> ::= <B> <A> | ε
            #    <B> ::= "b" | ε

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

        for production in tree.filter(and_(
            Node.is_production, is_epsilon_rule
        )):
            updated = True

            # Remove the epsilon sequence
            production.children[1].remove(and_(
                Node.is_sequence, is_epsilon_rule
            ))

            # Register to replace the symbol, or remove the production
            # entirely. (It is either empty, or represents optional values.)
            symbol = production.children[0].value
            assert symbol is not None
            has_nonempty_expression = production.children[1].children
            if has_nonempty_expression:
                replacement_candidates.add(symbol)
            else:
                # TODO: Remove symbol from all sequences?
                tree.remove(and_(
                    Node.is_production,
                    lambda x: x.children[0].value == symbol
                ))

        production_lookup = self._get_symbol_production_lookup(tree)

        # Add each permutation of the symbol's presence. (For each
        # occurrence, it could be present, or it could be absent.)
        for symbol in replacement_candidates:
            for production in production_lookup[symbol]:
                for sequence in production.filter(and_(
                    Node.is_sequence, Node.has_symbol(symbol)
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
            (node.children[1].value or ''
             if Node.has_annotation(node)
             else node.children[0].value or ''): node
            for node in tree.filter(Node.is_production)
        }

    def _eliminate_unit_productions(self, tree: Node):
        r"""Remove all unit productions from the tree.

        A unit production is a production matching

            A -> B

        Where B is a non-terminal.  This algorithm performs a
        post-order traversal of the grammar (as a graph), and each
        B in the above unit production with the non-unit products of
        B.

        The algorithm is a little complicated, so it's summarized below.
        In this pseudocode, we have elements following

            G = { p₁, p₂, ..., pₙ }
            pᵢ = [ "lhs" ⇸ sᵢ, "rhs" ⇸ { s₁, s₂, ..., sₘ } ]
            sᵢ ∈ { 〈sⱼ 〉, 〈sⱼ, sₛ〉, v }
                where
                    |v| = 0.

        where G is a grammar, p is a production, s is a sequence, and
        v is a value.

            Algorithm UnitRemoval(G)
                U ← { p ∈ G : is_unit(p) }
                φ ← [ p.lhs ∈ G ⇸ p ]

                Procedure Simplify(p)
                    // Does a Post-Order Traversal of U (LRN)
                    if p ∉ U then return
                    U ← U \ { p }
                    R ← { s ∈ p.rhs : |s| = 1 }
                    p.rhs ← p.rhs \ R
                    for s ∈ R do
                        Simplify(φ(s))
                        for z ∈ φ(s).rhs do
                            p.rhs ← p.rhs ∪ { z }

                while |U| > 0 do
                    let p ∈ U
                    Simplify(p.lhs)

        """
        def is_unit_sequence(x: Node) -> bool:
            if Node.has_annotation(x):
                return (
                    Node.is_sequence(x)
                    and len(x.children) == 2
                    and x.children[1].node_type == NodeType.SYMBOL
                )
            else:
                return (
                    Node.is_sequence(x)
                    and len(x.children) == 1
                    and x.children[0].node_type == NodeType.SYMBOL
                )

        def is_unit_production(x: Node) -> bool:
            return (
                Node.is_production(x)
                and len(x.children) > 1
                and exists(x.filter(is_unit_sequence))
            )

        # A Lookup from symbols to productions.
        lookup = {
            Node.get_symbol(production).value: production
            for production in tree.filter(Node.is_production)
        }
        unit_productions = set(tree.filter(is_unit_production))

        def simplify(production):
            if production not in unit_productions:
                return
            unit_productions.remove(production)
            unit_sequences = list(production.filter(is_unit_sequence))
            production.remove(is_unit_sequence)
            for unit_sequence in unit_sequences:
                if Node.is_annotations(unit_sequence.children[0]):
                    probability = unit_sequence.probability
                    annotations = unit_sequence.children[0]
                    symbol = unit_sequence.children[1].value
                else:
                    probability = unit_sequence.probability
                    annotations = None
                    symbol = unit_sequence.children[0].value
                simplify(lookup[symbol])
                for sequence in lookup[symbol].filter(Node.is_sequence):
                    expression = next(production.filter(Node.is_expression))
                    if not Node.has_sequence(expression, sequence):
                        cloned = sequence.clone()
                        cloned.probability = probability or cloned.probability
                        if annotations:
                            cloned.merge_annotations(annotations)
                        expression.children.append(cloned)

        while unit_productions:
            head = list(unit_productions)[0]
            simplify(head)

    def _build_adjacency_matrix(self, tree: Node) -> Dict[str, Set[str]]:
        """Return a graph of the grammar being represented.

        Args:
            tree: The tree representing the BNF of the grammar.

        Returns:
            A graph of the grammar represented in the BNF.

        """
        graph = dict()  # type: Dict[str, Set[str]]
        for production in tree.filter(Node.is_production):
            has_annotations = Node.is_annotations(production.children[0])
            if has_annotations:
                symbol = production.children[1].value
            else:
                symbol = production.children[0].value
            assert symbol is not None
            if symbol not in graph:
                graph[symbol] = set()

            expression = next(production.filter(Node.is_expression))
            for child in expression.filter(
                or_(Node.is_symbol, Node.is_terminal)
            ):
                assert child.value is not None
                graph[symbol].add(child.value)

        return graph

    def _remove_unused_productions(self,
                                   tree: Node,
                                   start_symbol: Optional[Node]
                                   ):
        # Only simplify if the starting symbol is present,
        # since other grammars will not be used except for
        # experimenting, anyway.
        if not start_symbol:
            return

        graph = self._build_adjacency_matrix(tree)

        # Walk the tree, from start, and mark all encountered nodes.
        encountered = set()  # type: Set[str]
        assert start_symbol.value
        queue = deque([start_symbol.value])
        while queue:
            current = queue.pop()
            encountered.add(current)
            is_terminal = current not in graph
            if is_terminal:
                continue
            for child in graph[current]:
                # Ignore children we've already processed, preventing cycles.
                if child not in encountered:
                    queue.appendleft(child)

        # Remove all non-encountered nodes.
        to_remove = set(graph.keys()) - encountered
        for production_symbol in to_remove:
            tree.remove(Node._production_with_lhs(production_symbol))

    def _remove_remaining_imports(self, tree: Node):
        assert tree.node_type == NodeType.GRAMMAR
        tree.remove(Node.is_imports)

    def _remove_start_symbol(self, tree: Node) -> Optional[Node]:
        symbols = list(tree.filter(Node.is_start))
        assert len(symbols) <= 1, 'There should only be one start.'
        if len(symbols) == 0:
            return None
        else:
            start_symbol = symbols[0]
            tree.remove(Node.is_start)
            return start_symbol

    def _add_in_start_symbol(self, tree: Node, start_symbol: Optional[Node]):
        if start_symbol:
            tree.children.insert(0, start_symbol)

    def _remove_non_fruitful_branches(self, tree: Node,
                                      start_symbol: Optional[Node]):
        # This is very inefficient, but seems to work well enough
        # in practice.  Ideally, this would be O(n) or something.
        if not start_symbol:
            return

        graph = self._build_adjacency_matrix(tree)

        def _dfs(node, encountered=set()):
            for child in graph.get(node, []):
                if child in encountered:
                    continue
                yield from _dfs(child, encountered | {node, child})
            yield node

        terminals = {x.value for x in tree.filter(Node.is_terminal)}

        def is_fruitful(node):
            if node in terminals:
                return True
            for child in _dfs(node):
                if child in terminals:
                    return True
            return False

        changed = True
        while changed:
            nonfruitful = set()
            for symbol in tree.filter(Node.is_symbol):
                if symbol and not is_fruitful(symbol.value):
                    nonfruitful.add(symbol.value)

            if not nonfruitful:
                break

            changed = False
            # Remove all sequences where the children are nonfruitful.
            changed |= tree.remove(lambda x: Node.is_sequence(x) and all([
                y.value in nonfruitful for y in x.filter(Node.is_symbol)]))

            # Remove all empty productions.
            changed |= tree.remove(
                lambda x: Node.is_production(x) and not (list(
                    x.filter(Node.is_sequence)) or list(
                        x.filter(Node.is_terminal))))

    def translate(self, tree: Node) -> Node:
        start_symbol = self._remove_start_symbol(tree)
        self._remove_remaining_imports(tree)
        self._reassign_start(tree, start_symbol)
        if start_symbol:
            tree.prepend(start_symbol)
        self._reassign_nonsolitary_terminals(tree)
        self._eliminate_rhs_with_3plus_symbols(tree)

        # Repeat the process until all epsilons are gone.
        max_iterations = 100
        while max_iterations and self._eliminate_epsilon_productions(tree):
            max_iterations -= 1

        if max_iterations == 0:
            raise Exception('Reached maximum epsilon expansion.')

        self._eliminate_unit_productions(tree)
        self._remove_unused_productions(tree, start_symbol)

        # TODO: remove nodes which don't lead to terminals?
        self._remove_non_fruitful_branches(tree, start_symbol)

        return tree
