from typing import (
    List,
    Iterator,
    Set,
)

from .subproduction import SubProduction



class FollowSet:
    """Represents a complete or partial follow set.

    Can be iterated over to find the solutions so far.

    """

    def __init__(
        self,
        partials: List[SubProduction],
        complete: List[SubProduction],
        follow: str,
        k: int,
    ):
        """Create a new FollowSet.

        Args:
            partials: Partial solutions, if this is a partial followset.
            complete: Complete solutions, if this is a complete followset.
            follow: The symbol which occurred on the LHS of the production
                under consideration.
            k: The lookahead we are aiming for.

        """
        self.partials = partials
        self.completes = complete
        self.follow = follow
        self.changed = False
        self.k = k
        self.is_complete = bool(complete)
        self.additional = set()  # type: Set[SubProduction]

    @staticmethod
    def complete(
        subproductions: List[SubProduction], follow: str, k: int
    ) -> "FollowSet":
        return FollowSet([], subproductions, follow, k)

    @staticmethod
    def empty(follow: str, k: int) -> "FollowSet":
        """Create an null-value followset.

        This followset shouldn't be used as a value itself.  It should only
        be used as a basis for constructing further followsets.  (Say,
        through a fold/reduce/etc.)  For that reason, it is complete.

        Args:
            follow: The lhs of the production where this symbol occurs.
            k: The production length we're aiming for.

        Returns:
            An empty followset.

        """
        f = FollowSet([], [], follow, k)
        f.is_complete = True
        return f

    @staticmethod
    def partial(
        partials: List[SubProduction],
        follow: str,
        k: int,
    ) -> "FollowSet":
        return FollowSet(
            partials,
            [],
            follow,
            k,
        )

    def append(self, followset: "FollowSet"):
        """Append the followset of the lhs to this one's solutions.

        Args:
            followset: The followset of the lhs of a production.

        """

        def _add(partial, sub, remaining):
            if len(sub) >= remaining:
                new_complete = (partial + sub)[: self.k]
                if new_complete not in self.additional:
                    self.changed = True
                    self.additional.add(new_complete)

        assert not self.is_complete, "Complete followsets are immutable."

        for partial in self.partials:
            remaining = self.k - len(partial)
            if followset.is_complete:
                for complete in followset.completes:
                    _add(partial, complete, remaining)
            else:
                for other_partial in followset.partials:
                    _add(partial, other_partial, remaining)
                for complete in followset.additional:
                    _add(partial, complete, remaining)

    def upgrade(self, followset: "FollowSet"):
        """Upgrade the lookahead, k, of the followset by absorbing another.

        In this way, you can go through a grammar, and calculate from i = 0..n
        the followset, upgrading the followsets for a particular symbol along
        the way.

        Args:
            followset: The basis for the upgrade (should contain a partial or
                complete solution.)

        Returns:
            The upgraded followset instance.

        """
        assert self.follow == followset.follow, (
            "Can only upgrade to the same follow type.  "
            "This ensures that the fixpoint solution will be found correctly."
        )
        # I'm not sure if this is valid. But it shouldn't be problematic, if
        # we're only calling this method after the fixpoint solution.
        self.partials.extend(followset.partials)
        self.completes.extend(followset.completes)
        self.k = max(self.k, followset.k)
        self.additional |= followset.additional
        self.is_complete = self.is_complete and followset.is_complete
        return self

    def __iter__(self) -> Iterator[SubProduction]:
        """Return an iterator over the completed subproductions.

        Returns:
            An iterator over the completed subproductions.

        """
        return (x for x in self.additional)

    def __str__(self) -> str:
        return (
            f"<FollowSet {self.follow} {self.partials} "
            f"{self.completes} {self.additional}>"
        )

    def __repr__(self) -> str:
        return str(self)
