from collections import deque
from typing import (
    Deque,
    List,
    Optional,
    Union,
    Iterator,
    Tuple,
    Iterable,
    Set,
    cast,
)

from .production import Production
from .subproduction import SubProduction
from .sequence import Sequence
from .symbols import (
    is_term,
    is_nonterm,
    is_epsilon,
)
from .utils import (
    longest_sequence,
)


class Grammar:
    def __init__(self, table: List[Production], start: Optional[str] = None):
        self.table = table
        self.start = start

    def __getitem__(
        self, key: Union[int, str]
    ) -> Union[SubProduction, List[SubProduction]]:
        if isinstance(key, int):
            return SubProduction(self.table[key][1])
        elif isinstance(key, str):
            return [
                SubProduction(rhs)
                for lhs, rhs in self.table
                if lhs == key
            ]
        else:
            raise ValueError(
                "Grammar only indexed by production index "
                "or non-terminal symbol."
            )

    def __iter__(self) -> Iterator[Tuple[str, SubProduction]]:
        return ((lhs, SubProduction(rhs)) for lhs, rhs in self.table)

    def __str__(self) -> str:
        if self.start:
            lines = [f"start: <{self.start}>\n"]
        else:
            lines = []
        prev = None
        for lhs, rhs in self.table:
            if lhs == prev:
                line = "  | "
            else:
                line = f"<{lhs}> ::="
            for symbol in rhs:
                if is_epsilon(symbol):
                    line += f" {symbol}"
                elif is_nonterm(symbol):
                    line += f" <{symbol}>"
                else:
                    line += f" {symbol}"
            prev = lhs
            lines.append(line)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return str(self)

    def get_exact(self, start: str, k: int) -> Iterable[SubProduction]:
        """Get a derivation of a symbol, which is of an exact length.

        Args:
            start: The symbol at which we should begin the derivation.
            k: The exact length we are hoping to obtain.

        Yields:
            SubProductions of length k which are derived from the given
                symbol, start.

        """
        if is_term(start):
            if k == 1:
                yield SubProduction([start])
            return

        queue = [(SubProduction([]), SubProduction([start]))]
        iteration_guard = 50000
        while queue:
            iteration_guard -= 1
            if not iteration_guard:
                raise Exception(
                    'Surpassed iteration limit: '
                    'Check for infinite left recursion.'
                )
            curr, rem = queue.pop()
            if not rem:
                if len(curr) == k:
                    yield curr
                continue
            head, rest = rem[0], rem[1:]
            assert isinstance(head, str), "Integer index didn't result in str"
            for prod in self[head]:
                if len(prod) == 1 and prod[0] == "ε":
                    assert isinstance(rest, SubProduction)
                    queue.append((curr, rest))
                    continue
                first_nonterm = 0
                while first_nonterm < len(prod) and is_term(
                    cast(str, prod[first_nonterm])
                ):
                    first_nonterm += 1
                if len(curr) + first_nonterm > k:
                    continue
                prod_before_first_nonterm = prod[first_nonterm:]
                assert isinstance(prod_before_first_nonterm, SubProduction)
                prod_after_first_nonterm = prod[:first_nonterm]
                assert isinstance(prod_after_first_nonterm, SubProduction)

                assert isinstance(rest, SubProduction)
                queue.append(
                    (
                        curr + prod_after_first_nonterm,
                        prod_before_first_nonterm + rest,
                    )
                )

    def _has_infinite_left_recursion(self, start: str) -> Optional[Set[str]]:
        """Return the set of encountered symbols from this start symbol.

        Args:
            start: The symbol where we should start.

        Returns:
            The set of encountered symbols, if we did not encounter infinite
            recursion.  Otherwise, None.

        # noqa: DAR401

        """
        encountered = set()
        queue = deque([start])  # type: Deque[Union[str, SubProduction]]
        while queue:
            curr = queue.pop()
            if isinstance(curr, str):
                key = curr
                rest = SubProduction([])
            elif isinstance(curr, SubProduction):
                key = cast(str, curr[0])
                rest = cast(SubProduction, curr[1:])
            else:
                raise Exception("Expected only strings and subproductions.")

            if key in encountered:
                return None

            encountered.add(key)

            for production in self[key]:
                assert isinstance(production, SubProduction)
                symbol = production[0]
                assert isinstance(symbol, str)
                if is_nonterm(symbol):
                    # We have to continue the search with nonterminals.
                    # If this production is only nonterminals, we have to
                    # continue with the rest of the current search, as well.
                    # Otherwise, we know that a fruitful production would
                    # occur in between, and we could just consider this
                    # next set of nonterminals.
                    sequence = longest_sequence(
                        is_nonterm, production, 0
                    )  # type: Sequence[str]
                    if len(sequence) == len(production):
                        queue.appendleft(
                            SubProduction.from_sequence(sequence) + rest
                        )
                    else:
                        queue.appendleft(SubProduction.from_sequence(sequence))
                elif is_term(symbol):
                    # Since it's a terminal, we can stop looking -- it
                    # was fruitful.
                    pass
                elif is_epsilon(symbol):
                    # The symbols after whatever this is replacing
                    # could result in an infinite recursion. So we
                    # have to check them, if they exist.
                    #
                    # We assume epsilons only occur on their own in a RHS.
                    if rest:
                        queue.appendleft(rest)
        return encountered

    def has_infinite_left_recursion(self) -> bool:
        """Return whether this grammar contains infinite left recursion.

        Returns:
            True if this grammar has an instance of infinite left recursion.

        """
        symbols = {lhs for lhs, rhs in self}
        while symbols:
            symbol = list(symbols)[0]
            encountered = self._has_infinite_left_recursion(symbol)
            if encountered:
                symbols -= encountered
            else:
                return True
        return False
