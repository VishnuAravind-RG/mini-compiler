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
    def add(a, b) {
        return a + b;
    }

    int x;
    int y;
    int result;

    x = 10;
    y = 4;
    result = add(x, y);

    if (result > 10) {
        print(result);
    } else {
        print(0);
    }

    while (x > 0) {
        x = x - 1;
    }
    print(x);
}
"""

def compile_program(source_code):
    print("=" * 42)
    print("INPUT PROGRAM")
    print("=" * 42)
    print(source_code)

    lexer  = Lexer(source_code)
    parser = Parser(lexer)
    tree   = parser.parse()
    print("Parsing OK")

    SemanticAnalyzer().visit(tree)
    print("Semantic analysis OK")

    tree = ASTOptimizer().visit(tree)
    print("Constant folding OK")

    ASTVisualizer().render(tree, "ast")

    ir_gen       = IRGenerator()
    instructions = ir_gen.generate(tree)
    print("\n--- THREE ADDRESS CODE ---")
    for i in instructions:
        print(i)

    ir_opt   = IROptimizer()
    opt_code = ir_opt.optimize([str(i) for i in instructions])
    print("\nFinal optimized IR:")
    for line in opt_code:
        print(line)

    cfg_builder = CFGBuilder(instructions)
    blocks      = cfg_builder.build()
    print("\n--- CFG BLOCKS ---")
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