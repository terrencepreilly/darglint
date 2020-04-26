"""Defines a base class far describing grammars."""

import abc
from typing import (  # noqa: F401
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from ..custom_assert import Assert


NonTerminalDerivation = Tuple[List, str, str, int]
TerminalDerivation = Tuple[str, int]
Derivation = Union[NonTerminalDerivation, TerminalDerivation]


class Production(object):
    """Represents a production in a grammar."""

    def __init__(self, lhs, *rhs, annotations=list()):
        # type: (str, Derivation, Optional[List[Any]]) -> None
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
        # a list, since enumerate actually takes a wider type (Iterable),
        # and it gets confused.
        Assert(
            isinstance(cls.productions, list),
            'Expected productions to be a list.'
        )
        if not isinstance(cls.productions, list):
            return dict()
        for i, production in enumerate(cls.productions):
            symbol = production.lhs
            lookup[symbol] = i
        return lookup

    @classmethod
    def to_dot(cls):
        # () -> str

        def normalize(name):
            return name.replace('-', '_').replace('.', '_')

        def interpolate(curr, max_weight):
            min_color = (200, 200, 200)
            max_color = (0, 0, 0)
            return tuple(
                int(u - (u - l) * (curr / max_weight))
                for l, u in zip(max_color, min_color)
            )

        def to_hex(color):
            return '#{}{}{}'.format(*[
                format(x, '02x') for x in color
            ])

        start = cls.start
        if not start:
            return ''

        max_weight = 0
        for production in cls.productions:
            for derivation in production.rhs:
                if len(derivation) == 4:
                    if derivation[-1] > max_weight:
                        max_weight = derivation[-1]

        join_count = 0
        ret = 'digraph G {\n'
        for production in cls.productions:
            lhs = normalize(production.lhs)
            for derivation in production.rhs:
                if len(derivation) == 2:
                    rhs = normalize(str(derivation[0]))
                    color = to_hex(interpolate(0, max_weight))
                    ret += (
                        '  {} -> {} [color="{}"];\n\n'.format(
                            lhs,
                            rhs,
                            color,
                        )
                    )
                elif len(derivation) == 4:
                    weight = derivation[-1]
                    color = to_hex(interpolate(weight, max_weight))
                    join_node = '_join{}'.format(join_count)
                    join_count += 1
                    annotations = [x.__name__ for x in derivation[0]]
                    if annotations:
                        node_color = '#c8e6c9'
                        if any(['error' in x.lower() for x in annotations]):
                            node_color = '#ffcdd2'
                        ret += (
                            '  {} [label="{}", shape="rect", '
                            'style="filled", fillcolor="{}"]\n'
                        ).format(
                            join_node,
                            '\\n'.join(annotations),
                            node_color,
                        )
                    else:
                        ret += (
                            '  {} [label="", color="none", '
                            'height="0", width="0"];\n'
                        ).format(join_node)
                    ret += (
                        '  {} -> {} [arrowhead="none", color="{}"];\n'
                    ).format(
                        lhs,
                        join_node,
                        color,
                    )
                    ret += (
                        '  {} -> {{ {}, {} }} [color="{}"];\n\n'
                    ).format(
                        join_node,
                        normalize(derivation[1]),
                        normalize(derivation[2]),
                        color,
                    )
        ret += '}'
        return ret
