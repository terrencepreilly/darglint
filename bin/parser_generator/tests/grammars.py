"""Defines some grammars useful for testing."""

from dataclasses import (dataclass, field)
import enum
from typing import (List, Optional, Union)


ONE_TOKEN_GRAMMAR = r'''
Grammar: OneTokenGrammar

start: <one>

<one> ::= "TokenType\.ONE"
'''

BINARY_GRAMMAR = r'''
Grammar: BinaryGrammar

start: <number>

<number>
    ::= <zero> <number>
    | <one> <number>
    | ε

<one> ::= "TokenType\.ONE"
<zero> ::= "TokenType\.ZERO"
'''


class TokenType(enum.Enum):
    ONE = "1"
    ZERO = "0"


@dataclass
class Token:
    token_type: TokenType
    value: str


@dataclass
class Node:
    node_type: Union[str, TokenType]
    value: Optional[Token] = None
    children: List['Node'] = field(default_factory=list)

    def __str__(self, indent: int = 0) -> str:
        ret = f'<Node {self.node_type}'
        if self.value is not None:
            ret += f' {self.value}'
        for child in self.children:
            ret += f'\n{" " * indent}{child.__str__(indent=indent + 2)}'
        ret += '>'
        return ret


def lex(contents):
    for char in contents:
        if char == '1':
            yield Token(TokenType.ONE, '1')
        elif char == '0':
            yield Token(TokenType.ZERO, '0')
        else:
            raise Exception(f'Unrecognized token "{char}"')
