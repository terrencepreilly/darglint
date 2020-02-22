from typing import (
    List,
    Optional,
)
from functools import (
    reduce,
)
from ..token import (
    Token,
    TokenType,
)
from ..node import (
    CykNode,
)
from ..peaker import (
    Peaker,
)
from .identifiers import (
    NoqaIdentifier,
)


def _is(peaker, token_type, index=1):
    # type: (Peaker[Token], Optional[TokenType], int) -> bool
    try:
        token = peaker.peak(lookahead=index)
    except IndexError:
        token = None
    if not token_type and not token:
        return True
    return bool(token and token.token_type == token_type)


def _are(peaker, *token_types):
    # type: (Peaker[Token], Optional[TokenType]) -> bool
    return all([
        _is(peaker, token_type, i + 1)
        for i, token_type in enumerate(token_types)
    ])


def _parse_noqa_head(peaker):
    # type: (Peaker[Token]) -> Optional[CykNode]
    if not (
        _are(peaker, TokenType.HASH, TokenType.NOQA, TokenType.NEWLINE)
        or _are(peaker, TokenType.HASH, TokenType.NOQA, None)
    ):
        return None
    noqa_hash = CykNode('hash', value=peaker.next())
    noqa = CykNode('noqa', value=peaker.next())
    if _is(peaker, TokenType.NEWLINE):
        peaker.next()
    return CykNode(
        'noqa',
        lchild=noqa_hash,
        rchild=noqa,
        annotations=[
            NoqaIdentifier,
        ],
    )


def _last_node(node):
    # type: (CykNode) -> CykNode
    curr = node
    rchild = curr.rchild
    while rchild:
        curr = rchild
        rchild = curr.rchild
    return curr


def foldr(fun, xs, acc):
    return reduce(lambda x, y: fun(y, x), xs[::-1], acc)


def _parse_words_until_newline_or_end(peaker):
    if not peaker.has_next() or _is(peaker, TokenType.NEWLINE):
        return None
    words = [CykNode('word', value=peaker.next())]
    while peaker.has_next() and not _is(peaker, TokenType.NEWLINE):
        words.append(CykNode('word', value=peaker.next()))

    if len(words) == 1:
        head = words[0]
        head.symbol = 'words'
        return head

    def join(x, y):
        return CykNode(
            'words',
            lchild=x,
            rchild=y,
        )

    acc = words.pop()
    acc.symbol = 'words'

    return foldr(join, words, acc)


def _parse_noqa(peaker):
    # type: (Peaker[Token]) -> Optional[CykNode]
    if not (
        _are(peaker, TokenType.HASH, TokenType.NOQA, TokenType.COLON,
             TokenType.WORD)
    ):
        return None
    noqa_hash = CykNode('hash', value=peaker.next())
    noqa = CykNode('noqa', value=peaker.next())
    colon = CykNode('colon', value=peaker.next())
    targets = _parse_words_until_newline_or_end(peaker)
    head = CykNode(
        'noqa',
        lchild=CykNode(
            'noqa-head',
            lchild=noqa_hash,
            rchild=noqa,
        ),
        rchild=CykNode(
            'noqa-statement1',
            lchild=colon,
            rchild=targets,
        ),
        annotations=[
            NoqaIdentifier,
        ],
    )
    return head


def _parse_long_description(peaker):
    # type: (Peaker[Token]) -> Optional[CykNode]
    if not peaker.has_next():
        return None
    head = _parse_noqa(peaker) or _parse_noqa_head(peaker)
    if head:
        new_head = CykNode(
            'long-description',
            lchild=head,
        )
        head = new_head
    else:
        head = CykNode(
            symbol='long-description',
            lchild=CykNode('long-description1', value=peaker.next()),
        )
    curr = _last_node(head)
    while peaker.has_next():
        noqa = _parse_noqa(peaker) or _parse_noqa_head(peaker)
        if not noqa:  # curr.rchild:
            curr.rchild = CykNode(
                symbol='long-description1',
                lchild=CykNode('long-description1', value=peaker.next()),
            )
        else:
            old_left = curr.lchild
            curr.lchild = CykNode(
                symbol='long-description1',
                lchild=old_left,
                rchild=noqa,
            )
        curr = _last_node(curr)
    return head


def parse(tokens):
    # type: (List[Token]) -> Optional[CykNode]
    peaker = Peaker((x for x in tokens), lookahead=5)
    if not peaker.has_next():
        return None

    return _parse_long_description(peaker)
