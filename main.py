# main.py
import sys, os
from lexer      import Lexer
from parser     import Parser
from semantic   import SemanticAnalyzer
from optimizer  import ASTOptimizer, IROptimizer
from ir         import IRGenerator
from cfg        import CFGBuilder, CFGVisualizer
from visualizer import ASTVisualizer

DEFAULT_PROGRAM = """
{
    // ── function with typed params ──────────────────
    def int add(int a, int b) {
        return a + b;
    }

    def int max(int x, int y) {
        if (x > y) { return x; } else { return y; }
    }

    // ── arrays ──────────────────────────────────────
    int nums[5];
    nums[0] = 10;
    nums[1] = 20;
    nums[2] = 30;

    // ── for loop ────────────────────────────────────
    int total;
    total = 0;
    for (int i = 0; i < 3; i = i + 1) {
        total = total + nums[i];
    }
    print(total);        // 60

    // ── float ───────────────────────────────────────
    float pi;
    pi = 3.14;

    // ── if / else ───────────────────────────────────
    int result;
    result = add(nums[0], nums[1]);
    if (result == 30) {
        print(1);
    } else {
        print(0);
    }

    // ── while ───────────────────────────────────────
    int x;
    x = max(5, 3);
    while (x > 0) {
        x = x - 1;
    }
    print(x);
}
"""

def compile_program(source_code):
    print("=" * 44)
    print("INPUT PROGRAM")
    print("=" * 44)
    print(source_code)

    lexer  = Lexer(source_code)
    parser = Parser(lexer)
    tree   = parser.parse()
    print("Parsing          OK")

    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    if analyzer.errors:
        print("Semantic errors:", analyzer.errors)
    else:
        print("Semantic analysis OK")

    tree = ASTOptimizer().visit(tree)
    print("Constant folding OK")

    ASTVisualizer().render(tree, "ast")

    ir_gen       = IRGenerator()
    instructions = ir_gen.generate(tree)
    print("\n--- THREE ADDRESS CODE ---")
    for i in instructions:
        print(i)

    opt_lines = IROptimizer().optimize([str(i) for i in instructions])
    print("\nFinal optimized IR:")
    for line in opt_lines: print(line)

    cfg_builder = CFGBuilder(instructions)
    blocks      = cfg_builder.build()
    print("\n--- CFG ---")
    for b in blocks:
        print(b)
        print("Successors:", [s.name for s in b.successors])

    CFGVisualizer(blocks).render("cfg")
    print("\nCompilation finished.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            src = f.read()
    else:
        src = DEFAULT_PROGRAM
    compile_program(src)