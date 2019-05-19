from collections import (
    deque,
)
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Union,
)

from lark import (
    Tree,
    Token,
)

from .functools import (
    exists,
)


class NodeType(Enum):

    GRAMMAR = 0
    PRODUCTION = 1
    SYMBOL = 2
    EXPRESSION = 3
    SEQUENCE = 4
    TERMINAL = 5

    ANNOTATIONS = 6
    ANNOTATION = 7


TERMINAL_NODES = {
    NodeType.TERMINAL,
    NodeType.SYMBOL,
    NodeType.ANNOTATION,
}
NONTERMINAL_NODES = {
    NodeType.GRAMMAR,
    NodeType.PRODUCTION,
    NodeType.EXPRESSION,
    NodeType.SEQUENCE,
    NodeType.ANNOTATIONS,
}


class Node(object):

    def __init__(self,
                 node_type: NodeType,
                 value: Optional[str] = None,
                 children: List['Node'] = list()):
        self.node_type = node_type
        self.value = value
        self.children = children
        self.cached_symbols = set()  # type: Set[str]

    def __str__(self):
        if self.node_type == NodeType.GRAMMAR:
            return '\n'.join([str(child) for child in self.children])
        elif self.node_type == NodeType.PRODUCTION:
            if len(self.children) == 2:
                return f'{self.children[0]} ::= {self.children[1]}'
            elif len(self.children) == 3:
                return (
                    f'{self.children[0]}\n'
                    f'{self.children[1]} ::= {self.children[2]}'
                )
        elif self.node_type == NodeType.SYMBOL:
            return f'<{self.value}>'
        elif self.node_type == NodeType.EXPRESSION:
            return ' | '.join(map(str, self.children))
        elif self.node_type == NodeType.SEQUENCE:
            return ' '.join(map(str, self.children))
        elif self.node_type == NodeType.TERMINAL:
            return self.value
        elif self.node_type == NodeType.ANNOTATION:
            return f'@{self.value}'
        elif self.node_type == NodeType.ANNOTATIONS:
            return '\n'.join([str(child) for child in self.children])
        else:
            raise Exception(f'Unrecognized node type {self.node_type}')

    def __repr__(self, indent: int = 0):
        r = '  ' * indent + str(self.node_type)[len('NodeType.'):] + ':'
        if self.children:
            for child in self.children:
                r += '\n' + child.__repr__(indent + 1)
        else:
            r += ' ' + (self.value or 'ø')
        return r

    def _bfs(self) -> Iterator['Node']:
        queue = deque([self])
        while queue:
            current = queue.pop()
            for child in current.children:
                queue.appendleft(child)
            yield current

    def defines(self, value: Any) -> bool:
        """Return whether this grammar defines the given symbol.

        Args:
            value: The value of the symbol we're looking for.

        Return:
            Whether the grammar contains the symbol's definition.

        """
        assert self.node_type == NodeType.GRAMMAR
        if self.cached_symbols:
            return value in self.cached_symbols

        for production in self.filter(
            lambda x: x.node_type == NodeType.PRODUCTION
        ):
            assert (
                production.children[1].value
                if Node.has_annotation(production)
                else production.children[0].value
            ), 'The productions must have a symbol value.'
            symbol = production.children[0].value
            self.cached_symbols.add(symbol or '')

        return value in self.cached_symbols

    def equals(self, other: Any) -> bool:
        if type(other) != type(self):
            return False
        if self.node_type != other.node_type:
            return False
        if self.node_type in TERMINAL_NODES:
            return self.value == other.value
        elif self.node_type in NONTERMINAL_NODES:
            return all([
                x.equals(y)
                for x, y in zip(self.children, other.children)
            ])
        else:
            raise Exception('Unrecognized node type.')

    def filter(self, filt: Callable[['Node'], bool]) -> Iterator['Node']:
        for node in self._bfs():
            if filt(node):
                yield node

    def remove(self, filt: Callable[['Node'], bool]):
        parents_to_children = dict()  # type: Dict['Node', List['Node']]
        for parent in self._bfs():
            for child in parent.children:
                if filt(child):
                    if parent not in parents_to_children:
                        parents_to_children[parent] = list()
                    parents_to_children[parent].append(child)

        # Since dicts are ordered in Python3.7, and since this was
        # a BFS, we can go through in reverse order and remove nodes.
        # We won't get a null reference in this way.
        parents = list(parents_to_children.keys())
        parents.reverse()
        for parent in parents:
            for child in parents_to_children[parent]:
                parent.children.remove(child)

    @classmethod
    def from_lark_tree(self, tree: Union[Tree, Token]) -> 'Node':
        if isinstance(tree, Token):
            return Node(
                NodeType.TERMINAL,
                value=tree.value,
            )

        assert isinstance(tree, Tree)
        if tree.data == 'start':
            return Node.from_lark_tree(tree.children[0])
        elif tree.data == 'grammar':
            return Node(
                NodeType.GRAMMAR,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'production':
            return Node(
                NodeType.PRODUCTION,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'symbol':
            return Node(
                NodeType.SYMBOL,
                value=tree.children[0].value,
            )
        elif tree.data == 'expression':
            return Node(
                NodeType.EXPRESSION,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'sequence':
            return Node(
                NodeType.SEQUENCE,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'annotations':
            return Node(
                NodeType.ANNOTATIONS,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'annotation':
            return Node(
                NodeType.ANNOTATION,
                value=tree.children[0].value,
            )
        else:
            raise Exception(
                f'Unrecognized Lark type "{tree.data}".  Check grammar.'
            )

    def _invalidate_cache(self):
        self.cached_symbols = set()

    def append(self, node: 'Node'):
        self._invalidate_cache()
        self.children.append(node)

    def prepend(self, node: 'Node'):
        self._invalidate_cache()
        self.children.insert(0, node)

    def clone(self) -> 'Node':
        return Node(
            node_type=self.node_type,
            children=[child.clone() for child in self.children],
            value=self.value,
        )

    def to_python(self) -> str:
        if self.node_type == NodeType.TERMINAL:
            # Terminals are encoded as token types, so
            # they should not be quoted.
            assert self.value is not None
            return self.value[1:-1].replace('\\', '')
        elif self.node_type == NodeType.SYMBOL:
            assert self.value is not None
            return f'"{self.value}"'
        elif self.node_type == NodeType.SEQUENCE:
            if len(self.children) == 1:
                return self.children[0].to_python()
            elif len(self.children) == 2:
                return (
                    f'({self.children[0].to_python()}, '
                    f'{self.children[1].to_python()})'
                )
            else:
                raise Exception(
                    f'Expected the sequence "{self}" to have one or '
                    f'two children, but it had {len(self.children)}'
                )
        elif self.node_type == NodeType.EXPRESSION:
            return ', '.join([x.to_python() for x in self.children])
        elif self.node_type == NodeType.PRODUCTION:
            symbol = self.children[0].to_python()
            expression = self.children[1].to_python()
            return ' ' * 8 + f'P({symbol}, {expression}),'
        elif self.node_type == NodeType.GRAMMAR:
            import datetime
            comment = (
                f'# Generated on {datetime.datetime.now()}'
            )
            values = [
                comment,
                'class Grammar(BaseGrammar):',
                '    productions = [',
            ]
            for production in self.children:
                values.append(production.to_python())
            values.append('    ]')
            values.extend(['', '    start = "start"'])
            return '\n'.join(values)
        else:
            raise Exception(f'Unrecognized node type, {self.node_type}')

    @staticmethod
    def is_symbol(x: 'Node') -> bool:
        return x.node_type == NodeType.SYMBOL

    @staticmethod
    def is_terminal(x: 'Node') -> bool:
        return x.node_type == NodeType.TERMINAL

    @staticmethod
    def is_production(x: 'Node') -> bool:
        return x.node_type == NodeType.PRODUCTION

    @staticmethod
    def is_sequence(x: 'Node') -> bool:
        return x.node_type == NodeType.SEQUENCE

    @staticmethod
    def is_expression(x: 'Node') -> bool:
        return x.node_type == NodeType.EXPRESSION

    @staticmethod
    def is_annotation(x: 'Node') -> bool:
        return x.node_type == NodeType.ANNOTATION

    @staticmethod
    def is_annotations(x: 'Node') -> bool:
        return x.node_type == NodeType.ANNOTATIONS

    @staticmethod
    def has_symbol(x: str) -> Callable[['Node'], bool]:
        def _inner(y: Node) -> bool:
            return exists(
                y.filter(lambda z: Node.is_symbol(z) and z.value == x)
            )
        return _inner

    @staticmethod
    def has_value(x: str) -> Callable[['Node'], bool]:
        def _inner(y: Node) -> bool:
            return hasattr(y, 'value') and y.value == x
        return _inner

    @staticmethod
    def _production_with_lhs(symbol: str) -> Callable[['Node'], bool]:
        def _inner(x: Node) -> bool:
            if not Node.is_production(x):
                return False
            if not x.children or not Node.is_symbol(x.children[0]):
                return False
            return x.children[0].value == symbol
        return _inner

    @staticmethod
    def has_annotation(node: 'Node') -> bool:
        return exists(node.filter(Node.is_annotations))

    # Production-specific functions
    @staticmethod
    def get_symbol(node: 'Node') -> 'Node':
        assert Node.is_production(node)
        if Node.is_annotations(node.children[0]):
            return node.children[1]
        return node.children[0]

    @staticmethod
    def has_sequence(node: 'Node', sequence: 'Node') -> bool:
        for child in node.filter(Node.is_sequence):
            if child.equals(sequence):
                return True
        return False

    def to_dot(self) -> str:
        """Prints the dot representation of the tree.

        This is primarily meant for debugging.

        Returns:
            The dot representation of the tree.

        """
        name_lookup = dict()  # type: Dict['Node', str]
        names = set()  # type: Set[str]
        def _node_name(node: 'Node') -> str:
            if node in name_lookup:
                return name_lookup[node]
            elif node.node_type in TERMINAL_NODES:
                name = node.value.replace(
                    '"', 'Q',
                ).replace(
                    '\\', 'B',
                ).replace(
                    '@', 'At',
                )
                i = 0
                while name + str(i) in names:
                    i += 1
                name = name + str(i)
                names.add(name)
                name_lookup[node] = name
                return name
            elif node.node_type in NONTERMINAL_NODES:
                name = str(node.node_type).replace('.', '_')
                i = 0
                while name + str(i) in names:
                    i += 1
                name = name + str(i)
                names.add(name)
                name_lookup[node] = name
                return name
            else:
                raise Exception(
                    f'Unrecognized node type {node.node_type}'
                )

        def _node_label(node: 'Node') -> str:
            if node.node_type in TERMINAL_NODES:
                assert node.value is not None
                return node.value.replace('"', '\\"')
            elif Node.is_expression(node):
                return ''
            else:
                return _node_name(node)

        def _node_shape(node: 'Node') -> str:
            if Node.is_annotation(node):
                return 'diamond'
            elif node.node_type in TERMINAL_NODES:
                return 'rectangle'
            else:
                return 'oval'

        lines = ['digraph G {']

        # Iterate through all the children to create the
        # definitions.
        for node in self._bfs():
            name = _node_name(node)
            label = _node_label(node)
            shape = _node_shape(node)
            lines.append(f'{name} [label="{label}", shape="{shape}"];')

        # Iterate through all the children to create the
        # relationships between nodes.
        for node in self._bfs():
            if node.node_type in TERMINAL_NODES:
                continue
            name = _node_name(node)
            for child in node.children:
                child_name = _node_name(child)
                lines.append(f'{name} -> {child_name};')

        lines.append('}')
        return '\n'.join(lines)
