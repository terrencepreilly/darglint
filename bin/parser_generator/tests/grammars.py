"""Defines some grammars useful for testing."""

from dataclasses import dataclass
import enum
from typing import (Union, Optional)


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
    value: Optional[Token]


def lex(contents):
    for char in contents:
        if char == '1':
            yield Token(TokenType.ONE, '1')
        elif char == '0':
            yield Token(TokenType.ZERO, '0')
        else:
            raise Exception(f'Unrecognized token "{char}"')
