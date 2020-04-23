# Generated on 2020-04-23 21:45:16.239170

from darglint.parse.grammar import (
    BaseGrammar,
    P,
)

from darglint.token import (
    TokenType,
)

from darglint.parse.identifiers import (
    NoqaIdentifier,
)

from darglint.errors import (
    EmptyDescriptionError,
    IndentError,
)

from darglint.parse.identifiers import (
    ExceptionIdentifier,
    ExceptionItemIdentifier,
)

class RaisesGrammar(BaseGrammar):
    productions = [
        P("raises-section", ([], "raises", "raises-section1", 0)),
        P("items-exception", ([], "item-exception", "items-exception0", 0), ([ExceptionItemIdentifier], "head-exception", "item-exception1", 2), ([ExceptionItemIdentifier], "head-exception", "line", 2), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception5", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception8", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception12", 0), ([ExceptionIdentifier, EmptyDescriptionError], "indent", "head-exception1", 0)),
        P("item-exception", ([ExceptionItemIdentifier], "head-exception", "item-exception1", 2), ([ExceptionItemIdentifier], "head-exception", "line", 2), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception5", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception8", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception12", 0), ([ExceptionIdentifier, EmptyDescriptionError], "indent", "head-exception1", 0)),
        P("head-exception", ([ExceptionIdentifier], "indent", "head-exception1", 0)),
        P("exception", (TokenType.WORD, 0)),
        P("paragraph-indented-two", ([], "indented-two", "paragraph-indented-two0", 0), ([], "indented-two", "line", 0)),
        P("paragraph", ([], "indents", "paragraph0", 0), ([], "indents", "line", 0), ([], "line", "paragraph2", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0), ([], "line", "paragraph1", 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("indented-two", ([], "indent", "indented-two0", 0)),
        P("indents", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("word", (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("colon", (TokenType.COLON, 0)),
        P("hash", (TokenType.HASH, 0)),
        P("indent", (TokenType.INDENT, 0)),
        P("newline", (TokenType.NEWLINE, 0)),
        P("raises", (TokenType.RAISES, 0)),
        P("noqa", (TokenType.NOQA, 0)),
        P("noqa-maybe", ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0)),
        P("noqa-head", ([], "hash", "noqa", 0)),
        P("words", ([], "word", "words", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("raises-section1", ([], "colon", "raises-section2", 0)),
        P("raises-section2", ([], "newline", "raises-section3", 0)),
        P("raises-section3", ([], "items-exception", "newlines", 0), ([], "item-exception", "items-exception0", 0), ([ExceptionItemIdentifier], "head-exception", "item-exception1", 2), ([ExceptionItemIdentifier], "head-exception", "line", 2), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception5", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception8", 0), ([IndentError, ExceptionItemIdentifier], "head-exception", "item-exception12", 0), ([ExceptionIdentifier, EmptyDescriptionError], "indent", "head-exception1", 0)),
        P("items-exception0", ([], "newline", "items-exception", 0)),
        P("item-exception1", ([], "line", "item-exception2", 0)),
        P("item-exception2", ([], "newline", "paragraph-indented-two", 0)),
        P("item-exception5", ([], "line", "item-exception6", 0)),
        P("item-exception6", ([], "newline", "paragraph", 0)),
        P("item-exception8", ([], "line", "item-exception9", 0)),
        P("item-exception9", ([], "newline", "item-exception10", 0)),
        P("item-exception10", ([], "paragraph", "newline", 0)),
        P("item-exception12", ([], "newline", "paragraph", 0)),
        P("head-exception1", ([], "exception", "colon", 0)),
        P("paragraph-indented-two0", ([], "line", "paragraph-indented-two1", 0)),
        P("paragraph-indented-two1", ([], "newline", "paragraph-indented-two", 0)),
        P("paragraph0", ([], "line", "paragraph1", 0)),
        P("paragraph1", ([], "newline", "paragraph", 0)),
        P("paragraph2", ([], "newline", "paragraph", 0)),
        P("indented-two0", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
    ]
    start = "raises-section"