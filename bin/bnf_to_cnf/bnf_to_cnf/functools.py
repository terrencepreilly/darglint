from typing import (
    Callable,
    Iterator,
    TypeVar,
)


def exists(it: Iterator) -> bool:
    try:
        next(it)
    except StopIteration:
        return False
    return True


T = TypeVar('T')


def and_(*args: Callable[[T], bool]) -> Callable[[T], bool]:
    def _inner(x: T) -> bool:
        for fn in args:
            if not fn(x):
                return False
        return True
    return _inner


def or_(*args: Callable[[T], bool]) -> Callable[[T], bool]:
    def _inner(x: T) -> bool:
        for fn in args:
            if fn(x):
                return True
        return False
    return _inner


def not_(fn: Callable[[T], bool]) -> Callable[[T], bool]:
    def _inner(x: T) -> bool:
        return not fn(x)
    return _inner
