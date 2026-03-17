# ir.py

from ast_nodes import *

CMP_OPS = {"<", ">", "<=", ">=", "==", "!="}

class IRInstruction:

    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op     = op
        self.arg1   = arg1
        self.arg2   = arg2
        self.result = result

    def __str__(self):
        if self.op == "assign":
            return f"{self.result} = {self.arg1}"
        if self.op in ("+", "-", "*", "/"):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op in CMP_OPS:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op == "print":
            return f"PRINT {self.arg1}"
        if self.op == "label":
            return f"LABEL {self.result}"
        if self.op == "goto":
            return f"GOTO {self.result}"
        if self.op == "ifnot":
            return f"IFNOT {self.arg1} GOTO {self.result}"
        if self.op == "call":
            # result = CALL name arg1 arg2 ...
            args_str = " ".join(str(a) for a in (self.arg2 or []))
            return f"{self.result} = CALL {self.arg1}({args_str})"
        if self.op == "return":
            return f"RETURN {self.arg1}"
        if self.op == "func_begin":
            return f"FUNC {self.result}:"
        if self.op == "func_end":
            return f"END_FUNC {self.result}"
        if self.op == "param":
            return f"PARAM {self.arg1} = {self.result}"
        return f"UNKNOWN({self.op})"


class IRGenerator:

    def __init__(self):
        self.instructions = []
        self.temp_count   = 0
        self.label_count  = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, *args, **kwargs):
        self.instructions.append(IRInstruction(*args, **kwargs))

    def generate(self, node):
        self.visit(node)
        return self.instructions

    # ----------------------------------------------------------------
    # Statements
    # ----------------------------------------------------------------

    def visit(self, node):

        if isinstance(node, Block):
            for child in node.children:
                self.visit(child)

        elif isinstance(node, VarDecl):
            pass

        elif isinstance(node, Assign):
            val = self.eval_expr(node.right)
            self.emit("assign", arg1=val, result=node.left.token.value)

        elif isinstance(node, Print):
            val = self.eval_expr(node.expr)
            self.emit("print", arg1=val)

        # while
        elif isinstance(node, While):
            start = self.new_label()
            end   = self.new_label()
            self.emit("label", result=start)
            cond = self.eval_expr(node.cond)
            self.emit("ifnot", arg1=cond, result=end)
            self.visit(node.body)
            self.emit("goto",  result=start)
            self.emit("label", result=end)

        # if (no else)
        elif isinstance(node, If):
            end = self.new_label()
            cond = self.eval_expr(node.cond)
            self.emit("ifnot", arg1=cond, result=end)
            self.visit(node.body)
            self.emit("label", result=end)

        # if-else
        elif isinstance(node, IfElse):
            else_label = self.new_label()
            end_label  = self.new_label()
            cond = self.eval_expr(node.cond)
            self.emit("ifnot", arg1=cond, result=else_label)
            self.visit(node.then_body)
            self.emit("goto",  result=end_label)
            self.emit("label", result=else_label)
            self.visit(node.else_body)
            self.emit("label", result=end_label)

        # function definition
        elif isinstance(node, FuncDef):
            self.emit("func_begin", result=node.name)
            for p in node.params:
                self.emit("param", arg1=p, result=node.name)
            self.visit(node.body)
            self.emit("func_end", result=node.name)

        # return
        elif isinstance(node, Return):
            val = self.eval_expr(node.expr)
            self.emit("return", arg1=val)

        # function call as statement
        elif isinstance(node, FuncCall):
            arg_vals = [self.eval_expr(a) for a in node.args]
            tmp = self.new_temp()
            self.emit("call", arg1=node.name, arg2=arg_vals, result=tmp)

    # ----------------------------------------------------------------
    # Expressions
    # ----------------------------------------------------------------

    def eval_expr(self, node):

        if isinstance(node, Num):
            return node.token.value

        if isinstance(node, Var):
            return node.token.value

        if isinstance(node, BinOp):
            left  = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            tmp   = self.new_temp()
            self.emit(node.op.value, left, right, tmp)
            return tmp

        if isinstance(node, FuncCall):
            arg_vals = [self.eval_expr(a) for a in node.args]
            tmp = self.new_temp()
            self.emit("call", arg1=node.name, arg2=arg_vals, result=tmp)
            return tmp

        raise Exception(f"Unknown expression type: {type(node)}")