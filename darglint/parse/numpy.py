from typing import (
    List,
    Optional,
)
from ..token import (
    Token,
)
from ..node import (
    CykNode,
)
from .cyk import (
    parse as cyk_parse,
)
from .grammars.numpy import (
    NumpyGrammar,
)
from .grammar import (
    BaseGrammar,
)


def parse(tokens):
    # # type: (List[Token]) -> Optional[CykNode]
    return cyk_parse(NumpyGrammar, tokens)
