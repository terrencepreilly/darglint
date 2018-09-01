from abc import ABC, abstractmethod
import enum
from typing import (  # noqa
    Dict,
    List,
    Set,
    Union,
    Tuple,
    Optional,
)
from ..node import (  # noqa
    Node,
    NodeType,
)


class DocstringStyle(enum.Enum):
    GOOGLE = 0
    SPHINX = 1


# TODO: Reduce the number of methods here.
class BaseDocstring(ABC):
    """The interface for a docstring object which can be used with checkers."""

    @abstractmethod
    def has_short_description(self):
        # type: () -> bool
        pass

    @abstractmethod
    def has_long_description(self):
        # type: () -> bool
        pass

    @abstractmethod
    def has_args_section(self):
        # type: () -> bool
        pass

    @abstractmethod
    def has_raises_section(self):
        # type: () -> bool
        pass

    @abstractmethod
    def has_yields_section(self):
        # type: () -> bool
        pass

    @abstractmethod
    def has_returns_section(self):
        # type: () -> bool
        pass

    @abstractmethod
    def get_return_type(self):
        # type: () -> Union[str, None]
        pass

    @abstractmethod
    def get_exception_types(self):
        # type: () -> List[str]
        pass

    @abstractmethod
    def get_yield_type(self):
        # type: () -> Union[str, None]
        pass

    @abstractmethod
    def get_argument_types(self):
        # type: () -> Dict[str, Optional[str]]
        pass

    @abstractmethod
    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        pass

    @abstractmethod
    def get_line_numbers(self, node_type):
        # type: (NodeType) -> Optional[Tuple[int, int]]
        pass

    @abstractmethod
    def get_line_numbers_for_value(self, node_type, value):
        # type: (NodeType, str) -> Optional[Tuple[int, int]]
        pass

    @abstractmethod
    def get_variables(self):
        # type: () -> List[str]
        pass

    @property
    @abstractmethod
    def raises_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def returns_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def yields_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def arguments_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def short_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def long_description(self):
        # type: () -> Optional[str]
        pass

    @property
    @abstractmethod
    def ignore_all(self):
        # type: () -> bool
        pass
