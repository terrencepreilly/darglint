r"""A parser combinator.

This combinator first parses a docstring into sections
(any block separated by two newlines), then calls individual
CYK parsers for each subsection.   The subparsers are called
in order of specificity.

Although weighting an overall CYK parser could handle an
entire docstring, this should be much more efficient.  A CYK
parser is O(n^3).  By reducing the docstring into k separate
sections, we can reduce this to

    O(n + k(n / k)^3)
    = O(n + k (n^3 / k^3))
    = O(n + (n^3 / k^2))

Which is still a member of O(n^3), since k is constant.  However,
since our k is around 4 members, this constant divisor will
actually impart a significant improvement, even though it doesn't
change the order.

Upon inspection, threading did not significantly improve performance.
The probem, it seems, is that some of the sections take much
longer than others, and so threading does nothing to improve
speed. (It actually made it worse.)

"""


def parser_combinator(top, lookup, combinator, tokens):
    """Parse the given tokens, combining in the given fashion.

    Args:
        top: The top-level parser.  Separates the tokens into
            sections which can be consumed by the parsers in the
            lookup function.
        lookup: For a given section from the top-level parser,
            returns a list of possible parsers.
        combinator: Combines the resultant nodes from parsing
            each section from the top-level parser.
        tokens: The tokens to be parsed.

    Returns:
        The top-level node from the combinator.

    """
    sections = top(tokens)
    parsed_sections = list()
    for i, section in enumerate(sections):
        parsed = None
        for parse in lookup(section, i):
            parsed = parse(section)
            if parsed:
                break
        if not parsed:
            return None
        parsed_sections.append(parsed)
    return combinator(*parsed_sections)
