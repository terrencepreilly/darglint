"""Describes Peaker, a stream transformer for peaking ahead."""

from typing import (
    Callable,
    Generic,
    Iterator,
    List,
    TypeVar,
)


T = TypeVar('T')


class Peaker(Generic[T]):
    """A stream transformer allowing us to peak ahead."""

    class _Empty(object):
        pass

    def __init__(self, stream: Iterator[T]):
        """Create a new peaker.

        Args:
            stream: An iterator of T objects, which may be empty.

        """
        self.stream = stream
        try:
            self.current = next(stream)
        except StopIteration:
            self.current = self._Empty()

    def next(self) -> T:
        """Get the next letter in the stream, moving it forward."""
        if not self.has_next():
            raise StopIteration
        previous = self.current
        try:
            self.current = next(self.stream)
        except StopIteration:
            self.current = self._Empty()
        return previous

    def peak(self) -> T:
        """Get the next letter in the stream, without moving it forward."""
        if isinstance(self.current, self._Empty):
            return None
        return self.current

    def has_next(self) -> bool:
        """Return true if there are more tokens in the stream."""
        return not isinstance(self.current, self._Empty)

    def take_while(self, test: Callable) -> List[T]:
        """Return elements from the stream while they pass the test.

        Args:
            test: A function which returns true if we would like to collect
                the token, or false if we would like to stop.
        """
        passing_elements = []
        while self.has_next() and test(self.peak()):
            passing_elements.append(self.next())
        return passing_elements
