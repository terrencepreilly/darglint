from enum import Enum
from typing import (
    List,
    Optional,
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


class Node(object):

    def __init__(self,
                 node_type: NodeType,
                 value: Optional[str] = None,
                 children: List['Node'] = list()):
        self.node_type = node_type
        self.value = value
        self.children = children

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
