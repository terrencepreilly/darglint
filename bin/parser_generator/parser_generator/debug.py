import uuid

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)


class RecurseDebug:
    """Allows graphing recursive function calls.

    An instance of this class should be instantiated before a
    recursive function call.  The call will have to be modified to
    include the parent debug symbol during each recursive call.

    For each call, then, the function should get a debug symbol for
    the call, using `add_call`.  For each recursive call, that debug
    symbol should be passed on.  If there is a parent debug symbol,
    the relationship should be made plain with `add_child`.  When
    a result is returned or yielded, `add_result` should be called.

    Finally, when the call has terminated, a graph can be generated
    using `get_dot`.

    This could probably be more self-contained (say, as a decorator),
    and could probably be used to capture memoization results.  But,
    it's worked so far, so it's good enough.

    """

    def __init__(
        self,
        function_name: str,
        get_memo_key: Optional[Callable[[Any], Any]] = None,
    ):
        self.function_name = function_name

        # Holds the call graph to be drawn.  Each key
        # represents a node, and the values represent child
        # nodes.
        self.debug = dict()  # type: Dict[str, List[str]]

        # The labels to give to the nodes in the graph.
        self.labels = dict()  # type: Dict[str, str]

    def _normalize(self, symbol):
        return (
            symbol.replace('"', "")
            .replace("(", "")
            .replace("$", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("{", "")
            .replace("}", "")
            .replace("<", "")
            .replace(">", "")
            .replace(",", "")
            .replace(" ", "")
            .replace("-", "_")
            .replace(":", "")
            .replace(".", "_")
            .replace("'", "")
        )

    def _label_normalize(self, label):
        return label.replace('"', '\\"')

    def add_call(
        self, args: List[Any], kwargs: Dict[str, Any], extra: List[str] = []
    ) -> str:
        symbol = self._normalize(f"{repr(kwargs)}_{uuid.uuid4()}")
        self.debug[symbol] = list()
        args_labels = [self._label_normalize(f"{arg}") for arg in args]
        kwargs_labels = [
            self._label_normalize(f"{key}={value}")
            for key, value in kwargs.items()
        ]
        all_arg_labels = args_labels + kwargs_labels
        label = f'{self.function_name}({", ".join(all_arg_labels)})'
        if extra:
            label += "\\n"
        for item in extra:
            label += f"\\n{item}"
        self.labels[symbol] = f'[label = "{label}"]'
        return symbol

    def add_child(self, parent_symbol: str, child_symbol: str):
        self.debug[parent_symbol].append(child_symbol)

    def add_result(self, symbol: str, result: Any):
        result_repr = self._normalize(f"result_{uuid.uuid4()}_{result}")
        self.debug[symbol].append(result_repr)
        result_label = repr(result).replace('"', '\\"')
        self.labels[result_repr] = f'[label = "{result_label}", shape="rect"]'

    def get_dot(self) -> str:
        ret = ["digraph G {"]
        for key, label in self.labels.items():
            ret.append(f"{key} {label};")
        for key, values in self.debug.items():
            for value in values:
                ret.append(f"{key} -> {{ {value} }};")
            ret.append("")
        ret.append("}")
        return "\n".join(ret)
