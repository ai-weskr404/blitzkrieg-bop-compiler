# =============================================================================
# repl.py  –  Interactive REPL (Read-Eval-Print Loop)
# Authors: Nadales, Russel Rome F. | Ornos, Csypres Klent B.
# Course : CS0035 - Programming Languages
# =============================================================================
# Per spec rule 1: every statement MUST end with a semicolon.
# Typing "var x = 5" without a semicolon will produce a ParseError.
# Typing "var x = 5;" works correctly.
# =============================================================================

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from lexer       import Lexer
from parser      import Parser
from semantics   import SemanticAnalyzer
from interpreter import Interpreter, Environment
from errors      import CompilerError


_BANNER = """\033[96m
╔══════════════════════════════════════════════════════════╗
║   MINI-LANGUAGE  –  Interactive REPL                     ║
║   CSTPLANGS · Nadales · Ornos                            ║
║                                                          ║
║   Every statement MUST end with a semicolon  ;           ║
║   Commands:  :quit  :clear  :vars  :help                 ║
╚══════════════════════════════════════════════════════════╝\033[0m
"""

_HELP = """
\033[1mREPL Commands\033[0m
  :quit          Exit the REPL
  :clear         Reset all variables (fresh environment)
  :vars          Show all declared variables and their values
  :help          Show this message

\033[1mLanguage Quick Reference\033[0m
  var x;             Declare variable x (uninitialized)
  var x = 5;         Declare and initialise
  x = expr;          Reassign (must be declared first with var)
  output expr;       Print a value
  input              Read a number from keyboard (use as expression)
  + - * / ^          Arithmetic  (^ = exponent, right-associative)
  ( )                Grouping
  # comment          Line comment
  /* comment */      Block comment

  \033[93mNOTE: Every statement must end with  ;\033[0m
  Missing semicolon → ParseError

\033[1mExamples\033[0m
  >>> var x = 10;
  >>> var y = x * 2;
  >>> output y;
  20
  >>> var z = input;
  5
  >>> output z + x;
  15
"""


def build_repl_parser():
    p = argparse.ArgumentParser(prog="repl", description="Mini-language interactive REPL")
    p.add_argument("--trace",        action="store_true")
    p.add_argument("--no-exp",       dest="no_exp",       action="store_true")
    p.add_argument("--strict-input", dest="strict_input", action="store_true")
    return p


def run_repl(*, trace=False, enable_caret=True, strict_input=False):
    print(_BANNER)

    env      = Environment()
    declared = set()

    while True:
        try:
            line = input("\033[96m>>>\033[0m ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return

        stripped = line.strip()

        if not stripped:
            continue

        # ── REPL commands ─────────────────────────────────────────────────
        if stripped in (":quit", ":q", "quit", "exit"):
            print("Bye!")
            return

        if stripped == ":clear":
            env, declared = Environment(), set()
            print("\033[93m[variables cleared]\033[0m")
            continue

        if stripped == ":vars":
            variables = env.all_vars()
            if not variables:
                print("\033[2m(no variables declared yet)\033[0m")
            else:
                print(f"\033[1m{'Variable':<20} Value\033[0m")
                print("─" * 35)
                for name, val in variables.items():
                    disp = "\033[2mNone (uninitialized)\033[0m" if val is None else str(val)
                    print(f"  {name:<18} {disp}")
            continue

        if stripped == ":help":
            print(_HELP)
            continue

        # ── Compile & execute ─────────────────────────────────────────────
        # No '\n' appended — user must type their own semicolon per spec rule 1.
        source = stripped
        try:
            lexer  = Lexer(source, enable_caret=enable_caret)
            tokens = lexer.tokenize()
            if trace:
                from cli import print_tokens; print_tokens(tokens)

            parser = Parser(tokens, source)
            ast    = parser.parse()
            if trace:
                from cli import print_ast; print_ast(ast)

            analyzer = SemanticAnalyzer(source)
            for name in declared:
                analyzer.symbols.declare(name)
            analyzer.analyze(ast)
            for name in analyzer.symbols.all_names():
                declared.add(name)

            interp     = Interpreter(source, strict_input=strict_input, io_in=input, io_out=print)
            interp.env = env
            interp.execute(ast)
            env        = interp.env

        except CompilerError as exc:
            print(exc.pretty(), file=sys.stderr)


if __name__ == "__main__":
    args = build_repl_parser().parse_args()
    run_repl(trace=args.trace, enable_caret=not args.no_exp, strict_input=args.strict_input)