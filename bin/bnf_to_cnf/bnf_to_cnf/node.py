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
    IMPORTS = 8
    IMPORT = 9
    NAME = 10
    EXTERNAL_IMPORTS = 12
    EXTERNAL_IMPORT = 13
    SOURCE = 14
    FILENAMES = 15
    FILENAME = 16

    ANNOTATIONS = 6
    ANNOTATION = 7
    START = 11

    # Next: 17


TERMINAL_NODES = {
    NodeType.TERMINAL,
    NodeType.SYMBOL,
    NodeType.ANNOTATION,
    NodeType.START,
    NodeType.SOURCE,
    NodeType.FILENAME,
}
NONTERMINAL_NODES = {
    NodeType.GRAMMAR,
    NodeType.PRODUCTION,
    NodeType.EXPRESSION,
    NodeType.SEQUENCE,
    NodeType.ANNOTATIONS,
    NodeType.EXTERNAL_IMPORTS,
    NodeType.EXTERNAL_IMPORT,
    NodeType.FILENAMES,
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
        elif self.node_type == NodeType.IMPORTS:
            return '\n'.join([str(child) for child in self.children]) + '\n'
        elif self.node_type == NodeType.IMPORT:
            return f'import {self.value}'
        elif self.node_type == NodeType.START:
            return f'start: <{self.value}>'
        elif self.node_type == NodeType.EXTERNAL_IMPORTS:
            return '\n'.join(map(str, self.children)) + '\n'
        elif self.node_type == NodeType.EXTERNAL_IMPORT:
            source = self.children[0].value
            filenames = [x.value for x in self.children[1].children]
            ret = f'from {source} import (\n'
            for filename in filenames:
                ret += f'    {filename},\n'
            ret += ')\n'
            return ret
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
            has_annotation = (
                len(production.children) > 1
                and Node.is_annotations(production.children[1])
            )
            if has_annotation:
                assert production.children[1].value, (
                    'The productions must have a symbol value.'
                )
                symbol = production.children[1].value
            else:
                assert production.children[0].value, (
                    'The productions must have a symbol value.'
                )
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
        elif self.node_type == NodeType.IMPORTS:
            # We ignore imports, since they should have been
            # expanded before translation.
            return True
        else:
            raise Exception(f'Unrecognized node type. {self.node_type}')

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
            # Don't include an import node if there were no
            # imports.  Imports will also be stripped out later.
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
        elif tree.data == 'imports':
            if tree.children:
                return Node(
                    NodeType.IMPORTS,
                    children=list(map(Node.from_lark_tree, tree.children)),
                )
            else:
                return None
        elif tree.data == 'import':
            assert len(tree.children) == 1
            return Node(
                NodeType.IMPORT,
                value=tree.children[0].value.strip(),
            )
        elif tree.data == 'name':
            assert len(tree.children) == 1
            return Node(
                NodeType.NAME,
                value=tree.children[0].value.strip(),
            )
        elif tree.data == 'start_expression':
            assert len(tree.children) == 1
            assert len(tree.children[0].children) == 1
            return Node(
                NodeType.START,
                value=tree.children[0].children[0].value.strip(),
            )
        elif tree.data == 'external_imports':
            return Node(
                NodeType.EXTERNAL_IMPORTS,
                children=list(map(Node.from_lark_tree, tree.children)),
            )
        elif tree.data == 'external_import':
            assert len(tree.children) == 2
            return Node(
                NodeType.EXTERNAL_IMPORT,
                children=[
                    Node(NodeType.SOURCE, tree.children[0].value),
                    Node.from_lark_tree(tree.children[1]),
                ],
            )
        elif tree.data == 'items':
            assert len(tree.children) > 0
            return Node(
                NodeType.FILENAMES,
                children=[
                    Node(NodeType.FILENAME, value=child.value)
                    for child in tree.children
                ]
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
                    f'([], {self.children[0].to_python()}, '
                    f'{self.children[1].to_python()})'
                )
            else:
                return (
                    '('
                    + ', '.join([x.to_python() for x in self.children])
                    + ')'
                )
        elif self.node_type == NodeType.EXPRESSION:
            return ', '.join([x.to_python() for x in self.children])
        elif self.node_type == NodeType.IMPORTS:
            # Ignore imports -- these should be inlined by the
            # translation process.
            return ''
        elif self.node_type == NodeType.NAME:
            # The name is handled below, along with the grammar, to
            # make sure it doesn't get out of order.
            return ''
        elif self.node_type == NodeType.PRODUCTION:
            has_annotation = (
                len(self.children) > 1
                and Node.is_annotations(self.children[0])
            )
            if has_annotation:
                annotation = self.children[0].to_python()
                symbol = self.children[1].to_python()
                expression = self.children[2].to_python()
                return (
                    ' ' * 8
                    + f'P.with_annotations('
                    + f'{annotation}, {symbol}, {expression})'
                )
            else:
                symbol = self.children[0].to_python()
                expression = self.children[1].to_python()
                return ' ' * 8 + f'P({symbol}, {expression}),'
        elif self.node_type == NodeType.ANNOTATIONS:
            return (
                '['
                + ', '.join([n.to_python() for n in self.children])
                + ']'
            )

        elif self.node_type == NodeType.START:
            return ''

        elif self.node_type == NodeType.ANNOTATION:
            assert self.value is not None
            return self.value
        elif self.node_type == NodeType.GRAMMAR:
            import datetime
            comment = (
                f'# Generated on {datetime.datetime.now()}'
            )
            name = 'Grammar'
            for name_node in self.filter(Node.is_name):
                assert name_node.value is not None
                name = name_node.value

            values = [
                comment,
            ]

            for node in self.filter(Node.is_external_imports):
                values.append(node.to_python())

            values.extend([
                f'class {name}(BaseGrammar):',
                '    productions = [',
            ])
            for production in self.filter(Node.is_production):
                values.append(production.to_python())
            values.append('    ]')
            for start_node in self.filter(Node.is_start):
                values.append(f'    start = "{start_node.value}"')
            return '\n'.join(values)
        elif self.node_type == NodeType.EXTERNAL_IMPORTS:
            return '\n'.join([x.to_python() for x in self.children]) + '\n'
        elif self.node_type == NodeType.EXTERNAL_IMPORT:
            source = self.children[0].value
            filenames = [x.value for x in self.children[1].children]
            ret = f'from {source} import (\n'
            for filename in filenames:
                ret += f'    {filename},\n'
            ret += ')\n'
            return ret
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
    def is_imports(x: 'Node') -> bool:
        return x.node_type == NodeType.IMPORTS

    @staticmethod
    def is_import(x: 'Node') -> bool:
        return x.node_type == NodeType.IMPORT

    @staticmethod
    def is_name(x: 'Node') -> bool:
        return x.node_type == NodeType.NAME

    @staticmethod
    def is_external_imports(x: 'Node') -> bool:
        return x.node_type == NodeType.EXTERNAL_IMPORTS

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

    @staticmethod
    def is_start(node: 'Node') -> bool:
        return node.node_type == NodeType.START

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
                assert node.value
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

    def merge(self, other: 'Node'):
        assert self.node_type == NodeType.GRAMMAR
        for production in other.filter(Node.is_production):
            cloned = production.clone()
            self.children.append(cloned)
