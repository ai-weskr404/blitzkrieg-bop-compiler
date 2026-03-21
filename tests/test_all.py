# =============================================================================
# tests/test_all.py  –  Unit tests for the mini-compiler pipeline
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# Run with:  python -m pytest tests/ -v
# (No external packages required beyond pytest)
#
# All code strings use semicolons per spec rule 1.
# Newlines are insignificant whitespace — they do NOT terminate statements.
# =============================================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from tokens      import Token, TT
from lexer       import Lexer
from parser      import Parser
from semantics   import SemanticAnalyzer
from interpreter import Interpreter
from errors      import LexError, ParseError, SemanticError, RuntimeError_, InputError
from cli         import run_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def lex(code: str, **kw) -> list:
    return Lexer(code, **kw).tokenize()

def token_types(code: str, **kw) -> list:
    # NEWLINE tokens no longer exist — newlines are silently skipped
    return [t.type for t in lex(code, **kw) if t.type != TT.EOF]

def run(code: str, inputs=None, **kw) -> list:
    outputs = []
    input_iter = iter(inputs or [])
    run_pipeline(
        code,
        io_in  = lambda: next(input_iter),
        io_out = outputs.append,
        **kw,
    )
    return outputs


# =============================================================================
# LEXER TESTS
# =============================================================================

class TestLexer:

    def test_keywords(self):
        types = token_types("var input output")
        assert TT.VAR    in types
        assert TT.INPUT  in types
        assert TT.OUTPUT in types

    def test_integer_literal(self):
        toks = [t for t in lex("42") if t.type != TT.EOF]
        assert toks[0].type  == TT.INTEGER
        assert toks[0].value == "42"

    def test_float_literal(self):
        toks = [t for t in lex("3.14") if t.type != TT.EOF]
        assert toks[0].type  == TT.FLOAT
        assert toks[0].value == "3.14"

    def test_operators(self):
        types = token_types("+ - * / =")
        assert TT.PLUS  in types
        assert TT.MINUS in types
        assert TT.STAR  in types
        assert TT.SLASH in types
        assert TT.EQUAL in types

    def test_semicolon_token(self):
        types = token_types(";")
        assert TT.SEMICOLON in types

    def test_newline_is_skipped(self):
        # Newlines are insignificant whitespace — no NEWLINE tokens produced
        types = token_types("var\nx")
        assert "NEWLINE" not in types
        assert TT.VAR   in types
        assert TT.IDENT in types

    def test_no_newline_tokens_ever(self):
        toks = lex("var x;\nvar y;\n")
        assert all(t.type != "NEWLINE" for t in toks)

    def test_caret_enabled(self):
        types = token_types("2 ^ 3", enable_caret=True)
        assert TT.CARET in types

    def test_caret_disabled(self):
        with pytest.raises(LexError):
            lex("2 ^ 3", enable_caret=False)

    def test_hash_comment_ignored(self):
        types = token_types("# this is a comment\nvar x")
        assert TT.VAR   in types
        assert TT.IDENT in types

    def test_block_comment_ignored(self):
        types = token_types("/* comment */ var x")
        assert TT.VAR   in types
        assert TT.IDENT in types

    def test_multiline_block_comment(self):
        code  = "var x /* this\nspans\nlines */ = 5;"
        types = token_types(code)
        assert TT.VAR   in types
        assert TT.IDENT in types
        assert TT.EQUAL in types

    def test_unterminated_block_comment(self):
        with pytest.raises(LexError, match="Unterminated"):
            lex("/* oops")

    def test_unknown_character(self):
        with pytest.raises(LexError, match="Unknown character"):
            lex("@bad")

    def test_line_tracking(self):
        # Even though \n is whitespace, line numbers still advance
        toks = [t for t in lex("var x;\nvar y;") if t.type == TT.IDENT]
        assert toks[0].line == 1
        assert toks[1].line == 2

    def test_column_tracking(self):
        toks = [t for t in lex("var x;") if t.type == TT.IDENT]
        assert toks[0].column == 4

    def test_parentheses(self):
        types = token_types("(x + y)")
        assert TT.LPAREN in types
        assert TT.RPAREN in types

    def test_eof_always_present(self):
        toks = lex("var x;")
        assert toks[-1].type == TT.EOF


# =============================================================================
# PARSER TESTS
# =============================================================================

class TestParser:

    def _parse(self, code: str):
        tokens = lex(code)
        return Parser(tokens, code).parse()

    def test_parse_vardecl_no_init(self):
        from ast_nodes import VarDecl
        prog = self._parse("var x;")
        assert isinstance(prog.statements[0], VarDecl)
        assert prog.statements[0].name == "x"

    def test_parse_vardecl_with_init(self):
        from ast_nodes import VarDecl, NumberLiteral
        prog = self._parse("var x = 5;")
        stmt = prog.statements[0]
        assert isinstance(stmt, VarDecl)
        assert isinstance(stmt.initializer, NumberLiteral)
        assert stmt.initializer.value == 5

    def test_parse_assignment(self):
        from ast_nodes import VarDecl, Assignment
        prog = self._parse("var x; x = 10;")
        assert isinstance(prog.statements[1], Assignment)

    def test_parse_output(self):
        from ast_nodes import VarDecl, OutputStmt
        prog = self._parse("var x = 1; output x;")
        assert isinstance(prog.statements[1], OutputStmt)

    def test_missing_semicolon_vardecl(self):
        with pytest.raises(ParseError, match="semicolon"):
            self._parse("var x")

    def test_missing_semicolon_assignment(self):
        with pytest.raises(ParseError, match="semicolon"):
            self._parse("var x; x = 5")

    def test_missing_semicolon_output(self):
        with pytest.raises(ParseError, match="semicolon"):
            self._parse("var x = 1; output x")

    def test_binary_op_precedence(self):
        from ast_nodes import BinaryOp
        tokens = lex("var r = 2 + 3 * 4;")
        prog   = Parser(tokens).parse()
        expr   = prog.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.op == "*"

    def test_parentheses_override_precedence(self):
        from ast_nodes import BinaryOp
        tokens = lex("var r = (2 + 3) * 4;")
        prog   = Parser(tokens).parse()
        expr   = prog.statements[0].initializer
        assert isinstance(expr, BinaryOp)
        assert expr.op == "*"

    def test_right_associative_exponent(self):
        from ast_nodes import BinaryOp
        tokens = lex("var r = 2 ^ 3 ^ 2;")
        prog   = Parser(tokens).parse()
        expr   = prog.statements[0].initializer
        assert isinstance(expr, BinaryOp) and expr.op == "^"
        assert isinstance(expr.right, BinaryOp) and expr.right.op == "^"

    def test_unary_minus(self):
        from ast_nodes import UnaryOp
        tokens = lex("var r = -5;")
        prog   = Parser(tokens).parse()
        expr   = prog.statements[0].initializer
        assert isinstance(expr, UnaryOp) and expr.op == "-"

    def test_missing_rparen_raises(self):
        with pytest.raises(ParseError):
            tokens = lex("var r = (1 + 2;")
            Parser(tokens).parse()

    def test_multiline_no_error(self):
        # Newlines are whitespace — spreading across lines is fine with semicolons
        prog = self._parse("var x = 5;\nvar y = 10;\noutput x;")
        assert len(prog.statements) == 3


# =============================================================================
# SEMANTIC TESTS
# =============================================================================

class TestSemantics:

    def _analyze(self, code: str):
        tokens   = lex(code)
        prog     = Parser(tokens, code).parse()
        analyzer = SemanticAnalyzer(code)
        analyzer.analyze(prog)
        return analyzer

    def test_undeclared_use_raises(self):
        with pytest.raises(SemanticError, match="undeclared"):
            self._analyze("output x;")

    def test_undeclared_assignment_raises(self):
        with pytest.raises(SemanticError, match="undeclared"):
            self._analyze("x = 5;")

    def test_duplicate_declaration_raises(self):
        with pytest.raises(SemanticError, match="already declared"):
            self._analyze("var x; var x;")

    def test_valid_program_passes(self):
        analyzer = self._analyze("var x = 5; var y = x + 1; output y;")
        assert analyzer.symbols.is_declared("x")
        assert analyzer.symbols.is_declared("y")

    def test_use_before_declaration_raises(self):
        with pytest.raises(SemanticError):
            self._analyze("output z; var z = 1;")


# =============================================================================
# INTERPRETER TESTS
# =============================================================================

class TestInterpreter:

    def test_simple_output(self):
        assert run("var x = 5; output x;") == [5]

    def test_addition(self):
        assert run("var r = 3 + 4; output r;") == [7]

    def test_subtraction(self):
        assert run("var r = 10 - 3; output r;") == [7]

    def test_multiplication(self):
        assert run("var r = 6 * 7; output r;") == [42]

    def test_division(self):
        result = run("var r = 10 / 4; output r;")
        assert abs(result[0] - 2.5) < 1e-9

    def test_exponentiation(self):
        assert run("var r = 2 ^ 10; output r;") == [1024]

    def test_right_associative_exp(self):
        assert run("var r = 2 ^ 3 ^ 2; output r;") == [512]

    def test_operator_precedence(self):
        assert run("var r = 2 + 3 * 4; output r;") == [14]

    def test_parentheses(self):
        assert run("var r = (2 + 3) * 4; output r;") == [20]

    def test_unary_minus(self):
        assert run("var r = -5; output r;") == [-5]

    def test_input_expression(self):
        result = run("var x = input; output x;", inputs=["7"])
        assert result == [7]

    def test_reassignment(self):
        result = run("var x = 1; x = 99; output x;")
        assert result == [99]

    def test_multiline_program(self):
        # Newlines are whitespace — should work fine
        result = run("var x = 5;\nvar y = 10;\noutput x + y;")
        assert result == [15]

    def test_division_by_zero(self):
        assert run_pipeline("var r = 10 / 0; output r;") == 1

    def test_none_in_arithmetic(self):
        assert run_pipeline("var x; var r = x + 1; output r;") == 1

    def test_non_numeric_input_strict(self):
        assert run_pipeline(
            "var x = input; output x;",
            io_in=lambda: "hello",
            strict_input=True,
        ) == 1

    def test_multiple_outputs(self):
        result = run("var a = 1; var b = 2; output a; output b;")
        assert result == [1, 2]

    def test_block_comment(self):
        result = run("var x = /* ignored */ 5; output x;")
        assert result == [5]

    def test_complex_expr(self):
        result = run("var a = 10; var b = 3; var r = (a + b) * (a - b); output r;")
        assert result == [91]


# =============================================================================
# INTEGRATION / PIPELINE TESTS
# =============================================================================

class TestPipeline:

    def test_exit_code_success(self):
        assert run_pipeline("var x = 1; output x;", io_out=lambda _: None) == 0

    def test_exit_code_missing_semicolon(self):
        assert run_pipeline("var x = 1") == 1

    def test_exit_code_lex_error(self):
        assert run_pipeline("@bad;") == 1

    def test_exit_code_semantic_error(self):
        assert run_pipeline("output z;") == 1

    def test_exit_code_runtime_error(self):
        assert run_pipeline("var x = 1 / 0; output x;") == 1

    def test_no_exp_flag(self):
        assert run_pipeline("var x = 2 ^ 3; output x;", enable_caret=False) == 1