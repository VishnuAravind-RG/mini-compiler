# MiniC Compiler Studio 

A full compiler pipeline built from scratch in Python, with an interactive web-based IDE. Write code in a custom C-like language and watch it flow through every stage of compilation in real time.

![MiniC Compiler Studio](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![License](https://img.shields.io/badge/license-MIT-purple)

---

## Features

### Language Support
- `int` and `float` variable types
- Arithmetic operators: `+` `-` `*` `/` `%`
- Comparison operators: `==` `!=` `<` `>` `<=` `>=`
- `if` / `else` statements
- `while` and `for` loops
- Functions with typed parameters and return values
- Arrays: `int a[10]`
- `print()` statement
- Single-line `//` and block `/* */` comments

### Compiler Pipeline
| Stage | Description |
|---|---|
| **Lexer** | Tokenizes source into typed tokens with line/column info |
| **Parser** | Recursive descent parser with error recovery (insertion, deletion, panic mode) |
| **Semantic Analysis** | Scoped symbol table, undeclared variable detection, function arity checks |
| **AST Optimizer** | Constant folding, constant propagation, dead code elimination |
| **IR Generator** | Three-address code (3AC) generation |
| **IR Optimizer** | Constant propagation and dead code elimination on IR |
| **CFG Builder** | Basic block construction with control flow edges |
| **x86-64 Generator** | Real NASM-syntax assembly with a linear scan register allocator |

### Web IDE
- Syntax-highlighted code editor (CodeMirror)
- Live pipeline trace — expand each compiler phase individually
- Token table, IR diff (before/after optimization), per-block optimization view
- x86-64 assembly output with register allocation details
- AST and CFG visualizations (requires Graphviz)
- Rich error reporting with source location and code snippets
- Built-in example programs

---

## Getting Started

### Prerequisites
- Python 3.10+
- Graphviz (optional — for AST/CFG diagrams)

**Install Graphviz:**
```bash
# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz

# Windows — download from https://graphviz.org/download/
# Make sure to check "Add to PATH" during install
```

### Installation

```bash
git clone https://github.com/VishnuAravind-RG/mini-compiler.git
cd mini-compiler

python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Run the Web IDE

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

### Run from Command Line

```bash
python main.py              # compiles the built-in demo program
python main.py myfile.mc    # compile a file
```

---

## Example Program

```c
{
    def int factorial(int n) {
        if (n <= 1) { return 1; }
        return n * factorial(n - 1);
    }

    int nums[5];
    nums[0] = 10;
    nums[1] = 20;

    int total;
    total = 0;
    for (int i = 0; i < 2; i = i + 1) {
        total = total + nums[i];
    }
    print(total);  // 30

    float pi;
    pi = 3.14;

    int result;
    result = factorial(5);
    print(result);  // 120
}
```

---

## Project Structure

```
mini-compiler/
├── app.py            # Flask web server + compiler API
├── lexer.py          # Tokenizer
├── parser.py         # Recursive descent parser with error recovery
├── ast_nodes.py      # AST node definitions
├── semantic.py       # Semantic analysis + scoped symbol table
├── optimizer.py      # AST + IR optimizer
├── ir.py             # IR instruction set + 3AC generator
├── cfg.py            # Control flow graph builder + visualizer
├── x86gen.py         # x86-64 NASM assembly generator
├── visualizer.py     # AST visualizer (Graphviz)
├── error_handler.py  # Rich error reporting
├── main.py           # CLI entry point
├── requirements.txt
└── templates/
    └── index.html    # Web IDE
```

---

## Requirements

```
flask
graphviz
```

---

*Educational project — built to demonstrate how a real compiler works, stage by stage.*
