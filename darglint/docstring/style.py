import enum


class DocstringStyle(enum.Enum):
    GOOGLE = 0
    SPHINX = 1
    NUMPY = 2

    @classmethod
    def from_string(cls, style):
        style = style.lower().strip()
        if style == 'google':
            return cls.GOOGLE
        if style == 'sphinx':
            return cls.SPHINX
        if style == 'numpy':
            return cls.NUMPY

        raise Exception(
                'Unrecognized style "{}".  Should be one of {}'.format(
                    style,
                    [x.name for x in DocstringStyle]
                )
            )
