# Mini-Language Compiler & Interpreter
### CS0057 - Programming Languages
**Authors:** Nadales, Russel Rome F. · Ornos, Csypress Klent  
**Institution:** FEU Institute of Technology – Computer Science Department

---

## Table of Contents
1. [Overview](#overview)
2. [Language Specification](#language-specification)
3. [Usage](#usage)
4. [Architecture](#architecture)
5. [Integration with T1 / T2 / T3](#integration-with-t1--t2--t3)
6. [Error Messages](#error-messages)
7. [Sample Programs](#sample-programs)
8. [Running Tests](#running-tests)

---

## Overview

This project implements a complete compiler pipeline for a minimal imperative language:

```
Lexer  →  Parser  →  Semantic Analyzer  →  Interpreter
```

It supports variable declaration, arithmetic, user input, and output—as specified in the project PDF. The code is intentionally modular so each compiler phase can be studied, tested, and extended independently.

---

## Language Specification

### Keywords
| Keyword  | Purpose |
|----------|---------|
| `var`    | Declare a variable (optionally with initializer) |
| `input`  | Read a number from stdin (used as an expression) |
| `output` | Print an expression to stdout |

### Identifiers
Must start with a letter or underscore, then any mix of letters, digits, underscores.  
`myVar`, `total_sum`, `x1` are all valid.

### Numbers
Integers (`42`) and floats (`3.14`) are both supported.

### Operators
| Symbol | Meaning | Associativity |
|--------|---------|---------------|
| `+`    | Addition | Left |
| `-`    | Subtraction / Unary minus | Left |
| `*`    | Multiplication | Left |
| `/`    | Division (float result) | Left |
| `^`    | Exponentiation (optional, disable with `--no-exp`) | **Right** |
| `=`    | Assignment | — |

Operator precedence (high → low): `^` > unary `-` > `* /` > `+ -`

### Comments
```
# This is a line comment

/* This is a
   block comment */
```

### Statement terminators
Either a **newline** or a **semicolon** ends a statement. Both styles work:
```
var x = 5
var y = 10; output y
```

### Grammar (EBNF)
```
program   := { statement } EOF
statement := vardecl | assign | outstmt
vardecl   := "var" IDENT [ "=" expr ] eol
assign    := IDENT "=" expr eol
outstmt   := "output" expr eol

expr      := term    { ("+" | "-") term  }
term      := power   { ("*" | "/") power }
power     := unary   { "^" unary }            # right-associative
unary     := "-" unary | factor
factor    := NUMBER | IDENT | "input" | "(" expr ")"

eol       := NEWLINE | ";"
```

### Semantics
- All variables **must be declared** with `var` before use.
- `var x` initialises `x` to `None`; arithmetic on `None` is a runtime error.
- `var x = expr` declares and initialises in one statement.
- Division `/` always returns a float; division by zero is a runtime error.
- `2 ^ 3 ^ 2` evaluates right-to-left as `2 ^ (3 ^ 2) = 512`.

---

## Usage

```bash
python main.py <source_file> [--trace] [--no-exp] [--strict-input]
```

| Flag | Description |
|------|-------------|
| `--trace` | Print token list and AST before executing |
| `--no-exp` | Disable `^`; using it becomes a LexError |
| `--strict-input` | Reject non-numeric user input with an error |

**Exit codes:** `0` = success · `1` = compile/runtime error · `2` = bad CLI args

### Examples
```bash
python main.py samples/math.src
python main.py samples/input_output.src --trace
python main.py samples/math.src --no-exp
python main.py samples/input_output.src --strict-input
```

---

## Architecture

```
minicompiler/
├── tokens.py       Token type constants (TT.*) and Token NamedTuple
├── lexer.py        Character-by-character scanner → token list
├── ast_nodes.py    Frozen dataclass AST nodes + NodeVisitor base
├── parser.py       Recursive-descent parser (grammar → AST)
├── semantics.py    Symbol table + declaration-before-use checks
├── interpreter.py  AST-walking evaluator with Environment store
├── errors.py       Error hierarchy with pretty line/caret diagnostics
├── cli.py          argparse config + pipeline orchestrator
├── main.py         Entry point
├── samples/
│   ├── hello.src          Basic var + output
│   ├── math.src           All operators, precedence, parentheses
│   └── input_output.src   Reading and computing with user input
└── tests/
    ├── test_all.py        pytest-compatible test classes (55 tests)
    └── run_tests.py       Standalone runner (no external deps)
```

### Data flow
```
source.src
   │
   ▼  Lexer(source)
List[Token]
   │
   ▼  Parser(tokens)
Program (AST)
   │
   ▼  SemanticAnalyzer(source).analyze(ast)
   │  (raises SemanticError on violation)
   │
   ▼  Interpreter(source).execute(ast)
stdout output
```

---

## Integration with T1 / T2 / T3

| Previous Work | How It's Used Here |
|---|---|
| **T1** – `Token` NamedTuple, `tokenization()` | `tokens.py` uses the same `Token(NamedTuple)` pattern with `type, value, line, column`. The lexer is a class-based evolution of `tokenization()`. |
| **T2** – Extended tokenizer, `SYNTAX_ERROR`, error highlighting | `TT.SYNTAX_ERROR` is preserved as a sentinel. ANSI red colouring for errors mirrors T2's `\033[91m` convention. `LexError` replaces inline `SYNTAX_ERROR` tokens with a proper exception + caret. |
| **T3** – First/Follow set calculator, symbol tables | `semantics.py`'s `SymbolTable` is a direct conceptual extension of T3's symbol tracking. The `NodeVisitor` pattern mirrors the recursive structure of T3's `calculate_first_set`. |

---

## Error Messages

Every error prints the offending source line with a `^` caret:

```
LexError at line 3, col 5:
    var @bad = 10
         ^
  Unknown character '@'

SemanticError at line 2, col 8:
    output z
           ^
  Use of undeclared variable 'z'

RuntimeError at line 4, col 11:
    var r = 10 / 0
               ^
  Division by zero
```

---

## Sample Programs

### samples/hello.src
```
var greeting
greeting = 42
output greeting

var x = 10
var y = 20
var sum = x + y
output sum
```
Output: `42`, `30`

### samples/math.src
Demonstrates all operators, precedence, and right-associative `^`.  
Output: `13  7  30  3.333...  512  26  -10  45.5`

### samples/input_output.src
Reads two numbers from the user and outputs their sum and doubled sum.

---

## Running Tests

**With pytest (if available):**
```bash
python -m pytest tests/ -v
```

**Without any external dependencies:**
```bash
python tests/run_tests.py
```

Expected: **55/55 tests passed**
