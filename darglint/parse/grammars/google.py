from darglint.parse.grammar import BaseGrammar
from darglint.parse.grammar import Production as P
from darglint.token import TokenType

# Generated on 2019-05-26 21:30:21.231252
class Grammar(BaseGrammar):
    productions = [
        P("start", ([], "short-description", "docstring0"), ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("sections", ([], "split", "sections0"), ([], "split", "sections1"), ([], "split", "sections2")),
        P("short-description", ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("long-description", ([], "paragraph", "block0"), ([], "line", "paragraph0"), ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("returns-section", ([], "returns", "returns-section0")),
        P("yields-section", ([], "yields", "yields-section0")),
        P("block-indented", ([], "paragraph-indented", "block-indented0"), ([], "indented", "paragraph-indented0"), ([], "indented", "line")),
        P("block", ([], "paragraph", "block0"), ([], "line", "paragraph0"), ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("paragraph-indented", ([], "indented", "paragraph-indented0"), ([], "indented", "line")),
        P("paragraph", ([], "line", "paragraph0"), ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("line", ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("indented", ([], "indent", "indents"), TokenType.INDENT),
        P("indents", ([], "indent", "indents"), TokenType.INDENT),
        P("split", ([], "newline", "split0")),
        P("newlines", ([], "newline", "newlines"), TokenType.NEWLINE),
        P("returns", TokenType.RETURNS),
        P("yields", TokenType.YIELDS),
        P("colon", TokenType.COLON),
        P("word", TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN),
        P("indent", TokenType.INDENT),
        P("newline", TokenType.NEWLINE),
        P("docstring0", ([], "sections", "newlines"), ([], "split", "sections0"), ([], "split", "sections1"), ([], "split", "sections2"), ([], "newline", "newlines"), TokenType.NEWLINE),
        P("sections0", ([], "long-description", "sections"), ([], "paragraph", "block0"), ([], "line", "paragraph0"), ([], "word", "line"), TokenType.WORD, TokenType.RETURNS, TokenType.COLON, TokenType.LPAREN, TokenType.RPAREN, TokenType.INDENT),
        P("sections1", ([], "returns-section", "sections"), ([], "returns", "returns-section0")),
        P("sections2", ([], "yields-section", "sections"), ([], "yields", "yields-section0")),
        P("returns-section0", ([], "colon", "returns-section1")),
        P("returns-section1", ([], "newline", "block-indented")),
        P("yields-section0", ([], "colon", "yields-section1")),
        P("yields-section1", ([], "newline", "block-indented")),
        P("block-indented0", ([], "split", "block-indented")),
        P("block0", ([], "split", "block")),
        P("paragraph-indented0", ([], "line", "paragraph-indented1")),
        P("paragraph-indented1", ([], "newline", "paragraph-indented")),
        P("paragraph0", ([], "newline", "paragraph")),
        P("split0", ([], "newline", "newlines"), TokenType.NEWLINE),
    ]

    start = "start"