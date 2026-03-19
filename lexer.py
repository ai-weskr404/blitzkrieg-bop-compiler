# =============================================================================
# lexer.py  –  Hand-written lexer for the mini-language
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0057 - Programming Languages
# =============================================================================
# Architecture is a direct evolution of the regex-based tokenizer from
# Technical Assessments 1 and 2, refactored into a class with:
#   • line / column tracking
#   • both /* ... */ block comments (project spec) and # line comments
#   • --trace-friendly token list output
#   • precise error positions via LexError
# =============================================================================

from __future__ import annotations

from typing import List

from tokens  import Token, TT, KEYWORDS
from errors  import LexError


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class Lexer:
    """Converts raw source text into a flat list of Tokens.

    Parameters
    ----------
    source      : the complete source program as a string
    enable_caret: when True the '^' character produces TT.CARET tokens;
                  when False it raises a LexError (mirrors --no-exp flag)
    """

    def __init__(self, source: str, *, enable_caret: bool = True) -> None:
        self._source       = source
        self._enable_caret = enable_caret
        self._pos          = 0             # current character index
        self._line         = 1             # current 1-based line
        self._col          = 0             # current 0-based column

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def source(self) -> str:
        return self._source

    def tokenize(self) -> List[Token]:
        """Scan the entire source and return the token list (including EOF)."""
        tokens: List[Token] = []

        while not self._at_end():
            tok = self._next_token()
            if tok is not None:             # None == whitespace was consumed
                tokens.append(tok)

        tokens.append(self._make_token(TT.EOF, ""))
        return tokens

    # ── Internal helpers ──────────────────────────────────────────────────

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _peek(self, offset: int = 0) -> str:
        """Return character at pos+offset without advancing, or '' if past end."""
        idx = self._pos + offset
        return self._source[idx] if idx < len(self._source) else ""

    def _advance(self) -> str:
        """Consume and return the current character; update line/col tracking."""
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col   = 0
        else:
            self._col  += 1
        return ch

    def _make_token(self, ttype: str, value: str, *, line: int = -1, col: int = -1) -> Token:
        return Token(ttype, value, line if line >= 0 else self._line,
                                   col  if col  >= 0 else self._col)

    # ── Skip helpers ──────────────────────────────────────────────────────

    def _skip_line_comment(self) -> None:
        """Skip from '#' to end of line (does NOT consume the newline itself)."""
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        """Skip /* ... */ block comments that may span multiple lines."""
        start_line = self._line
        start_col  = self._col
        self._advance()  # consume '*' (caller already consumed '/')
        while not self._at_end():
            ch = self._advance()
            if ch == "*" and self._peek() == "/":
                self._advance()  # consume closing '/'
                return
        # Reached EOF without closing */
        raise LexError(
            "Unterminated block comment (missing */)",
            start_line, start_col, self._source,
        )

    # ── Main dispatch ─────────────────────────────────────────────────────

    def _next_token(self) -> Token | None:
        """Scan one logical token and return it, or None for ignored whitespace."""
        start_line = self._line
        start_col  = self._col
        ch         = self._advance()

        # ── Whitespace (non-newline) ───────────────────────────────────────
        if ch in (" ", "\t", "\r"):
            return None                         # silently skip

        # ── Newline (statement boundary) ──────────────────────────────────
        if ch == "\n":
            return Token(TT.NEWLINE, "\\n", start_line, start_col)

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
            ";": TT.SEMICOLON,
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
        """Consume an integer or floating-point literal."""
        buf = first_ch
        while not self._at_end() and self._peek().isdigit():
            buf += self._advance()

        # Optional decimal part
        if self._peek() == "." and self._peek(1).isdigit():
            buf += self._advance()              # consume '.'
            while not self._at_end() and self._peek().isdigit():
                buf += self._advance()
            return Token(TT.FLOAT, buf, line, col)

        return Token(TT.INTEGER, buf, line, col)

    def _scan_ident(self, first_ch: str, line: int, col: int) -> Token:
        """Consume an identifier; check keyword table."""
        buf = first_ch
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            buf += self._advance()

        ttype = KEYWORDS.get(buf, TT.IDENT)
        return Token(ttype, buf, line, col)