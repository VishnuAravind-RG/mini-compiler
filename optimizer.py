# optimizer.py

from ast_nodes import *
from lexer import Token

CMP_OPS = {"LT", "GT", "LTE", "GTE", "EQ", "NEQ"}
OP_MAP  = {"LT": "<", "GT": ">", "LTE": "<=", "GTE": ">=", "EQ": "==", "NEQ": "!="}

# ============================================================
# AST OPTIMIZER  (Constant Folding)
# ============================================================

class ASTOptimizer:

    def visit(self, node):

        if isinstance(node, Block):
            node.children = [self.visit(c) for c in node.children]
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

        if isinstance(node, If):
            node.cond = self.visit(node.cond)
            node.body = self.visit(node.body)
            return node

        if isinstance(node, IfElse):
            node.cond      = self.visit(node.cond)
            node.then_body = self.visit(node.then_body)
            node.else_body = self.visit(node.else_body)
            return node

        if isinstance(node, FuncDef):
            node.body = self.visit(node.body)
            return node

        if isinstance(node, Return):
            node.expr = self.visit(node.expr)
            return node

        if isinstance(node, FuncCall):
            node.args = [self.visit(a) for a in node.args]
            return node

        if isinstance(node, BinOp):
            node.left  = self.visit(node.left)
            node.right = self.visit(node.right)

            # fold arithmetic constants
            if isinstance(node.left, Num) and isinstance(node.right, Num):
                a, b = node.left.token.value, node.right.token.value
                op   = node.op.type
                if op == "PLUS":    v = a + b
                elif op == "MINUS": v = a - b
                elif op == "MUL":   v = a * b
                elif op == "DIV":   v = a // b if b != 0 else 0
                elif op in CMP_OPS:
                    raw = eval(f"{a} {OP_MAP[op]} {b}")
                    v   = 1 if raw else 0
                else:
                    return node
                return Num(Token("INTEGER", v, 0, 0))

            return node

        return node


# ============================================================
# IR OPTIMIZER
# ============================================================

class IROptimizer:

    def constant_propagation(self, code):
        constants = {}
        new_code  = []
        for line in code:
            parts = line.split()
            # simple:  x = 5
            if len(parts) == 3 and parts[1] == "=" and str(parts[2]).lstrip("-").isdigit():
                constants[parts[0]] = parts[2]
                new_code.append(line)
                continue
            # replace known constants in the line
            for var, val in constants.items():
                # whole-word replace only
                import re
                line = re.sub(rf'\b{re.escape(var)}\b', str(val), line)
            new_code.append(line)
        return new_code

    def dead_code_elimination(self, code):
        used      = set()
        optimized = []
        for line in reversed(code):
            parts = line.replace("=", " = ").split()
            if "=" in parts:
                lhs      = parts[0]
                rhs_vars = [p for p in parts[2:] if p.isidentifier()]
                if lhs in used or line.startswith("PRINT") or line.startswith("RETURN"):
                    optimized.insert(0, line)
                    for v in rhs_vars:
                        used.add(v)
                else:
                    continue
            else:
                optimized.insert(0, line)
        return optimized

    def optimize(self, code):
        print("\n--- CONSTANT PROPAGATION ---")
        code = self.constant_propagation(code)
        for c in code: print(c)

        print("\n--- DEAD CODE ELIMINATION ---")
        code = self.dead_code_elimination(code)
        for c in code: print(c)

        return code