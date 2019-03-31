import re
from typing import (
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


def exists(it: Iterator) -> bool:
    try:
        next(it)
    except StopIteration:
        return False
    return True


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
                NodeType.SEQUENCE,
                children=old_children,
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
        for production in productions:
            self._break_sequences_up(tree, production)

    def translate(self, tree: Node):
        self._reassign_start(tree)
        self._reassign_nonsolitary_terminals(tree)
        self._eliminate_rhs_with_3plus_symbols(tree)
        return tree
