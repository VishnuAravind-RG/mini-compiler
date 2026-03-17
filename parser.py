# parser.py

from ast_nodes import *
from lexer import Token

class Parser:

    def __init__(self, lexer):
        self.lexer   = lexer
        self.current = lexer.get_next_token()

    def eat(self, type_):
        if self.current.type == type_:
            self.current = self.lexer.get_next_token()
        else:
            raise Exception(
                f"Syntax error at line {self.current.line}: "
                f"expected {type_}, got {self.current.type} ('{self.current.value}')"
            )

    # ----------------------------------------------------------------
    # Expressions  (comparison < arithmetic)
    # ----------------------------------------------------------------

    def factor(self):
        token = self.current

        if token.type == "INTEGER":
            self.eat("INTEGER")
            return Num(token)

        if token.type == "ID":
            self.eat("ID")
            # function call?
            if self.current.type == "LPAREN":
                return self.func_call(token.value)
            return Var(token)

        if token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.comparison()
            self.eat("RPAREN")
            return node

        raise Exception(f"Invalid factor: {token.type} ('{token.value}') at line {token.line}")

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

    def comparison(self):
        """comparison: expr ((LT|GT|LTE|GTE|EQ|NEQ) expr)?"""
        node = self.expr()
        if self.current.type in ("LT", "GT", "LTE", "GTE", "EQ", "NEQ"):
            op = self.current
            self.eat(op.type)
            node = BinOp(node, op, self.expr())
        return node

    # ----------------------------------------------------------------
    # Function call  (already ate the name token)
    # ----------------------------------------------------------------

    def func_call(self, name):
        self.eat("LPAREN")
        args = []
        if self.current.type != "RPAREN":
            args.append(self.comparison())
            while self.current.type == "COMMA":
                self.eat("COMMA")
                args.append(self.comparison())
        self.eat("RPAREN")
        return FuncCall(name, args)

    # ----------------------------------------------------------------
    # Statements
    # ----------------------------------------------------------------

    def statement(self):

        # variable declaration:  int x;
        if self.current.type == "INT":
            self.eat("INT")
            token = self.current
            self.eat("ID")
            self.eat("SEMI")
            return VarDecl(token)

        # function definition:  def name(a, b) { ... }
        if self.current.type == "DEF":
            return self.func_def()

        # return statement:  return expr;
        if self.current.type == "RETURN":
            self.eat("RETURN")
            expr = self.comparison()
            self.eat("SEMI")
            return Return(expr)

        # if / if-else
        if self.current.type == "IF":
            return self.if_statement()

        # while loop
        if self.current.type == "WHILE":
            self.eat("WHILE")
            self.eat("LPAREN")
            cond = self.comparison()
            self.eat("RPAREN")
            body = self.statement()
            return While(cond, body)

        # print(expr);
        if self.current.type == "PRINT":
            self.eat("PRINT")
            self.eat("LPAREN")
            expr = self.comparison()
            self.eat("RPAREN")
            self.eat("SEMI")
            return Print(expr)

        # assignment or standalone function call:  x = ... ;  OR  foo(...);
        if self.current.type == "ID":
            token = self.current
            self.eat("ID")

            # function call as statement
            if self.current.type == "LPAREN":
                node = self.func_call(token.value)
                self.eat("SEMI")
                return node

            # assignment
            self.eat("ASSIGN")
            right = self.comparison()
            self.eat("SEMI")
            return Assign(Var(token), right)

        # block
        if self.current.type == "LBRACE":
            return self.block()

        raise Exception(
            f"Invalid statement: {self.current.type} ('{self.current.value}') at line {self.current.line}"
        )

    def if_statement(self):
        self.eat("IF")
        self.eat("LPAREN")
        cond = self.comparison()
        self.eat("RPAREN")
        then_body = self.statement()

        if self.current.type == "ELSE":
            self.eat("ELSE")
            else_body = self.statement()
            return IfElse(cond, then_body, else_body)

        return If(cond, then_body)

    def func_def(self):
        self.eat("DEF")
        name = self.current.value
        self.eat("ID")
        self.eat("LPAREN")
        params = []
        if self.current.type == "ID":
            params.append(self.current.value)
            self.eat("ID")
            while self.current.type == "COMMA":
                self.eat("COMMA")
                params.append(self.current.value)
                self.eat("ID")
        self.eat("RPAREN")
        body = self.block()
        return FuncDef(name, params, body)

    def block(self):
        node = Block()
        self.eat("LBRACE")
        while self.current.type not in ("RBRACE", "EOF"):
            node.children.append(self.statement())
        self.eat("RBRACE")
        return node

    def parse(self):
        return self.block()