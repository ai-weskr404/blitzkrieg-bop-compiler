# =============================================================================
# interpreter.py  –  AST-walking interpreter / evaluator
# Authors: Nadales, Russel Rome F. | Ornos, Csypres Klent B.
# Course : CS0035 - Programming Languages
# =============================================================================
# The interpreter visits each node of the AST and either:
#   • executes a statement (VarDecl, Assignment, OutputStmt), or
#   • evaluates an expression and returns a Python int/float
#
# Runtime errors (div-by-zero, None in arithmetic, non-numeric input) are
# surfaced as RuntimeError_ with source-line diagnostics.
# =============================================================================

from __future__ import annotations

from typing import Dict, Optional, Union

from ast_nodes  import (
    ASTNode, Program, VarDecl, Assignment, OutputStmt,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, InputExpr, NodeVisitor,
)
from errors import RuntimeError_, InputError

Number = Union[int, float]


# ---------------------------------------------------------------------------
# Environment  (runtime variable store)
# ---------------------------------------------------------------------------

class Environment:
    """Maps variable names to their current values.

    A value of None means the variable was declared but never initialised.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Optional[Number]] = {}

    def declare(self, name: str, value: Optional[Number] = None) -> None:
        self._store[name] = value

    def assign(self, name: str, value: Number) -> None:
        self._store[name] = value

    def get(self, name: str) -> Optional[Number]:
        return self._store.get(name)

    def all_vars(self) -> Dict[str, Optional[Number]]:
        return dict(self._store)


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class Interpreter(NodeVisitor):
    """Walks the AST produced by Parser and evaluates / executes every node.

    Parameters
    ----------
    source        : original source text (for error messages)
    strict_input  : when True, non-numeric stdin raises InputError instead
                    of attempting a lenient conversion
    io_in         : callable for reading input (default: built-in input)
    io_out        : callable for writing output (default: built-in print)
    """

    def __init__(
        self,
        source:       str       = "",
        *,
        strict_input: bool      = False,
        io_in                   = None,
        io_out                  = None,
    ) -> None:
        self._source       = source
        self._strict_input = strict_input
        self._io_in        = io_in  if io_in  is not None else input
        self._io_out       = io_out if io_out is not None else print
        self.env           = Environment()

    # ── Public entry point ────────────────────────────────────────────────

    def execute(self, program: Program) -> None:
        """Run the entire program. Raises RuntimeError_ on runtime failures."""
        self.visit(program)

    # ── Statement visitors ────────────────────────────────────────────────

    def visit_Program(self, node: Program) -> None:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDecl(self, node: VarDecl) -> None:
        value = None
        if node.initializer is not None:
            value = self._eval(node.initializer)
        self.env.declare(node.name, value)

    def visit_Assignment(self, node: Assignment) -> None:
        value = self._eval(node.value)
        self.env.assign(node.name, value)

    def visit_OutputStmt(self, node: OutputStmt) -> None:
        value = self._eval(node.expr)
        self._io_out(value)

    # ── Expression visitors ───────────────────────────────────────────────

    def visit_NumberLiteral(self, node: NumberLiteral) -> Number:
        return node.value

    def visit_Identifier(self, node: Identifier) -> Number:
        value = self.env.get(node.name)
        if value is None:
            raise RuntimeError_(
                f"Variable '{node.name}' is used before being assigned a value",
                node.line, node.col, self._source,
            )
        return value

    def visit_InputExpr(self, node: InputExpr) -> Number:
        raw = self._io_in()
        raw = raw.strip()
        try:
            return int(raw) if "." not in raw else float(raw)
        except ValueError:
            if self._strict_input:
                raise InputError(
                    f"Non-numeric input {raw!r} (--strict-input is active)",
                    node.line, node.col, self._source,
                )
            # Lenient: try float fallback
            try:
                return float(raw)
            except ValueError:
                raise InputError(
                    f"Cannot convert input {raw!r} to a number",
                    node.line, node.col, self._source,
                )

    def visit_UnaryOp(self, node: UnaryOp) -> Number:
        operand = self._eval(node.operand)
        if node.op == "-":
            return -operand
        raise RuntimeError_(
            f"Unknown unary operator '{node.op}'",
            node.line, node.col, self._source,
        )

    def visit_BinaryOp(self, node: BinaryOp) -> Number:
        left  = self._eval(node.left)
        right = self._eval(node.right)

        # Guard against None (uninitialized) reaching arithmetic
        for val, side in [(left, "left"), (right, "right")]:
            if val is None:
                raise RuntimeError_(
                    f"The {side} operand of '{node.op}' is uninitialized (None)",
                    node.line, node.col, self._source,
                )

        op = node.op
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise RuntimeError_(
                    "Division by zero",
                    node.line, node.col, self._source,
                )
            return left / right
        if op == "^":
            return left ** right

        raise RuntimeError_(
            f"Unknown binary operator '{op}'",
            node.line, node.col, self._source,
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _eval(self, node: ASTNode) -> Number:
        """Evaluate an expression node; guarantee a numeric result or raise."""
        return self.visit(node)