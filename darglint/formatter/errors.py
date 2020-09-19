from typing import (
    Optional,
)
from darglint.errors import (
    DarglintError,
)
from darglint.node import (
    CykNode,
)


class BrokenNumberException(DarglintError):
    error_code = 'DAR999'
    description = (
        'There\'s an extra space in the number.'
    )

    def __init__(self, source):
        # type: (SyntaxError) -> None  # noqa: E501
        """Instantiate the error's message.

        Args:
            source: The syntax error which was raised by ast.

        """
        self.general_message = 'Extra space number.'
        self.terse_message = 's {}'.format(source)
        self.line_numbers = (source.lineno, source.lineno)

    @staticmethod
    def fix(node):
        # type: (CykNode) -> Optional[CykNode]
        if node.lchild.symbol == 'space' and node.rchild.symbol == 'digits':
            return node.rchild
