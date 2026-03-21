# =============================================================================
# lexer.py  –  Hand-written lexer for the mini-language
# Authors: Nadales, Russel Rome F. | Ornos, Csypres Klent B.
# Course : CS0035 - Programming Languages
# =============================================================================
# Per project spec:
#   Rule 1 → All statements end in a SEMICOLON.
#   Rule 2 → Whitespace is NOT significant (spaces, tabs, newlines all ignored).
#
# Therefore \n is treated exactly like a space — silently skipped.
# Only ';' produces a statement-terminator token.
# =============================================================================

from __future__ import annotations
from typing import List

from tokens import Token, TT, KEYWORDS
from errors import LexError


class Lexer:
    """Converts raw source text into a flat list of Tokens.

    Parameters
    ----------
    source        : the complete source program as a string
    enable_caret  : when True '^' produces TT.CARET; when False raises LexError
    """

    def __init__(self, source: str, *, enable_caret: bool = True) -> None:
        self._source       = source
        self._enable_caret = enable_caret
        self._pos          = 0
        self._line         = 1
        self._col          = 0

    @property
    def source(self) -> str:
        return self._source

    def tokenize(self) -> List[Token]:
        """Scan the entire source and return the token list (including EOF)."""
        tokens: List[Token] = []
        while not self._at_end():
            tok = self._next_token()
            if tok is not None:
                tokens.append(tok)
        tokens.append(self._make_token(TT.EOF, ""))
        return tokens

    # ── Internal helpers ──────────────────────────────────────────────────

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        return self._source[idx] if idx < len(self._source) else ""

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col   = 0
        else:
            self._col  += 1
        return ch

    def _make_token(self, ttype: str, value: str, *, line: int = -1, col: int = -1) -> Token:
        return Token(ttype, value,
                     line if line >= 0 else self._line,
                     col  if col  >= 0 else self._col)

    # ── Skip helpers ──────────────────────────────────────────────────────

    def _skip_line_comment(self) -> None:
        """Skip from '#' to end of line (newline itself handled as whitespace)."""
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        """Skip /* ... */ block comments (may span multiple lines)."""
        start_line = self._line
        start_col  = self._col
        self._advance()     # consume '*'
        while not self._at_end():
            ch = self._advance()
            if ch == "*" and self._peek() == "/":
                self._advance()     # consume '/'
                return
        raise LexError(
            "Unterminated block comment (missing */)",
            start_line, start_col, self._source,
        )

    # ── Main dispatch ─────────────────────────────────────────────────────

    def _next_token(self) -> Token | None:
        start_line = self._line
        start_col  = self._col
        ch         = self._advance()

        # ── ALL whitespace (spaces, tabs, newlines) → ignored ─────────────
        # Spec rule 2: "Whitespace is not significant"
        if ch in (" ", "\t", "\r", "\n"):
            return None

        # ── Comments ──────────────────────────────────────────────────────
        if ch == "#":
            self._skip_line_comment()
            return None

        if ch == "/" and self._peek() == "*":
            self._skip_block_comment()
            return None

        # ── Single-character tokens ────────────────────────────────────────
        _SIMPLE: dict[str, str] = {
            "+": TT.PLUS,
            "-": TT.MINUS,
            "*": TT.STAR,
            "/": TT.SLASH,
            "=": TT.EQUAL,
            "(": TT.LPAREN,
            ")": TT.RPAREN,
            ";": TT.SEMICOLON,   # ← only valid statement terminator
        }
        if ch in _SIMPLE:
            return Token(_SIMPLE[ch], ch, start_line, start_col)

        # ── Caret (optional exponentiation) ───────────────────────────────
        if ch == "^":
            if not self._enable_caret:
                raise LexError(
                    "Exponentiation operator '^' is disabled (use without --no-exp)",
                    start_line, start_col, self._source,
                )
            return Token(TT.CARET, ch, start_line, start_col)

        # ── Numbers ───────────────────────────────────────────────────────
        if ch.isdigit():
            return self._scan_number(ch, start_line, start_col)

        # ── Identifiers and keywords ───────────────────────────────────────
        if ch.isalpha() or ch == "_":
            return self._scan_ident(ch, start_line, start_col)

        # ── Unknown / illegal character ───────────────────────────────────
        raise LexError(
            f"Unknown character {ch!r}",
            start_line, start_col, self._source,
        )

    # ── Scanners for multi-char tokens ────────────────────────────────────

    def _scan_number(self, first_ch: str, line: int, col: int) -> Token:
        buf = first_ch
        while not self._at_end() and self._peek().isdigit():
            buf += self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            buf += self._advance()
            while not self._at_end() and self._peek().isdigit():
                buf += self._advance()
            return Token(TT.FLOAT, buf, line, col)
        return Token(TT.INTEGER, buf, line, col)

    def _scan_ident(self, first_ch: str, line: int, col: int) -> Token:
        buf = first_ch
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            buf += self._advance()
        ttype = KEYWORDS.get(buf, TT.IDENT)
        return Token(ttype, buf, line, col)