from typing import (
    Dict,
    Iterator,
    Set,
)

from .node import (
    Node,
    NodeType,
)


def is_symbol(x: Node) -> bool:
    return x.node_type == NodeType.SYMBOL


def is_terminal(x: Node) -> bool:
    return x.node_type == NodeType.TERMINAL


def exists(it: Iterator) -> bool:
    try:
        next(it)
    except StopIteration:
        return False
    return True


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

        new_production = Node(
            NodeType.PRODUCTION,
            children=[
                Node(
                    NodeType.SYMBOL,
                    value='start',
                ),
                Node(
                    NodeType.EXPRESSION,
                    children=[
                        Node(
                            NodeType.SEQUENCE,
                            children=[
                                Node(
                                    NodeType.SYMBOL,
                                    value=f'start{start_suffix}',
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
        tree.children.insert(0, new_production)

    def _reassign_nonsolitary_terminals(self, tree: Node):
        def contains_nonsolitary_terminal(x):
            return (
                x.node_type == NodeType.SEQUENCE
                and exists(x.find(lambda y: y.node_type == NodeType.SYMBOL))
                and exists(x.find(lambda y: y.node_type == NodeType.TERMINAL))
            )

        def defines_terminal(x):
            if x.node_type != NodeType.PRODUCTION:
                return False

            if len(x.children) < 2:
                return False

            lhs = x.children[0]
            if lhs.node_type != NodeType.SYMBOL:
                return False

            expression = x.chlidren[1]
            return (
                exists(expression.find(
                    lambda y: y.node_type == NodeType.TERMINAL
                ))
                and not exists(expression.find(
                    lambda y: y.node_type == NodeType.SYMBOL
                ))
            )

        # Find non-solitary terminals.
        # See if there is a corresponding lhs.
        # If so, replace with that.
        # Otherwise, create it and replace with that.

    def translate(self, tree: Node):
        self._reassign_start(tree)
        self._reassign_nonsolitary_terminals(tree)
        return tree
