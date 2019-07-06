
from lark import (
    Lark,
    Tree,
)

from .node import (
    Node,
    NodeType,
)


class Parser(object):

    grammar = r'''
        start: grammar

        grammar: imports? external_imports? name? start_expression? production+

        production: annotations? symbol _OPER expression
        _OPER: "::="

        expression: sequence (_BAR sequence)*
        _BAR: "|"
        sequence: annotations? (symbol | TERMINAL) (_WHITESPACE (symbol | TERMINAL))*
        TERMINAL: "\"" (LETTER | ESCAPED | NUMBER | "_" | "-" | ":")+ "\""
            | "ε"
        ESCAPED: "\\" ("." | "," | "*" | "^" | "("
                      | ")" | "+" | "-" | "/" | "\""
                      | " " | "]" | "[" | "|")

        start_expression: _START symbol
        _START: "start:"

        name: _GRAMMAR NAME
        NAME: LETTER+
        _GRAMMAR: "Grammar:"

        external_imports: external_import+
        external_import: _FROM FILENAME _IMPORT _LP items _RP
        _FROM: "from"
        _LP: "("
        _RP: ")"
        items: ITEM ","?
            | ITEM "," items
        ITEM: /\w+/

        imports: import+
        import: _IMPORT FILENAME
        FILENAME: /(\w|\\|\.|-|_)+/
        _IMPORT: "import"

        annotations: annotation+
        annotation: _AT IDENT
        _AT: "@"

        symbol: _LB IDENT _RB
        _LB: "<"
        _RB: ">"
        IDENT: LETTER (LETTER | NUMBER | "_" | "-")*

        %import common.LETTER
        %import common.NUMBER

        _COMMENT: /#[^\n]*/
        %ignore _COMMENT

        _WHITESPACE: (" " | "\n" | "\t")+
        %ignore _WHITESPACE
    '''  # noqa: E501

    def __init__(self):
        self.delegate = Lark(self.grammar)

    def parse(self, value: str) -> Node:
        tree = self.delegate.parse(value)
        return Node.from_lark_tree(tree)

    def parse_production(self, value: str) -> Node:
        """Parse just an production.

        Args:
            value: The string to parse.

        Throws:
            Exception: If there is more than a single production in the
                value.

        Returns:
            A node which is the head of the production (not the grammar.)

        """
        if '\n' in value:
            raise Exception(
                'There should only be a single product, but '
                'a newline is present.'
            )
        grammar = self.parse(value)
        if grammar.children[0].node_type == NodeType.PRODUCTION:
            production = grammar.children[0]
        else:
            production = grammar.children[1]
        grammar.children = list()
        return production
