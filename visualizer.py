# visualizer.py

from graphviz import Digraph
from ast_nodes import *
import subprocess


# ============================================================
# AST VISUALIZER
# ============================================================

class ASTVisualizer:

    def __init__(self):
        self.dot = Digraph()
        self.node_count = 0

    def new_node(self, label):
        node_id = str(self.node_count)
        self.dot.node(node_id, label)
        self.node_count += 1
        return node_id

    # ------------------------------------------------------------
    # Visitor
    # ------------------------------------------------------------

    def visit(self, node):

        if isinstance(node, Block):
            current = self.new_node("BLOCK")
            for child in node.children:
                child_id = self.visit(child)
                self.dot.edge(current, child_id)
            return current

        elif isinstance(node, VarDecl):
            return self.new_node(f"DECL {node.token.value}")

        elif isinstance(node, Assign):
            current = self.new_node("ASSIGN")
            left = self.new_node(node.left.token.value)
            right = self.visit(node.right)
            self.dot.edge(current, left)
            self.dot.edge(current, right)
            return current

        elif isinstance(node, BinOp):
            current = self.new_node(node.op.value)
            left = self.visit(node.left)
            right = self.visit(node.right)
            self.dot.edge(current, left)
            self.dot.edge(current, right)
            return current

        elif isinstance(node, Num):
            return self.new_node(str(node.token.value))

        elif isinstance(node, Var):
            return self.new_node(node.token.value)

        elif isinstance(node, Print):
            current = self.new_node("PRINT")
            expr = self.visit(node.expr)
            self.dot.edge(current, expr)
            return current

        elif isinstance(node, While):
            current = self.new_node("WHILE")
            cond = self.visit(node.cond)
            body = self.visit(node.body)
            self.dot.edge(current, cond)
            self.dot.edge(current, body)
            return current

        else:
            return self.new_node("UNKNOWN")

    # ------------------------------------------------------------
    # Render (Manual dot execution)
    # ------------------------------------------------------------

    def render(self, tree, filename="ast"):
        self.visit(tree)

        dot_file = filename + ".dot"
        png_file = filename + ".png"

        self.dot.save(dot_file)

        dot_path = r"C:\Users\TEMP.WINSERVER.194\Desktop\windows_10_cmake_Release_Graphviz-14.1.2-win64\Graphviz-14.1.2-win64\bin\dot.exe"

        subprocess.run([dot_path, "-Tpng", dot_file, "-o", png_file], check=True)

        print(f"{png_file} generated successfully.")