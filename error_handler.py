# error_handler.py  —  Tier 3: Rich error reporting with recovery

import re


class CompilerError:
    def __init__(self, stage, message, line=None, col=None, snippet=None):
        self.stage   = stage
        self.message = message
        self.line    = line
        self.col     = col
        self.snippet = snippet

    def to_dict(self):
        return {
            "stage":   self.stage,
            "message": self.message,
            "line":    self.line,
            "col":     self.col,
            "snippet": self.snippet,
        }

    def __str__(self):
        loc = f" (line {self.line})" if self.line else ""
        return f"[{self.stage}]{loc} {self.message}"


class ErrorHandler:
    """Collects errors from all stages, formats them nicely."""

    def __init__(self, source: str):
        self.source = source
        self.lines  = source.splitlines()
        self.errors = []

    def add(self, stage, message, line=None, col=None):
        snippet = None
        if line and 1 <= line <= len(self.lines):
            src_line = self.lines[line - 1]
            pointer  = (" " * ((col - 1) if col else 0)) + "^"
            snippet  = f"{src_line}\n{pointer}"
        err = CompilerError(stage, message, line, col, snippet)
        self.errors.append(err)
        return err

    def parse_exception(self, exc: Exception, stage: str):
        """Extract line/col from exception message if present."""
        msg = str(exc)
        # match "line N" or "N:M"
        m = re.search(r'[Ll]ine\s+(\d+)', msg)
        line = int(m.group(1)) if m else None
        m2 = re.search(r':(\d+)', msg)
        col  = int(m2.group(1)) if m2 else None
        return self.add(stage, msg, line, col)

    def has_errors(self):
        return len(self.errors) > 0

    def format_all(self):
        out = []
        for e in self.errors:
            out.append(str(e))
            if e.snippet:
                for sl in e.snippet.splitlines():
                    out.append("  " + sl)
        return "\n".join(out)

    def to_list(self):
        return [e.to_dict() for e in self.errors]