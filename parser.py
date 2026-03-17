# parser.py

from ast_nodes import *
from lexer import Token


class ParseError(Exception):
    pass


class Parser:

    def __init__(self, lexer):
        self.lexer   = lexer
        self.current = lexer.get_next_token()

    def eat(self, type_):
        if self.current.type == type_:
            tok = self.current
            self.current = self.lexer.get_next_token()
            return tok
        raise ParseError(
            f"Line {self.current.line}: expected '{type_}', "
            f"got '{self.current.type}' ('{self.current.value}')"
        )

    # ----------------------------------------------------------------
    # Expressions: unary → factor → term → expr → comparison
    # ----------------------------------------------------------------

    def factor(self):
        token = self.current

        # unary minus / plus
        if token.type in ("MINUS", "PLUS"):
            self.eat(token.type)
            return UnaryOp(token, self.factor())

        if token.type == "INTEGER":
            self.eat("INTEGER")
            return Num(token)

        if token.type == "FLOAT":
            self.eat("FLOAT")
            return FloatNum(token)

        if token.type == "ID":
            self.eat("ID")
            # function call
            if self.current.type == "LPAREN":
                return self._func_call(token.value, token.line)
            # array access  a[i]
            if self.current.type == "LBRACKET":
                self.eat("LBRACKET")
                idx = self.comparison()
                self.eat("RBRACKET")
                return ArrayAccess(token.value, idx)
            return Var(token)

        if token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.comparison()
            self.eat("RPAREN")
            return node

        raise ParseError(
            f"Line {token.line}: unexpected token '{token.type}' ('{token.value}')"
        )

    def term(self):
        node = self.factor()
        while self.current.type in ("MUL", "DIV", "MOD"):
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
        node = self.expr()
        if self.current.type in ("LT", "GT", "LTE", "GTE", "EQ", "NEQ"):
            op = self.current
            self.eat(op.type)
            node = BinOp(node, op, self.expr())
        return node

    # ----------------------------------------------------------------
    # Function call  (name already eaten)
    # ----------------------------------------------------------------

    def _func_call(self, name, line):
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
    # Type keyword helper  →  ("int" | "float")
    # ----------------------------------------------------------------

    def _type(self):
        if self.current.type == "INT":
            self.eat("INT")
            return "int"
        if self.current.type == "FLOAT_TYPE":
            self.eat("FLOAT_TYPE")
            return "float"
        raise ParseError(
            f"Line {self.current.line}: expected type, got '{self.current.type}'"
        )

    # ----------------------------------------------------------------
    # Statements
    # ----------------------------------------------------------------

    def statement(self):

        # variable / array declaration:  int x;  |  int a[10];  |  float y;
        if self.current.type in ("INT", "FLOAT_TYPE"):
            vtype = self._type()
            name_tok = self.eat("ID")
            # array?
            if self.current.type == "LBRACKET":
                self.eat("LBRACKET")
                size_tok = self.eat("INTEGER")
                self.eat("RBRACKET")
                self.eat("SEMI")
                return ArrayDecl(name_tok.value, size_tok.value, vtype)
            self.eat("SEMI")
            return VarDecl(name_tok, vtype)

        # function definition
        if self.current.type == "DEF":
            return self._func_def()

        # return
        if self.current.type == "RETURN":
            self.eat("RETURN")
            expr = self.comparison()
            self.eat("SEMI")
            return Return(expr)

        # if / if-else
        if self.current.type == "IF":
            return self._if_stmt()

        # while
        if self.current.type == "WHILE":
            self.eat("WHILE")
            self.eat("LPAREN")
            cond = self.comparison()
            self.eat("RPAREN")
            return While(cond, self.statement())

        # for  →  for (init; cond; step) body
        if self.current.type == "FOR":
            return self._for_stmt()

        # print
        if self.current.type == "PRINT":
            self.eat("PRINT")
            self.eat("LPAREN")
            expr = self.comparison()
            self.eat("RPAREN")
            self.eat("SEMI")
            return Print(expr)

        # assignment, array assign, or standalone func call
        if self.current.type == "ID":
            name_tok = self.current
            self.eat("ID")

            # standalone func call
            if self.current.type == "LPAREN":
                node = self._func_call(name_tok.value, name_tok.line)
                self.eat("SEMI")
                return node

            # array assign  a[i] = expr;
            if self.current.type == "LBRACKET":
                self.eat("LBRACKET")
                idx = self.comparison()
                self.eat("RBRACKET")
                self.eat("ASSIGN")
                val = self.comparison()
                self.eat("SEMI")
                return ArrayAssign(name_tok.value, idx, val)

            # regular assign
            self.eat("ASSIGN")
            right = self.comparison()
            self.eat("SEMI")
            return Assign(Var(name_tok), right)

        if self.current.type == "LBRACE":
            return self.block()

        raise ParseError(
            f"Line {self.current.line}: invalid statement '{self.current.type}' ('{self.current.value}')"
        )

    def _if_stmt(self):
        self.eat("IF")
        self.eat("LPAREN")
        cond = self.comparison()
        self.eat("RPAREN")
        then = self.statement()
        if self.current.type == "ELSE":
            self.eat("ELSE")
            return IfElse(cond, then, self.statement())
        return If(cond, then)

    def _for_stmt(self):
        """for (int i = 0; i < 10; i = i + 1) { body }"""
        self.eat("FOR")
        self.eat("LPAREN")

        # init:  int i = 0  (no semicolon yet — we eat it)
        if self.current.type in ("INT", "FLOAT_TYPE"):
            vtype    = self._type()
            name_tok = self.eat("ID")
            self.eat("ASSIGN")
            init_val = self.comparison()
            init = Assign(Var(name_tok), init_val)
            # also declare the variable
            decl = VarDecl(name_tok, vtype)
        else:
            name_tok = self.eat("ID")
            self.eat("ASSIGN")
            init_val = self.comparison()
            init = Assign(Var(name_tok), init_val)
            decl = None
        self.eat("SEMI")

        cond = self.comparison()
        self.eat("SEMI")

        # step:  i = i + 1  (no semicolon — ends at RPAREN)
        step_name = self.eat("ID")
        self.eat("ASSIGN")
        step_val = self.comparison()
        step = Assign(Var(step_name), step_val)

        self.eat("RPAREN")
        body = self.statement()

        for_node = For(init, cond, step, body)
        if decl:
            # wrap decl + for in a tiny block
            b = Block()
            b.children = [decl, for_node]
            return b
        return for_node

    def _func_def(self):
        self.eat("DEF")
        # optional return type:  def int add(...)  OR  def add(...)
        if self.current.type in ("INT", "FLOAT_TYPE"):
            rtype = self._type()
        else:
            rtype = "int"
        name = self.eat("ID").value
        self.eat("LPAREN")
        params = []
        if self.current.type != "RPAREN":
            # typed params:  int a, float b   OR  plain a, b
            if self.current.type in ("INT", "FLOAT_TYPE"):
                ptype    = self._type()
                pname    = self.eat("ID").value
                params.append((pname, ptype))
                while self.current.type == "COMMA":
                    self.eat("COMMA")
                    ptype = self._type()
                    pname = self.eat("ID").value
                    params.append((pname, ptype))
            else:
                pname = self.eat("ID").value
                params.append((pname, "int"))
                while self.current.type == "COMMA":
                    self.eat("COMMA")
                    pname = self.eat("ID").value
                    params.append((pname, "int"))
        self.eat("RPAREN")
        body = self.block()
        return FuncDef(name, params, body, rtype)

    def block(self):
        node = Block()
        self.eat("LBRACE")
        while self.current.type not in ("RBRACE", "EOF"):
            node.children.append(self.statement())
        self.eat("RBRACE")
        return node

    def parse(self):
        return self.block()