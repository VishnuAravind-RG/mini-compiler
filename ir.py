# ir.py

from ast_nodes import *


# ============================================================
# THREE ADDRESS CODE GENERATOR
# ============================================================

class IRInstruction:
    """
    Represents a single 3AC instruction.
    """

    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):

        if self.op == "assign":
            return f"{self.result} = {self.arg1}"

        if self.op in ("+", "-", "*", "/"):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

        if self.op == "print":
            return f"PRINT {self.arg1}"

        if self.op == "label":
            return f"LABEL {self.result}"

        if self.op == "goto":
            return f"GOTO {self.result}"

        if self.op == "ifnot":
            return f"IFNOT {self.arg1} GOTO {self.result}"

        return "UNKNOWN"


# ============================================================
# IR GENERATOR
# ============================================================

class IRGenerator:

    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    # ------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------

    def generate(self, node):
        self.visit(node)
        return self.instructions

    # ------------------------------------------------------------
    # Visitor
    # ------------------------------------------------------------

    def visit(self, node):

        if isinstance(node, Block):
            for child in node.children:
                self.visit(child)

        elif isinstance(node, VarDecl):
            # no IR needed for declaration
            pass

        elif isinstance(node, Assign):
            value = self.eval_expr(node.right)
            self.instructions.append(
                IRInstruction("assign", arg1=value, result=node.left.token.value)
            )

        elif isinstance(node, Print):
            value = self.eval_expr(node.expr)
            self.instructions.append(
                IRInstruction("print", arg1=value)
            )

        elif isinstance(node, While):

            start_label = self.new_label()
            end_label = self.new_label()

            self.instructions.append(
                IRInstruction("label", result=start_label)
            )

            cond_value = self.eval_expr(node.cond)

            self.instructions.append(
                IRInstruction("ifnot", arg1=cond_value, result=end_label)
            )

            self.visit(node.body)

            self.instructions.append(
                IRInstruction("goto", result=start_label)
            )

            self.instructions.append(
                IRInstruction("label", result=end_label)
            )

    # ------------------------------------------------------------
    # Expression Evaluation
    # ------------------------------------------------------------

    def eval_expr(self, node):

        if isinstance(node, Num):
            return node.token.value

        if isinstance(node, Var):
            return node.token.value

        if isinstance(node, BinOp):
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)

            temp = self.new_temp()

            self.instructions.append(
                IRInstruction(node.op.value, left, right, temp)
            )

            return temp

        raise Exception("Unknown expression type")