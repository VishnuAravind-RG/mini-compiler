# semantic.py

from ast_nodes import *


class SemanticError(Exception):
    pass


class SemanticAnalyzer:

    def __init__(self):
        self.scopes    = [{}]       # stack of {name: type}
        self.functions = {}         # name -> FuncDef
        self.arrays    = {}         # name -> (size, type)
        self.errors    = []

    # ----------------------------------------------------------------
    # Scope helpers
    # ----------------------------------------------------------------

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name, vtype="int"):
        if name in self.scopes[-1]:
            self._warn(f"Redeclaration of '{name}'")
        self.scopes[-1][name] = vtype

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self._error(f"Undeclared variable '{name}'")
        return None

    def _error(self, msg):
        self.errors.append(f"[Error] {msg}")
        print(f"[Semantic Error] {msg}")

    def _warn(self, msg):
        print(f"[Semantic Warning] {msg}")

    # ----------------------------------------------------------------
    # Visitor
    # ----------------------------------------------------------------

    def visit(self, node):

        if isinstance(node, Block):
            self.enter_scope()
            for c in node.children:
                self.visit(c)
            self.exit_scope()

        elif isinstance(node, VarDecl):
            self.declare(node.token.value, node.var_type)

        elif isinstance(node, ArrayDecl):
            self.arrays[node.name] = (node.size, node.var_type)
            self.declare(node.name, node.var_type + "[]")

        elif isinstance(node, ArrayAccess):
            if node.name not in self.arrays:
                self._error(f"'{node.name}' is not an array")
            self.visit(node.index)

        elif isinstance(node, ArrayAssign):
            if node.name not in self.arrays:
                self._error(f"'{node.name}' is not an array")
            self.visit(node.index)
            self.visit(node.value)

        elif isinstance(node, Assign):
            self.lookup(node.left.token.value)
            self.visit(node.right)

        elif isinstance(node, Var):
            self.lookup(node.token.value)

        elif isinstance(node, Num):
            pass

        elif isinstance(node, FloatNum):
            pass

        elif isinstance(node, UnaryOp):
            self.visit(node.expr)

        elif isinstance(node, BinOp):
            self.visit(node.left)
            self.visit(node.right)

        elif isinstance(node, Print):
            self.visit(node.expr)

        elif isinstance(node, While):
            self.visit(node.cond)
            self.visit(node.body)

        elif isinstance(node, For):
            self.enter_scope()
            self.visit(node.init)
            self.visit(node.cond)
            self.visit(node.step)
            self.visit(node.body)
            self.exit_scope()

        elif isinstance(node, If):
            self.visit(node.cond)
            self.visit(node.body)

        elif isinstance(node, IfElse):
            self.visit(node.cond)
            self.visit(node.then_body)
            self.visit(node.else_body)

        elif isinstance(node, FuncDef):
            self.functions[node.name] = node
            self.enter_scope()
            for pname, ptype in node.params:
                self.declare(pname, ptype)
            self.visit(node.body)
            self.exit_scope()

        elif isinstance(node, FuncCall):
            if node.name not in self.functions:
                self._error(f"Undefined function '{node.name}'")
            else:
                expected = len(self.functions[node.name].params)
                got      = len(node.args)
                if expected != got:
                    self._error(
                        f"Function '{node.name}' expects {expected} args, got {got}"
                    )
            for arg in node.args:
                self.visit(arg)

        elif isinstance(node, Return):
            self.visit(node.expr)