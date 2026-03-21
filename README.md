# Mini-Language Interpreter

### CS0035 - Programming Languages

**Authors:** Nadales, Russel Rome F. · Ornos, Csypress Klent  
**Institution:** FEU Institute of Technology – Computer Science Department

---

## Table of Contents

1. [Overview](#overview)
2. [Language Specification](#language-specification)
3. [Usage](#usage)
4. [Interactive REPL](#interactive-repl)
5. [Architecture](#architecture)
6. [Integration with T1 / T2 / T3](#integration-with-t1--t2--t3)
7. [Error Messages](#error-messages)
8. [Sample Programs](#sample-programs)
9. [File Extensions Explained](#file-extensions-explained)
10. [Running Tests](#running-tests)

---

## Overview

This project implements a pipeline for a minimal imperative language that covers
the front-end phases of a compiler: lexical analysis, syntax analysis, semantic
analysis, and interpretation.

> **Note:** This version does **not** include a code generation phase.
> The pipeline ends at the interpreter — the AST is walked and executed directly
> in memory. No target code (machine code, bytecode, or Python source) is produced.

```
source.src
    │
    ▼  lexer.py        Lexical analysis   — source text → List[Token]
    ▼  parser.py       Syntax analysis    — List[Token] → AST
    ▼  semantics.py    Semantic analysis  — checks declarations and types
    ▼  interpreter.py  Evaluation         — walks AST and produces output
```

---

## Language Specification

### Keywords

| Keyword  | Purpose                                          |
| -------- | ------------------------------------------------ |
| `var`    | Declare a variable (optionally with initializer) |
| `input`  | Read a number from stdin (used as an expression) |
| `output` | Print an expression to stdout                    |

### Identifiers

Must start with a letter or underscore, then any mix of letters, digits, underscores.
`myVar`, `total_sum`, `x1` are all valid.

### Numbers

Integers (`42`) and floats (`3.14`) are both supported.

### Operators

| Symbol | Meaning                                  | Associativity |
| ------ | ---------------------------------------- | ------------- |
| `+`    | Addition                                 | Left          |
| `-`    | Subtraction / Unary minus                | Left          |
| `*`    | Multiplication                           | Left          |
| `/`    | Division (float result)                  | Left          |
| `^`    | Exponentiation (disable with `--no-exp`) | **Right**     |
| `=`    | Assignment                               | —             |

Operator precedence (high → low): `^` > unary `-` > `* /` > `+ -`

### Statement terminator

Every statement **must end with a semicolon** `;` — this is spec rule 1.
A missing semicolon is a `ParseError`.

### Whitespace

Spaces, tabs, and newlines are all insignificant — spec rule 2.
`a+b` is identical to `a + b`, and a statement may span multiple lines
as long as it ends with `;`.

### Comments

```
# This is a line comment

/* This is a
   block comment */
```

### Grammar (EBNF)

```
program   := { statement } EOF
statement := vardecl | assign | outstmt
vardecl   := "var" IDENT [ "=" expr ] ";"
assign    := IDENT "=" expr ";"
outstmt   := "output" expr ";"

expr      := term    { ("+" | "-") term  }
term      := power   { ("*" | "/") power }
power     := unary   { "^" unary }            # right-associative
unary     := "-" unary | factor
factor    := NUMBER | IDENT | "input" | "(" expr ")"
```

### Semantics

- All variables **must be declared** with `var` before use.
- `var x;` initialises `x` to `None`; arithmetic on `None` is a runtime error.
- `var x = expr;` declares and initialises in one statement.
- Division `/` always returns a float; division by zero is a runtime error.
- `2 ^ 3 ^ 2` evaluates right-to-left as `2 ^ (3 ^ 2) = 512`.

---

## Usage

```bash
python main.py <source_file> [--trace] [--no-exp] [--strict-input]
```

| Flag             | Description                                   |
| ---------------- | --------------------------------------------- |
| `--trace`        | Print the token list and AST before executing |
| `--no-exp`       | Disable `^`; using it becomes a `LexError`    |
| `--strict-input` | Reject non-numeric user input with an error   |

**Exit codes:** `0` = success · `1` = compile/runtime error · `2` = bad arguments

### Examples

```bash
python main.py samples/math.src
python main.py samples/math.src --trace
python main.py samples/math.src --no-exp
python main.py samples/input_output.src --strict-input
```

---

## Interactive REPL

Instead of running a `.src` file, you can type statements directly in the
terminal — one line at a time, just like Python's interactive mode.

```bash
python repl.py
```

Every statement must still end with `;`:

```
>>> var x = 10;
>>> var y = x * 2;
>>> output y;
20
>>> var z = input;
5
>>> output z + x;
15
```

Variables persist across lines for the entire session.

### REPL commands

| Command  | What it does                                         |
| -------- | ---------------------------------------------------- |
| `:vars`  | Show all declared variables and their current values |
| `:clear` | Reset the session (all variables erased)             |
| `:help`  | Show language quick reference                        |
| `:quit`  | Exit the REPL                                        |

### REPL flags

```bash
python repl.py --trace         # show tokens and AST for each statement
python repl.py --no-exp        # disable ^ operator
python repl.py --strict-input  # reject non-numeric input
```

---

## Architecture

```
minicompiler/
├── tokens.py        Token type constants (TT.*) and Token NamedTuple
├── lexer.py         Lexical analysis: source text → List[Token]
├── ast_nodes.py     AST node definitions (frozen dataclasses) + NodeVisitor
├── parser.py        Recursive-descent parser: List[Token] → Program (AST)
├── semantics.py     Semantic analysis: SymbolTable, declaration-before-use checks
├── interpreter.py   AST-walking evaluator: executes the program, manages Environment
├── errors.py        Error hierarchy with line + caret diagnostics
├── cli.py           Pipeline orchestrator (run_pipeline) and trace helpers
├── main.py          Entry point — reads a .src file and runs the pipeline
├── repl.py          Interactive terminal REPL
├── samples/
│   ├── hello.src            Basic var + output
│   ├── math.src             All operators, precedence, parentheses
│   └── input_output.src     Reading and computing with user input
└── tests/
    ├── test_all.py          pytest-compatible test classes
    └── run_tests.py         Standalone runner (no external dependencies)
```

### Pipeline data flow

```
source.src
   │
   ▼  Lexer(source).tokenize()
List[Token]
   │
   ▼  Parser(tokens, source).parse()
Program (AST)
   │
   ▼  SemanticAnalyzer(source).analyze(ast)
   │  raises SemanticError on violation
   │
   ▼  Interpreter(source).execute(ast)
stdout output
```

---

## Integration with T1 / T2 / T3

| Previous Work                                                   | How It's Used Here                                                                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **T1** – `Token` NamedTuple, `tokenization()`                   | `tokens.py` uses the identical `Token(type, value, line, column)` pattern. `lexer.py` is a class-based evolution of `tokenization()`.                                                            |
| **T2** – Extended tokenizer, `SYNTAX_ERROR`, ANSI error colours | `TT.SYNTAX_ERROR` is preserved as a sentinel. ANSI colouring in `errors.py` mirrors T2's `\033[91m` convention. `LexError` replaces inline error tokens with a proper exception + caret pointer. |
| **T3** – First/Follow set calculator, recursive symbol logic    | `semantics.py`'s `SymbolTable` is the runtime extension of T3's symbol tracking. `NodeVisitor.visit()` mirrors the recursive dispatch pattern of T3's `calculate_first_set`.                     |

---

## Error Messages

Every error prints the offending source line with a `^` caret:

```
LexError at line 1, col 0:
    @bad;
    ^
  Unknown character '@'

ParseError at line 1, col 9:
    var x = 1
             ^
  Missing ';' at end of statement — found EOF instead.
  Spec rule 1: ALL statements must end with a semicolon.

SemanticError at line 1, col 7:
    output z;
           ^
  Use of undeclared variable 'z'

RuntimeError at line 1, col 11:
    var r = 10 / 0;
               ^
  Division by zero
```

---

## Sample Programs

### samples/hello.src

```
var greeting;
greeting = 42;
output greeting;    /* 42 */

var x = 10;
var y = 20;
var sum = x + y;
output sum;         /* 30 */
```

### samples/math.src

```
var a = 10;
var b = 3;
var add_result = a + b;
output add_result;          /* 13   */
var exp_result = 2 ^ 3 ^ 2;
output exp_result;          /* 512  */
var paren_result = (a + b) * 2;
output paren_result;        /* 26   */
```

### samples/input_output.src

```
var x = input;
var y = input;
var total = x + y;
output total;
var doubled = total * 2;
output doubled;
```

---

## File Extensions Explained

| Extension | Example                 | What it is                                                      |
| --------- | ----------------------- | --------------------------------------------------------------- |
| `.py`     | `lexer.py`, `main.py`   | Python source — the compiler/interpreter modules themselves     |
| `.src`    | `math.src`, `hello.src` | Mini-language programs — plain text input fed into our pipeline |
| `.md`     | `README.md`             | Markdown documentation — not code                               |

`.src` files cannot be run directly by Python because `var x = 10;` is not
valid Python syntax. They are read as plain text by `main.py` and processed
through the pipeline.

---

## Running Tests

```bash
# No external dependencies needed
python tests/run_tests.py

# With pytest (if installed)
python -m pytest tests/ -v
```

Expected result: **56/56 tests passed**

The test suite covers all four pipeline stages independently:
lexer, parser, semantic analyzer, interpreter, and full pipeline exit codes.
