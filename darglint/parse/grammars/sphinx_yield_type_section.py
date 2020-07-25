# Generated on 2020-07-25 08:37:51.194118

from darglint.parse.grammar import (
    BaseGrammar,
    P,
)

from darglint.errors import (
    IndentError,
)

from darglint.token import (
    TokenType,
)

from darglint.parse.identifiers import (
    NoqaIdentifier,
)

from darglint.errors import (
    EmptyDescriptionError,
)

class YieldTypeGrammar(BaseGrammar):
    productions = [
        P("yield-type-section", ([], "ythead", "yield-type-section1", 0), ([], "ythead-no-follow", "newlines", 0), ([EmptyDescriptionError], "colon", "ythead-no-follow1", 0)),
        P("ythead", ([], "colon", "ythead0", 0)),
        P("ythead-no-follow", ([EmptyDescriptionError], "colon", "ythead-no-follow1", 0)),
        P("item-body", ([], "line", "item-body0", 2), ([], "line", "item-body1", 2), ([], "line", "item-body2", 2), ([], "word", "line", 2), ([], "word", "noqa-maybe", 2), ([NoqaIdentifier], "hash", "noqa", 2), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 2), (TokenType.INDENT, 2), (TokenType.COLON, 2), (TokenType.HASH, 2), (TokenType.LPAREN, 2), (TokenType.RPAREN, 2), (TokenType.WORD, 2), (TokenType.RAISES, 2), (TokenType.ARGUMENTS, 2), (TokenType.ARGUMENT_TYPE, 2), (TokenType.RETURNS, 2), (TokenType.RETURN_TYPE, 2), (TokenType.YIELDS, 2), (TokenType.YIELD_TYPE, 2), (TokenType.VARIABLES, 2), (TokenType.VARIABLE_TYPE, 2), (TokenType.NOQA, 2), (TokenType.OTHER, 2), (TokenType.RECEIVES, 2), (TokenType.WARNS, 2), (TokenType.SEE, 2), (TokenType.ALSO, 2), (TokenType.NOTES, 2), (TokenType.EXAMPLES, 2), (TokenType.REFERENCES, 2), (TokenType.HEADER, 2), ([IndentError], "line", "item-body7", 1)),
        P("block-indented", ([], "paragraph-indented", "block-indented0", 0), ([], "paragraph-indented", "block-indented1", 0), ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("split-indented", ([], "newline", "split-indented0", 0), (TokenType.NEWLINE, 0)),
        P("paragraph-indented", ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("indented", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("block", ([], "paragraph", "block0", 0), ([], "indents", "paragraph0", 0), ([], "indents", "line", 0), ([], "line", "paragraph2", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0), ([], "line", "paragraph1", 0)),
        P("paragraph", ([], "indents", "paragraph0", 0), ([], "indents", "line", 0), ([], "line", "paragraph2", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0), ([], "line", "paragraph1", 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("indents", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("split", ([], "newline", "split0", 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("word", (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("colon", (TokenType.COLON, 0)),
        P("hash", (TokenType.HASH, 0)),
        P("indent", (TokenType.INDENT, 0)),
        P("newline", (TokenType.NEWLINE, 0)),
        P("yield-type", (TokenType.YIELD_TYPE, 0)),
        P("noqa", (TokenType.NOQA, 0)),
        P("noqa-maybe", ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0)),
        P("noqa-head", ([], "hash", "noqa", 0)),
        P("words", ([], "word", "words", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("yield-type-section1", ([], "item-body", "newlines", 0), ([], "line", "item-body0", 2), ([], "line", "item-body1", 2), ([], "line", "item-body2", 2), ([], "word", "line", 2), ([], "word", "noqa-maybe", 2), ([NoqaIdentifier], "hash", "noqa", 2), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 2), (TokenType.INDENT, 2), (TokenType.COLON, 2), (TokenType.HASH, 2), (TokenType.LPAREN, 2), (TokenType.RPAREN, 2), (TokenType.WORD, 2), (TokenType.RAISES, 2), (TokenType.ARGUMENTS, 2), (TokenType.ARGUMENT_TYPE, 2), (TokenType.RETURNS, 2), (TokenType.RETURN_TYPE, 2), (TokenType.YIELDS, 2), (TokenType.YIELD_TYPE, 2), (TokenType.VARIABLES, 2), (TokenType.VARIABLE_TYPE, 2), (TokenType.NOQA, 2), (TokenType.OTHER, 2), (TokenType.RECEIVES, 2), (TokenType.WARNS, 2), (TokenType.SEE, 2), (TokenType.ALSO, 2), (TokenType.NOTES, 2), (TokenType.EXAMPLES, 2), (TokenType.REFERENCES, 2), (TokenType.HEADER, 2), ([IndentError], "line", "item-body7", 1)),
        P("ythead0", ([], "yield-type", "colon", 0)),
        P("ythead-no-follow1", ([], "yield-type", "colon", 0)),
        P("item-body0", ([], "newline", "block-indented", 0)),
        P("item-body1", ([], "newlines", "block-indented", 0), ([], "paragraph-indented", "block-indented0", 0), ([], "paragraph-indented", "block-indented1", 0), ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("item-body2", ([], "newline", "item-body3", 0)),
        P("item-body3", ([], "indent", "item-body4", 0)),
        P("item-body4", ([], "newline", "item-body5", 0)),
        P("item-body5", ([], "newlines", "block-indented", 0), ([], "paragraph-indented", "block-indented0", 0), ([], "paragraph-indented", "block-indented1", 0), ([], "indented", "paragraph-indented0", 0), ([], "indented", "line", 0)),
        P("item-body7", ([], "newline", "block", 0)),
        P("block-indented0", ([], "split", "block-indented", 0)),
        P("block-indented1", ([], "split-indented", "block-indented", 0)),
        P("split-indented0", ([], "indents", "newlines", 0), ([], "indent", "indents", 0), (TokenType.INDENT, 0), ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("paragraph-indented0", ([], "line", "paragraph-indented1", 0)),
        P("paragraph-indented1", ([], "newline", "paragraph-indented", 0)),
        P("block0", ([], "split", "block", 0)),
        P("paragraph0", ([], "line", "paragraph1", 0)),
        P("paragraph1", ([], "newline", "paragraph", 0)),
        P("paragraph2", ([], "newline", "paragraph", 0)),
        P("split0", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
    ]
    start = "yield-type-section"