from typing import (
    List,
    Tuple,
    Optional,
    Iterator,
    Union,
    Any,
)
from .sequence import Sequence
from .symbols import (
    is_term,
)


class SubProduction:
    """Identifies a subset of a give production.

    A subset of a production is here given to be some
    ordered set of terminal and non-terminal symbols which
    occur on the RHS of some production P in G:

        ⟨s₁, s₂, ..., sₙ⟩

    """

    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.__index = 0

    @staticmethod
    def from_sequence(sequence: Sequence) -> "SubProduction":
        return SubProduction(sequence.sequence)

    def head(self) -> Tuple[Optional[str], "SubProduction"]:
        if self.symbols:
            return self.symbols[0], SubProduction(self.symbols[1:])
        return None, self

    def initial_terminals(
        self, k: int
    ) -> Tuple["SubProduction", "SubProduction"]:
        if k == 0 and self.symbols and self.symbols[0] == "ε":
            return SubProduction(["ε"]), SubProduction([])
        i = 0
        while (
            i < k
            and i < len(self.symbols)
            and (is_term(self.symbols[i]) or self.symbols[i] == "ε")
        ):
            i += 1
        return SubProduction(self.symbols[:i]), SubProduction(self.symbols[i:])

    def normalized(self) -> List[str]:
        if len(self) <= 1:
            return self.symbols
        return [x for x in self.symbols if x != "ε"]

    def __add__(self, other: "SubProduction") -> "SubProduction":
        return SubProduction(self.symbols + other.symbols)

    def __str__(self) -> str:
        return repr(self.symbols)

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self.symbols)

    def __len__(self) -> int:
        return len(self.symbols)

    def __key(self) -> Tuple[str, ...]:
        return tuple(self.symbols)

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SubProduction):
            return self.__key() == other.__key()
        return False

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[str, "SubProduction"]:
        if isinstance(index, int):
            return self.symbols[index]
        else:
            return SubProduction(self.symbols.__getitem__(index))

    # Although __getitem__ makes it possible to pass this
    # into a list, mypy wants to know that this is an iterator.
    def __iter__(self) -> Iterator[str]:
        self.__index = 0
        return self

    def __next__(self) -> str:
        if self.__index >= len(self):
            raise StopIteration
        ret = self[self.__index]
        self.__index += 1
        assert isinstance(ret, str)
        return ret
