# cfg.py

from ir import IRInstruction
from graphviz import Digraph
import subprocess
import shutil


# ============================================================
# BASIC BLOCK
# ============================================================

class BasicBlock:

    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.successors = []

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def add_successor(self, block):
        if block not in self.successors:
            self.successors.append(block)

    def __str__(self):
        content = "\n".join(str(i) for i in self.instructions)
        return f"{self.name}:\n{content}"


# ============================================================
# CFG BUILDER
# ============================================================

class CFGBuilder:

    def __init__(self, instructions):
        self.instructions = instructions
        self.blocks = []
        self.label_map = {}

    def find_leaders(self):
        leaders = set()
        leaders.add(0)

        for i, instr in enumerate(self.instructions):

            if instr.op == "label":
                leaders.add(i)

            if instr.op in ("goto", "ifnot"):
                if i + 1 < len(self.instructions):
                    leaders.add(i + 1)

        return sorted(leaders)

    def build_blocks(self):

        leaders = self.find_leaders()
        leader_set = set(leaders)

        current_block = None
        block_count = 0

        for i, instr in enumerate(self.instructions):

            if i in leader_set:
                current_block = BasicBlock(f"B{block_count}")
                self.blocks.append(current_block)
                block_count += 1

            current_block.add_instruction(instr)

            if instr.op == "label":
                self.label_map[instr.result] = current_block

        return self.blocks

    def connect_blocks(self):

        for i, block in enumerate(self.blocks):

            if not block.instructions:
                continue

            last = block.instructions[-1]

            if last.op == "goto":
                target_block = self.label_map.get(last.result)
                if target_block:
                    block.add_successor(target_block)

            elif last.op == "ifnot":
                target_block = self.label_map.get(last.result)
                if target_block:
                    block.add_successor(target_block)

                if i + 1 < len(self.blocks):
                    block.add_successor(self.blocks[i + 1])

            else:
                if i + 1 < len(self.blocks):
                    block.add_successor(self.blocks[i + 1])

    def build(self):
        self.build_blocks()
        self.connect_blocks()
        return self.blocks


# ============================================================
# CFG VISUALIZER
# ============================================================

class CFGVisualizer:

    def __init__(self, blocks):
        self.blocks = blocks

    def render(self, filename="cfg"):

        dot = Digraph()

        for block in self.blocks:
            label = "\n".join(str(instr) for instr in block.instructions)
            dot.node(block.name, label)

        for block in self.blocks:
            for succ in block.successors:
                dot.edge(block.name, succ.name)

        dot_file = filename + ".dot"
        png_file = filename + ".png"

        dot.save(dot_file)

        dot_path = shutil.which("dot")
        if not dot_path:
            raise Exception("Graphviz 'dot' not found. Install it and ensure it's in PATH.")

        subprocess.run([dot_path, "-Tpng", dot_file, "-o", png_file], check=True)

        print(f"{png_file} generated successfully.")