from collections import (
    defaultdict,
    deque,
)
from typing import (  # noqa: F401
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from ..custom_assert import (
    Assert,
)
from .base import (  # noqa: F401
    BaseDocstring,
    DocstringStyle,
    Sections,
)
from ..node import (
    CykNode,
)
from ..parse.google import (
    parse,
)
from ..lex import (
    condense,
    lex,
)
from ..errors import (
    DarglintError,
)
from ..config import (
    Strictness,
)
from ..parse.identifiers import (
    ArgumentIdentifier,
    ArgumentItemIdentifier,
    ArgumentTypeIdentifier,
    ExceptionIdentifier,
    ExceptionItemIdentifier,
    Identifier,
    NoqaIdentifier,
)


class _CykVisitor(object):
    """A class for walking the CYK tree.

    This visitor can mark branches of the tree with an arbitrary
    string.  This is useful for giving context to leaf nodes which
    must be interpreted in the context of their branch root.

    """

    def __init__(self, root):
        self.stack = deque([root])
        self.marks = deque([])

    def __iter__(self):
        return self

    def __next__(self):
        if self.stack:
            curr = self.stack.pop()
            if self.marks:
                mark = self.marks.pop()
            else:
                mark = None
            if curr.lchild:
                self.stack.append(curr.lchild)
                if mark:
                    self.marks.append(mark)
            if curr.rchild:
                self.stack.append(curr.rchild)
                if mark:
                    self.marks.append(mark)
            return (curr, mark)
        else:
            raise StopIteration()

    def mark(self, mark):
        Assert(not self.marks, 'Marks should be non-overlapping.')
        self.marks.append(mark)


class Docstring(BaseDocstring):
    """The docstring class interprets the AST of a docstring."""

    def __init__(self, root, style=DocstringStyle.GOOGLE):
        # type: (Union[CykNode, str], DocstringStyle) -> None
        """Create a new docstring from the AST.

        Args:
            root: The root of the AST, or the docstring
                (as a string.)  If it is a string, the
                string will be parsed.
            style: The style of the docstring.  Discarded,
                since this Docstring is always the Google style.

        """
        if isinstance(root, CykNode):
            self.root = root
        else:
            self.root = parse(condense(lex(root)))
        self._lookup = self._discover()

    def _discover(self):
        # type: () -> Dict[str, List[CykNode]]
        """Walk the tree, finding all non-terminal nodes.

        Returns:
            A lookup table for compound Nodes by their NodeType.

        """
        lookup = defaultdict(
            lambda: list()
        )  # type: Dict[str, List[CykNode]]
        for node in self.root.in_order_traverse():
            if node.annotations:
                for annotation in node.annotations:
                    if issubclass(annotation, Identifier):
                        lookup[annotation.key].append(node)
            lookup[node.symbol].append(node)
        return lookup

    def get_section(self, section):
        # type: (Sections) -> Optional[str]
        nodes = []  # type: Optional[List[CykNode]]

        if section == Sections.SHORT_DESCRIPTION:
            nodes = self._lookup.get('short-description', None)
        elif section == Sections.LONG_DESCRIPTION:
            nodes = self._lookup.get('long-description', None)
        elif section == Sections.ARGUMENTS_SECTION:
            nodes = self._lookup.get('arguments-section', None)
        elif section == Sections.RAISES_SECTION:
            nodes = self._lookup.get('raises-section', None)
        elif section == Sections.YIELDS_SECTION:
            nodes = self._lookup.get('yields-section', None)
        elif section == Sections.RETURNS_SECTION:
            nodes = self._lookup.get('returns-section', None)
        elif section == Sections.NOQAS:
            nodes = self._lookup.get('noqa', None)
        else:
            raise Exception(
                'Unsupported section type {}'.format(section.name)
            )

        if not nodes:
            return None

        return_value = ''
        for node in nodes:
            return_value += '\n\n' + node.reconstruct_string()

        return return_value.strip() or None

    def _get_argument_types(self):
        # type: () ->  Optional[List[Optional[str]]]
        """Get a list of types corresponding to arguments.

        Returns:
            A dictionary matching arguments to types.

        """
        lookup = self._get_compound_item_type_lookup('arguments-section')
        if not lookup:
            return None

        names_and_types = sorted(lookup.items())
        return [x[1] for x in names_and_types]

    def _get_return_type(self):
        # type: () -> Optional[str]
        """Get the return type specified by the docstring, if any.

        Returns:
            The return type or None.

        """
        for type_node in self._lookup['returns-type']:
            if not type_node.lchild or not type_node.lchild.value:
                continue
            return type_node.lchild.value.value
        return None

    def get_types(self, section):
        # type: (Sections) -> Union[None, str, List[Optional[str]]]
        if section == Sections.ARGUMENTS_SECTION:
            if 'arguments-section' not in self._lookup:
                return None
            return self._get_argument_types()
        elif section == Sections.RETURNS_SECTION:
            return self._get_return_type()
        elif section == Sections.YIELDS_SECTION:
            return self._get_yield_type()
        else:
            raise Exception(
                'Section type {} does not have types, '.format(
                    section.name
                ) + 'or is not yet supported'
            )
        return None

    def _get_compound_item_type_lookup(self, node_type):
        # type: (str) -> Optional[Dict[str, Optional[str]]]
        """Get a map of names to types for the section.

        Args:
            node_type: The type of the section.

        Returns:
            A lookup of items to types.

        """
        if node_type not in self._lookup:
            return None

        item_types = dict()  # type: Dict[str, Optional[str]]
        for item in self._lookup[ArgumentTypeIdentifier.key]:
            item_types[
                ArgumentIdentifier.extract(item)
            ] = ArgumentTypeIdentifier.extract(item)
        for item in self._lookup[ArgumentIdentifier.key]:
            name = ArgumentIdentifier.extract(item)
            if name not in item_types:
                item_types[name] = None
        return item_types

    def _get_compound_items(self, symbol):
        # type: (str) -> Optional[List[str]]
        lookup = self._get_compound_item_type_lookup(symbol)
        if lookup is None:
            return None
        return sorted(lookup.keys())

    def _get_raises_section_items(self):
        # type: () -> Optional[List[str]]
        items = list()
        for item in self._lookup[ExceptionIdentifier.key]:
            items.append(ExceptionIdentifier.extract(item))
        return sorted(items) or None

    def get_items(self, section):
        # type: (Sections) -> Optional[List[str]]
        if section == Sections.ARGUMENTS_SECTION:
            return self._get_compound_items('arguments-section')
        elif section == Sections.RAISES_SECTION:
            return self._get_raises_section_items()
        else:
            raise Exception(
                'Section type {} does not have items, '.format(
                    section.name
                ) + 'or is not yet supported.'
            )
        return None

    def _get_yield_type(self):
        # type: () -> Optional[str]
        """Get the yield type specified by the docstring, if any.

        Returns:
            The yield type or None

        """
        for type_node in self._lookup['yields-type']:
            if not type_node.lchild or not type_node.lchild.value:
                continue
            return type_node.lchild.value.value
        return None

    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        """Get a map of the errors ignored to their targets.

        Returns:
            A dictionary containing the errors to ignore as keys and
            a list of which targets to apply these exceptions to as
            the values.  A blank list implies a global noqa.

        """
        def _get_branch_name(node):
            for child in node.walk():
                for annotation in child.annotations:
                    if (
                        issubclass(annotation, ArgumentIdentifier)
                        or issubclass(annotation, ExceptionIdentifier)
                    ):
                        return annotation.extract(child)

        noqas = defaultdict(lambda: set())  # type: Dict[str, Set[str]]

        for node in self._lookup[NoqaIdentifier.key]:
            error = NoqaIdentifier.extract(node)
            if error:
                noqas[error] |= set(NoqaIdentifier.extract_targets(node))
            else:
                noqas['*'] = set()

        # If the noqa did not have a target, but it had an error and was
        # in an item or error description, then the item or error in question
        # is the target.
        for section in (
            self._lookup['arguments-section'] + self._lookup['raises-section']
        ):
            visitor = _CykVisitor(section)
            for node, mark in visitor:
                for annotation in node.annotations:
                    if issubclass(annotation, ArgumentItemIdentifier):
                        visitor.mark(_get_branch_name(node))
                    elif issubclass(annotation, ExceptionItemIdentifier):
                        visitor.mark(_get_branch_name(node))
                    elif issubclass(annotation, NoqaIdentifier):
                        error = annotation.extract(node)
                        if error and mark:
                            noqas[error].add(mark)

        for section in self._lookup['raises-section']:
            pass

        return {
            key: sorted(values)
            for key, values in noqas.items()
        }

    def get_style_errors(self):
        # type: () -> Iterable[Tuple[Callable, Tuple[int, int]]]
        """Get any style errors annotated on the tree.

        Yields:
            Instances of DarglintErrors for style issues.

        # noqa: I302

        """
        for node, _ in _CykVisitor(self.root):
            for annotation in node.annotations:
                if issubclass(annotation, DarglintError):
                    yield annotation, node.line_numbers

    def get_line_numbers(self, symbol):
        # type: (str) -> Optional[Tuple[int, int]]
        """Get the line numbers for the first instance of the given section.

        Args:
            symbol: The type of node which we want line numbers for.
                These should be unique instances. (I.e. they should be
                in the set of compound NodeTypes which only occur
                once in a docstring. For example, "raises-section" and
                "arguments-section".

        Returns:
            The line numbers for the first instance of the given node type.

        """
        nodes = self._lookup[symbol]
        if nodes:
            return nodes[0].line_numbers
        return None

    def get_line_numbers_for_value(self, symbol, value):
        # type: (str, str) -> Optional[Tuple[int, int]]
        """Get the line number for a node with the given value.

        Args:
            symbol: The compound node which should contain the
                node we are searching for.
            value: The value of the node.

        Returns:
            A list of line numbers for nodes which match the
            parameters.

        """
        nodes = self._lookup[symbol]
        for node in nodes:
            for child in node.walk():
                if (child.value
                        and child.value.value == value
                        and child.line_numbers):
                    return child.line_numbers
        return None

    @property
    def ignore_all(self):
        # type: () -> bool
        """Return whether we should ignore everything in the docstring.

        This happens when there is a bare noqa in the docstring, or
        there is "noqa: *" in the docstring.

        Returns:
            True if we should ignore everything, otherwise false.

        """
        noqas = self.get_noqas()
        return '*' in noqas

    def satisfies_strictness(self, strictness):
        # type: (Strictness) -> bool
        """Return true if the docstring has no more than the min strictness.

        Args:
            strictness: The minimum amount of strictness which should
                be present in the docstring.

        Returns:
            True if there is no more than the minimum amount of strictness.

        """
        sections = {
            section for section in Sections
            for section in {
                Sections.SHORT_DESCRIPTION,
                Sections.LONG_DESCRIPTION,
                Sections.ARGUMENTS_SECTION,
                Sections.RAISES_SECTION,
                Sections.YIELDS_SECTION,
                Sections.RETURNS_SECTION,
                Sections.NOQAS,
            }
            if self.get_section(section)
        }
        if strictness == Strictness.SHORT_DESCRIPTION:
            return sections == {Sections.SHORT_DESCRIPTION}
        elif strictness == Strictness.LONG_DESCRIPTION:
            return sections in [
                {Sections.SHORT_DESCRIPTION},
                # Shouldn't be possible, but if it is in the future, then
                # we should allow this.
                {Sections.LONG_DESCRIPTION},
                {Sections.SHORT_DESCRIPTION, Sections.LONG_DESCRIPTION},
            ]
        else:
            return False
