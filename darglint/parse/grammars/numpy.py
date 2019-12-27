# Generated on 2019-12-25 08:14:01.936293

from darglint.parse.identifiers import (
    NoqaIdentifier,
)

from darglint.token import (
    TokenType,
)

from darglint.parse.grammar import (
    BaseGrammar,
    P,
)

from darglint.parse.identifiers import (
    ShortDescriptionIdentifier,
)

class NumpyGrammar(BaseGrammar):
    productions = [
        P("docstring", ([], "short-description", "long-description", 0), ([ShortDescriptionIdentifier], "word", "line", 0), ([ShortDescriptionIdentifier], "word", "noqa-maybe", 0), ([NoqaIdentifier, ShortDescriptionIdentifier], "hash", "noqa", 0), ([NoqaIdentifier, ShortDescriptionIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), ([ShortDescriptionIdentifier], "line", "newlines", 0)),
        P("long-description", ([], "line", "long-description0", 0), ([], "line", "newlines", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), ([], TokenType.COLON, 0), ([], TokenType.HASH, 0), ([], TokenType.INDENT, 0), ([], TokenType.LPAREN, 0), ([], TokenType.RPAREN, 0), ([], TokenType.WORD, 0), ([], TokenType.RAISES, 0), ([], TokenType.ARGUMENTS, 0), ([], TokenType.ARGUMENT_TYPE, 0), ([], TokenType.RETURNS, 0), ([], TokenType.RETURN_TYPE, 0), ([], TokenType.YIELDS, 0), ([], TokenType.YIELD_TYPE, 0), ([], TokenType.VARIABLES, 0), ([], TokenType.VARIABLE_TYPE, 0), ([], TokenType.NOQA, 0)),
        P("short-description", ([ShortDescriptionIdentifier], "word", "line", 0), ([ShortDescriptionIdentifier], "word", "noqa-maybe", 0), ([NoqaIdentifier, ShortDescriptionIdentifier], "hash", "noqa", 0), ([NoqaIdentifier, ShortDescriptionIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), ([ShortDescriptionIdentifier], "line", "newlines", 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), ([], TokenType.COLON, 0), ([], TokenType.HASH, 0), ([], TokenType.INDENT, 0), ([], TokenType.LPAREN, 0), ([], TokenType.RPAREN, 0), ([], TokenType.WORD, 0), ([], TokenType.RAISES, 0), ([], TokenType.ARGUMENTS, 0), ([], TokenType.ARGUMENT_TYPE, 0), ([], TokenType.RETURNS, 0), ([], TokenType.RETURN_TYPE, 0), ([], TokenType.YIELDS, 0), ([], TokenType.YIELD_TYPE, 0), ([], TokenType.VARIABLES, 0), ([], TokenType.VARIABLE_TYPE, 0), ([], TokenType.NOQA, 0)),
        P("newlines", ([], "newline", "newlines", 0), ([], TokenType.NEWLINE, 0)),
        P("word", ([], TokenType.COLON, 0), ([], TokenType.HASH, 0), ([], TokenType.INDENT, 0), ([], TokenType.LPAREN, 0), ([], TokenType.RPAREN, 0), ([], TokenType.WORD, 0), ([], TokenType.RAISES, 0), ([], TokenType.ARGUMENTS, 0), ([], TokenType.ARGUMENT_TYPE, 0), ([], TokenType.RETURNS, 0), ([], TokenType.RETURN_TYPE, 0), ([], TokenType.YIELDS, 0), ([], TokenType.YIELD_TYPE, 0), ([], TokenType.VARIABLES, 0), ([], TokenType.VARIABLE_TYPE, 0), ([], TokenType.NOQA, 0)),
        P("colon", ([], TokenType.COLON, 0)),
        P("hash", ([], TokenType.HASH, 0)),
        P("newline", ([], TokenType.NEWLINE, 0)),
        P("noqa", ([], TokenType.NOQA, 0)),
        P("noqa-maybe", ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0)),
        P("noqa-head", ([], "hash", "noqa", 0)),
        P("words", ([], "word", "words", 0), ([], TokenType.COLON, 0), ([], TokenType.HASH, 0), ([], TokenType.INDENT, 0), ([], TokenType.LPAREN, 0), ([], TokenType.RPAREN, 0), ([], TokenType.WORD, 0), ([], TokenType.RAISES, 0), ([], TokenType.ARGUMENTS, 0), ([], TokenType.ARGUMENT_TYPE, 0), ([], TokenType.RETURNS, 0), ([], TokenType.RETURN_TYPE, 0), ([], TokenType.YIELDS, 0), ([], TokenType.YIELD_TYPE, 0), ([], TokenType.VARIABLES, 0), ([], TokenType.VARIABLE_TYPE, 0), ([], TokenType.NOQA, 0)),
        P("long-description0", ([], "newlines", "long-description", 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
    ]
    start = "docstring"