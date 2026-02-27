# main.py
import os

os.environ["GRAPHVIZ_DOT"] = r"C:\Users\TEMP.WINSERVER.194\Desktop\windows_10_cmake_Release_Graphviz-14.1.2-win64\Graphviz-14.1.2-win64\bin\dot.exe"

import sys
import graphviz
import sys

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from optimizer import ASTOptimizer, IROptimizer
from ir import IRGenerator
from cfg import CFGBuilder, CFGVisualizer
from visualizer import ASTVisualizer


# ============================================================
# SAMPLE PROGRAM (Default)
# ============================================================

import sys
import os

# ============================================================
# LOAD INPUT PROGRAM
# ============================================================

def load_program():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)

        with open(file_path, "r") as f:
            return f.read()


# ============================================================
# COMPILER PIPELINE
# ============================================================

def compile_program(source_code):

    print("======================================")
    print("INPUT PROGRAM")
    print("======================================")
    print(source_code)

    # --------------------------------------------------------
    # LEXER + PARSER
    # --------------------------------------------------------

    print("\n======================================")
    print("PARSING")
    print("======================================")

    lexer = Lexer(source_code)
    parser = Parser(lexer)
    tree = parser.parse()

    print("Parsing completed.")

    # --------------------------------------------------------
    # SEMANTIC ANALYSIS
    # --------------------------------------------------------

    print("\n======================================")
    print("SEMANTIC ANALYSIS")
    print("======================================")

    semantic = SemanticAnalyzer()
    semantic.visit(tree)

    print("Semantic analysis completed.")

    # --------------------------------------------------------
    # AST OPTIMIZATION (Level 3 - Constant Folding)
    # --------------------------------------------------------

    print("\n======================================")
    print("AST OPTIMIZATION")
    print("======================================")

    ast_optimizer = ASTOptimizer()
    tree = ast_optimizer.visit(tree)

    print("Constant folding applied.")

    # --------------------------------------------------------
    # AST VISUALIZATION
    # --------------------------------------------------------

    print("\nGenerating AST image...")

    ast_vis = ASTVisualizer()
    ast_vis.render(tree, "ast")

    print("AST saved as ast.png")

    # --------------------------------------------------------
    # IR GENERATION (Three Address Code)
    # --------------------------------------------------------

    print("\n======================================")
    print("THREE ADDRESS CODE (IR)")
    print("======================================")

    ir_gen = IRGenerator()
    instructions = ir_gen.generate(tree)

    for instr in instructions:
        print(instr)

    # --------------------------------------------------------
    # IR OPTIMIZATION
    # --------------------------------------------------------

    print("\n======================================")
    print("IR OPTIMIZATION")
    print("======================================")

    ir_optimizer = IROptimizer()
    optimized_code = ir_optimizer.optimize([str(i) for i in instructions])

    print("\nFinal Optimized IR:")
    for line in optimized_code:
        print(line)

    # --------------------------------------------------------
    # CFG BUILDING
    # --------------------------------------------------------

    print("\n======================================")
    print("CONTROL FLOW GRAPH")
    print("======================================")

    cfg_builder = CFGBuilder(instructions)
    blocks = cfg_builder.build()

    for block in blocks:
        print(block)
        print("Successors:", [s.name for s in block.successors])
        print()

    # --------------------------------------------------------
    # CFG VISUALIZATION
    # --------------------------------------------------------

    print("Generating CFG image...")
    cfg_vis = CFGVisualizer(blocks)
    cfg_vis.render("cfg")

    print("CFG saved as cfg.png")

    print("\n======================================")
    print("COMPILATION FINISHED")
    print("======================================")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            program = f.read()
    else:
        program = DEFAULT_PROGRAM

    compile_program(program)