from unittest import (
    TestCase,
)
from darglint.parse.grammar import (
    BaseGrammar,
)
from darglint.parse.combinator import (
    parser_combinator,
)
from darglint.parse.cyk import (
    parse,
)
from darglint.node import (
    CykNode,
)
from darglint.parse.grammar import Production as P
from darglint.token import (
    BaseTokenType,
    Token,
)


class PoetryTokenType(BaseTokenType):

    WORD = 1
    NEWLINE = 2


# This grammar requires that a poem end in a newline.
class TotalPoetryGrammar(BaseGrammar):

    productions = [
        P('word', (PoetryTokenType.WORD, 0)),
        P('newline', (PoetryTokenType.NEWLINE, 0)),
        P('line',
            ([], 'word', 'newline', 0),
            ([], 'word', 'line', 0)),
        P('stanza',
            ([], 'line', 'newline', 0),
            ([], 'line', 'stanza', 0)),
        P('poem',
            # A single-stanza poem.
            ([], 'line', 'stanza', 0),
            # A multi-stanza poem.
            ([], 'stanza', 'stanza', 0))
    ]

    start = 'poem'


class StanzaGrammar(BaseGrammar):

    productions = [
        P('word', (PoetryTokenType.WORD, 0)),
        P('newline', (PoetryTokenType.NEWLINE, 0)),
        P('line', ([], 'word', 'newline', 0), ([], 'word', 'line', 0)),
        P('stanza', ([], 'line', 'newline', 0), ([], 'line', 'stanza', 0)),
    ]

    start = 'stanza'


def combine(*nodes, encountered=False):
    if len(nodes) == 1:
        if not encountered:
            n = nodes[0]
            n.symbol = 'poem'
            return n
        else:
            return nodes[0]
    else:
        return CykNode(
            symbol='poem',
            lchild=nodes[0],
            rchild=combine(*nodes[1:], encountered=True)
        )


def lex(poem):
    tokens = list()
    word = ''
    i = 0
    for letter in poem:
        if letter == '\n':
            if word:
                tokens.append(Token(
                    value=word,
                    token_type=PoetryTokenType.WORD,
                    line_number=i,
                ))
            word = ''
            tokens.append(Token(
                value='\n',
                token_type=PoetryTokenType.NEWLINE,
                line_number=i,
            ))
            i += 1
        elif letter.isspace():
            if word:
                tokens.append(Token(
                    value=word,
                    token_type=PoetryTokenType.WORD,
                    line_number=i,
                ))
            word = ''
        else:
            word += letter
    if word:
        tokens.append(Token(
            value=word,
            token_type=PoetryTokenType.WORD,
            line_number=i,
        ))
    return tokens


def lookup(*args):
    return [lambda x: parse(StanzaGrammar, x)]


def top_parse(tokens):
    ret = list()
    curr = list()
    for token in tokens:
        curr.append(token)
        if len(curr) > 1:
            if (
                curr[-1].token_type == PoetryTokenType.NEWLINE
                and curr[-2].token_type == PoetryTokenType.NEWLINE
            ):
                ret.append(curr)
                curr = list()
    if curr:
        ret.append(curr)
    return ret


poems = [
    'Roly poly\nSomething holey\n\nIn and out\nAnd round about.\n\n',
    'In the braken brambles\nHides a scruffy vagrant\n'
    'Wearied out from shambles\n\n',
    'A\n\nC\n\n',
]


class ParserCombinatorTests(TestCase):

    def test_total_grammar(self):
        for poem in poems:
            tokens = lex(poem)
            parsed = parse(TotalPoetryGrammar, tokens)
            self.assertTrue(parsed is not None)

    def test_equivalent_to_combined(self):
        for poem in poems:
            tokens = lex(poem)
            total = parse(TotalPoetryGrammar, tokens)
            combined = parser_combinator(
                top_parse,
                lookup,
                combine,
                tokens,
            )
            self.assertTrue(
                total.equals(combined),
            )
