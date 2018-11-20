"""Utilities for debugging Darglint."""

from .node import Node  # noqa: F401


def generate_dot(node):
    # type: (Node) -> str
    """Generate a dot file for the given AST.

    Once generated, the returned tree can be rendered using
    the graphviz library.  For example, to render as an SVG:

        dot -Tsvg rendered_tree.dot -o rendered_tree.svg

    Args:
        node: The root of the tree we are generating.

    Returns:
        The rendered tree, as a dot file.

    """

    def _node_type_str(n):
        return str(n.node_type).replace('NodeType.', '')

    def _get_node_name(n):
        # type: (Node) -> str
        return '{}_{}'.format(
            _node_type_str(n), hash(n)
        ).replace('-', '')

    def _render_node_definition(n):
        # type: (Node) -> str
        name = _get_node_name(n)
        node_is_parent = n.value is None
        if node_is_parent:
            return '{} [label="{}"];'.format(
                name,
                _node_type_str(n),
            )
        else:
            assert n.value is not None
            value = '\\n\\"' + n.value + '\\"'
            return '{} [label="{} {}", shape="rectangle"];'.format(
                name,
                _node_type_str(n),
                value
            )

    def _render_relations(n):
        # type: (Node) -> str
        if not n.children:
            return ''
        ret = '{} -> \t{};'.format(
            _get_node_name(n),
            '\n\t, '.join([_get_node_name(child) for child in n.children])
        )
        for child in [x for x in n.children if x.children]:
            ret += '\n' + _render_relations(child)
        return ret

    definitions = [
        _render_node_definition(n) for n in node.walk()
    ]
    relations = _render_relations(node)

    return '\n\n'.join([
        'digraph G {',
        '\n'.join(definitions),
        relations,
        '}',
    ])
