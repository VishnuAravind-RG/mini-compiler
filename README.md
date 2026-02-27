# Mini Compiler - Level 3

A custom educational compiler built in Python featuring:

- Lexer
- Recursive descent parser
- AST generation
- Semantic analysis with scoped symbol table
- Three Address Code (IR)
- IR optimization (constant folding, propagation, dead code elimination)
- Control Flow Graph generation
- AST & CFG visualization using Graphviz

## Supported Language Features

- int variables
- Assignment
- Arithmetic expressions (+, -, *, /)
- while loops
- print statement
- Block scoping

Example program:

```
{
    int x;
    x = 5 + 3 * 2;
    while (x) {
        x = x - 1;
    }
    print(x);
}
```

## How to Run

```
pip install -r requirements.txt
python main.py
```

To compile a file:

```
python main.py example.cig
```

## Output

- AST image (ast.png)
- CFG image (cfg.png)
- Optimized IR printed in console

---

Educational project. Not a full C compiler.