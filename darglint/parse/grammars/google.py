from darglint.parse.grammar import BaseGrammar
from darglint.parse.grammar import Production as P
from darglint.token import TokenType


# Generated on 2019-05-25 19:53:15.635616
class Grammar(BaseGrammar):
    productions = [
        P("start", ([], "word", "line"), TokenType.WORD),
        P("line", ([], "word", "line"), TokenType.WORD),
        P("word", TokenType.WORD),
    ]

    start = "start"
