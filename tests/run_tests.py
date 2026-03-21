#!/usr/bin/env python3
"""Quick test runner – no external dependencies."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lexer       import Lexer
from parser      import Parser
from semantics   import SemanticAnalyzer
from interpreter import Interpreter
from cli         import run_pipeline
from errors      import LexError, ParseError, SemanticError, RuntimeError_, InputError

passed = 0
failed = 0

def eq(a, b):
    assert a == b, f"{a!r} != {b!r}"

def raises(fn, exc):
    try:
        fn()
        raise AssertionError(f"Expected {exc.__name__} but nothing was raised")
    except exc:
        pass

def check(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  \033[92m✓\033[0m {name}")
        passed += 1
    except Exception as e:
        print(f"  \033[91m✗\033[0m {name}: {e}")
        failed += 1

def run(code, inputs=None, **kw):
    outputs = []
    input_iter = iter(inputs or [])
    run_pipeline(code, io_in=lambda: next(input_iter), io_out=outputs.append, **kw)
    return outputs

# ── LEXER ─────────────────────────────────────────────────────────────────────
print("\n\033[1m── LEXER ──\033[0m")
check("integer token",       lambda: eq(Lexer("42").tokenize()[0].type, "INTEGER"))
check("float token",         lambda: eq(Lexer("3.14").tokenize()[0].type, "FLOAT"))
check("keyword var",         lambda: eq(Lexer("var").tokenize()[0].type, "VAR"))
check("keyword input",       lambda: eq(Lexer("input").tokenize()[0].type, "INPUT"))
check("keyword output",      lambda: eq(Lexer("output").tokenize()[0].type, "OUTPUT"))
check("identifier",          lambda: eq(Lexer("myVar").tokenize()[0].type, "IDENT"))
check("semicolon token",     lambda: eq(Lexer(";").tokenize()[0].type, "SEMICOLON"))
check("newline skipped",     lambda: eq(Lexer("var\nx").tokenize()[0].type, "VAR"))  # \n is whitespace
check("caret enabled",       lambda: eq(Lexer("^", enable_caret=True).tokenize()[0].type, "CARET"))
check("caret disabled",      lambda: raises(lambda: Lexer("^", enable_caret=False).tokenize(), LexError))
check("hash comment",        lambda: eq(len([t for t in Lexer("# hi\nvar x").tokenize() if t.type not in ("EOF",)]), 2))
check("block comment",       lambda: eq(len([t for t in Lexer("/* hi */var x").tokenize() if t.type not in ("EOF",)]), 2))
check("multiline comment",   lambda: eq(len([t for t in Lexer("/* a\nb */var x").tokenize() if t.type not in ("EOF",)]), 2))
check("unknown char raises",  lambda: raises(lambda: Lexer("@x").tokenize(), LexError))
check("no NEWLINE tokens",   lambda: eq(all(t.type != "NEWLINE" for t in Lexer("var\nx\n").tokenize()), True))
check("EOF always present",  lambda: eq(Lexer("var x").tokenize()[-1].type, "EOF"))

# ── PARSER ────────────────────────────────────────────────────────────────────
from ast_nodes import VarDecl, Assignment, OutputStmt, BinaryOp, UnaryOp, NumberLiteral

def parse(code):
    toks = Lexer(code).tokenize()
    return Parser(toks, code).parse()

print("\n\033[1m── PARSER ──\033[0m")
check("vardecl with semicolon",    lambda: eq(isinstance(parse("var x;").statements[0], VarDecl), True))
check("vardecl with init + semi",  lambda: eq(parse("var x = 5;").statements[0].initializer.value, 5))
check("assignment with semi",      lambda: eq(isinstance(parse("var x; x = 10;").statements[1], Assignment), True))
check("output with semi",          lambda: eq(isinstance(parse("var x = 1; output x;").statements[1], OutputStmt), True))
check("missing semicolon → error", lambda: raises(lambda: parse("var x"), ParseError))
check("missing semi on assign",    lambda: raises(lambda: parse("var x; x = 5"), ParseError))
check("missing semi on output",    lambda: raises(lambda: parse("var x = 1; output x"), ParseError))
check("prec: + before *",          lambda: eq(parse("var r = 2 + 3 * 4;").statements[0].initializer.op, "+"))
check("parens override prec",      lambda: eq(parse("var r = (2+3)*4;").statements[0].initializer.op, "*"))
check("right-assoc caret",         lambda: eq(parse("var r = 2^3^2;").statements[0].initializer.right.op, "^"))
check("unary minus",               lambda: eq(isinstance(parse("var r = -5;").statements[0].initializer, UnaryOp), True))
check("missing rparen error",      lambda: raises(lambda: parse("var r = (1+2;"), ParseError))

# ── SEMANTICS ─────────────────────────────────────────────────────────────────
def analyze(code):
    toks = Lexer(code).tokenize()
    prog = Parser(toks, code).parse()
    a    = SemanticAnalyzer(code)
    a.analyze(prog)
    return a

print("\n\033[1m── SEMANTICS ──\033[0m")
check("undeclared use raises",    lambda: raises(lambda: analyze("output x;"), SemanticError))
check("undeclared assign raises", lambda: raises(lambda: analyze("x = 5;"), SemanticError))
check("duplicate decl raises",    lambda: raises(lambda: analyze("var x; var x;"), SemanticError))
check("valid program passes",     lambda: eq(analyze("var x = 5; var y = x+1; output y;").symbols.is_declared("x"), True))

# ── INTERPRETER ───────────────────────────────────────────────────────────────
print("\n\033[1m── INTERPRETER ──\033[0m")
check("simple output",        lambda: eq(run("var x = 5; output x;"), [5]))
check("addition",             lambda: eq(run("var r = 3 + 4; output r;"), [7]))
check("subtraction",          lambda: eq(run("var r = 10 - 3; output r;"), [7]))
check("multiplication",       lambda: eq(run("var r = 6 * 7; output r;"), [42]))
check("division",             lambda: eq(abs(run("var r = 10 / 4; output r;")[0] - 2.5) < 1e-9, True))
check("exponent",             lambda: eq(run("var r = 2 ^ 10; output r;"), [1024]))
check("right-assoc ^",        lambda: eq(run("var r = 2 ^ 3 ^ 2; output r;"), [512]))
check("precedence",           lambda: eq(run("var r = 2 + 3 * 4; output r;"), [14]))
check("parentheses",          lambda: eq(run("var r = (2 + 3) * 4; output r;"), [20]))
check("unary minus",          lambda: eq(run("var r = -5; output r;"), [-5]))
check("multiline src",        lambda: eq(run("var x = 5;\nvar y = 10;\noutput x + y;"), [15]))
check("reassignment",         lambda: eq(run("var x = 1; x = 99; output x;"), [99]))
check("input expr",           lambda: eq(run("var x = input; output x;", inputs=["7"]), [7]))
check("div by zero → exit 1", lambda: eq(run_pipeline("var r = 10 / 0; output r;"), 1))
check("none in arith → exit 1",lambda: eq(run_pipeline("var x; var r = x + 1; output r;"), 1))
check("strict bad input → 1", lambda: eq(run_pipeline("var x = input; output x;", io_in=lambda: "hi", strict_input=True), 1))
check("multi outputs",        lambda: eq(run("var a = 1; var b = 2; output a; output b;"), [1, 2]))
check("complex expr",         lambda: eq(run("var a=10; var b=3; var r=(a+b)*(a-b); output r;"), [91]))

# ── PIPELINE ──────────────────────────────────────────────────────────────────
print("\n\033[1m── PIPELINE EXIT CODES ──\033[0m")
check("success → 0",             lambda: eq(run_pipeline("var x = 1; output x;", io_out=lambda _: None), 0))
check("missing semicolon → 1",   lambda: eq(run_pipeline("var x = 1"), 1))
check("lex error → 1",           lambda: eq(run_pipeline("@bad;"), 1))
check("semantic error → 1",      lambda: eq(run_pipeline("output z;"), 1))
check("runtime error → 1",       lambda: eq(run_pipeline("var x = 1/0; output x;"), 1))
check("no-exp flag → 1",         lambda: eq(run_pipeline("var x = 2^3;", enable_caret=False), 1))

# ── SUMMARY ───────────────────────────────────────────────────────────────────
total  = passed + failed
pct    = int(passed / total * 100) if total else 0
colour = "\033[92m" if failed == 0 else "\033[93m"
print(f"\n{colour}{'─'*40}")
print(f"  Results: {passed}/{total} passed  ({pct}%)")
print(f"{'─'*40}\033[0m\n")
sys.exit(0 if failed == 0 else 1)