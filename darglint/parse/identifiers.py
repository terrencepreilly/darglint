import abc

from .cyk import CykNode
from typing import (
    List,
)
from ..token import (
    TokenType,
)


class Identifier(abc.ABC):
    """Identifies a particular target in the grammar.

    Since the transformation from BNF to CNF messes up
    the grammars, we can use this class to mark pieces
    of the grammar we need access to.  This should greatly
    simplify the process of interpreting the produced tree.

    """

    @property
    @abc.abstractmethod
    def key(self):
        # type: () -> str
        pass

    @staticmethod
    @abc.abstractmethod
    def extract(node):
        # type: (CykNode) -> str
        pass

    def __str__(self):
        return '<identifier: {}>'.format(self.key)

    def __repr__(self):
        return str(self)


# TODO: Write a class to extract a given value from a base node
# given a path.  Use that to simplify the extract methods below.

class ArgumentItemIdentifier(Identifier):

    key = 'id_ArgsItem'

    @staticmethod
    def extract(node):
        return ''


class ArgumentIdentifier(Identifier):

    key = 'id_Args'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.rchild
        assert node.rchild.lchild
        assert node.rchild.lchild.value
        assert node.rchild.lchild.value.value
        return node.rchild.lchild.value.value


class ArgumentTypeIdentifier(Identifier):

    key = 'id_ArgType'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.rchild
        assert node.rchild.rchild
        assert node.rchild.rchild.lchild
        assert node.rchild.rchild.lchild.rchild
        assert node.rchild.rchild.lchild.rchild.lchild
        if node.rchild.rchild.lchild.rchild.lchild.value:
            return node.rchild.rchild.lchild.rchild.lchild.value.value
        else:
            return node.rchild.rchild.lchild.rchild.lchild.reconstruct_string()


class ExceptionItemIdentifier(Identifier):

    key = 'id_ExceptItem'

    @staticmethod
    def extract(node):
        return ''


class ExceptionIdentifier(Identifier):

    key = 'id_Except'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.rchild
        assert node.rchild.lchild
        assert node.rchild.lchild.value
        return node.rchild.lchild.value.value


class NoqaIdentifier(Identifier):

    key = 'id_Noqa'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        if node.rchild and node.rchild.rchild:
            if node.rchild.rchild.value:
                return node.rchild.rchild.value.value
            elif node.rchild.rchild.lchild:
                assert node.rchild.rchild.lchild.value
                return node.rchild.rchild.lchild.value.value
            else:
                assert False
        else:
            return ''

    @staticmethod
    def extract_targets(node):
        # type: (CykNode) -> List[str]
        if (
            node.rchild
            and node.rchild.rchild
        ):
            children = list()
            for child in node.rchild.rchild.walk():
                if child.value and child.value.token_type == TokenType.WORD:
                    children.append(child.value.value)
            if len(children) > 1:
                return children[1:]
        return []
