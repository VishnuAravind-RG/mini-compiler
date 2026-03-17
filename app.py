# app.py  —  Flask Web UI for Mini Compiler

import os, sys, io, traceback, tempfile
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, render_template, send_file

from lexer      import Lexer
from parser     import Parser
from semantic   import SemanticAnalyzer
from optimizer  import ASTOptimizer, IROptimizer
from ir         import IRGenerator
from cfg        import CFGBuilder, CFGVisualizer
from visualizer import ASTVisualizer

app = Flask(__name__)

WORK_DIR = tempfile.mkdtemp()   # where we write ast.png / cfg.png

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compile", methods=["POST"])
def compile_route():
    source = request.json.get("code", "")

    try:
        # 1. lex + parse
        lexer  = Lexer(source)
        parser = Parser(lexer)
        tree   = parser.parse()

        # 2. semantic
        SemanticAnalyzer().visit(tree)

        # 3. optimize AST
        tree = ASTOptimizer().visit(tree)

        # 4. AST image
        ast_vis = ASTVisualizer()
        ast_vis.render(tree, os.path.join(WORK_DIR, "ast"))

        # 5. IR
        ir_gen       = IRGenerator()
        instructions = ir_gen.generate(tree)
        ir_lines     = [str(i) for i in instructions]

        # 6. CFG
        cfg_builder = CFGBuilder(instructions)
        blocks      = cfg_builder.build()

        # 7. CFG image
        CFGVisualizer(blocks).render(os.path.join(WORK_DIR, "cfg"))

        # 8. optimized IR (for display)
        buf = io.StringIO()
        old_stdout, sys.stdout = sys.stdout, buf
        opt_lines = IROptimizer().optimize(ir_lines)
        sys.stdout = old_stdout

        cfg_data = [
            {
                "name": b.name,
                "instructions": [str(i) for i in b.instructions],
                "successors": [s.name for s in b.successors],
            }
            for b in blocks
        ]

        return jsonify(ir=ir_lines, cfg=cfg_data)

    except Exception as e:
        return jsonify(error=traceback.format_exc(limit=4))

@app.route("/image/<string:name>")
def serve_image(name):
    if name not in ("ast", "cfg"):
        return "not found", 404
    path = os.path.join(WORK_DIR, name + ".png")
    if not os.path.exists(path):
        return "not compiled yet", 404
    return send_file(path, mimetype="image/png")

if __name__ == "__main__":
    print(f"\n  Mini Compiler Studio → http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)