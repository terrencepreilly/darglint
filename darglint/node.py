from collections import (
    deque,
)
from typing import (
    Any,
    Iterator,
    Optional,
    List,
    Tuple,
)

from .token import (
    Token,
    TokenType,
)

WHITESPACE = {TokenType.INDENT, TokenType.NEWLINE}


# A best guess at the maximum height of a docstring tree,
# for use in recursion bounds checking.
MAX_TREE_HEIGHT = 300


class CykNode(object):
    """A node for use in a cyk parse."""

    def __init__(self,
                 symbol,
                 lchild=None,
                 rchild=None,
                 value=None,
                 annotations=list(),
                 weight=0):
        # type: (str, Optional[CykNode], Optional[CykNode], Optional[Token], List[Any], int) -> None  # noqa: E501
        self.symbol = symbol
        self.lchild = lchild
        self.rchild = rchild
        self.value = value
        self.annotations = annotations
        self._line_number_cache = None  # type: Optional[Tuple[int, int]]

        # If there is an explicit weight, we definitely want to use
        # that (there was probably a good reason it was given.)
        #
        # If no weight was given, but the children have weights, then
        # we probably want to give preference to this node over a node
        # which has no weights at all.
        if weight:
            self.weight = weight
        else:
            self.weight = max([
                0,
                self.lchild.weight if self.lchild else 0,
                self.rchild.weight if self.rchild else 0,
            ])

    def __repr__(self):
        if hasattr(self.value, 'token_type'):
            return '<{}: {}>'.format(
                self.symbol,
                str(self.value.token_type)[10:] if self.value else '',
            )
        return '<{}>'.format(self.value)

    def __str__(self, indent=0):
        if self.value:
            ret = (
                ' ' * indent
                + str(self.value.token_type)
                + ': '
                + repr(self.value.value)
            )
        else:
            ret = ' ' * indent + self.symbol
        if self.annotations:
            ret += ': ' + ', '.join([str(x) for x in self.annotations])
        if self.lchild:
            ret += '\n' + self.lchild.__str__(indent + 2)
        if self.rchild:
            ret += '\n' + self.rchild.__str__(indent + 2)
        return ret

    def in_order_traverse(self):
        if self.lchild:
            yield from self.lchild.in_order_traverse()
        yield self
        if self.rchild:
            yield from self.rchild.in_order_traverse()

    def breadth_first_walk(self):
        queue = deque([self])
        while queue:
            curr = queue.pop()
            yield curr
            if curr.lchild:
                queue.appendleft(curr.lchild)
            if curr.rchild:
                queue.appendleft(curr.rchild)

    def first_instance(self, symbol):
        # type: (str) -> Optional['CykNode']
        for node in self.breadth_first_walk():
            if node.symbol == symbol:
                return node
        return None

    def walk(self):
        # type: () -> Iterator['CykNode']
        yield from self.in_order_traverse()

    def equals(self, other):
        # type: (Optional['CykNode']) -> bool
        if other is None:
            return False
        if self.symbol != other.symbol:
            return False
        if self.value != other.value:
            return False
        if self.lchild and not self.lchild.equals(other.lchild):
            return False
        if self.rchild and not self.rchild.equals(other.rchild):
            return False
        return True

    def reconstruct_string(self, strictness=0):
        # type: (int) -> str
        """Reconstruct the docstring.

        This method should rebuild the docstring while fixing style
        errors.  The errors themselves determine how to fix the node
        they apply to.  (If there isn't a good fix, then it's just the
        identity function.)

        Args:
            strictness: How strictly we should correct.  If an error
                doesn't match the strictness, we won't correct for
                that error.

        Returns:
            The docstring, reconstructed.

        """
        # In order to make a reasonable guess as to the whitespace
        # to apply between characters, we use a 3-token sliding
        # window.
        window_size = 3
        window = deque(maxlen=window_size)  # type: deque
        source = self.in_order_traverse()

        # Fill the buffer.
        while len(window) < window_size:
            try:
                node = next(source)
            except StopIteration:
                break
            if node.value:
                window.append(node.value)

        if not window:
            return ''

        ret = window[0].value

        # Slide the window, filling the return value.
        while len(window) > 1:
            is_whitespace = (
                window[0].token_type in WHITESPACE
                or window[1].token_type in WHITESPACE
            )
            is_colon = window[1].token_type == TokenType.COLON
            if is_whitespace or is_colon:
                ret += window[1].value
            else:
                ret += ' ' + window[1].value

            found_token = False
            for node in source:
                if node.value:
                    window.append(node.value)
                    found_token = True
                    break
            if not found_token:
                break

        if len(window) == 3:
            if (window[1].token_type in WHITESPACE
                    or window[2].token_type in WHITESPACE
                    or window[2].token_type == TokenType.COLON):
                ret += window[2].value
            else:
                ret += ' ' + window[2].value

        return ret

    def _get_line_numbers_cached(self, recurse=0):
        # type: (int) -> Tuple[int, int]
        if recurse > MAX_TREE_HEIGHT:
            return (-1, -1)
        if self.value:
            return (self.value.line_number, self.value.line_number)
        elif self._line_number_cache:
            return self._line_number_cache
        leftmost = -1
        if self.lchild:
            leftmost = self.lchild._get_line_numbers_cached(recurse + 1)[0]
        rightmost = leftmost
        if self.rchild:
            rightmost = self.rchild._get_line_numbers_cached(recurse + 1)[1]
        self._line_number_cache = (leftmost, rightmost)
        return self._line_number_cache or (-1, -1)

    @property
    def line_numbers(self):
        # type: () -> Tuple[int, int]
        return self._get_line_numbers_cached()
