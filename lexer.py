# lexer.py

class Token:
    def __init__(self, type_, value, line, column):
        self.type   = type_
        self.value  = value
        self.line   = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


class LexerError(Exception):
    pass


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
        self.pos          += 1
        self.column       += 1
        self.current_char  = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        nxt = self.pos + 1
        return self.text[nxt] if nxt < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_line_comment(self):
        while self.current_char and self.current_char != "\n":
            self.advance()

    def skip_block_comment(self):            # T1: /* ... */
        self.advance(); self.advance()       # consume /*
        while self.current_char:
            if self.current_char == "*" and self.peek() == "/":
                self.advance(); self.advance()
                return
            self.advance()
        raise LexerError(f"Unterminated block comment at line {self.line}")

    def number(self):
        start_col = self.column
        value     = ""
        is_float  = False
        while self.current_char and self.current_char.isdigit():
            value += self.current_char
            self.advance()
        if self.current_char == "." and self.peek() and self.peek().isdigit():
            is_float = True
            value   += self.current_char
            self.advance()
            while self.current_char and self.current_char.isdigit():
                value += self.current_char
                self.advance()
        if is_float:
            return Token("FLOAT", float(value), self.line, start_col)
        return Token("INTEGER", int(value), self.line, start_col)

    def identifier(self):
        start_col = self.column
        value     = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            value += self.current_char
            self.advance()
        keywords = {
            "int":    "INT",
            "float":  "FLOAT_TYPE",           # T1
            "print":  "PRINT",
            "while":  "WHILE",
            "for":    "FOR",                  # T1
            "if":     "IF",
            "else":   "ELSE",
            "def":    "DEF",
            "return": "RETURN",
        }
        return Token(keywords.get(value, "ID"), value, self.line, start_col)

    def get_next_token(self):
        while self.current_char:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # comments
            if self.current_char == "/" and self.peek() == "/":
                self.skip_line_comment()
                continue
            if self.current_char == "/" and self.peek() == "*":
                self.skip_block_comment()
                continue

            if self.current_char.isdigit():
                return self.number()

            # float starting with dot  .5
            if self.current_char == "." and self.peek() and self.peek().isdigit():
                return self.number()

            if self.current_char.isalpha() or self.current_char == "_":
                return self.identifier()

            start_col = self.column

            # two-char tokens
            two = {
                "==": "EQ",  "!=": "NEQ",
                "<=": "LTE", ">=": "GTE",
            }
            ch2 = self.current_char + (self.peek() or "")
            if ch2 in two:
                self.advance(); self.advance()
                return Token(two[ch2], ch2, self.line, start_col)

            single = {
                "=": "ASSIGN", "+": "PLUS",  "-": "MINUS",
                "*": "MUL",    "/": "DIV",   "%": "MOD",   # T1: modulo
                "(": "LPAREN", ")": "RPAREN",
                "{": "LBRACE", "}": "RBRACE",
                "[": "LBRACKET", "]": "RBRACKET",           # T2: arrays
                ";": "SEMI",   ",": "COMMA",
                "<": "LT",     ">": "GT",
            }
            if self.current_char in single:
                char = self.current_char
                self.advance()
                return Token(single[char], char, self.line, start_col)

            raise LexerError(
                f"Invalid character '{self.current_char}' at line {self.line}, column {self.column}"
            )

        return Token("EOF", None, self.line, self.column)