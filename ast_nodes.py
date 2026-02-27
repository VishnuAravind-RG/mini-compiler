# ast_nodes.py

class AST: pass

class Num(AST):
    def __init__(self, token):
        self.token = token

class Var(AST):
    def __init__(self, token):
        self.token = token

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Assign(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class VarDecl(AST):
    def __init__(self, token):
        self.token = token

class Print(AST):
    def __init__(self, expr):
        self.expr = expr

class Block(AST):
    def __init__(self):
        self.children = []

class While(AST):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body