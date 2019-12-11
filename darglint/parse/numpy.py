from typing import (
    Iterable,
)
from ..token import (
    Token,
)
from ..node import (
    CykNode,
)


def parse(tokens):
    # type: (Iterable[Token]) -> CykNode
    return CykNode('null')
