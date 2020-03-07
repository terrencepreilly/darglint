"""Defines the tokens that result from lexing, as well as their types."""

from enum import Enum


class BaseTokenType(Enum):
    pass


class TokenType(BaseTokenType):
    """The possible types of tokens."""

    WORD = 1
    COLON = 2
    DOCTERM = 3  # """
    NEWLINE = 4
    INDENT = 5  # Assumed to always be 4 spaces
    HASH = 6  # A hash mark (for comments/noqa).
    LPAREN = 7  # (
    RPAREN = 8  # )

    RETURNS = 9
    YIELDS = 10
    RAISES = 11
    ARGUMENTS = 12
    NOQA = 13
    RETURN_TYPE = 14
    YIELD_TYPE = 15
    VARIABLES = 16
    VARIABLE_TYPE = 17
    ARGUMENT_TYPE = 18
    HEADER = 19
    OTHER = 20
    RECEIVES = 21
    WARNS = 22
    SEE = 23
    ALSO = 24
    NOTES = 25
    EXAMPLES = 26
    REFERENCES = 27

    # next: 28


KEYWORDS = {
    TokenType.RETURNS,
    TokenType.YIELDS,
    TokenType.RAISES,
    TokenType.ARGUMENTS,
    TokenType.NOQA,
    TokenType.RETURN_TYPE,
    TokenType.YIELD_TYPE,
    TokenType.VARIABLES,
    TokenType.VARIABLE_TYPE,
    TokenType.ARGUMENT_TYPE,
    TokenType.RECEIVES,
    TokenType.WARNS,
    TokenType.NOTES,
    TokenType.EXAMPLES,
    TokenType.REFERENCES,
}


class Token(object):
    """A token representing anything which can appear in a docstring."""

    def __init__(self,
                 value: str,
                 token_type: TokenType,
                 line_number: int
                 ) -> None:
        """Create a new Token.

        Args:
            value: The value of the token. (The actual string.)
            token_type: The type of token this represents.
            line_number: The line number where this token resides.
                Used when reporting errors.

        """
        self.value = value
        self.token_type = token_type
        self.line_number = line_number

    def __str__(self):
        """Return readable representation for debugging.

        Returns:
            A readable representation for debugging.

        """
        return '<Token {} {}>'.format(repr(self.value), self.token_type)

    def __repr__(self):
        """Return readable representation for debugging.

        Returns:
            A readable representation for debugging.

        """
        return str(self)
