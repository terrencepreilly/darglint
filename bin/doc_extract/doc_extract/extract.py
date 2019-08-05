"""Functions for extracting docstrings from a file."""

import ast

from darglint.function_description import (
    get_function_descriptions,
)


def extract(contents: str):
    """Extract all docstrings from the given file.

    Args:
        contents: The contents of the python file.

    Yields:
        The docstrings from the function descriptions.

    """
    tree = ast.parse(contents)
    for function_description in get_function_descriptions(tree):
        yield function_description.docstring
