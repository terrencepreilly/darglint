from darglint.parse.grammar import BaseGrammar
from darglint.parse.grammar import Production as P
from darglint.token import TokenType


# Generated on 2019-05-25 20:18:59.904567
class Grammar(BaseGrammar):
    productions = [
        P("start", ([], "line", "newline"), ([], "word", "line"), TokenType.WORD),
        P("line", ([], "word", "line"), TokenType.WORD),
        P("word", TokenType.WORD),
        P("newline", TokenType.NEWLINE),
    ]

    start = "start"

