# Generated on 2019-10-19 16:36:02.659285

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
        P("items-argument", ([], "item-argument", "items-argument0", 0), ([ArgumentItemIdentifier], "head-argument", "item-argument1", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument4", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument8", 2), ([ArgumentItemIdentifier], "head-argument", "line", 2), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument11", 0), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument14", 0)),
        P("item-argument", ([ArgumentItemIdentifier], "head-argument", "item-argument1", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument4", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument8", 2), ([ArgumentItemIdentifier], "head-argument", "line", 2), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument11", 0), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument14", 0)),
        P("head-argument", ([ArgumentIdentifier], "indent", "head-argument1", 0), ([ArgumentIdentifier, ArgumentTypeIdentifier], "indent", "head-argument3", 0)),
        P("paragraph-indented-two", ([], "indented-two", "paragraph-indented-two0", 0), ([], "indented-two", "line", 0)),
        P("paragraph", ([], "indents", "paragraph0", 0), ([], "indents", "line", 0), ([], "line", "paragraph2", 0), ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0), ([], "line", "paragraph1", 0)),
        P("line", ([], "word", "line", 0), ([], "word", "noqa-maybe", 0), ([NoqaIdentifier], "hash", "noqa", 0), ([NoqaIdentifier], "noqa-head", "noqa-statement1", 0), (TokenType.INDENT, 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0)),
        P("indented-two", ([], "indent", "indented-two0", 0)),
        P("indents", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("newlines", ([], "newline", "newlines", 0), (TokenType.NEWLINE, 0)),
        P("word", (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0)),
        P("ident", (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0)),
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
        P("words", ([], "word", "words", 0), (TokenType.COLON, 0), (TokenType.HASH, 0), (TokenType.INDENT, 0), (TokenType.LPAREN, 0), (TokenType.RPAREN, 0), (TokenType.WORD, 0), (TokenType.RAISES, 0), (TokenType.ARGUMENTS, 0), (TokenType.ARGUMENT_TYPE, 0), (TokenType.RETURNS, 0), (TokenType.RETURN_TYPE, 0), (TokenType.YIELDS, 0), (TokenType.YIELD_TYPE, 0), (TokenType.VARIABLES, 0), (TokenType.VARIABLE_TYPE, 0), (TokenType.NOQA, 0)),
        P("type-section-parens", ([], "lparen", "type-section-parens0", 0)),
        P("type-words-colon", ([], "type-word-colon", "type-words-colon", 0), ([], "type-word-colon", "type-words-colon0", 0), (TokenType.WORD, 0), (TokenType.COLON, 0), (TokenType.INDENT, 0)),
        P("type-word-colon", (TokenType.WORD, 0), (TokenType.COLON, 0), (TokenType.INDENT, 0)),
        P("arguments-section1", ([], "colon", "arguments-section2", 0)),
        P("arguments-section2", ([], "newline", "arguments-section3", 0)),
        P("arguments-section3", ([], "items-argument", "newlines", 0), ([], "item-argument", "items-argument0", 0), ([ArgumentItemIdentifier], "head-argument", "item-argument1", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument4", 2), ([ArgumentItemIdentifier], "head-argument", "item-argument8", 2), ([ArgumentItemIdentifier], "head-argument", "line", 2), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument11", 0), ([IndentError, ArgumentItemIdentifier], "head-argument", "item-argument14", 0)),
        P("items-argument0", ([], "newline", "items-argument", 0)),
        P("item-argument1", ([], "line", "item-argument2", 0)),
        P("item-argument2", ([], "newline", "paragraph-indented-two", 0)),
        P("item-argument4", ([], "line", "item-argument5", 0)),
        P("item-argument5", ([], "newline", "item-argument6", 0)),
        P("item-argument6", ([], "paragraph-indented-two", "newline", 0)),
        P("item-argument8", ([], "line", "newline", 0)),
        P("item-argument11", ([], "line", "item-argument12", 0)),
        P("item-argument12", ([], "newline", "paragraph", 0)),
        P("item-argument14", ([], "line", "item-argument15", 0)),
        P("item-argument15", ([], "newline", "item-argument16", 0)),
        P("item-argument16", ([], "paragraph", "newline", 0)),
        P("head-argument1", ([], "ident", "colon", 0)),
        P("head-argument3", ([], "ident", "head-argument4", 0)),
        P("head-argument4", ([], "type-section-parens", "colon", 0)),
        P("paragraph-indented-two0", ([], "line", "paragraph-indented-two1", 0)),
        P("paragraph-indented-two1", ([], "newline", "paragraph-indented-two", 0)),
        P("paragraph0", ([], "line", "paragraph1", 0)),
        P("paragraph1", ([], "newline", "paragraph", 0)),
        P("paragraph2", ([], "newline", "paragraph", 0)),
        P("indented-two0", ([], "indent", "indents", 0), (TokenType.INDENT, 0)),
        P("noqa-statement1", ([], "colon", "words", 0)),
        P("type-section-parens0", ([], "type-words-colon", "rparen", 0), (TokenType.RPAREN, 0)),
        P("type-words-colon0", ([], "newline", "type-words-colon1", 0), (TokenType.NEWLINE, 0)),
        P("type-words-colon1", ([], "indents", "type-words-colon", 0), ([], "indent", "indents", 0), (TokenType.INDENT, 0), ([], "type-word-colon", "type-words-colon", 0), ([], "type-word-colon", "type-words-colon0", 0), (TokenType.WORD, 0), (TokenType.COLON, 0)),
    ]
    start = "arguments-section"