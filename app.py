# app.py  —  Flask Web UI for Mini Compiler

import os, sys, io, traceback, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, render_template, send_file

from lexer          import Lexer
from parser         import Parser
from semantic       import SemanticAnalyzer
from optimizer      import ASTOptimizer, IROptimizer
from ir             import IRGenerator
from cfg            import CFGBuilder, CFGVisualizer
from visualizer     import ASTVisualizer
from x86gen         import X86Generator
from error_handler  import ErrorHandler

app      = Flask(__name__)
WORK_DIR = tempfile.mkdtemp()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/compile", methods=["POST"])
def compile_route():
    source = request.json.get("code", "")
    eh     = ErrorHandler(source)

    try:
        # ── 1. Lex + Parse ────────────────────────────────────────
        try:
            tree = Parser(Lexer(source)).parse()
        except Exception as e:
            eh.parse_exception(e, "Parser")
            return jsonify(errors=eh.to_list(), stage="parse")

        # ── 2. Semantic Analysis ──────────────────────────────────
        analyzer = SemanticAnalyzer()
        analyzer.visit(tree)
        for err in analyzer.errors:
            eh.add("Semantic", err)

        # ── 3. AST Optimization ───────────────────────────────────
        try:
            tree = ASTOptimizer().visit(tree)
        except Exception as e:
            eh.parse_exception(e, "Optimizer")
            return jsonify(errors=eh.to_list(), stage="optimize")

        # ── 4. AST Visualization ──────────────────────────────────
        try:
            ASTVisualizer().render(tree, os.path.join(WORK_DIR, "ast"))
        except Exception:
            pass  # non-fatal

        # ── 5. IR Generation ──────────────────────────────────────
        ir_gen       = IRGenerator()
        instructions = ir_gen.generate(tree)
        ir_lines     = [str(i) for i in instructions]

        # ── 6. IR Optimization ───────────────────────────────────
        old, sys.stdout = sys.stdout, io.StringIO()
        opt_lines = IROptimizer().optimize(ir_lines)
        sys.stdout = old

        # ── 7. CFG ───────────────────────────────────────────────
        cfg_builder = CFGBuilder(instructions)
        blocks      = cfg_builder.build()
        try:
            CFGVisualizer(blocks).render(os.path.join(WORK_DIR, "cfg"))
        except Exception:
            pass

        cfg_data = [
            {
                "name":         b.name,
                "instructions": [str(i) for i in b.instructions],
                "successors":   [s.name for s in b.successors],
            }
            for b in blocks
        ]

        # ── 8. x86-64 Assembly Generation ────────────────────────
        x86 = ""
        try:
            gen = X86Generator(instructions)
            x86 = gen.generate()
        except Exception as e:
            x86 = f"; x86 generation error: {e}"

        return jsonify(
            ir        = ir_lines,
            ir_opt    = opt_lines,
            cfg       = cfg_data,
            x86       = x86,
            errors    = eh.to_list(),
            warnings  = analyzer.errors,
        )

    except Exception:
        tb = traceback.format_exc(limit=6)
        eh.add("Internal", tb)
        return jsonify(errors=eh.to_list(), stage="internal")


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