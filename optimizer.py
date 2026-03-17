# optimizer.py

from ast_nodes import *
from lexer import Token

CMP_OPS = {"LT": "<", "GT": ">", "LTE": "<=", "GTE": ">=", "EQ": "==", "NEQ": "!="}


class ASTOptimizer:
    """Constant folding + constant propagation at AST level."""

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

        if isinstance(node, For):
            node.init = self.visit(node.init)
            node.cond = self.visit(node.cond)
            node.step = self.visit(node.step)
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

        if isinstance(node, ArrayAssign):
            node.value = self.visit(node.value)
            return node

        if isinstance(node, UnaryOp):
            node.expr = self.visit(node.expr)
            if isinstance(node.expr, Num):
                v = -node.expr.token.value if node.op.type == "MINUS" else node.expr.token.value
                return Num(Token("INTEGER", v, 0, 0))
            if isinstance(node.expr, FloatNum):
                v = -node.expr.token.value if node.op.type == "MINUS" else node.expr.token.value
                return FloatNum(Token("FLOAT", v, 0, 0))
            return node

        if isinstance(node, BinOp):
            node.left  = self.visit(node.left)
            node.right = self.visit(node.right)

            l_const = isinstance(node.left,  (Num, FloatNum))
            r_const = isinstance(node.right, (Num, FloatNum))

            if l_const and r_const:
                a  = node.left.token.value
                b  = node.right.token.value
                op = node.op.type

                if op == "PLUS":    v = a + b
                elif op == "MINUS": v = a - b
                elif op == "MUL":   v = a * b
                elif op == "DIV":   v = a // b if isinstance(a, int) else a / b
                elif op == "MOD":   v = a % b
                elif op in CMP_OPS:
                    raw = eval(f"{a} {CMP_OPS[op]} {b}")
                    v   = 1 if raw else 0
                else:
                    return node

                tok_type = "FLOAT" if isinstance(v, float) else "INTEGER"
                cls      = FloatNum if tok_type == "FLOAT" else Num
                return cls(Token(tok_type, v, 0, 0))

            return node

        return node


class IROptimizer:

    def constant_propagation(self, code):
        import re
        constants = {}
        new_code  = []
        for line in code:
            parts = line.split()
            # x = 5   or   x = 3.14
            if len(parts) == 3 and parts[1] == "=":
                try:
                    float(parts[2])
                    constants[parts[0]] = parts[2]
                    new_code.append(line)
                    continue
                except ValueError:
                    pass
            for var, val in constants.items():
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
                rhs_vars = [p for p in parts[2:] if p.replace(".", "").isdigit() is False and p.isidentifier()]
                keep = (lhs in used
                        or line.startswith("PRINT")
                        or line.startswith("RETURN")
                        or line.startswith("FUNC")
                        or line.startswith("END_FUNC")
                        or line.startswith("PARAM")
                        or line.startswith("ARRAY"))
                if keep:
                    optimized.insert(0, line)
                    used.update(rhs_vars)
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