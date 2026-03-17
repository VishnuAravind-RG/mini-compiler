# visualizer.py

from graphviz import Digraph
from ast_nodes import *
import subprocess, shutil

class ASTVisualizer:

    def __init__(self):
        self.dot     = Digraph()
        self.counter = 0

    def new_id(self):
        self.counter += 1
        return f"n{self.counter}"

    def visit(self, node):
        nid = self.new_id()

        if isinstance(node, Block):
            self.dot.node(nid, "Block")
            for child in node.children:
                self.dot.edge(nid, self.visit(child))

        elif isinstance(node, Num):
            self.dot.node(nid, str(node.token.value))

        elif isinstance(node, Var):
            self.dot.node(nid, str(node.token.value))

        elif isinstance(node, BinOp):
            self.dot.node(nid, node.op.value)
            self.dot.edge(nid, self.visit(node.left))
            self.dot.edge(nid, self.visit(node.right))

        elif isinstance(node, Assign):
            self.dot.node(nid, "=")
            self.dot.edge(nid, self.visit(node.left))
            self.dot.edge(nid, self.visit(node.right))

        elif isinstance(node, VarDecl):
            self.dot.node(nid, f"int {node.token.value}")

        elif isinstance(node, Print):
            self.dot.node(nid, "print")
            self.dot.edge(nid, self.visit(node.expr))

        elif isinstance(node, While):
            self.dot.node(nid, "while")
            self.dot.edge(nid, self.visit(node.cond), label="cond")
            self.dot.edge(nid, self.visit(node.body), label="body")

        elif isinstance(node, If):
            self.dot.node(nid, "if")
            self.dot.edge(nid, self.visit(node.cond), label="cond")
            self.dot.edge(nid, self.visit(node.body), label="then")

        elif isinstance(node, IfElse):
            self.dot.node(nid, "if-else")
            self.dot.edge(nid, self.visit(node.cond),      label="cond")
            self.dot.edge(nid, self.visit(node.then_body), label="then")
            self.dot.edge(nid, self.visit(node.else_body), label="else")

        elif isinstance(node, FuncDef):
            params = ", ".join(node.params)
            self.dot.node(nid, f"def {node.name}({params})")
            self.dot.edge(nid, self.visit(node.body), label="body")

        elif isinstance(node, FuncCall):
            self.dot.node(nid, f"call {node.name}")
            for i, arg in enumerate(node.args):
                self.dot.edge(nid, self.visit(arg), label=f"arg{i+1}")

        elif isinstance(node, Return):
            self.dot.node(nid, "return")
            self.dot.edge(nid, self.visit(node.expr))

        else:
            self.dot.node(nid, "?")

        return nid

    def render(self, tree, filename="ast"):
        self.visit(tree)
        dot_file = filename + ".dot"
        png_file = filename + ".png"
        self.dot.save(dot_file)
        dot_path = shutil.which("dot")
        if not dot_path:
            raise Exception("Graphviz 'dot' not found.")
        subprocess.run([dot_path, "-Tpng", dot_file, "-o", png_file], check=True)
        print(f"{png_file} generated.")