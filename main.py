#!/usr/bin/env python3
# =============================================================================
# main.py  –  Entry point for the mini-language compiler & interpreter
# Authors: Nadales, Russel Rome F. | Ornos, Csypres Klent B.
# Course : CS0035 - Programming Languages
# =============================================================================
# Usage:
#   python main.py <source_file> [--trace] [--no-exp] [--strict-input]
#
# Exit codes:
#   0  – success
#   1  – compile or runtime error
#   2  – CLI usage error (bad arguments, file not found)
# =============================================================================

import sys
import os

from cli import build_arg_parser, run_pipeline


_BANNER = """\033[96m
╔══════════════════════════════════════════════════════╗
║        MINI-LANGUAGE INTERPRETER                     ║
║        CSTPLANGS – Translation of Programming Lang   ║
║        Nadales, Russel Rome F.                       ║
║        Ornos, Csypres Klent B.                       ║
╚══════════════════════════════════════════════════════╝\033[0m
"""


def main() -> None:
    parser = build_arg_parser()

    # Show usage if called with no arguments
    if len(sys.argv) < 2:
        print(_BANNER)
        parser.print_help()
        sys.exit(2)

    args = parser.parse_args()

    # ── Read source file ──────────────────────────────────────────────────
    path = args.source_file
    if not os.path.exists(path):
        print(f"\033[91mError:\033[0m Source file not found: {path!r}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print(f"\033[91mError:\033[0m Cannot read {path!r}: {exc}", file=sys.stderr)
        sys.exit(2)

    # ── Print banner only in trace mode (keeps normal output clean) ───────
    if args.trace:
        print(_BANNER)
        print(f"  Source file : {path}")
        print(f"  Trace       : ON")
        print(f"  Exponent ^  : {'OFF' if args.no_exp else 'ON'}")
        print(f"  Strict input: {'ON' if args.strict_input else 'OFF'}")

    # ── Run the full pipeline ─────────────────────────────────────────────
    exit_code = run_pipeline(
        source,
        trace        = args.trace,
        enable_caret = not args.no_exp,
        strict_input = args.strict_input,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()