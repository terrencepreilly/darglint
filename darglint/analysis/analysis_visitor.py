from .raise_visitor import RaiseVisitor
from .return_visitor import ReturnVisitor
from .yield_visitor import YieldVisitor
from .function_scoped_visitor import FunctionScopedVisitorMixin


class AnalysisVisitor(RaiseVisiter,
                      YieldVisitor,
                      ReturnVisitor,
                      FunctionScopedVisitorMixin):
    """Finds attributes which should be part of the function signature."""
    pass
