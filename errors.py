# =============================================================================
# errors.py  –  Compiler error hierarchy with pretty diagnostics
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# Every error carries the original source text so it can render a
# "line preview + caret" indicator, e.g.:
#
#   LexError at line 3, col 5:
#       var @bad = 10;
#            ^
#   Unknown character '@'
# =============================================================================

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class CompilerError(Exception):
    """Root of the compiler error hierarchy.

    Parameters
    ----------
    message    : human-readable description of the error
    line       : 1-based line number in source (0 = unknown)
    column     : 0-based column index          (−1 = unknown)
    source     : full source string, used to render the caret line
    """

    label = "CompilerError"          # overridden in subclasses

    def __init__(
        self,
        message: str,
        line:    int  = 0,
        column:  int  = -1,
        source:  str  = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line    = line
        self.column  = column
        self.source  = source

    # ── Rendering ─────────────────────────────────────────────────────────

    def _source_line(self) -> str:
        """Return the text of the offending source line (stripped of \n)."""
        if not self.source or self.line < 1:
            return ""
        lines = self.source.splitlines()
        idx   = self.line - 1
        return lines[idx] if idx < len(lines) else ""

    def pretty(self) -> str:
        """Multi-line formatted error string for terminal display."""
        loc    = f"line {self.line}" if self.line else "unknown location"
        if self.column >= 0:
            loc += f", col {self.column}"

        src_line = self._source_line()
        lines = [
            f"\033[91m{self.label}\033[0m at {loc}:",
        ]
        if src_line:
            # indent source line and add caret
            lines.append(f"    {src_line}")
            if self.column >= 0:
                caret_pos = self.column + 4          # offset for the 4-space indent
                lines.append(" " * caret_pos + "\033[93m^\033[0m")
        lines.append(f"  {self.message}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.pretty()


# ---------------------------------------------------------------------------
# Specialisations
# ---------------------------------------------------------------------------

class LexError(CompilerError):
    """Raised by the Lexer when it encounters an illegal character sequence."""
    label = "LexError"


class ParseError(CompilerError):
    """Raised by the Parser when the token stream violates the grammar."""
    label = "ParseError"


class SemanticError(CompilerError):
    """Raised during semantic analysis (undeclared vars, type issues, etc.)."""
    label = "SemanticError"


class RuntimeError_(CompilerError):
    """Raised during interpretation (div-by-zero, None arithmetic, etc.).

    Named RuntimeError_ to avoid shadowing Python's built-in RuntimeError.
    """
    label = "RuntimeError"


class InputError(CompilerError):
    """Raised when --strict-input is active and user enters non-numeric text."""
    label = "InputError"