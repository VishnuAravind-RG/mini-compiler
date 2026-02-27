# semantic.py

from ast_nodes import *

class SemanticAnalyzer:

    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name, token):
        if name in self.scopes[-1]:
            print(f"[Semantic Error] Redeclaration of {name}")
        self.scopes[-1][name] = "int"

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        print(f"[Semantic Error] Undeclared variable {name}")
        return False

    def visit(self, node):

        if isinstance(node, Block):
            self.enter_scope()
            for c in node.children:
                self.visit(c)
            self.exit_scope()

        elif isinstance(node, VarDecl):
            self.declare(node.token.value, node.token)

        elif isinstance(node, Assign):
            self.lookup(node.left.token.value)
            self.visit(node.right)

        elif isinstance(node, Var):
            self.lookup(node.token.value)

        elif isinstance(node, BinOp):
            self.visit(node.left)
            self.visit(node.right)

        elif isinstance(node, Print):
            self.visit(node.expr)

        elif isinstance(node, While):
            self.visit(node.cond)
            self.visit(node.body)