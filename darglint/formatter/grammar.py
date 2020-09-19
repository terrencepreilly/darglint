# Generated on 2020-09-19 10:57:03.256522

from darglint.parse.grammar import (
    BaseGrammar,
    P,
)

from darglint.token import (
    TokenType,
)

from darglint.formatter.errors import (
    BrokenNumberException,
)

class HexNumberGrammar(BaseGrammar):
    productions = [
        P("numbers", ([], "number", "numbers1", 0), ([], "prefix", "digits", 0)),
        P("numbers0", ([], "number", "numbers1", 0), ([], "prefix", "digits", 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("number", ([], "prefix", "digits", 0)),
        P("digits", ([], "digit", "digits", 0), ([BrokenNumberException], "space", "digits", 0), (TokenType.DIGIT, 0)),
        P("prefix", (TokenType.NUMBER_PREFIX, 0)),
        P("digit", (TokenType.DIGIT, 0)),
        P("newline", (TokenType.NEWLINE, 0)),
        P("space", (TokenType.SPACE, 0)),
        P("numbers1", ([], "newlines", "numbers0", 0)),
    ]
    start = "numbers"
