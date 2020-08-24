"""Utilities for debugging Darglint.

This file should not be imported into Darglint,
and should ideally be excluded from the sources.

"""
from ast import (
    AST,
)
from collections import (
    deque,
)
from typing import (
    Any,
    List,
    Optional,
    Set,
)
from .node import CykNode
from .config import (
    get_config,
    Configuration,
)


class AstNodeUtils(object):

    @staticmethod
    def iter_fields(node):
        for field in node._fields:
            try:
                yield field, getattr(node, field)
            except AttributeError:
                pass

    @staticmethod
    def _get_node_label(node):
        if hasattr(node, 'id'):
            return r'{}\nid: {}'.format(
                node.__class__.__name__,
                node.id,
            )
        elif hasattr(node, 'attr') and isinstance(node.attr, str):
            return r'{}\nattr: {}'.format(
                node.__class__.__name__,
                node.attr,
             )
        else:
            return node.__class__.__name__

    @staticmethod
    def to_dot(node):
        # type: (AST) -> str
        dot = ['digraph G {']  # type: List[str]
        id = 0
        queue = deque([(id, node)])
        while queue:
            parent_id, curr = queue.pop()
            dot.insert(1, '  {}_{} [label="{}"];'.format(
                curr.__class__.__name__,
                parent_id,
                AstNodeUtils._get_node_label(curr),
            ))
            for field, value in AstNodeUtils.iter_fields(curr):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, AST):
                            id += 1
                            queue.appendleft((id, item))
                            dot.append('  {}_{} -> {}_{};'.format(
                                curr.__class__.__name__, parent_id,
                                item.__class__.__name__, id,
                            ))
                elif isinstance(value, AST):
                    id += 1
                    queue.appendleft((id, value))
                    dot.append('  {}_{} -> {}_{};'.format(
                        curr.__class__.__name__, parent_id,
                        value.__class__.__name__, id,
                    ))
        dot.append('}')
        return '\n'.join(dot)


class CykNodeUtils(object):

    @staticmethod
    def contains(self, symbol=None, value=None):
        # type: (CykNode, Optional[str], Optional[str]) -> bool
        """Return true if the tree contains the given symbol.

        This is intended only for testing.

        Args:
            self: The node where we should begin the search.
            symbol: The symbol to search for.
            value: If defined, the string value the node should
                have in order to match.

        Returns:
            True if the symbol/value is in the tree, false otherwise.

        """
        def _match(n):
            symbol_match = symbol is None or n.symbol == symbol
            value_match = value is None or n.value == value
            return symbol_match and value_match
        for node in self.walk():
            if _match(node):
                return True
        return False

    @staticmethod
    def get_annotated(self, annotation):
        # type: (CykNode, Any) -> Set[CykNode]
        nodes = set()
        for node in self.walk():
            if annotation in node.annotations:
                nodes.add(node)
        return nodes

    @staticmethod
    def to_dot(cyk_node, is_root=True, encountered=set()):
        # type: (CykNode, bool, Set[str]) -> str
        def _get_name(node):
            i = 0
            name = node.symbol
            if node.value:
                if node.value.value:
                    name += '_' + node.value.value
                else:
                    name += '_' + str(node.value)
            for x in '.*!@#$%^*,- ;:\'"\n\t{}[]()':
                name = name.replace(x, '_')
            while name.replace('__', '_') != name:
                name = name.replace('__', '_')
            name = name.lower()
            while name + str(i) in encountered:
                i += 1
            return name + str(i)

        def _get_value(node):
            if cyk_node.value and cyk_node.value.value:
                if cyk_node.value.value.isspace():
                    return repr(cyk_node.value.value).replace('\\', '\\\\')
                return cyk_node.value.value
            elif cyk_node.value:
                return str(cyk_node.value)
            else:
                return cyk_node.symbol

        if is_root:
            ret = 'digraph G {\n'
        else:
            ret = ''

        # Print this node's relationship with its children.
        name = _get_name(cyk_node)
        encountered.add(name)
        if cyk_node.lchild or cyk_node.rchild:
            ret += name + (
                '  [shape="oval", style="filled", '
                ' label="{}",'
                ' fillcolor="#fffde7"];\n'
            ).format(_get_value(cyk_node))
            if cyk_node.lchild:
                childname = _get_name(cyk_node.lchild)
                ret += '{} -> {}'.format(name, childname)
                if cyk_node.annotations:
                    ret += '[label="'
                    for annotation in cyk_node.annotations:
                        ret += annotation.__name__ + ',\\n'
                    ret += '"]'
                ret += ';\n'
            if cyk_node.rchild:
                childname = _get_name(cyk_node.rchild)
                if cyk_node.lchild and _get_name(cyk_node.lchild) == childname:
                    childname += '_'
                ret += '{} -> {};\n'.format(name, childname)
        else:
            ret += name + (
                ' [shape="rectangle", style="filled",'
                ' label="{}"'
                ' fillcolor="#80deea"];\n'
            ).format(_get_value(cyk_node))

        # Add all of the children's relationships.
        if cyk_node.lchild:
            ret += CykNodeUtils.to_dot(
                cyk_node.lchild, False, encountered
            ) + '\n'
        if cyk_node.rchild:
            ret += CykNodeUtils.to_dot(
                cyk_node.rchild, False, encountered
            ) + '\n'

        if is_root:
            ret += '}'
        return ret


class ConfigurationContext(object):
    """A context manager for the configuration.

    Resets the configuration to the value it had prior
    to entering the context.

    """

    def __init__(self, **kwargs):
        self.original = dict()
        self.config = get_config()
        self.kwargs = kwargs

    def __enter__(self):
        # Save the state of the original item.
        for keyword, value in vars(self.config).items():
            self.original[keyword] = getattr(self.config, keyword)

        # Override with the default configuration.
        default_config = Configuration.get_default_instance()
        for keyword in self.original:
            setattr(self.config, keyword, getattr(default_config, keyword))

        # Apply test-specific values.
        for keyword, value in self.kwargs.items():
            setattr(self.config, keyword, value)

        return self.config

    def __exit__(self, exc_type, exc_value, exc_traceack):
        for keyword, value in self.original.items():
            setattr(self.config, keyword, value)
