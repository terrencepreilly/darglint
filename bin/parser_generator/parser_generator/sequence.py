from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Generic,
    List,
    Optional,
    TypeVar,
)


T = TypeVar("T")


@dataclass
class Sequence(Generic[T]):

    start: Optional[int] = None
    end: Optional[int] = None
    sequence: List[T] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.start is not None and bool(self.sequence)

    def __len__(self) -> int:
        return len(self.sequence)
