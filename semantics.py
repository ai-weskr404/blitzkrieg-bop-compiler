# =============================================================================
# semantics.py  –  Semantic analysis pass
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# The semantic pass walks the AST *before* execution to catch:
#   1. Use of an undeclared variable
#   2. Duplicate variable declarations
#   3. Assignment to an undeclared variable
# All errors raise SemanticError with line/col information.
# =============================================================================

from __future__ import annotations

from typing import Set

from ast_nodes  import (
    ASTNode, Program, VarDecl, Assignment, OutputStmt,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, InputExpr, NodeVisitor,
)
from errors import SemanticError


# ---------------------------------------------------------------------------
# Symbol table  (simple set of declared names for this single-scope language)
# ---------------------------------------------------------------------------

class SymbolTable:
    """Tracks declared variable names in the current scope."""

    def __init__(self) -> None:
        self._declared: Set[str] = set()

    def declare(self, name: str) -> None:
        self._declared.add(name)

    def is_declared(self, name: str) -> bool:
        return name in self._declared

    def all_names(self) -> Set[str]:
        return frozenset(self._declared)


# ---------------------------------------------------------------------------
# SemanticAnalyzer
# ---------------------------------------------------------------------------

class SemanticAnalyzer(NodeVisitor):
    """Single-pass semantic visitor.

    Usage
    -----
    analyzer = SemanticAnalyzer(source)
    analyzer.analyze(program_node)   # raises SemanticError on first violation
    symbol_table = analyzer.symbols  # available after analysis succeeds
    """

    def __init__(self, source: str = "") -> None:
        self._source  = source
        self.symbols  = SymbolTable()

    # ── Entry point ───────────────────────────────────────────────────────

    def analyze(self, program: Program) -> None:
        """Walk the program AST and perform semantic checks."""
        self.visit(program)

    # ── Statement visitors ────────────────────────────────────────────────

    def visit_Program(self, node: Program) -> None:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDecl(self, node: VarDecl) -> None:
        # Check for duplicate declaration
        if self.symbols.is_declared(node.name):
            raise SemanticError(
                f"Variable '{node.name}' is already declared",
                node.line, node.col, self._source,
            )
        self.symbols.declare(node.name)

        # Validate the initializer expression (if present)
        if node.initializer is not None:
            self.visit(node.initializer)

    def visit_Assignment(self, node: Assignment) -> None:
        if not self.symbols.is_declared(node.name):
            raise SemanticError(
                f"Assignment to undeclared variable '{node.name}'. "
                f"Declare it first with:  var {node.name}",
                node.line, node.col, self._source,
            )
        self.visit(node.value)

    def visit_OutputStmt(self, node: OutputStmt) -> None:
        self.visit(node.expr)

    # ── Expression visitors ───────────────────────────────────────────────

    def visit_BinaryOp(self, node: BinaryOp) -> None:
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: UnaryOp) -> None:
        self.visit(node.operand)

    def visit_NumberLiteral(self, node: NumberLiteral) -> None:
        pass            # always valid

    def visit_Identifier(self, node: Identifier) -> None:
        if not self.symbols.is_declared(node.name):
            raise SemanticError(
                f"Use of undeclared variable '{node.name}'",
                node.line, node.col, self._source,
            )

    def visit_InputExpr(self, node: InputExpr) -> None:
        pass            # input is valid anywhere an expression is expected