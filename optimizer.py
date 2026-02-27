# optimizer.py

from ast_nodes import *
from lexer import Token


# ============================================================
# AST LEVEL OPTIMIZER (Constant Folding)
# ============================================================

class ASTOptimizer:

    def visit(self, node):

        if isinstance(node, Block):
            new_children = []
            for c in node.children:
                new_children.append(self.visit(c))
            node.children = new_children
            return node

        if isinstance(node, Assign):
            node.right = self.visit(node.right)
            return node

        if isinstance(node, Print):
            node.expr = self.visit(node.expr)
            return node

        if isinstance(node, While):
            node.cond = self.visit(node.cond)
            node.body = self.visit(node.body)
            return node

        if isinstance(node, BinOp):
            node.left = self.visit(node.left)
            node.right = self.visit(node.right)

            if isinstance(node.left, Num) and isinstance(node.right, Num):
                a = node.left.token.value
                b = node.right.token.value

                if node.op.type == "PLUS":
                    value = a + b
                elif node.op.type == "MINUS":
                    value = a - b
                elif node.op.type == "MUL":
                    value = a * b
                elif node.op.type == "DIV":
                    value = a // b
                else:
                    return node

                return Num(Token("INTEGER", value, 0, 0))

            return node

        return node


# ============================================================
# IR LEVEL OPTIMIZER
# ============================================================

class IROptimizer:

    # ------------------------------------------------------------
    # Constant Propagation
    # ------------------------------------------------------------

    def constant_propagation(self, code):
        constants = {}
        new_code = []

        for line in code:

            parts = line.split()

            # x = 5
            if "=" in line and parts[2].isdigit():
                constants[parts[0]] = parts[2]
                new_code.append(line)
                continue

            # replace known constants
            for var in constants:
                if var in line:
                    line = line.replace(var, constants[var])

            new_code.append(line)

        return new_code


    # ------------------------------------------------------------
    # Dead Code Elimination (Safe)
    # ------------------------------------------------------------

    def dead_code_elimination(self, code):

        used = set()
        optimized = []

        # traverse backwards
        for line in reversed(code):

            parts = line.replace("=", " = ").split()

            if "=" in parts:
                lhs = parts[0]
                rhs_vars = [p for p in parts if p.isalpha()]

                if lhs in used or line.startswith("PRINT"):
                    optimized.insert(0, line)
                    for var in rhs_vars:
                        used.add(var)
                else:
                    continue
            else:
                optimized.insert(0, line)

        return optimized


    # ------------------------------------------------------------
    # Full Optimization Pipeline
    # ------------------------------------------------------------

    def optimize(self, code):

        print("\n--- CONSTANT PROPAGATION ---")
        code = self.constant_propagation(code)
        for c in code:
            print(c)

        print("\n--- DEAD CODE ELIMINATION ---")
        code = self.dead_code_elimination(code)
        for c in code:
            print(c)

        return code