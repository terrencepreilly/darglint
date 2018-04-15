"""Describes Peaker, a stream transformer for peaking ahead."""
from collections import deque

from typing import (
    Callable,
    Generic,
    Iterator,
    List,
    TypeVar,
    Union,
    Deque
)


T = TypeVar('T')


class Peaker(Generic[T]):
    """A stream transformer allowing us to peak ahead."""

    class _Empty(object):
        value = None

    def __init__(self, stream, lookahead=1):
        # type: (Iterator[T], int) -> None
        """Create a new peaker.

        Args:
            stream: An iterator of T objects, which may be empty.
            lookahead: The amount of lookahead this should allow
                in the stream.

        """
        self.stream = stream
        self.buffer = deque() # type: Deque[T]
        self.lookahead = lookahead
        self._buffer_to(lookahead)

    def _buffer_to(self, amount):
        """Extend the internal buffer to the given amount.

        Only adds items up to that amount, and while there
        are items to add.

        Args:
            amount: The length to make the buffer.
        
        """
        if amount > self.lookahead:
            raise Exception(
                'Cannot extend buffer to {}: beyond buffer lookahead {}'.format(
                    amount, self.lookahead
                )
            )
        while len(self.buffer) < amount:
            try:
                self.buffer.appendleft(next(self.stream))
            except StopIteration:
                break

    def next(self):
        # type: () -> T
        """Get the next item in the stream, moving it forward.

        Side effects:
            Moves the stream forward.

        Raises:
            StopIteration: If there are no more items in the stream.

        Returns:
            The next item of type T in the stream.

        """
        if len(self.buffer) == 0:
            raise StopIteration
        previous = self.buffer.pop()
        self._buffer_to(self.lookahead)
        return previous

    def peak(self, lookahead=1):
        # type: (int) -> T
        """Get the next letter in the stream, without moving it forward.

        Args:
            lookahead: The amount of tokens to look ahead in
                the buffer.

        Returns:
            The next item of type T in the stream.

        """
        if lookahead > self.lookahead:
            raise Exception(
                'Cannot peak to {}: beyond buffer lookahead {}'.format(
                    lookahead, self.lookahead
                )
            )
        if lookahead > len(self.buffer):
            return None
        index = len(self.buffer) - lookahead
        return self.buffer[index]

    def has_next(self):
        # type: () -> bool
        """Tell whether there are more tokens in the stream.

        Returns:
            True if there are more tokens, false otherwise.

        """
        return len(self.buffer) > 0

    def take_while(self, test):
        # type: (Callable) -> List[T]
        """Return elements from the stream while they pass the test.

        Args:
            test: A function which returns true if we would like to collect
                the token, or false if we would like to stop.

        Returns:
            A list of items (of type T), which pass the given test function.

        """
        passing_elements = [] # type: List[T]
        while self.has_next() and test(self.peak()):
            passing_elements.append(self.next())
        return passing_elements
