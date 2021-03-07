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


def gen_cache(max_iterator_depth=200):
    """A memoization wrapper for functions which return generators.

    The generator is evaluated at cache time, and a new generator
    is returned based on those results.  This means that the generator
    which is returned cannot be cyclic in nature, or caching it will
    loop forever.  For that reason, you can specify a max recursion depth
    for this cache.

    Args:
        max_iterator_depth: The maximum amount of items which can be pulled
            from the generator.

    Returns:
        A decorator which caches the results from functions which return
        generators.

    """

    def _wrapper(fun):
        _cache = dict()

        def _inner(*args, **kwargs):
            key = (tuple(args), tuple(kwargs.items()))
            if key not in _cache:
                _cache[key] = list()
                counter = 0
                for value in fun(*args, **kwargs):
                    _cache[key].append(value)
                    counter += 1
                    if counter > max_iterator_depth:
                        raise Exception("Max iterator depth reached.")
            return (x for x in _cache[key])

        return _inner

    return _wrapper

