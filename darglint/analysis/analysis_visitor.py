from .raise_visitor import RaiseVisitor
from .return_visitor import ReturnVisitor
from .yield_visitor import YieldVisitor
from .function_scoped_visitor import FunctionScopedVisitorMixin
from .argument_visitor import ArgumentVisitor
from .assert_visitor import AssertVisitor
from .variable_visitor import VariableVisitor


class AnalysisVisitor(FunctionScopedVisitorMixin,
                      RaiseVisitor,
                      YieldVisitor,
                      ArgumentVisitor,
                      VariableVisitor,
                      ReturnVisitor,
                      AssertVisitor):
    """Finds attributes which should be part of the function signature."""
    pass
