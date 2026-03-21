# =============================================================================
# cli.py  –  Command-line interface helpers
# Authors: Nadales, Russel Rome F. | Ornos, Csypres Klent B.
# Course : CS0035 - Programming Languages
# =============================================================================
# Provides:
#   • build_arg_parser()  – argparse configuration
#   • print_tokens()      – pretty token table (--trace)
#   • print_ast()         – indented AST dump (--trace)
#   • run_pipeline()      – orchestrates lexer → parser → semantics → interpreter
# =============================================================================

from __future__ import annotations

import argparse
import sys
from typing import List

from tokens      import Token, TT
from ast_nodes   import ASTNode
from errors      import CompilerError


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog        = "minicompiler",
        description = "Mini-language interpreter (Programming Languages)",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = """
Examples:
  python main.py samples/math.src
  python main.py samples/input_output.src --trace
  python main.py samples/math.src --no-exp
  python main.py samples/input_output.src --strict-input
        """,
    )
    p.add_argument(
        "source_file",
        help="Path to the source program file",
    )
    p.add_argument(
        "--trace",
        action  = "store_true",
        default = False,
        help    = "Print token list and AST before running",
    )
    p.add_argument(
        "--no-exp",
        dest    = "no_exp",
        action  = "store_true",
        default = False,
        help    = "Disable the '^' exponentiation operator",
    )
    p.add_argument(
        "--strict-input",
        dest    = "strict_input",
        action  = "store_true",
        default = False,
        help    = "Reject non-numeric user input with an error",
    )
    return p


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------

# ANSI colour codes (safe to use in virtually any modern terminal)
_CYAN  = "\033[96m"
_RESET = "\033[0m"
_DIM   = "\033[2m"
_BOLD  = "\033[1m"


def print_tokens(tokens: List[Token]) -> None:
    """Render a formatted token table to stdout (--trace mode)."""
    w = 18
    separator = "-" * (w * 3 + 10)
    print(f"\n{_BOLD}{'─'*55}")
    print(f"  TOKEN LIST")
    print(f"{'─'*55}{_RESET}")
    print(f"  {_CYAN}{'Type':<{w}}{'Value':<{w}}{'Location'}{_RESET}")
    print(f"  {separator}")
    for tok in tokens:
        if tok.type in (TT.NEWLINE, TT.EOF):
            continue                    # skip noise tokens in trace
        loc = f"Ln {tok.line}, Col {tok.column}"
        print(f"  {tok.type:<{w}}{tok.value!r:<{w}}{loc}")
    print()


def print_ast(node: ASTNode, indent: int = 0) -> None:
    """Recursively render an AST to stdout (--trace mode)."""
    if indent == 0:
        print(f"\n{_BOLD}{'─'*55}")
        print("  ABSTRACT SYNTAX TREE")
        print(f"{'─'*55}{_RESET}")

    prefix = "  " + "  " * indent
    name   = type(node).__name__

    from ast_nodes import (
        Program, VarDecl, Assignment, OutputStmt,
        BinaryOp, UnaryOp, NumberLiteral, Identifier, InputExpr,
    )

    if isinstance(node, Program):
        print(f"{prefix}{_CYAN}Program{_RESET} ({len(node.statements)} statements)")
        for s in node.statements:
            print_ast(s, indent + 1)

    elif isinstance(node, VarDecl):
        init = "" if node.initializer is None else " (with initializer)"
        print(f"{prefix}{_CYAN}VarDecl{_RESET} '{node.name}'{init} @ Ln {node.line}")
        if node.initializer:
            print_ast(node.initializer, indent + 1)

    elif isinstance(node, Assignment):
        print(f"{prefix}{_CYAN}Assignment{_RESET} '{node.name}' @ Ln {node.line}")
        print_ast(node.value, indent + 1)

    elif isinstance(node, OutputStmt):
        print(f"{prefix}{_CYAN}Output{_RESET} @ Ln {node.line}")
        print_ast(node.expr, indent + 1)

    elif isinstance(node, BinaryOp):
        print(f"{prefix}{_CYAN}BinaryOp{_RESET} '{node.op}'")
        print_ast(node.left,  indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{prefix}{_CYAN}UnaryOp{_RESET} '{node.op}'")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, NumberLiteral):
        print(f"{prefix}{_DIM}Number{_RESET} {node.value}")

    elif isinstance(node, Identifier):
        print(f"{prefix}{_DIM}Identifier{_RESET} '{node.name}'")

    elif isinstance(node, InputExpr):
        print(f"{prefix}{_DIM}Input{_RESET}")

    else:
        print(f"{prefix}{name}")

    if indent == 0:
        print()


# ---------------------------------------------------------------------------
# Pipeline  (used by main.py and by tests)
# ---------------------------------------------------------------------------

def run_pipeline(
    source:       str,
    *,
    trace:        bool = False,
    enable_caret: bool = True,
    strict_input: bool = False,
    io_in               = None,
    io_out              = None,
) -> int:
    """Run the full compiler pipeline on a source string.

    Returns
    -------
    0  on success
    1  on any compiler / runtime error
    """
    from lexer       import Lexer
    from parser      import Parser
    from semantics   import SemanticAnalyzer
    from interpreter import Interpreter

    try:
        # 1. Lex
        lexer  = Lexer(source, enable_caret=enable_caret)
        tokens = lexer.tokenize()

        if trace:
            print_tokens(tokens)

        # 2. Parse
        parser = Parser(tokens, source)
        ast    = parser.parse()

        if trace:
            print_ast(ast)

        # 3. Semantic analysis
        analyzer = SemanticAnalyzer(source)
        analyzer.analyze(ast)

        # 4. Execute
        interp = Interpreter(
            source,
            strict_input = strict_input,
            io_in        = io_in,
            io_out       = io_out,
        )
        interp.execute(ast)

        return 0

    except CompilerError as exc:
        print(exc.pretty(), file=sys.stderr)
        return 1