# parser.py

from ast_nodes import *
from lexer import Token


class ParseError(Exception):
    pass


# ============================================================
# ERROR RECOVERY STRATEGIES USED:
#
# 1. ERROR RECOVERY BY INSERTION
#    Missing semicolons, brackets — pretend they exist and continue
#
# 2. ERROR RECOVERY BY DELETION
#    Unexpected token — skip it and keep parsing
#
# 3. PANIC MODE RECOVERY
#    Statement completely broken — skip all tokens until a safe
#    restart point (semicolon, closing brace, keyword)
#
# 4. ERROR REPAIR
#    ++ and -- detected and reported as meaningful error with fix hint
# ============================================================

class Parser:

    def __init__(self, lexer):
        self.lexer   = lexer
        self.current = lexer.get_next_token()
        self.errors  = []   # collects ALL errors without crashing

    # ----------------------------------------------------------------
    # eat() — with error recovery by insertion / deletion
    # ----------------------------------------------------------------

    def eat(self, type_):
        if self.current.type == type_:
            tok = self.current
            self.current = self.lexer.get_next_token()
            return tok

        # ── Error recovery by insertion ───────────────────────────
        # For tokens that are commonly forgotten, insert them silently
        err = (f"Line {self.current.line}: expected '{type_}', "
               f"got '{self.current.type}' ('{self.current.value}')")
        self.errors.append(err)

        if type_ in ("SEMI", "RPAREN", "RBRACE", "RBRACKET"):
            # pretend the missing token was there — continue without advancing
            return Token(type_, type_, self.current.line, self.current.column)

        # ── Error recovery by deletion ────────────────────────────
        # For other mismatches — skip the bad token and continue
        skipped = self.current
        self.current = self.lexer.get_next_token()
        return skipped

    # ----------------------------------------------------------------
    # synchronize() — panic mode recovery
    # Skip tokens until a safe restart point is found
    # ----------------------------------------------------------------

    def synchronize(self):
        safe = {"SEMI", "RBRACE", "IF", "WHILE", "FOR",
                "INT", "FLOAT_TYPE", "DEF", "PRINT", "RETURN", "EOF"}
        while self.current.type not in safe:
            self.current = self.lexer.get_next_token()
        if self.current.type == "SEMI":
            self.current = self.lexer.get_next_token()

    # ----------------------------------------------------------------
    # Expressions
    # ----------------------------------------------------------------

    def factor(self):
        token = self.current

        # unary minus / plus
        if token.type in ("MINUS", "PLUS"):
            self.eat(token.type)
            # unary plus — no-op, just return inner expression
            if token.type == "PLUS":
                return self.factor()
            # unary minus
            return UnaryOp(token, self.factor())

        if token.type == "INTEGER":
            self.eat("INTEGER")
            return Num(token)

        if token.type == "FLOAT":
            self.eat("FLOAT")
            return FloatNum(token)

        if token.type == "ID":
            self.eat("ID")
            if self.current.type == "LPAREN":
                return self._func_call(token.value, token.line)
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

        # ── Error recovery by deletion ────────────────────────────
        self.errors.append(
            f"Line {token.line}: unexpected token '{token.type}' "
            f"('{token.value}') in expression — substituting 0"
        )
        self.current = self.lexer.get_next_token()
        return Num(Token("INTEGER", 0, token.line, token.column))

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

            # ── Error repair: detect ++ or -- ─────────────────────
            # After eating one +/-, if we see another +/- immediately
            # that means the user wrote ++ or -- between operands
            if self.current.type in ("PLUS", "MINUS"):
                combined = op.value + self.current.value  # "++" or "--" or "+-" or "-+"
                self.errors.append(
                    f"Line {self.current.line}: invalid operator '{combined}' — "
                    f"'++' and '--' are not supported in this language. "
                    f"Use 'i = i + 1' for increment or 'a = a + b' for addition."
                )
                # ── Error recovery by deletion: skip the second operator
                self.current = self.lexer.get_next_token()
                # treat as single + or - (whichever the first one was)

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
    # Function call
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
    # Type helper
    # ----------------------------------------------------------------

    def _type(self):
        if self.current.type == "INT":
            self.eat("INT")
            return "int"
        if self.current.type == "FLOAT_TYPE":
            self.eat("FLOAT_TYPE")
            return "float"
        self.errors.append(
            f"Line {self.current.line}: expected type (int/float), "
            f"got '{self.current.type}' — defaulting to int"
        )
        return "int"

    # ----------------------------------------------------------------
    # Statements — panic mode wraps every statement
    # ----------------------------------------------------------------

    def statement(self):
        try:
            return self._statement_inner()
        except Exception as e:
            # ── Panic mode recovery ───────────────────────────────
            self.errors.append(f"Line {self.current.line}: {e} — skipping to next statement")
            self.synchronize()
            return None

    def _statement_inner(self):

        # variable / array declaration
        if self.current.type in ("INT", "FLOAT_TYPE"):
            vtype    = self._type()
            name_tok = self.eat("ID")
            if self.current.type == "LBRACKET":
                self.eat("LBRACKET")
                size_tok = self.eat("INTEGER")
                self.eat("RBRACKET")
                self.eat("SEMI")
                return ArrayDecl(name_tok.value, size_tok.value, vtype)
            self.eat("SEMI")
            return VarDecl(name_tok, vtype)

        if self.current.type == "DEF":
            return self._func_def()

        if self.current.type == "RETURN":
            self.eat("RETURN")
            expr = self.comparison()
            self.eat("SEMI")
            return Return(expr)

        if self.current.type == "IF":
            return self._if_stmt()

        if self.current.type == "WHILE":
            self.eat("WHILE")
            self.eat("LPAREN")
            cond = self.comparison()
            self.eat("RPAREN")
            return While(cond, self.statement())

        if self.current.type == "FOR":
            return self._for_stmt()

        if self.current.type == "PRINT":
            self.eat("PRINT")
            self.eat("LPAREN")
            expr = self.comparison()
            self.eat("RPAREN")
            self.eat("SEMI")
            return Print(expr)

        if self.current.type == "ID":
            name_tok = self.current
            self.eat("ID")

            if self.current.type == "LPAREN":
                node = self._func_call(name_tok.value, name_tok.line)
                self.eat("SEMI")
                return node

            if self.current.type == "LBRACKET":
                self.eat("LBRACKET")
                idx = self.comparison()
                self.eat("RBRACKET")
                self.eat("ASSIGN")
                val = self.comparison()
                self.eat("SEMI")
                return ArrayAssign(name_tok.value, idx, val)

            self.eat("ASSIGN")
            right = self.comparison()
            self.eat("SEMI")
            return Assign(Var(name_tok), right)

        if self.current.type == "LBRACE":
            return self.block()

        # ── Error recovery by deletion ────────────────────────────
        self.errors.append(
            f"Line {self.current.line}: unexpected '{self.current.type}' "
            f"('{self.current.value}') — skipping"
        )
        self.synchronize()
        return None

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
        self.eat("FOR")
        self.eat("LPAREN")
        if self.current.type in ("INT", "FLOAT_TYPE"):
            vtype    = self._type()
            name_tok = self.eat("ID")
            self.eat("ASSIGN")
            init_val = self.comparison()
            init     = Assign(Var(name_tok), init_val)
            decl     = VarDecl(name_tok, vtype)
        else:
            name_tok = self.eat("ID")
            self.eat("ASSIGN")
            init_val = self.comparison()
            init     = Assign(Var(name_tok), init_val)
            decl     = None
        self.eat("SEMI")
        cond      = self.comparison()
        self.eat("SEMI")
        step_name = self.eat("ID")
        self.eat("ASSIGN")
        step_val  = self.comparison()
        step      = Assign(Var(step_name), step_val)
        self.eat("RPAREN")
        body      = self.statement()
        for_node  = For(init, cond, step, body)
        if decl:
            b          = Block()
            b.children = [decl, for_node]
            return b
        return for_node

    def _func_def(self):
        self.eat("DEF")
        rtype = self._type() if self.current.type in ("INT","FLOAT_TYPE") else "int"
        name  = self.eat("ID").value
        self.eat("LPAREN")
        params = []
        if self.current.type != "RPAREN":
            if self.current.type in ("INT", "FLOAT_TYPE"):
                ptype = self._type(); pname = self.eat("ID").value
                params.append((pname, ptype))
                while self.current.type == "COMMA":
                    self.eat("COMMA")
                    ptype = self._type(); pname = self.eat("ID").value
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
            stmt = self.statement()
            if stmt is not None:
                node.children.append(stmt)
        self.eat("RBRACE")
        return node

    def parse(self):
        tree = self.block()
        return tree, self.errors