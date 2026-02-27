# lexer.py

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column


class Lexer:

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = text[self.pos] if text else None

    def advance(self):
        if self.current_char == "\n":
            self.line += 1
            self.column = 0
        self.pos += 1
        self.column += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
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
            "int": "INT",
            "print": "PRINT",
            "while": "WHILE"
        }

        return Token(keywords.get(value, "ID"), value, self.line, start_col)

    def get_next_token(self):

        while self.current_char:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return self.number()

            if self.current_char.isalpha():
                return self.identifier()

            start_col = self.column

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
                ";": "SEMI"
            }

            if self.current_char in single_tokens:
                char = self.current_char
                self.advance()
                return Token(single_tokens[char], char, self.line, start_col)

            raise Exception(f"Invalid character {self.current_char} at {self.line}:{self.column}")

        return Token("EOF", None, self.line, self.column)