# =============================================================================
# tokens.py  –  Token types and Token dataclass
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0057 - Programming Languages
# =============================================================================
# Extends the Token NamedTuple pattern from Technical Assessments 1 & 2.
# =============================================================================

from typing import NamedTuple


# ---------------------------------------------------------------------------
# Token type constants  (strings keep error messages human-readable)
# ---------------------------------------------------------------------------

class TT:
    """Namespace for all token-type string constants."""

    # ── Literals ──────────────────────────────────────────────────────────
    INTEGER   = "INTEGER"
    FLOAT     = "FLOAT"
    STRING    = "STRING"          # future-proof; not used in v1 grammar

    # ── Keywords ──────────────────────────────────────────────────────────
    VAR       = "VAR"
    INPUT     = "INPUT"
    OUTPUT    = "OUTPUT"

    # ── Identifier ────────────────────────────────────────────────────────
    IDENT     = "IDENT"

    # ── Arithmetic operators ──────────────────────────────────────────────
    PLUS      = "PLUS"            # +
    MINUS     = "MINUS"           # -
    STAR      = "STAR"            # *
    SLASH     = "SLASH"           # /
    CARET     = "CARET"           # ^  (optional exponentiation)

    # ── Assignment ────────────────────────────────────────────────────────
    EQUAL     = "EQUAL"           # =

    # ── Grouping ──────────────────────────────────────────────────────────
    LPAREN    = "LPAREN"          # (
    RPAREN    = "RPAREN"          # )

    # ── Statement terminators ─────────────────────────────────────────────
    NEWLINE   = "NEWLINE"         # \n (treated as statement boundary)
    SEMICOLON = "SEMICOLON"       # ;

    # ── End of file ───────────────────────────────────────────────────────
    EOF       = "EOF"

    # ── Error sentinel (mirrors T2 SYNTAX_ERROR convention) ───────────────
    SYNTAX_ERROR = "SYNTAX_ERROR"


# Mapping of keyword strings → token types
KEYWORDS: dict[str, str] = {
    "var":    TT.VAR,
    "input":  TT.INPUT,
    "output": TT.OUTPUT,
}


# ---------------------------------------------------------------------------
# Token  –  extends the NamedTuple pattern from T1 / T2
# ---------------------------------------------------------------------------

class Token(NamedTuple):
    """Immutable record produced by the Lexer.

    Attributes
    ----------
    type    : one of the TT.* constants
    value   : raw text captured from source
    line    : 1-based line number
    column  : 0-based column index within the line
    """
    type:   str
    value:  str
    line:   int
    column: int

    # ── Convenience helpers ───────────────────────────────────────────────

    def is_eol(self) -> bool:
        """Return True if this token acts as a statement terminator."""
        return self.type in (TT.NEWLINE, TT.SEMICOLON)

    def __repr__(self) -> str:          # compact for debug / --trace
        return f"Token({self.type}, {self.value!r}, Ln {self.line} Col {self.column})"