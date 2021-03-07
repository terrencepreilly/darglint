from .subproduction import SubProduction


class FirstSet:
    def __init__(self, *sequences: SubProduction):
        self.sequences = list(sequences)

    def __len__(self) -> int:
        return len(self.sequences)

    def __mul__(self, other: "FirstSet") -> "FirstSet":
        result = FirstSet()
        for first_sequence in self.sequences:
            for second_sequence in other.sequences:
                if first_sequence == ["ε"]:
                    result.sequences.append(second_sequence)
                elif second_sequence == ["ε"]:
                    result.sequences.append(first_sequence)
                else:
                    result.sequences.append(first_sequence + second_sequence)
        return result

    def __bool__(self) -> bool:
        return bool(self.sequences)

    def __or__(self, other: "FirstSet") -> "FirstSet":
        return FirstSet(*self.sequences, *other.sequences)

    def __str__(self) -> str:
        return "{" + ", ".join(map(str, self.sequences)) + "}"

    def __repr__(self) -> str:
        return str(self)
