"""Defines some grammars useful for testing."""

from dataclasses import dataclass


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


@dataclass
class Token:
    token_type: str
    value: str


def lex(contents):
    for char in contents:
        if char == '1':
            yield Token('TokenType.ONE', '1')
        elif char == '0':
            yield Token('TokenType.ZERO', '0')
        else:
            raise Exception(f'Unrecognized token "{char}"')
