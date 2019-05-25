
from typing import (
    Callable,
    Optional,
)


REFACTORING_COMPLETE = False


def replace(name=''):
    # type: (str) -> Callable
    """Decorates a function which must be replaced.

    If the above global, REFACTORING_COMPLETE is True,
    then it will fail if no alternate is defined for
    it.

    Args:
        name: The name of the method which is replacing it.

    Returns:
        The same function, failing if the refactoring is complete.

    """
    def wrapper(fn):
        # type: (Callable) -> Callable

        def _inner(*args, **kwargs):
            self = args[0]
            if not hasattr(self, name) and REFACTORING_COMPLETE:
                self.fail('No replacement defined!')
            return fn(*args, **kwargs)
        return _inner

    return wrapper


def remove(fn):
    # type: (Callable) -> Callable
    """Describes a method which should be removed after refactoring.

    Args:
        fn: The method which should be removed.

    Returns:
        A method which will fail if refactoring has completed.

    """

    def _inner(*args, **kwargs):
        if REFACTORING_COMPLETE:
            self = args[0]
            self.fail('This should have been removed!')
        return fn(*args, **kwargs)

    return _inner
