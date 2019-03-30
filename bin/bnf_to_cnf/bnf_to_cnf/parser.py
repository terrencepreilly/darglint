
from lark import (
    Lark,
    Tree,
)

from .node import (
    Node,
)


class Parser(object):

    grammar = r'''
        start: grammar

        grammar: production+

        production: symbol _OPER expression
        _OPER: "::="

        expression: sequence (_BAR sequence)*
        _BAR: "|"
        sequence: (symbol | TERMINAL) (_WHITESPACE (symbol | TERMINAL))*
        TERMINAL: "\"" (LETTER | ESCAPED | NUMBER | "_" | "-" | ":")+ "\""
        ESCAPED: "\\" ("." | "*" )

        symbol: _LB IDENT _RB
        _LB: "<"
        _RB: ">"
        IDENT: LETTER (LETTER | NUMBER | "_" | "-")*

        %import common.LETTER
        %import common.NUMBER
        _WHITESPACE: (" " | "\n" | "\t")+
        %ignore _WHITESPACE
    '''

    def __init__(self):
        self.delegate = Lark(self.grammar)

    def parse(self, value: str) -> Node:
        tree = self.delegate.parse(value)
        return Node.from_lark_tree(tree)
