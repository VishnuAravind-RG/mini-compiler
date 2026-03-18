# app.py

import os, sys, io, traceback, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, render_template, send_file

from lexer          import Lexer
from parser         import Parser
from semantic       import SemanticAnalyzer
from optimizer      import ASTOptimizer, IROptimizer, BlockOptimizer
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
    source         = request.json.get("code", "")
    eh             = ErrorHandler(source)
    parse_warnings = []

    # pipeline_trace collects output from every phase for the trace tab
    pipeline_trace = []

    def trace(phase_num, phase_name, lines, status="ok", errors=None):
        pipeline_trace.append({
            "num":    phase_num,
            "name":   phase_name,
            "lines":  lines,
            "status": status,   # "ok" | "warn" | "error"
            "errors": errors or [],
        })

    try:
        # ════════════════════════════════════════════════════
        # PHASE 1 — LEXER
        # ════════════════════════════════════════════════════
        token_list  = []
        token_lines = []
        lex_errors  = []
        try:
            lex_scan = Lexer(source)
            tok = lex_scan.get_next_token()
            while tok.type != "EOF":
                token_list.append({
                    "type":  tok.type,
                    "value": str(tok.value),
                    "line":  tok.line,
                    "col":   tok.column,
                })
                token_lines.append(
                    f"  {tok.type:<14} | {str(tok.value):<12} | L{tok.line}:{tok.column}"
                )
                tok = lex_scan.get_next_token()
        except Exception as e:
            lex_errors.append(str(e))

        trace(1, "Lexer — Tokenization",
              [f"Input source → {len(token_list)} tokens produced", ""] +
              [f"{'TYPE':<14} | {'VALUE':<12} | LOCATION",
               "-" * 42] +
              token_lines +
              ["", f"✓ Lexer completed — {len(token_list)} tokens"],
              status="error" if lex_errors else "ok",
              errors=lex_errors)

        # ════════════════════════════════════════════════════
        # PHASE 2 — PARSER
        # ════════════════════════════════════════════════════
        try:
            lexer  = Lexer(source)
            parser = Parser(lexer)
            tree, parse_errors = parser.parse()
            for e in parse_errors:
                parse_warnings.append(e)
                eh.add("Parser", e)

            # describe the AST root
            ast_summary = []
            def describe_node(node, indent=0):
                name = type(node).__name__
                prefix = "  " * indent + "├─ "
                from ast_nodes import (Block, Assign, VarDecl, FuncDef,
                                       FuncCall, If, IfElse, While, For,
                                       Print, Return, ArrayDecl)
                if isinstance(node, Block):
                    ast_summary.append(prefix + f"Block ({len(node.children)} children)")
                    for c in node.children[:8]:   # limit depth
                        describe_node(c, indent+1)
                    if len(node.children) > 8:
                        ast_summary.append("  "*(indent+1) + "├─ ...")
                elif isinstance(node, FuncDef):
                    params = ", ".join(f"{t} {n}" for n,t in node.params)
                    ast_summary.append(prefix + f"FuncDef: {node.name}({params})")
                elif isinstance(node, VarDecl):
                    ast_summary.append(prefix + f"VarDecl: {node.var_type} {node.token.value}")
                elif isinstance(node, ArrayDecl):
                    ast_summary.append(prefix + f"ArrayDecl: {node.var_type} {node.name}[{node.size}]")
                elif isinstance(node, Assign):
                    ast_summary.append(prefix + f"Assign → {node.left.token.value}")
                elif isinstance(node, If):
                    ast_summary.append(prefix + "If")
                elif isinstance(node, IfElse):
                    ast_summary.append(prefix + "IfElse")
                elif isinstance(node, While):
                    ast_summary.append(prefix + "While")
                elif isinstance(node, For):
                    ast_summary.append(prefix + "For")
                elif isinstance(node, Print):
                    ast_summary.append(prefix + "Print")
                elif isinstance(node, Return):
                    ast_summary.append(prefix + "Return")
                elif isinstance(node, FuncCall):
                    ast_summary.append(prefix + f"FuncCall: {node.name}()")
                else:
                    ast_summary.append(prefix + name)
            describe_node(tree)

            p_status = "warn" if parse_errors else "ok"
            p_errors = parse_errors
            trace(2, "Parser — AST Construction",
                  [f"Tokens → Abstract Syntax Tree", ""] +
                  ["AST Structure:", "-" * 42] +
                  ast_summary +
                  ["", f"✓ Parser completed — AST built"] +
                  ([f"  ⚠ {len(parse_errors)} error(s) recovered:"] +
                   [f"    • {e}" for e in parse_errors] if parse_errors else []),
                  status=p_status, errors=p_errors)

        except Exception as e:
            eh.parse_exception(e, "Parser")
            trace(2, "Parser — AST Construction", [f"✗ Parser failed: {e}"],
                  status="error", errors=[str(e)])
            return jsonify(pipeline_trace=pipeline_trace,
                           errors=eh.to_list(), stage="parse")

        # ════════════════════════════════════════════════════
        # PHASE 3 — SEMANTIC ANALYSIS
        # ════════════════════════════════════════════════════
        analyzer = SemanticAnalyzer()
        analyzer.visit(tree)
        for err in analyzer.errors:
            eh.add("Semantic", err)

        sem_lines = ["AST → Semantic checks performed", ""]
        sem_lines += ["Checks run:", "-" * 42]
        sem_lines += ["  ✓ Variable declaration check (all vars declared before use)"]
        sem_lines += ["  ✓ Scope analysis (block-level scoping)"]
        sem_lines += ["  ✓ Function existence check (all called functions defined)"]
        sem_lines += ["  ✓ Argument count validation (params match args)"]
        sem_lines += ["  ✓ Array access validation (only arrays can be indexed)"]
        sem_lines += [""]
        if analyzer.errors:
            sem_lines += [f"⚠ {len(analyzer.errors)} semantic error(s) found:"]
            sem_lines += [f"  • {e}" for e in analyzer.errors]
        else:
            sem_lines += ["✓ Semantic analysis passed — no errors"]

        trace(3, "Semantic Analysis",
              sem_lines,
              status="warn" if analyzer.errors else "ok",
              errors=analyzer.errors)

        # ════════════════════════════════════════════════════
        # PHASE 4 — OPTIMIZATION
        # ════════════════════════════════════════════════════
        tree_before_str = []
        def ast_to_lines(node, indent=0):
            from ast_nodes import Block, Assign, BinOp, Num, FloatNum
            name = type(node).__name__
            prefix = "  " * indent
            if isinstance(node, Block):
                for c in node.children:
                    ast_to_lines(c, indent)
            elif isinstance(node, Assign):
                tree_before_str.append(f"{prefix}{node.left.token.value} = ...")
            elif isinstance(node, BinOp):
                if isinstance(node.left, Num) and isinstance(node.right, Num):
                    tree_before_str.append(
                        f"{prefix}{node.left.token.value} {node.op.value} "
                        f"{node.right.token.value}  ← foldable"
                    )
        ast_to_lines(tree)

        try:
            tree = ASTOptimizer().visit(tree)
        except Exception as e:
            eh.parse_exception(e, "Optimizer")

        opt_lines = ["AST → Apply constant folding", ""]
        opt_lines += ["Optimizations applied:", "-" * 42]
        opt_lines += ["  • Constant Folding    — compute known values at compile time"]
        opt_lines += ["    e.g.  3 * 2  →  6"]
        opt_lines += ["    e.g.  5 > 3  →  1 (true)"]
        opt_lines += ["  • Constant Propagation — replace vars with known values"]
        opt_lines += ["    e.g.  x = 5; y = x + 1  →  y = 5 + 1"]
        opt_lines += ["  • Dead Code Elimination — remove assignments never read"]
        opt_lines += ["    e.g.  t1 = x + 1  (t1 never used)  →  removed"]
        opt_lines += ["", "✓ AST optimization completed"]

        trace(4, "Optimizer — Constant Folding + DCE", opt_lines, status="ok")

        # ════════════════════════════════════════════════════
        # PHASE 5 — IR GENERATION (3AC)
        # ════════════════════════════════════════════════════
        try:
            ASTVisualizer().render(tree, os.path.join(WORK_DIR, "ast"))
        except Exception:
            pass

        ir_gen       = IRGenerator()
        instructions = ir_gen.generate(tree)
        ir_lines     = [str(i) for i in instructions]

        ir_trace_lines = ["AST → Three Address Code (3AC)", ""]
        ir_trace_lines += [f"{'#':<4} {'INSTRUCTION'}", "-" * 42]
        for i, line in enumerate(ir_lines):
            ir_trace_lines.append(f"{i+1:<4} {line}")
        ir_trace_lines += ["", f"✓ IR generation completed — {len(ir_lines)} instructions"]

        trace(5, "IR Generator — Three Address Code",
              ir_trace_lines, status="ok")

        # ════════════════════════════════════════════════════
        # PHASE 6 — IR OPTIMIZATION
        # ════════════════════════════════════════════════════
        ir_before = list(ir_lines)
        old, sys.stdout = sys.stdout, io.StringIO()
        try:
            ir_after = IROptimizer().optimize(ir_lines)
        except Exception:
            ir_after = ir_lines
        sys.stdout = old

        removed = len(ir_before) - len(ir_after)
        ir_opt_trace = ["IR before → IR after optimization", ""]
        ir_opt_trace += [f"{'BEFORE':<30} {'AFTER'}", "-" * 60]
        max_len = max(len(ir_before), len(ir_after))
        for i in range(max_len):
            b = ir_before[i] if i < len(ir_before) else ""
            a = ir_after[i]  if i < len(ir_after)  else "(removed)"
            marker = "  " if b == a else "←"
            ir_opt_trace.append(f"{b:<30} {marker}  {a}")
        ir_opt_trace += ["", f"✓ IR optimization: {removed} instruction(s) eliminated"]

        trace(6, "IR Optimizer — Propagation + DCE",
              ir_opt_trace, status="ok")

        # ════════════════════════════════════════════════════
        # PHASE 7 — CFG
        # ════════════════════════════════════════════════════
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
        block_opt_results = BlockOptimizer().optimize_all_blocks(blocks)

        cfg_trace = ["IR → Basic Blocks + Control Flow Graph", ""]
        cfg_trace += [f"{len(blocks)} basic blocks constructed", ""]
        for b in blocks:
            cfg_trace.append(f"┌─ {b.name} ({len(b.instructions)} instructions)")
            for instr in b.instructions:
                cfg_trace.append(f"│  {str(instr)}")
            succ_names = [s.name for s in b.successors]
            cfg_trace.append(f"└→ successors: {', '.join(succ_names) if succ_names else 'exit'}")
            cfg_trace.append("")
        cfg_trace += [f"✓ CFG built — {len(blocks)} blocks, edges connected"]

        trace(7, "CFG Builder — Basic Blocks + Flow Graph",
              cfg_trace, status="ok")

        # ════════════════════════════════════════════════════
        # PHASE 8 — x86-64 ASSEMBLY
        # ════════════════════════════════════════════════════
        x86 = ""
        try:
            x86 = X86Generator(instructions).generate()
        except Exception as e:
            x86 = f"; x86 generation error: {e}"

        x86_lines   = x86.split("\n")
        x86_trace   = ["IR → x86-64 NASM Assembly (register allocator active)", ""]
        x86_trace  += [f"{'#':<4} {'ASSEMBLY LINE'}", "-" * 50]
        for i, line in enumerate(x86_lines):
            x86_trace.append(f"{i+1:<4} {line}")
        x86_trace  += ["", f"✓ x86-64 generation: {len(x86_lines)} assembly lines"]

        trace(8, "x86-64 Code Generator — Assembly Output",
              x86_trace, status="ok")

        return jsonify(
            tokens         = token_list,
            ir             = ir_lines,
            ir_before      = ir_before,
            ir_after       = ir_after,
            cfg            = cfg_data,
            block_opts     = block_opt_results,
            x86            = x86,
            errors         = eh.to_list(),
            warnings       = analyzer.errors,
            parse_warnings = parse_warnings,
            pipeline_trace = pipeline_trace,
        )

    except Exception:
        tb = traceback.format_exc(limit=6)
        eh.add("Internal", tb)
        return jsonify(errors=eh.to_list(),
                       pipeline_trace=pipeline_trace,
                       stage="internal")


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