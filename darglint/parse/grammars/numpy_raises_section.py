# Generated on 2020-07-14 06:23:48.749257

from darglint.token import (
    TokenType,
)

from darglint.parse.identifiers import (
    NoqaIdentifier,
)

from darglint.parse.grammar import (
    BaseGrammar,
    P,
)

from darglint.parse.identifiers import (
    ExceptionItemIdentifier,
)

from darglint.errors import (
    EmptyDescriptionError,
    EmptyTypeError,
)

class RaisesGrammar(BaseGrammar):
    productions = [
        P("raises-section", ([], "raises-header", "newlines", 0), ([], "raises-header", "raises-section1", 0), ([], "raises", "raises-header0", 0)),
        P("raises-header", ([], "raises", "raises-header0", 0)),
        P("raises-body", ([], "raises-item", "raises-body0", 0), ([ExceptionItemIdentifier], "ident", "raises-item1", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item4", 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item8", 0)),
        P("raises-item", ([ExceptionItemIdentifier], "ident", "raises-item1", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item4", 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item8", 0)),
        P("block-indented", ([], "paragraph-indented", "block-indented0", 0), ([], "paragraph-indented", "block-indented1", 0), ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("split-indented", ([], "newline", "split-indented0", 0)),
        P("paragraph-indented", ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("indented", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("indents", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("split", ([], "newline", "split0", 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("word", (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("ident", (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0)),
        P("header", (TokenType.HEADER, 0)),
        P("colon", (TokenType.COLON, 0)),
        P("hash", (TokenType.HASH, 0)),
        P("indent", (TokenType.INDENT, 0)),
        P("newline", (TokenType.NEWLINE, 0)),
        P("raises", (TokenType.RAISES, 0)),
        P("noqa", (TokenType.NOQA, 0)),
        P("noqa-maybe", ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0)),
        P("noqa-head", ([], "hash", "noqa", 0)),
        P("words", ([], "word", "words", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("raises-section1", ([], "newline", "raises-section2", 0)),
        P("raises-section2", ([], "raises-body", "newlines", 0), ([], "raises-item", "raises-body0", 0), ([ExceptionItemIdentifier], "ident", "raises-item1", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item4", 0), ([ExceptionItemIdentifier, EmptyTypeError], "ident", "raises-item8", 0)),
        P("raises-header0", ([], "newline", "header", 0)),
        P("raises-body0", ([], "newline", "raises-body", 0)),
        P("raises-item1", ([], "noqa-maybe", "raises-item2", 0), ([], "newline", "block-indented", 0)),
        P("raises-item2", ([], "newline", "block-indented", 0)),
        P("raises-item4", ([], "colon", "raises-item5", 0)),
        P("raises-item5", ([], "line", "raises-item6", 0)),
        P("raises-item6", ([], "newline", "block-indented", 0)),
        P("raises-item8", ([], "colon", "raises-item9", 0)),
        P("raises-item9", ([], "noqa-maybe", "raises-item10", 0), ([], "newline", "block-indented", 0)),
        P("raises-item10", ([], "newline", "block-indented", 0)),
        P("block-indented0", ([], "split", "block-indented", 0)),
        P("block-indented1", ([], "split-indented", "block-indented", 0)),
        P("split-indented0", ([], "indents", "split-indented1", 0), ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("split-indented1", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("paragraph-indented0", ([], "line", "paragraph-indented1", 0)),
        P("paragraph-indented1", ([], "newline", "paragraph-indented", 0)),
        P("split0", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
    ]
    start = "raises-section"