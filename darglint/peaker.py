"""Describes Peaker, a stream transformer for peaking ahead."""

from typing import (
    Callable,
    Generic,
    Iterator,
    List,
    TypeVar,
    Union,
)


T = TypeVar('T')


class Peaker(Generic[T]):
    """A stream transformer allowing us to peak ahead."""

    class _Empty(object):
        value = None

    def __init__(self, stream):
        # type: (Iterator[T]) -> None
        """Create a new peaker.

        Args:
            stream: An iterator of T objects, which may be empty.

        """
        self.stream = stream
        try:
            self.current = next(stream) # type: Union[T, Peaker._Empty]
        except StopIteration:
            self.current = self._Empty()

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
        if not self.has_next():
            raise StopIteration
        previous = self.current  # type: T
        try:
            self.current = next(self.stream)
        except StopIteration:
            self.current = self._Empty()
        return previous

    def peak(self):
        # type: () -> T
        """Get the next letter in the stream, without moving it forward.

        Returns:
            The next item of type T in the stream.

        """
        if isinstance(self.current, self._Empty):
            return None
        return self.current

    def has_next(self):
        # type: () -> bool
        """Tell whether there are more tokens in the stream.

        Returns:
            True if there are more tokens, false otherwise.

        """
        return not isinstance(self.current, self._Empty)

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
