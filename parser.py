# =============================================================================
# parser.py  –  Recursive-descent parser
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# Per project spec rule 1: ALL statements MUST end with a semicolon.
# Newlines are insignificant whitespace (already dropped by the Lexer).
# Therefore _consume_eol() ONLY accepts TT.SEMICOLON — nothing else.
#
# Grammar (EBNF):
#   program   := { statement } EOF
#   statement := vardecl | assign | outstmt
#   vardecl   := "var" IDENT [ "=" expr ] ";"
#   assign    := IDENT "=" expr ";"
#   outstmt   := "output" expr ";"
#
#   expr      := term    { ("+" | "-")  term    }
#   term      := power   { ("*" | "/")  power   }
#   power     := unary   { "^"          unary   }   # right-assoc via recursion
#   unary     := "-" unary | factor
#   factor    := NUMBER | IDENT | "input" | "(" expr ")"
# =============================================================================

from __future__ import annotations
from typing import List, Optional

from tokens    import Token, TT
from ast_nodes import (
    ASTNode, Program, VarDecl, Assignment, OutputStmt,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, InputExpr,
)
from errors import ParseError


class Parser:
    """Converts a token list produced by the Lexer into an AST."""

    def __init__(self, tokens: List[Token], source: str = "") -> None:
        self._tokens = tokens
        self._source = source
        self._pos    = 0

    # ── Public entry point ────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts: list[ASTNode] = []
        while not self._check(TT.EOF):
            stmt = self._statement()
            if stmt is not None:
                stmts.append(stmt)
        self._expect(TT.EOF)
        first_tok = self._tokens[0]
        return Program(statements=tuple(stmts), line=first_tok.line, col=first_tok.column)

    # ── Token-stream helpers ──────────────────────────────────────────────

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = self._pos + offset
        return self._tokens[idx] if idx < len(self._tokens) else self._tokens[-1]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return tok

    def _check(self, *types: str) -> bool:
        return self._current().type in types

    def _match(self, *types: str) -> Optional[Token]:
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, ttype: str, *, msg: str = "") -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._current()
        default_msg = f"Expected {ttype}, but found {tok.type} ({tok.value!r})"
        raise ParseError(msg or default_msg, tok.line, tok.column, self._source)

    def _consume_semicolon(self) -> None:
        """Require a semicolon — the ONLY valid statement terminator per spec rule 1."""
        if not self._check(TT.SEMICOLON):
            tok = self._current()
            raise ParseError(
                f"Missing ';' at end of statement — found {tok.type} ({tok.value!r}) instead.\n"
                f"  Spec rule 1: ALL statements must end with a semicolon.",
                tok.line, tok.column, self._source,
            )
        self._advance()     # consume the ';'

    # ── Statements ────────────────────────────────────────────────────────

    def _statement(self) -> Optional[ASTNode]:
        tok = self._current()

        if tok.type == TT.VAR:
            return self._var_decl()

        if tok.type == TT.OUTPUT:
            return self._output_stmt()

        if tok.type == TT.IDENT:
            if self._peek().type == TT.EQUAL:
                return self._assignment()
            else:
                raise ParseError(
                    f"Unexpected identifier {tok.value!r} — "
                    "did you mean 'output' or an assignment?",
                    tok.line, tok.column, self._source,
                )

        raise ParseError(
            f"Unexpected token {tok.type} ({tok.value!r}) at start of statement",
            tok.line, tok.column, self._source,
        )

    def _var_decl(self) -> VarDecl:
        """var IDENT [ '=' expr ] ';'"""
        kw   = self._advance()
        name = self._expect(TT.IDENT, msg="Expected an identifier after 'var'")
        initializer: Optional[ASTNode] = None
        if self._match(TT.EQUAL):
            initializer = self._expr()
        self._consume_semicolon()
        return VarDecl(name=name.value, initializer=initializer,
                       line=kw.line, col=kw.column)

    def _assignment(self) -> Assignment:
        """IDENT '=' expr ';'"""
        name = self._advance()
        self._expect(TT.EQUAL)
        value = self._expr()
        self._consume_semicolon()
        return Assignment(name=name.value, value=value,
                          line=name.line, col=name.column)

    def _output_stmt(self) -> OutputStmt:
        """'output' expr ';'"""
        kw   = self._advance()
        expr = self._expr()
        self._consume_semicolon()
        return OutputStmt(expr=expr, line=kw.line, col=kw.column)

    # ── Expressions ───────────────────────────────────────────────────────

    def _expr(self) -> ASTNode:
        left = self._term()
        while self._check(TT.PLUS, TT.MINUS):
            op_tok = self._advance()
            right  = self._term()
            left   = BinaryOp(op=op_tok.value, left=left, right=right,
                               line=op_tok.line, col=op_tok.column)
        return left

    def _term(self) -> ASTNode:
        left = self._power()
        while self._check(TT.STAR, TT.SLASH):
            op_tok = self._advance()
            right  = self._power()
            left   = BinaryOp(op=op_tok.value, left=left, right=right,
                               line=op_tok.line, col=op_tok.column)
        return left

    def _power(self) -> ASTNode:
        base = self._unary()
        if self._check(TT.CARET):
            op_tok = self._advance()
            exp    = self._power()
            return BinaryOp(op="^", left=base, right=exp,
                            line=op_tok.line, col=op_tok.column)
        return base

    def _unary(self) -> ASTNode:
        if self._check(TT.MINUS):
            op_tok  = self._advance()
            operand = self._unary()
            return UnaryOp(op="-", operand=operand,
                           line=op_tok.line, col=op_tok.column)
        return self._factor()

    def _factor(self) -> ASTNode:
        tok = self._current()

        if tok.type == TT.INTEGER:
            self._advance()
            return NumberLiteral(value=int(tok.value), line=tok.line, col=tok.column)

        if tok.type == TT.FLOAT:
            self._advance()
            return NumberLiteral(value=float(tok.value), line=tok.line, col=tok.column)

        if tok.type == TT.IDENT:
            self._advance()
            return Identifier(name=tok.value, line=tok.line, col=tok.column)

        if tok.type == TT.INPUT:
            self._advance()
            return InputExpr(line=tok.line, col=tok.column)

        if tok.type == TT.LPAREN:
            self._advance()
            inner = self._expr()
            self._expect(TT.RPAREN, msg="Expected ')' to close parenthesised expression")
            return inner

        raise ParseError(
            f"Expected a value or expression, but found {tok.type} ({tok.value!r})",
            tok.line, tok.column, self._source,
        )