# =============================================================================
# ast_nodes.py  –  Abstract Syntax Tree node definitions
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# Each node is a frozen dataclass so the tree is immutable after parsing.
# The 'line' and 'col' fields on every node let error messages pinpoint
# the exact source location of a semantic / runtime problem.
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing      import List, Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ASTNode:
    """Abstract base for every node in the syntax tree."""
    line: int = field(compare=False, repr=False)
    col:  int = field(compare=False, repr=False)


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Program(ASTNode):
    """Root node – holds an ordered list of statements."""
    statements: tuple  # tuple[ASTNode, ...]


@dataclass(frozen=True)
class VarDecl(ASTNode):
    """var x  or  var x = expr"""
    name:        str
    initializer: Optional[ASTNode]    # None if no initializer


@dataclass(frozen=True)
class Assignment(ASTNode):
    """x = expr"""
    name:  str
    value: ASTNode


@dataclass(frozen=True)
class OutputStmt(ASTNode):
    """output expr"""
    expr: ASTNode


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """Left <op> Right"""
    op:    str          # one of: + - * / ^
    left:  ASTNode
    right: ASTNode


@dataclass(frozen=True)
class UnaryOp(ASTNode):
    """Unary minus:  -expr"""
    op:      str        # '-'
    operand: ASTNode


@dataclass(frozen=True)
class NumberLiteral(ASTNode):
    """An integer or float literal."""
    value: int | float


@dataclass(frozen=True)
class Identifier(ASTNode):
    """A variable reference."""
    name: str


@dataclass(frozen=True)
class InputExpr(ASTNode):
    """The 'input' keyword used inside an expression – reads from stdin."""
    pass


# ---------------------------------------------------------------------------
# Visitor helper  (not required, but useful for semantic pass & interpreter)
# ---------------------------------------------------------------------------

class NodeVisitor:
    """Simple visitor base class.

    Subclasses implement visit_<ClassName>(node) methods.
    Call self.visit(node) to dispatch.
    """

    def visit(self, node: ASTNode):
        method_name = f"visit_{type(node).__name__}"
        visitor     = getattr(self, method_name, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node: ASTNode):
        raise NotImplementedError(
            f"{type(self).__name__} has no visitor for {type(node).__name__}"
        )