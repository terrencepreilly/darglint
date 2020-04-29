from collections import defaultdict
from typing import (  # noqa
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from .base import (
    BaseDocstring,
    DocstringStyle,
    Sections,
)
from ..custom_assert import Assert
from ..node import (
    CykNode,
)
from ..parse.identifiers import (
    Identifier,
    NoqaIdentifier,
)
from ..parse.sphinx import (
    parse,
)
from ..lex import (
    lex,
    condense,
)
from ..config import (
    Strictness,
)
from ..errors import (
    DarglintError,
)


class Docstring(BaseDocstring):
    """The docstring class interprets the AST of a docstring."""

    def __init__(self, root, style=DocstringStyle.SPHINX):
        # type: (Union[CykNode, str], DocstringStyle) -> None  # noqa: E501
        """Create a new docstring from the AST.

        Args:
            root: The root of the AST, or the docstring
                (as a string.)  If it is a string, the
                string will be parsed.
            style: The docstring style.  Discarded, since this
                docstring always represents the Sphinx style.

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
            lookup[node.symbol].append(node)
            for annotation in node.annotations:
                if issubclass(annotation, Identifier):
                    lookup[annotation.key].append(node)
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
        elif section == Sections.VARIABLES_SECTION:
            nodes = self._lookup.get('variables-section', None)
        elif section == Sections.NOQAS:
            nodes = self._lookup.get('noqa', None)
        else:
            raise Exception(
                'Unsupported section type, {}'.format(section)
            )

        if not nodes:
            return None

        return_value = ''
        for node in nodes:
            return_value += '\n\n' + node.reconstruct_string()

        return return_value.strip() or None

    def _get_argument_type_lookup(self):
        # type: () -> Dict[str, Optional[str]]
        ret = dict()  # type: Dict[str, Optional[str]]
        for section in self._lookup['arguments-section']:

            Assert(section.lchild, 'Section unexpected had no left child.')
            if section.lchild is None:
                continue

            argument = section.lchild.first_instance('word')
            if argument and argument.value:
                ret[argument.value.value] = None
        # TODO: Change to use @ArgumentTypeIdentifier
        for argtype in self._lookup['argument-type-section']:
            if argtype.lchild:
                word = argtype.lchild.first_instance('word')
                if word:
                    argument_type = None
                    if argtype.rchild:
                        argument_type = (
                            argtype.rchild.reconstruct_string().strip()
                        )
                    Assert(word.value, 'Word unexpectedly had no value')
                    if not word.value:
                        continue
                    ret[word.value.value] = argument_type or None
        return ret

    def _get_raises_type(self):
        # type: () -> List[Optional[str]]
        ret = list()  # type: List[Optional[str]]
        for section in self._lookup['raises-section']:
            Assert(section.lchild, 'Section unexpected had no left child.')
            if section.lchild is None:
                continue
            exception = section.lchild.first_instance('word')
            if exception and exception.value:
                ret.append(exception.value.value)
            else:
                ret.append(None)
        return ret

    def _get_variable_type_lookup(self):
        # type: () -> Dict[str, Optional[str]]
        ret = defaultdict()  # type: Dict[str, Optional[str]]
        for section in self._lookup['variables-section']:
            Assert(section.lchild, 'Section unexpected had no left child.')
            if section.lchild is None:
                continue
            variable = section.lchild.first_instance('word')
            if variable and variable.value:
                ret[variable.value.value] = None
        for section in self._lookup['variable-type-section']:
            Assert(section.lchild, 'Section unexpected had no left child.')
            if section.lchild is None:
                continue
            variable = section.lchild.first_instance('word')
            if variable and variable.value:
                Assert(
                    section.rchild,
                    'Section unexpected had no right child.'
                )
                if section.rchild is None:
                    continue
                vartype = section.rchild.reconstruct_string().strip()
                ret[variable.value.value] = vartype
        return ret

    def _get_return_type(self):
        # type: () -> Optional[str]
        if 'return-type-section' not in self._lookup:
            return None
        return_type_section = self._lookup['return-type-section'][0]

        Assert(
            return_type_section.rchild,
            'Return type unexpectedly had no right child.'
        )
        if not return_type_section.rchild:
            return None
        return return_type_section.rchild.reconstruct_string().strip()

    def _get_yield_type(self):
        # type: () -> Optional[str]
        if 'yield-type-section' not in self._lookup:
            return None
        yield_type_section = self._lookup['yield-type-section'][0]

        Assert(
            yield_type_section.rchild,
            'Yield type unexpectedly had not right child.'
        )
        if not yield_type_section.rchild:
            return None
        return yield_type_section.rchild.reconstruct_string().strip()

    def _sorted_values(self, lookup):
        # type: (Dict[str, Optional[str]]) -> List[Optional[str]]
        return [lookup[key] for key in sorted(lookup.keys())]

    def _sorted_keys(self, lookup):
        return sorted(lookup.keys())

    def get_types(self, section):
        # type: (Sections) -> Optional[Union[str, List[Optional[str]]]]
        if section == Sections.ARGUMENTS_SECTION:
            if 'arguments-section' not in self._lookup:
                return None
            return (
                self._sorted_values(self._get_argument_type_lookup())
                or None
            )
        elif section == Sections.VARIABLES_SECTION:
            if 'variables-section' not in self._lookup:
                return None
            return (
                self._sorted_values(self._get_variable_type_lookup())
                or None
            )
        elif section == Sections.RETURNS_SECTION:
            return self._get_return_type() or None
        elif section == Sections.YIELDS_SECTION:
            return self._get_yield_type() or None
        else:
            raise Exception(
                'Section type {} does not have types, '.format(
                    section.name
                ) + 'or is not yet supported'
            )
        return None

    def get_items(self, section):
        # type: (Sections) -> Optional[List[str]]
        if section == Sections.ARGUMENTS_SECTION:
            return self._sorted_keys(self._get_argument_type_lookup()) or None
        elif section == Sections.RAISES_SECTION:
            return sorted(
                [x or '' for x in self._get_raises_type()],
                key=lambda x: x or ''
            ) or None
        elif section == Sections.VARIABLES_SECTION:
            return self._sorted_keys(self._get_variable_type_lookup()) or None
        else:
            raise Exception(
                'Section type {} does not have items, '.format(
                    section.name
                ) + 'or is not yet supported.'
            )
        return None

    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        """Get a map of the errors ignored to their targets.

        Returns:
            A dictionary containing the errors to ignore as keys and
            a list of which targets to apply these exceptions to as
            the values.  A blank list implies a global noqa.

        """
        noqas = dict()
        for noqa in self._lookup[NoqaIdentifier.key]:
            noqas[NoqaIdentifier.extract(noqa) or '*'] = (
                NoqaIdentifier.extract_targets(noqa)
            )
        return noqas

    def get_line_numbers(self, node_type):
        # type: (str) -> Optional[Tuple[int, int]]
        """Get the line numbers for the first instance of the given section.

        Args:
            node_type: The NodeType which we want line numbers for.
                These should be unique instances. (I.e. they should be
                in the set of compound NodeTypes which only occur
                once in a docstring. For example, "Raises" and "Args".

        Returns:
            The line numbers for the first instance of the given node type.

        """
        nodes = self._lookup[node_type]
        if nodes:
            return nodes[0].line_numbers
        return None

    def get_line_numbers_for_value(self, node_type, value):
        # type: (str, str) -> Optional[Tuple[int, int]]
        """Get the line number for a node with the given value.

        Args:
            node_type: The compound node which should contain the
                node we are searching for.
            value: The value of the node.

        Returns:
            A list of line numbers for nodes which match the
            parameters.

        """
        nodes = self._lookup[node_type]
        for node in nodes:
            for child in node.walk():
                if child.value == value and child.line_numbers:
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
        return False

    def get_style_errors(self):
        # type: () -> Iterable[Tuple[Callable, Tuple[int, int]]]
        """Get any style errors annotated on the tree.

        Yields:
            Instances of DarglintErrors for style issues.

        # noqa: I302

        """
        for node in self.root.in_order_traverse():
            for annotation in node.annotations:
                if issubclass(annotation, DarglintError):
                    yield annotation, node.line_numbers

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
