# =============================================================================
# repl.py  –  Interactive REPL (Read-Eval-Print Loop)
# Authors: Nadales, Russel Rome F. | Ornos, Csypress Klent
# Course : CS0035 - Programming Languages
# =============================================================================
# Lets the user type mini-language code line by line in the terminal,
# just like Python's interactive mode.  Run with:
#
#   python repl.py
#   python repl.py --trace
#   python repl.py --strict-input
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
║   Type your code line by line.                           ║
║   End a multi-line block with a blank line.              ║
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
  var x          Declare variable x (value = None)
  var x = 5      Declare and initialise
  x = expr       Assign (variable must be declared first)
  output expr    Print a value
  input          Read a number from keyboard (use inside an expression)
  + - * / ^      Arithmetic  (^ = exponent, right-associative)
  ( )            Grouping
  # comment      Line comment
  /* comment */  Block comment

\033[1mExamples\033[0m
  var x = 10
  var y = x * 2
  output y          → 20

  var z = input     (you will be prompted to type a number)
  output z + x
"""


def build_repl_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog        = "repl",
        description = "Mini-language interactive REPL",
    )
    p.add_argument("--trace",        action="store_true", help="Show tokens and AST for each input")
    p.add_argument("--no-exp",       dest="no_exp",       action="store_true", help="Disable ^ operator")
    p.add_argument("--strict-input", dest="strict_input", action="store_true", help="Reject non-numeric input")
    return p


def run_repl(*, trace: bool = False, enable_caret: bool = True, strict_input: bool = False) -> None:
    """Start the interactive REPL loop."""

    print(_BANNER)

    # Persistent state across all inputs in this session
    env      = Environment()
    declared = set()          # track names already validated by semantic pass

    while True:
        # ── Prompt and collect input ──────────────────────────────────────
        try:
            lines = []
            prompt = "\033[96m>>>\033[0m "

            while True:
                line = input(prompt)
                prompt = "\033[96m...\033[0m "   # continuation prompt

                # ── REPL commands ─────────────────────────────────────────
                stripped = line.strip()

                if stripped in (":quit", ":q", "quit", "exit"):
                    print("Bye!")
                    return

                if stripped == ":clear":
                    env      = Environment()
                    declared = set()
                    print("\033[93m[variables cleared]\033[0m")
                    lines = []
                    break

                if stripped == ":vars":
                    variables = env.all_vars()
                    if not variables:
                        print("\033[2m(no variables declared yet)\033[0m")
                    else:
                        print(f"\033[1m{'Variable':<20} Value\033[0m")
                        print("─" * 35)
                        for name, val in variables.items():
                            display = "\033[2mNone (uninitialized)\033[0m" if val is None else str(val)
                            print(f"  {name:<18} {display}")
                    lines = []
                    break

                if stripped == ":help":
                    print(_HELP)
                    lines = []
                    break

                if stripped:
                    lines.append(line)

                # A blank line (or non-empty single line) submits the block
                if not stripped or (lines and not stripped):
                    break

            if not lines:
                continue

        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return

        # ── Compile and run the entered snippet ───────────────────────────
        source = "\n".join(lines) + "\n"

        try:
            # 1. Lex
            lexer  = Lexer(source, enable_caret=enable_caret)
            tokens = lexer.tokenize()

            if trace:
                from cli import print_tokens
                print_tokens(tokens)

            # 2. Parse
            parser = Parser(tokens, source)
            ast    = parser.parse()

            if trace:
                from cli import print_ast
                print_ast(ast)

            # 3. Semantic check  ── only check newly introduced names;
            #    re-inject already-declared names so cross-line references work.
            analyzer = SemanticAnalyzer(source)
            for name in declared:
                analyzer.symbols.declare(name)
            analyzer.analyze(ast)

            # Record any new declarations for future inputs
            for name in analyzer.symbols.all_names():
                declared.add(name)

            # 4. Execute — reuse the persistent Environment
            interp = Interpreter(
                source,
                strict_input = strict_input,
                io_in        = input,
                io_out       = print,
            )
            interp.env = env          # ← inject the shared environment
            interp.execute(ast)

            # Sync env back (Interpreter may have added/changed values)
            env = interp.env

        except CompilerError as exc:
            print(exc.pretty(), file=sys.stderr)


if __name__ == "__main__":
    args = build_repl_parser().parse_args()
    run_repl(
        trace        = args.trace,
        enable_caret = not args.no_exp,
        strict_input = args.strict_input,
    )