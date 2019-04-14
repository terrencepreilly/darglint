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


class NodeType(Enum):

    GRAMMAR = 0
    PRODUCTION = 1
    SYMBOL = 2
    EXPRESSION = 3
    SEQUENCE = 4
    TERMINAL = 5


TERMINAL_NODES = {NodeType.TERMINAL, NodeType.SYMBOL}
NONTERMINAL_NODES = {
    NodeType.GRAMMAR,
    NodeType.PRODUCTION,
    NodeType.EXPRESSION,
    NodeType.SEQUENCE,
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
            return f'{self.children[0]} ::= {self.children[1]}'
        elif self.node_type == NodeType.SYMBOL:
            return f'<{self.value}>'
        elif self.node_type == NodeType.EXPRESSION:
            return ' | '.join(map(str, self.children))
        elif self.node_type == NodeType.SEQUENCE:
            return ' '.join(map(str, self.children))
        elif self.node_type == NodeType.TERMINAL:
            return self.value

    def __repr__(self):
        return str(self)

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
            assert production.children[0].value is not None
            symbol = production.children[0].value
            self.cached_symbols.add(symbol)

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
