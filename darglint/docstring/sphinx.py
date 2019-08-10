from collections import defaultdict
from typing import (  # noqa
    Dict,
    List,
    Set,
    Union,
    Tuple,
    Optional,
)

from .base import (
    BaseDocstring,
    DocstringStyle,
    Sections,
)
from ..node import (
    Node,
    NodeType,
)
from ..parse import (
    sphinx,
)
from ..config import (
    Strictness,
)
from ..lex import lex
from ..peaker import Peaker


class Docstring(BaseDocstring):
    """The docstring class interprets the AST of a docstring."""

    def __init__(self, root, style=DocstringStyle.SPHINX):
        # type: (Union[Node, str], DocstringStyle) -> None
        """Create a new docstring from the AST.

        Args:
            root: The root of the AST, or the docstring
                (as a string.)  If it is a string, the
                string will be parsed.
            style: The docstring style.  Discarded, since this
                docstring always represents the Sphinx style.

        """
        if isinstance(root, Node):
            self.root = root
        else:
            self.root = sphinx.parse(Peaker(lex(root), lookahead=2))
        self._lookup = self._discover()

    def _discover(self):
        # type: () -> Dict[NodeType, List[Node]]
        """Walk the tree, finding all non-terminal nodes.

        Returns:
            A lookup table for compound Nodes by their NodeType.

        """
        lookup = defaultdict(
            lambda: list()
        )  # type: Dict[NodeType, List[Node]]
        for node in self.root.breadth_first_walk(leaves=False):
            lookup[node.node_type].append(node)
        return lookup

    def get_section(self, section):
        # type: (Sections) -> Optional[str]
        nodes = []  # type: Optional[List[Node]]

        if section == Sections.SHORT_DESCRIPTION:
            nodes = self._lookup.get(NodeType.SHORT_DESCRIPTION, None)
        elif section == Sections.LONG_DESCRIPTION:
            nodes = self._lookup.get(NodeType.LONG_DESCRIPTION, None)
        elif section == Sections.ARGUMENTS_SECTION:
            nodes = self._lookup.get(NodeType.ARGS_SECTION, None)
        elif section == Sections.RAISES_SECTION:
            nodes = self._lookup.get(NodeType.RAISES_SECTION, None)
        elif section == Sections.YIELDS_SECTION:
            nodes = self._lookup.get(NodeType.YIELDS_SECTION, None)
        elif section == Sections.RETURNS_SECTION:
            nodes = self._lookup.get(NodeType.RETURNS_SECTION, None)
        elif section == Sections.VARIABLES_SECTION:
            nodes = self._lookup.get(NodeType.VARIABLES_SECTION, None)
        elif section == Sections.NOQAS:
            nodes = self._lookup.get(NodeType.NOQA, None)
        else:
            raise Exception(
                'Unsupported section type, {}'.format(section)
            )

        if not nodes:
            return None

        return_value = ''
        for node in nodes:
            return_value += '\n' + node.reconstruct_string()

        return return_value.strip() or None

    def _get_item_name(self, section):
        # type: (Node) -> Optional[str]
        item_name = section.first_instance(NodeType.ITEM_NAME)
        if item_name is None:
            return None
        name = item_name.first_instance(NodeType.WORD)
        if name is None:
            return None
        return name.value

    def _get_item_type_lookup(self, section_type):
        # type: (NodeType) -> Dict[str, Optional[str]]
        assert section_type in [
            NodeType.ARGS_SECTION,
            NodeType.VARIABLES_SECTION,
            NodeType.RAISES_SECTION,
        ], 'Only Arguments and variables should have type information by item.'

        item_types = dict()  # type: Dict[str, Optional[str]]

        for section in self._lookup[section_type]:
            name = self._get_item_name(section)
            if name and name not in item_types:
                item_types[name] = None
            is_type = section.first_instance(NodeType.TYPE)
            if not is_type:
                continue
            description = section.first_instance(NodeType.ITEM_DEFINITION)
            if name and description:
                item_types[name] = description.reconstruct_string().strip()

        return item_types

    def _get_argument_types(self):
        # type: () ->  List[Optional[str]]
        """Get a list of types corresponding to arguments.

        Returns:
            A dictionary matching arguments to types.

        """
        argtypes = self._get_item_type_lookup(NodeType.ARGS_SECTION)
        sorted_items = sorted(argtypes.items())
        return [x[1] for x in sorted_items]

    def _get_variable_types(self):
        # type: () -> List[Optional[str]]
        vartypes = self._get_item_type_lookup(NodeType.VARIABLES_SECTION)
        sorted_items = sorted(vartypes.items())
        return [x[1] for x in sorted_items]

    def _get_return_type(self):
        # type: () -> Optional[str]
        for section in self._lookup[NodeType.RETURNS_SECTION]:
            is_type = section.first_instance(NodeType.TYPE)
            if not is_type:
                continue
            description = section.first_instance(NodeType.ITEM_DEFINITION)
            if description is None:
                return None
            else:
                return description.reconstruct_string().strip()
        return None

    def get_types(self, section):
        # type: (Sections) -> Optional[Union[str, List[Optional[str]]]]
        if section == Sections.ARGUMENTS_SECTION:
            if NodeType.ARGS_SECTION not in self._lookup:
                return None
            return self._get_argument_types() or None
        elif section == Sections.VARIABLES_SECTION:
            if NodeType.VARIABLES_SECTION not in self._lookup:
                return None
            return self._get_variable_types() or None
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
            args_types = self._get_item_type_lookup(NodeType.ARGS_SECTION)
            sorted_items = sorted(args_types.items())
            return [x[0] for x in sorted_items] or None
        elif section == Sections.RAISES_SECTION:
            raises_types = self._get_item_type_lookup(NodeType.RAISES_SECTION)
            sorted_items = sorted(raises_types.items())
            return [x[0] for x in sorted_items] or None
        elif section == Sections.VARIABLES_SECTION:
            var_types = self._get_item_type_lookup(NodeType.VARIABLES_SECTION)
            sorted_items = sorted(var_types.items())
            return [x[0] for x in sorted_items] or None
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
        for yield_node in self._lookup[NodeType.YIELDS_SECTION]:
            type_node = yield_node.first_instance(NodeType.TYPE)
            if type_node is None:
                continue
            definition = yield_node.first_instance(NodeType.ITEM_DEFINITION)
            assert definition is not None
            return definition.reconstruct_string().strip()
        return None

    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        """Get a map of the errors ignored to their targets.

        Returns:
            A dictionary containing the errors to ignore as keys and
            a list of which targets to apply these exceptions to as
            the values.  A blank list implies a global noqa.

        """
        encountered = set()  # type: Set[Node]
        global_noqas = set()  # type: Set[Node]
        noqas = defaultdict(list)  # type: Dict[str, List[str]]

        # Get exceptions with implied targets
        for item_node in self._lookup[NodeType.ITEM]:
            item = None  # type: Optional[str]
            for node in item_node.breadth_first_walk(leaves=False):
                # We will always encounter the item name first.
                if node.node_type == NodeType.ITEM_NAME:
                    iname = node.first_instance(NodeType.WORD)
                    if iname is None:
                        continue
                    item = iname.value
                elif node.node_type == NodeType.NOQA_BODY:
                    assert item is not None
                    exception = node.children[0]
                    assert exception.value is not None
                    encountered.add(exception)
                    noqas[exception.value].append(item)

        # Get all other exceptions
        for noqa_node in self._lookup[NodeType.NOQA_BODY]:
            exception = noqa_node.children[0]
            if exception in encountered:
                continue

            if len(noqa_node.children) == 1:
                global_noqas.add(exception)
                continue

            for word_node in noqa_node.children[1].children:
                word = word_node.value
                assert word is not None
                assert exception.value is not None
                if word.endswith(','):
                    word = word[:-1]
                noqas[exception.value].append(word)

        # We overwrite any previous targets, because it was defined
        # as a global. (This could happen before a target is defined.)
        for global_noqa in global_noqas:
            assert global_noqa.value is not None
            noqas[global_noqa.value] = list()

        return dict(noqas)

    def get_line_numbers(self, node_type):
        # type: (NodeType) -> Optional[Tuple[int, int]]
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
        # type: (NodeType, str) -> Optional[Tuple[int, int]]
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
        for node in self._lookup[NodeType.NOQA]:
            body = None
            for child in node.walk():
                if child.node_type == NodeType.NOQA_BODY:
                    body = child
                    break

            if body is None or any([x.value == '*' for x in body.children]):
                return True

        return False

    def satisfies_strictness(self, strictness):
        # type: (Strictness) -> bool
        """Return true if the docstring has no more than the min strictness.

        Args:
            strictness: The minimum amount of strictness which should
                be present in the docstring.

        Returns:
            True if there is no more than the minimum amount of strictness.

        """
        if len(self.root.children) != 1:
            return False
        top_levels = {
            x.node_type for x in self.root.children[0].children
        }
        if strictness == Strictness.SHORT_DESCRIPTION:
            return top_levels == {NodeType.SHORT_DESCRIPTION}
        elif strictness == Strictness.LONG_DESCRIPTION:
            return top_levels in [
                {NodeType.SHORT_DESCRIPTION},
                {NodeType.SHORT_DESCRIPTION, NodeType.LONG_DESCRIPTION},
                # Shouldn't be possible, but if it is in the future, then
                # we should allow this.
                {NodeType.LONG_DESCRIPTION},
            ]
        else:
            # We don't need to check FULL_DESCRIPTION because it's the
            # same situation as when strictness is not satisfied.
            return False
