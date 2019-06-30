from collections import (
    defaultdict,
    deque,
)
from typing import (  # noqa: F401
    Any,
    Dict,
    Deque,
    List,
    Set,
    Union,
    Tuple,
    Optional,
)

from .base import (  # noqa: F401
    BaseDocstring,
    DocstringStyle,
    Sections,
)
# from ..node import (
#     Node,
#     NodeType,
# )
from ..parse.cyk import (
    CykNode,
)
from ..parse.new_google import (
    parse,
)
# from ..parse import (
#     google,
# )
from ..lex import (
    condense,
    lex,
)
# from ..peaker import Peaker


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
            # self.root = google.parse(Peaker(lex(root), lookahead=3))
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
        # type: () ->  List[Optional[str]]
        """Get a list of types corresponding to arguments.

        Returns:
            A dictionary matching arguments to types.

        """
        lookup = self._get_compound_item_type_lookup('arguments-section')
        if lookup is None:
            return []

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
        for node in self._lookup[node_type]:
            for item_name in node.breadth_first_walk():
                if item_name.symbol not in {
                    'head-argument1', 'head-exception0'
                }:
                    continue
                name = item_name.lchild.value
                if not name or not name.value:
                    continue
                _type = item_name.first_instance('type-section-parens')
                if _type is None:
                    item_types[name.value] = None
                else:
                    _type_repr = _type.reconstruct_string()
                    _type_repr = _type_repr[1:-1].strip()
                    item_types[name.value] = _type_repr
        return item_types

    def _get_compound_items(self, symbol):
        # type: (str) -> Optional[List[str]]
        lookup = self._get_compound_item_type_lookup(symbol)
        if lookup is None:
            return None
        return sorted(lookup.keys())

    def get_items(self, section):
        # type: (Sections) -> Optional[List[str]]
        if section == Sections.ARGUMENTS_SECTION:
            return self._get_compound_items('arguments-section')
        elif section == Sections.RAISES_SECTION:
            return self._get_compound_items('raises-section')
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

    # TODO: Refactor.
    # Some ideas for how to refactor:
    # -   Define a query selector for Cyk nodes,
    #     to make getting a child easier.
    # -   Do a DFS storing nodes, and when you encounter
    #     a noqa, record the parent items, if they exist.
    #     Then operate entirely off of this list.
    def get_noqas(self):
        # type: () -> Dict[str, List[str]]
        """Get a map of the errors ignored to their targets.

        Returns:
            A dictionary containing the errors to ignore as keys and
            a list of which targets to apply these exceptions to as
            the values.  A blank list implies a global noqa.

        """
        item_symbols = {'head-argument', 'head-exception'}

        def _is_noqa_parent(node):
            return (
                node.symbol == 'noqa-maybe'
                or (node.lchild and 'noqa-statement' in node.lchild.symbol)
                or (node.rchild and 'noqa-statement' in node.rchild.symbol)
            )

        def _get_noqa_target(node):
            noqa_statement0 = node.rchild
            assert noqa_statement0 and noqa_statement0.rchild
            word = noqa_statement0.rchild
            assert word.value
            words = word.value.value.split()
            return words[0], words[1:]

        def _is_item(node):
            return (
                (node.rchild and node.rchild.symbol in item_symbols)
                or (node.lchild and node.lchild.symbol in item_symbols)
            )

        def _get_item(node):
            if node.lchild and node.lchild.symbol in item_symbols:
                head_item = node.lchild
            else:
                assert node.rchild
                head_item = node.rchild
            head_item0 = head_item.rchild
            assert head_item0
            word = head_item0.lchild
            assert word and word.value
            return word.value.value

        global_noqas = set()  # type: Set[str]
        noqas = defaultdict(lambda: set())  # type: Dict[str, Set[str]]

        sections = list()
        sections.extend(self._lookup['arguments-section'])
        sections.extend(self._lookup['raises-section'])

        # Perform an in-order DFS of the tree.
        # This way, we can mark when we're in an item, and
        # we can ensure we encounter an item name before the noqa.
        for args_section in sections:
            stack = deque([args_section])  # type: Deque[Any]
            item = None
            while stack:
                curr = stack.pop()

                # Leave the context of this argument.
                if isinstance(curr, str):
                    item = None
                    continue

                if _is_item(curr):
                    item = _get_item(curr)
                    stack.append(item)
                elif _is_noqa_parent(curr):
                    exception, targets = _get_noqa_target(curr)
                    if not targets and item:
                        targets = [item]
                    elif not targets:
                        global_noqas.add(exception)

                    for target in targets:
                        noqas[exception].add(target)

                if curr.rchild:
                    stack.append(curr.rchild)
                if curr.lchild:
                    stack.append(curr.lchild)

        sections = list()
        sections.extend(self._lookup['long-description'])
        sections.extend(self._lookup['short-description'])

        for section in sections:
            stack = deque([section])
            while stack:
                curr = stack.pop()
                if _is_noqa_parent(curr):
                    exception, targets = _get_noqa_target(curr)
                    noqas[exception] |= set(targets)

                    # Don't add the children -- that way we
                    # capture universal noqas.
                    continue
                if curr.symbol == 'noqa':
                    global_noqas.add('*')

                if curr.rchild:
                    stack.append(curr.rchild)
                if curr.lchild:
                    stack.append(curr.lchild)

        # We overwrite any previous targets, because it was defined
        # as a global. (This could happen before a target is defined.)
        for global_noqa in global_noqas:
            noqas[global_noqa] = set()

        return {
            key: sorted(values)
            for key, values in noqas.items()
        }

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
        for node in self._lookup['noqa-maybe']:
            body = list()
            for child in node.walk():
                if child.symbol == 'words':
                    body.append(child)

            if not body or any([
                x.value and x.value.value == '*' for x in body
            ]):
                return True

        return False
