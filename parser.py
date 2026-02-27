# parser.py

from ast_nodes import *
from lexer import Token

class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.current = lexer.get_next_token()

    def eat(self, type_):
        if self.current.type == type_:
            self.current = self.lexer.get_next_token()
        else:
            raise Exception(f"Expected {type_}")

    def factor(self):
        token = self.current

        if token.type == "INTEGER":
            self.eat("INTEGER")
            return Num(token)

        if token.type == "ID":
            self.eat("ID")
            return Var(token)

        if token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.expr()
            self.eat("RPAREN")
            return node

        raise Exception("Invalid factor")

    def term(self):
        node = self.factor()
        while self.current.type in ("MUL", "DIV"):
            op = self.current
            self.eat(op.type)
            node = BinOp(node, op, self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current.type in ("PLUS", "MINUS"):
            op = self.current
            self.eat(op.type)
            node = BinOp(node, op, self.term())
        return node

    def statement(self):

        if self.current.type == "INT":
            self.eat("INT")
            token = self.current
            self.eat("ID")
            self.eat("SEMI")
            return VarDecl(token)

        if self.current.type == "ID":
            left = Var(self.current)
            self.eat("ID")
            self.eat("ASSIGN")
            right = self.expr()
            self.eat("SEMI")
            return Assign(left, right)

        if self.current.type == "PRINT":
            self.eat("PRINT")
            self.eat("LPAREN")
            expr = self.expr()
            self.eat("RPAREN")
            self.eat("SEMI")
            return Print(expr)

        if self.current.type == "WHILE":
            self.eat("WHILE")
            self.eat("LPAREN")
            cond = self.expr()
            self.eat("RPAREN")
            body = self.statement()
            return While(cond, body)

        if self.current.type == "LBRACE":
            return self.block()

        raise Exception("Invalid statement")

    def block(self):
        block = Block()
        self.eat("LBRACE")

        while self.current.type != "RBRACE":
            block.children.append(self.statement())

        self.eat("RBRACE")
        return block

    def parse(self):
        return self.block()