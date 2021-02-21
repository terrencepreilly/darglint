from typing import (
    cast,
    Any,
    Callable,
    List,
    TypeVar,
    Union,
)
from .sequence import (
    Sequence,
)
from .subproduction import SubProduction


T = TypeVar("T")


def longest_sequence(
    test: Callable[[Any], bool],
    items: Union[List[T], SubProduction],
    index: int = 0,
) -> Sequence[T]:
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
        item = cast(T, items[i])
        seq.append(item)
        i += 1

    return Sequence(start=start, end=i, sequence=seq)
