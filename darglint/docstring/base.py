from abc import ABC, abstractmethod
from typing import (
    ClassVar,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Iterable,
)

from .sections import Sections
from ..strictness import Strictness


class BaseDocstring(ABC):
    """The interface for a docstring object which can be used with checkers.

    Unfortunately, slight differences in the parsers result
    in kind of inconsistent values for different nodes. (Sometimes
    there are blank lines and such.)  For that reason, we include some
    tests to try to make the output from the below three methods as
    consistent as possible.

    """

    supported_sections = tuple(Sections) # type: ClassVar[Tuple[Sections, ...]]

    @abstractmethod
    def get_section(self, section):
        # type: (Sections) -> Optional[str]
        """Get an entire section of the docstring.

        Args:
            section: The section to get.

        Raises:
            Exception: If the section type is unsupported.

        Returns:
            A string representing the section as a contiguous piece,
            or None if the section was not there.

        # noqa: I202
        # noqa: I402

        """
        pass

    @abstractmethod
    def get_types(self, section):
        # type: (Sections) -> Optional[Union[str, List[Optional[str]]]]
        """Get the type of the section, or of the items in the section.

        Args:
            section: The section whose type or types we are getting.
                If the section is a returns section, for example, we get
                the return type (or none if not specified).  If it is an
                arguments section, we get the types for each item.

        Raises:
            Exception: If the given section does not have a type.
                (For example, the short description.)

        Returns:
            The type or types of the section, or None if it's not
            defined.

        # noqa: I202
        # noqa: I402

        """
        pass

    @abstractmethod
    def get_items(self, section):
        # type: (Sections) -> Optional[List[str]]
        """Get the item names in the section.

        Args:
            section: The section whose item names we are getting.

        Raises:
            Exception: If the given section is not composed of
                items (e.g. a returns section, or a long description.)

        Returns:
            The items in the section (or None of the section is
            not defined.)

        # noqa: I202
        # noqa: I402

        """
        pass

    @abstractmethod
    def get_style_errors(self):
        # type: () -> Iterable[Tuple[Callable, Tuple[int, int]]]
        """Get any style errors annotated on the tree.

        Yields:
            Instances of DarglintErrors for style issues.

        # noqa: I302

        """
        pass

    @abstractmethod
    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        pass

    @abstractmethod
    def get_line_numbers(self, node_type):
        # type: (str) -> Optional[Tuple[int, int]]
        pass

    @abstractmethod
    def get_line_numbers_for_value(self, node_type, value):
        # type: (str, str) -> Optional[Tuple[int, int]]
        pass

    @property
    @abstractmethod
    def ignore_all(self):
        # type: () -> bool
        pass

    def satisfies_strictness(self, strictness):
        # type(Strictness) -> bool
        """Return true if the docstring has no more than the min strictness.

        Args:
            strictness: The minimum amount of strictness which should
                be present in the docstring.

        Returns:
            True if there is no more than the minimum amount of strictness.

        """
        sections = {
            section
            for section in self.supported_sections
            if self.get_section(section)
        }
        if strictness == Strictness.SHORT_DESCRIPTION:
            return sections == {Sections.SHORT_DESCRIPTION}
        elif strictness == Strictness.LONG_DESCRIPTION:
            return sections in (
                {Sections.SHORT_DESCRIPTION},
                # Shouldn't be possible, but if it is in the future, then
                # we should allow this.
                {Sections.LONG_DESCRIPTION},
                {Sections.SHORT_DESCRIPTION, Sections.LONG_DESCRIPTION},
            )
        else:
            return False
