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
        Assert(
            not self._sealed,
            'Sealed continuations shouldn\'t be extended!',
        )
        if isinstance(self.child, Continuation):
            self.child.of(path)
        elif self.child is None:
            self.child = Continuation(path, lambda _: True, None)
        return self

    def branch(self, *continuations):
        # type: (Continuation) -> Continuation
        Assert(
            not self._sealed,
            'Sealed continuations shouldn\'t be extended!',
        )
        self.child = continuations
        self._sealed = True
        return self

    def extract(self, node):
        # type: (CykNode) -> Union[str, CykNode, None]
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
            else:
                return None
        if curr is None:
            return None

        is_branch = isinstance(self.child, tuple)
        is_continuation = isinstance(self.child, Continuation)
        if is_branch:
            for branch in self.child:  # type: ignore
                next_curr = branch.extract(curr)
                if isinstance(next_curr, str):
                    return next_curr
                elif next_curr is None:
                    # In branching, we try each branch until
                    # one succeeds.
                    continue
                elif isinstance(next_curr, CykNode):
                    return next_curr
                else:
                    Assert(
                        False,
                        'Expected path extraction to yield str '
                        'or None or CykNode but was {}'.format(
                            next_curr.__class__.__name__
                        )
                    )
                    return None
            # Branches are always terminal.  If we haven't
            # found the result by this point, there is none.
            return None
        elif is_continuation:
            next_curr = self.child.extract(curr)  # type: ignore
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
        return curr


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

    @property
    @abc.abstractmethod
    def path(self):
        # type: () -> Continuation
        pass

    @classmethod
    def extract(cls, node):
        # type: (CykNode) -> str
        # TODO: Fix the type annotation here.
        value = cls.path.extract(node)  # type: ignore
        Assert(
            value is not None,
            'Failed to extract {}'.format(cls.key)
        )
        return value or ''

    def __str__(self):
        return '<identifier: {}>'.format(self.key)

    def __repr__(self):
        return str(self)


class ArgumentItemIdentifier(Identifier):

    key = 'id_ArgsItem'
    path = Path.of('lv')


class ArgumentIdentifier(Identifier):

    key = 'id_Args'
    path = Path.of('rlv')


class ArgumentTypeIdentifier(Identifier):

    key = 'id_ArgType'
    path = Path.of('rrl').branch(
        Path.if_right('r').branch(Path.of('lv'), Path.of('l')),
        Path.of('v'),
        Path.of(''),
    )

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        value = ArgumentTypeIdentifier.path.extract(node)
        is_leaf = isinstance(value, str)
        is_branch = isinstance(value, CykNode)
        Assert(is_leaf or is_branch, 'Unable to extract argument type.')
        if is_leaf:
            return value  # type: ignore
        elif is_branch:
            return value.reconstruct_string()  # type: ignore
        else:
            return ''


class ExceptionItemIdentifier(Identifier):

    key = 'id_ExceptItem'
    path = Path.of('lv')


class ExceptionIdentifier(Identifier):

    key = 'id_Except'
    path = Path.of('rlv')


class ReturnTypeIdentifier(Identifier):

    key = 'id_ReturnType'
    path = Path.of('lv')


class YieldTypeIdentifier(Identifier):

    key = 'id_YieldType'
    path = Path.of('lv')


class NoqaIdentifier(Identifier):

    key = 'id_Noqa'
    path = Path.of('rr').branch(Path.of('v'), Path.if_left('lv'))

    @staticmethod
    def extract(node):
        # type: (CykNode) -> str
        if node.rchild and node.rchild.rchild:
            path = Path.branch(Path.of('rrv'), Path.of('rrlv'))
            value = path.extract(node)
            if isinstance(value, str):
                return value
            # path2 = Path.of('rrlv')
            # value = path2.extract(node)
            # if isinstance(value, str):
            #     return value
            return ''
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
