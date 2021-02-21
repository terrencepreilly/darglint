def is_term(symbol: str) -> bool:
    return symbol.startswith('"') and symbol.endswith('"')


def is_epsilon(symbol: str) -> bool:
    return symbol == "ε"


def is_nonterm(symbol: str) -> bool:
    return not (is_term(symbol) or is_epsilon(symbol))
