# lexer.py

class Token:
    def __init__(self, type_, value, line, column):
        self.type   = type_
        self.value  = value
        self.line   = line
        self.column = column


class Lexer:

    def __init__(self, text):
        self.text         = text
        self.pos          = 0
        self.line         = 1
        self.column       = 1
        self.current_char = text[self.pos] if text else None

    def advance(self):
        if self.current_char == "\n":
            self.line  += 1
            self.column = 0
        self.pos        += 1
        self.column     += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        nxt = self.pos + 1
        return self.text[nxt] if nxt < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        # single-line comments //
        while self.current_char and self.current_char != "\n":
            self.advance()

    def number(self):
        start_col = self.column
        value = ""
        while self.current_char and self.current_char.isdigit():
            value += self.current_char
            self.advance()
        return Token("INTEGER", int(value), self.line, start_col)

    def identifier(self):
        start_col = self.column
        value = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            value += self.current_char
            self.advance()

        keywords = {
            "int":    "INT",
            "print":  "PRINT",
            "while":  "WHILE",
            "if":     "IF",       # NEW
            "else":   "ELSE",     # NEW
            "def":    "DEF",      # NEW
            "return": "RETURN",   # NEW
        }
        return Token(keywords.get(value, "ID"), value, self.line, start_col)

    def get_next_token(self):
        while self.current_char:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # skip single-line comments
            if self.current_char == "/" and self.peek() == "/":
                self.skip_comment()
                continue

            if self.current_char.isdigit():
                return self.number()

            if self.current_char.isalpha() or self.current_char == "_":
                return self.identifier()

            start_col = self.column

            # two-char tokens first
            if self.current_char == "=" and self.peek() == "=":
                self.advance(); self.advance()
                return Token("EQ", "==", self.line, start_col)

            if self.current_char == "!" and self.peek() == "=":
                self.advance(); self.advance()
                return Token("NEQ", "!=", self.line, start_col)

            if self.current_char == "<" and self.peek() == "=":
                self.advance(); self.advance()
                return Token("LTE", "<=", self.line, start_col)

            if self.current_char == ">" and self.peek() == "=":
                self.advance(); self.advance()
                return Token("GTE", ">=", self.line, start_col)

            single_tokens = {
                "=": "ASSIGN",
                "+": "PLUS",
                "-": "MINUS",
                "*": "MUL",
                "/": "DIV",
                "(": "LPAREN",
                ")": "RPAREN",
                "{": "LBRACE",
                "}": "RBRACE",
                ";": "SEMI",
                ",": "COMMA",   # NEW – for func params/args
                "<": "LT",      # NEW
                ">": "GT",      # NEW
            }

            if self.current_char in single_tokens:
                char = self.current_char
                self.advance()
                return Token(single_tokens[char], char, self.line, start_col)

            raise Exception(f"Invalid character '{self.current_char}' at {self.line}:{self.column}")

        return Token("EOF", None, self.line, self.column)