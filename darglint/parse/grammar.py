"""Defines a base class far describing grammars."""

import abc
from typing import (  # noqa: F401
    Dict,
    List,
    Tuple,
    Union,
)


NonTerminalDerivation = Tuple[str, str]  # Add BaseGrammar to this as union.
TerminalDerivation = str
Derivation = Union[NonTerminalDerivation, TerminalDerivation]


class Production(object):
    """Represents a production in a grammar."""

    def __init__(self, lhs, *rhs, annotations=list()):
        # # type: (str, Union[NonTerminalDerivation, TerminalDerivation]) -> None  # noqa: E501
        """Create a new production.

        Args:
            lhs: The left-hand side of the production.
            *rhs: The items in the right-hand side of the
                production.
            annotations: A list of annotations.  Here, they should
                be the class of errors which are to be raised as a
                result of the given production being parsed.

        """
        self.lhs = lhs
        self.rhs = rhs
        self.annotations = annotations

    @classmethod
    def with_annotations(cls, lhs, annotations, *rhs):
        return cls(lhs, annotations=annotations, *rhs)


# Convenience name.
P = Production


class BaseGrammar(abc.ABC):

    @property
    @abc.abstractmethod
    def productions(self):
        # type: () -> List[Production]
        pass

    @property
    @abc.abstractmethod
    def start(self):
        # type: () -> str
        pass

    @classmethod
    def get_symbol_lookup(cls):
        # type: () -> Dict[str, int]
        lookup = dict()  # type: Dict[str, int]

        # We have to tell the type checker that productions is, in fact,
        # a list, since it enumerate actually takes a wider type (Iterable),
        # and it gets confused.
        assert isinstance(cls.productions, list)
        for i, production in enumerate(cls.productions):
            symbol = production.lhs
            lookup[symbol] = i
        return lookup
