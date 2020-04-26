import abc

from ..custom_assert import Assert
from .cyk import CykNode
from typing import (
    Callable,
    List,
    Optional,
    Union,
    Tuple,
)
from ..token import (
    TokenType,
)


class Continuation(object):
    """Represents a continuation of a path.

    This is the actual representation of the path in the parse
    tree.  The wrapper, Path, returns continuations.  Each
    continuation either performs a branching or a chain.

    """

    def __init__(self, path, condition, child=None):
        # type: (str, Callable[[CykNode], bool], Union[Continuation, Tuple[Continuation, ...], None]) -> None  # noqa: E501
        self.path = path
        self.condition = condition
        self.child = child
        self._sealed = False

    def of(self, path):
        # type: (str) -> Continuation
        assert not self._sealed
        if isinstance(self.child, Continuation):
            self.child.of(path)
        elif self.child is None:
            self.child = Continuation(path, lambda _: True, None)
        return self

    def branch(self, *continuations):
        # type: (Continuation) -> Continuation
        assert not self._sealed
        self.child = continuations
        self._sealed = True
        return self

    def extract(self, node):
        # type: (CykNode) -> Optional[str]
        """Extract the value of the leaf node described by this path.

        Args:
            node: The root of the path we're about to follow.

        Returns:
            The value of the token, if correctly described by this
            path.

        """
        if not self.condition(node):
            return None
        curr = node  # type: Optional[CykNode]
        for letter in self.path:
            if curr and letter == 'r':
                curr = curr.rchild
            elif curr and letter == 'l':
                curr = curr.lchild
            elif curr and letter == 'v' and curr.value:
                return curr.value.value
        if curr is None:
            return None
        if isinstance(self.child, tuple):
            for subchild in self.child:
                next_curr = subchild.extract(curr)
                if isinstance(next_curr, str):
                    return next_curr
                elif next_curr is None:
                    # In branching, we try each branch until
                    # one succeeds.
                    continue
                else:
                    Assert(
                        False,
                        'Expected path extraction to yield str '
                        'or None but was {}'.format(
                            next_curr.__class__.__name__
                        )
                    )
                    return None
        elif isinstance(self.child, Continuation):
            next_curr = self.child.extract(curr)
            if isinstance(next_curr, str):
                return next_curr
            elif next_curr is None:
                # In an unconditional chain, we fail if any
                # in the chain fail.
                return None
            else:
                Assert(
                    False,
                    'Expected path extraction to yield str '
                    'or None but was {}'.format(
                        next_curr.__class__.__name__
                    )
                )
                return None
        return None


class Path(object):
    """Represents a path which can be taken in a parse tree.

    The purpose of this path is to extract the value of a
    token in the leaves of the tree.  We previously handled
    this my simply accessing the members of the CykNodes
    in the tree, and making asserts.  However, that can sometimes
    result in runtime errors.  Rather, we should want to
    log the failure in a type-safe manner.

    """

    @staticmethod
    def of(path):
        # type: (str) -> Continuation
        """Construct a path composed of left and right turns.

        If this is the terminal path, it should end with the
        character, 'v'.

        Args:
            path: The path to take.  Should be a string composed
                of the characters, 'l', 'r', and 'v'.

        Returns:
            A continuation of the path.

        """
        return Continuation(path, lambda _: True)

    @staticmethod
    def branch(*paths):
        # type: (Continuation) -> Continuation
        """A path which accepts the first succeeding path.

        Args:
            paths: The paths to try, in order.

        Returns:
            A continuation representing the path.

        """
        return Continuation('', lambda _: True, paths)

    # These methods are technically unnecessary -- they are
    # synonymous with an `of`.  However, it makes for nicer
    # documentation of intent, I think.
    @staticmethod
    def if_left(path):
        # type: (str) -> Continuation
        return Continuation(path, lambda x: bool(x.lchild))

    @staticmethod
    def if_right(path):
        # type: (str) -> Continuation
        return Continuation(path, lambda x: bool(x.rchild))


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


class ArgumentItemIdentifier(Identifier):

    key = 'id_ArgsItem'

    @staticmethod
    def extract(node):
        return node.lchild.value.value


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
        if node.rchild.rchild.lchild.rchild:
            assert node.rchild.rchild.lchild.rchild.lchild
            if node.rchild.rchild.lchild.rchild.lchild.value:
                return node.rchild.rchild.lchild.rchild.lchild.value.value
            else:
                return (
                    node.rchild.rchild.lchild.rchild
                        .lchild.reconstruct_string()
                )
        else:
            if node.rchild.rchild.lchild.value:
                return node.rchild.rchild.lchild.value.value
            return node.rchild.rchild.lchild.reconstruct_string()


class ExceptionItemIdentifier(Identifier):

    key = 'id_ExceptItem'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.lchild
        assert node.lchild.value
        return node.lchild.value.value


class ExceptionIdentifier(Identifier):

    key = 'id_Except'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.rchild
        assert node.rchild.lchild
        assert node.rchild.lchild.value
        return node.rchild.lchild.value.value


class ReturnTypeIdentifier(Identifier):

    key = 'id_ReturnType'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.lchild
        assert node.lchild.value
        return node.lchild.value.value


class YieldTypeIdentifier(Identifier):

    key = 'id_YieldType'

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        assert node.lchild
        assert node.lchild.value
        return node.lchild.value.value


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
