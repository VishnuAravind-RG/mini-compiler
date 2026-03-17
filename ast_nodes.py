# ast_nodes.py

class AST: pass

class Num(AST):
    def __init__(self, token):
        self.token = token

class FloatNum(AST):                          # T1: float literals
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

class UnaryOp(AST):                           # T1: unary minus  -x
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class Assign(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class VarDecl(AST):
    def __init__(self, token, type_="int"):   # T1: type info
        self.token = token
        self.var_type = type_

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

class For(AST):                               # T1: for loop
    def __init__(self, init, cond, step, body):
        self.init = init   # Assign
        self.cond = cond   # comparison
        self.step = step   # Assign
        self.body = body   # Block

class If(AST):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class IfElse(AST):
    def __init__(self, cond, then_body, else_body):
        self.cond      = cond
        self.then_body = then_body
        self.else_body = else_body

class FuncDef(AST):
    def __init__(self, name, params, body, return_type="int"):
        self.name        = name
        self.params      = params   # list of (name, type) tuples
        self.body        = body
        self.return_type = return_type

class FuncCall(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class Return(AST):
    def __init__(self, expr):
        self.expr = expr

class ArrayDecl(AST):                         # T2: int a[10];
    def __init__(self, name, size, var_type="int"):
        self.name     = name
        self.size     = size
        self.var_type = var_type

class ArrayAccess(AST):                       # T2: a[i]
    def __init__(self, name, index):
        self.name  = name
        self.index = index

class ArrayAssign(AST):                       # T2: a[i] = expr;
    def __init__(self, name, index, value):
        self.name  = name
        self.index = index
        self.value = value