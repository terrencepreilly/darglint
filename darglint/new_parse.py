r"""
__EBNF for a google-style docstring__:

  <docstring> ::= <docterm><short-description><docterm>
                | <docterm><short-description><newline>
                    <long-description>*
                    <section>*
                  <docterm>

  <short-description> ::= <word>[<word><colon><keyword>]*
  <long-description>  ::= <head-line>+
  <head-line> ::= <indent>
                    [<word><colon><indent>]
                    [<word><colon><indent><keyword>]*<newline>
  <section> ::= <indent><keyword><colon><newline>
                (<indent><line>)+
              | <indent><keyword><colon><newline>
                    <indent>{2}<word><type>?<colon>
                    [<word><colon><keyword>]*<newline>
                    (<indent>{2}<line>)*
  <line> ::= <indent>
                [<word><colon><indent><keyword>]*<newline>
  <type> ::= "(" <word> ")"

  <keyword> ::= "Args"
            | "Arguments"
            | "Returns
            | "Yields"
            | "Raises"
  <indent>  ::= " "{4}
  <docterm> ::= \"\"\"
  <word>    ::= [^\ \n\:\"\#\t]+
  <colon>   ::= ":"
  <newline> ::= "\n"

"""

from .parse import ParserException
from .peaker import Peaker
from .token import Token, TokenType
from .node import Node, NodeType

KEYWORDS = {
    'Args': NodeType.ARGUMENTS,
    'Arguments': NodeType.ARGUMENTS,
    'Returns': NodeType.RETURNS,
    'Yields': NodeType.YIELDS,
    'Raises': NodeType.RAISES,
}


def parse_keyword(peaker):
    # type: (Peaker[Token]) -> Node
    """Parse a keyword.

    Args:
        peaker: A stream of tokens from lexing a docstring.

    Returns:
        A Node with Keyword NodeType.
    
    """
    is_empty = not peaker.has_next()
    if is_empty:
        raise ParserException('Unable to parse keyword: stream is empty.')

    isnt_word = peaker.peak().token_type != TokenType.WORD
    if isnt_word:
        raise ParserException(
            'Unable to parse keyword: expected {} but '
            'received {}.'.format(TokenType.WORD, peaker.peak().token_type)
        )

    isnt_keyword = peaker.peak().value not in KEYWORDS
    if isnt_keyword:
        raise ParserException(
            'Unable to parse keyword: "{}" is not a keyword.'.format(
                peaker.peak().value
            )
        )
    token = peaker.next()
    return Node(KEYWORDS[token.value], value=token.value)

def parse_indent(peaker):
    # type: (Peaker[Token]) -> Node
    is_empty = not peaker.has_next()
    if is_empty:
        raise ParserException('Unable to parse indent: stream is empty.')

    isnt_indent = peaker.peak().token_type != TokenType.INDENT
    if isnt_indent:
        raise ParserException(
            'Unable to parse indent: expected {} but received {}'.format(
                TokenType.INDENT, peaker.peak().token_type
            )
        )
    token = peaker.next()
    return Node(NodeType.INDENT, value=token.value)
