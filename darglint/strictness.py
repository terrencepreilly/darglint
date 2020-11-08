from enum import Enum


class Strictness(Enum):
    """The minimum strictness with which to apply checks.

    Strictness does not describe whether or not a check
    should be applied. Rather, if a check is done, strictness
    describes how intense/strict/deep the check should be.

    Each level here describes what is required of the
    docstring at the given level of strictness.  For example,
    SHORT_DESCRIPTION describes the situation where one-liners are
    allowed, and sections are not required.

    If the docstring being checked contains more than the
    allowed amount below, then it is assumed that everything
    must be checked.

    """

    # Allow a single-line description.
    SHORT_DESCRIPTION = 1

    # Allow a single-line description followed by a long
    # description, but no sections.
    LONG_DESCRIPTION = 2

    # Require everything.
    FULL_DESCRIPTION = 3

    @classmethod
    def from_string(cls, strictness):
        strictness = strictness.lower().strip()
        if strictness in {'short_description', 'short'}:
            return cls.SHORT_DESCRIPTION
        if strictness in {'long_description', 'long'}:
            return cls.LONG_DESCRIPTION
        if strictness in {'full_description', 'full'}:
            return cls.FULL_DESCRIPTION

        raise Exception(
            'Unrecognized strictness amount "{}".  '.format(strictness) +
            'Should be one of {"short", "long", "full"}'
        )
