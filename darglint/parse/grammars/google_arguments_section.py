# Generated on 2020-05-31 10:21:20.274591

from darglint.errors import (
    ParameterMalformedError,
)

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
    EmptyTypeError,
    IndentError,
)

from darglint.parse.identifiers import (
    ArgumentIdentifier,
    ArgumentItemIdentifier,
    ArgumentTypeIdentifier,
)

class ArgumentsGrammar(BaseGrammar):
    productions = [
        P("arguments-section", ([], "arguments", "arguments-section1", 0)),
        P("items-argument", ([], "item-argument", "items-argument0", 0), ([ArgumentItemIdentifier], "head-argument", "item-body", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument1", 0), ([ArgumentIdentifier, EmptyTypeError, EmptyDescriptionError], "indent", "head-argument3", 2), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument7", 0), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument10", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument14", 0)),
        P("item-argument", ([ArgumentItemIdentifier], "head-argument", "item-body", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument1", 0), ([ArgumentIdentifier, EmptyTypeError, EmptyDescriptionError], "indent", "head-argument3", 2), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument7", 0), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument10", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument14", 0)),
        P("head-argument", ([ArgumentIdentifier], "indent", "head-argument1", 0), ([ArgumentIdentifier, EmptyTypeError], "indent", "head-argument3", 2), ([ArgumentIdentifier, ArgumentTypeIdentifier], "indent", "head-argument7", 0), ([ArgumentIdentifier, ArgumentTypeIdentifier], "indent", "head-argument10", 0), ([ArgumentIdentifier], "indent", "head-argument14", 0)),
        P("item-body", ([], "line", "item-body0", 2), ([], "line", "item-body1", 2), ([], "line", "newline", 2), ([], "word", "line", 2), ([], "word", "noqa-maybe", 2), ([NoqaIdentifier], "hash", "noqa", 2), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 2), (TokenType.INDENT, 2), (TokenType.COLON, 2), (TokenType.HASH, 2), (TokenType.LPAREN, 2), (TokenType.RPAREN, 2), (TokenType.WORD, 2), (TokenType.RAISES, 2), (TokenType.ARGUMENTS, 2), (TokenType.ARGUMENT_TYPE, 2), (TokenType.RETURNS, 2), (TokenType.RETURN_TYPE, 2), (TokenType.YIELDS, 2), (TokenType.YIELD_TYPE, 2), (TokenType.VARIABLES, 2), (TokenType.VARIABLE_TYPE, 2), (TokenType.NOQA, 2), (TokenType.OTHER, 2), (TokenType.RECEIVES, 2), (TokenType.WARNS, 2), (TokenType.SEE, 2), (TokenType.ALSO, 2), (TokenType.NOTES, 2), (TokenType.EXAMPLES, 2), (TokenType.REFERENCES, 2), (TokenType.HEADER, 2), ([IndentError], "line", "item-body4", 0), ([IndentError], "line", "item-body6", 0)),
        P("paragraph-indented-two", ([], "indented-two", "paragraph-indented-two0", 0), ([], "indented-two", "line", 0)),
        P("paragraph", ([], "indents", "paragraph0", 0), ([], "indents", "line", 0), ([], "line", "paragraph2", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0), ([], "line", "paragraph1", 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("indented-two", ([], "indent", "indented-two0", 0)),
        P("indents", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("word", (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("ident", (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0)),
        P("arguments", (TokenType.ARGUMENTS, 0)),
        P("colon", (TokenType.COLON, 0)),
        P("hash", (TokenType.HASH, 0)),
        P("indent", (TokenType.INDENT, 0)),
        P("lparen", (TokenType.LPAREN, 0)),
        P("newline", (TokenType.NEWLINE, 0)),
        P("rparen", (TokenType.RPAREN, 0)),
        P("noqa", (TokenType.NOQA, 0)),
        P("noqa-maybe", ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0)),
        P("noqa-head", ([], "hash", "noqa", 0)),
        P("words", ([], "word", "words", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.HEADER, 0)),
        P("type-section-parens", ([], "lparen", "type-section-parens0", 0)),
        P("type-words-colon", ([], "type-word-colon", "type-words-colon", 0), ([], "type-word-colon", "type-words-colon0", 0), ([ParameterMalformedError], "malformed-type-word", "malformed-type-words", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.COLON, 0), (TokenType.INDENT, 0)),
        P("type-word-colon", (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.COLON, 0), (TokenType.INDENT, 0)),
        P("malformed-type-words", ([], "malformed-type-word", "malformed-type-words", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0)),
        P("malformed-type-word", (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0)),
        P("arguments-section1", ([], "colon", "arguments-section2", 0)),
        P("arguments-section2", ([], "newline", "arguments-section3", 0)),
        P("arguments-section3", ([], "items-argument", "newlines", 0), ([], "item-argument", "items-argument0", 0), ([ArgumentItemIdentifier], "head-argument", "item-body", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument1", 0), ([ArgumentIdentifier, EmptyTypeError, EmptyDescriptionError], "indent", "head-argument3", 2), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument7", 0), ([ArgumentIdentifier, ArgumentTypeIdentifier, EmptyDescriptionError], "indent", "head-argument10", 0), ([ArgumentIdentifier, EmptyDescriptionError], "indent", "head-argument14", 0)),
        P("items-argument0", ([], "newline", "items-argument", 0)),
        P("head-argument1", ([], "ident", "colon", 0)),
        P("head-argument3", ([], "ident", "head-argument4", 0)),
        P("head-argument4", ([], "lparen", "head-argument5", 0)),
        P("head-argument5", ([], "rparen", "colon", 0)),
        P("head-argument7", ([], "ident", "head-argument8", 0)),
        P("head-argument8", ([], "type-section-parens", "colon", 0)),
        P("head-argument10", ([], "ident", "head-argument11", 0)),
        P("head-argument11", ([], "type-section-parens", "head-argument12", 0)),
        P("head-argument12", ([], "colon", "newline", 0)),
        P("head-argument14", ([], "ident", "head-argument15", 0)),
        P("head-argument15", ([], "colon", "newline", 0)),
        P("item-body0", ([], "newline", "paragraph-indented-two", 0)),
        P("item-body1", ([], "newline", "item-body2", 0)),
        P("item-body2", ([], "paragraph-indented-two", "newline", 0)),
        P("item-body4", ([], "newline", "paragraph", 0)),
        P("item-body6", ([], "newline", "item-body7", 0)),
        P("item-body7", ([], "paragraph", "newline", 0)),
        P("paragraph-indented-two0", ([], "line", "paragraph-indented-two1", 0)),
        P("paragraph-indented-two1", ([], "newline", "paragraph-indented-two", 0)),
        P("paragraph0", ([], "line", "paragraph1", 0)),
        P("paragraph1", ([], "newline", "paragraph", 0)),
        P("paragraph2", ([], "newline", "paragraph", 0)),
        P("indented-two0", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
        P("type-section-parens0", ([], "type-words-colon", "rparen", 0), (TokenType.RPAREN, 0)),
        P("type-words-colon0", ([], "newline", "type-words-colon1", 0), (TokenType.NEWLINE, 0)),
        P("type-words-colon1", ([], "indents", "type-words-colon", 0), ([], "indent", "indents", 0), (TokenType.INDENT, 0), ([], "type-word-colon", "type-words-colon", 0), ([], "type-word-colon", "type-words-colon0", 0), ([ParameterMalformedError], "malformed-type-word", "malformed-type-words", 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), (TokenType.OTHER, 0), (TokenType.RECEIVES, 0), (TokenType.WARNS, 0), (TokenType.SEE, 0), (TokenType.ALSO, 0), (TokenType.NOTES, 0), (TokenType.EXAMPLES, 0), (TokenType.REFERENCES, 0), (TokenType.COLON, 0)),
    ]
    start = "arguments-section"