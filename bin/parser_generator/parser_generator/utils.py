from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Callable,
    Generic,
    List,
    Optional,
    TypeVar,
)


T = TypeVar('T')


@dataclass
class Sequence(Generic[T]):

    start: Optional[int] = None
    end: Optional[int] = None
    sequence: List[T] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.start is not None and bool(self.sequence)

    def __len__(self) -> int:
        return len(self.sequence)


def longest_sequence(test: Callable[[T], bool],
                     items: List[T],
                     index: int = 0) -> Sequence[T]:
    seq = list()
    i = index

    # Move the pointer to the first passing item.
    while i < len(items) and not test(items[i]):
        i += 1

    if i == len(items):
        return Sequence()
    start = i

    # Move the pointer forward while it passes.
    while i < len(items) and test(items[i]):
        seq.append(items[i])
        i += 1

    return Sequence(start=start, end=i, sequence=seq)
