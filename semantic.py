# semantic.py

from ast_nodes import *

class SemanticAnalyzer:

    def __init__(self):
        self.scopes   = [{}]           # stack of dicts
        self.functions = {}            # name -> FuncDef

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name):
        if name in self.scopes[-1]:
            print(f"[Semantic Warning] Redeclaration of '{name}'")
        self.scopes[-1][name] = "int"

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        print(f"[Semantic Error] Undeclared variable '{name}'")
        return False

    def visit(self, node):

        if isinstance(node, Block):
            self.enter_scope()
            for c in node.children:
                self.visit(c)
            self.exit_scope()

        elif isinstance(node, VarDecl):
            self.declare(node.token.value)

        elif isinstance(node, Assign):
            self.lookup(node.left.token.value)
            self.visit(node.right)

        elif isinstance(node, Var):
            self.lookup(node.token.value)

        elif isinstance(node, Num):
            pass

        elif isinstance(node, BinOp):
            self.visit(node.left)
            self.visit(node.right)

        elif isinstance(node, Print):
            self.visit(node.expr)

        elif isinstance(node, While):
            self.visit(node.cond)
            self.visit(node.body)

        # NEW: if / if-else
        elif isinstance(node, If):
            self.visit(node.cond)
            self.visit(node.body)

        elif isinstance(node, IfElse):
            self.visit(node.cond)
            self.visit(node.then_body)
            self.visit(node.else_body)

        # NEW: functions
        elif isinstance(node, FuncDef):
            self.functions[node.name] = node
            self.enter_scope()
            for p in node.params:
                self.declare(p)
            self.visit(node.body)
            self.exit_scope()

        elif isinstance(node, FuncCall):
            if node.name not in self.functions and node.name != "print":
                print(f"[Semantic Error] Undefined function '{node.name}'")
            for arg in node.args:
                self.visit(arg)

        elif isinstance(node, Return):
            self.visit(node.expr)