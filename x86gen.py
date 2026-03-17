# x86gen.py  —  Tier 3: x86-64 Assembly Code Generator
# Generates real NASM-style x86-64 assembly from IR instructions

class X86Generator:

    # registers available for allocation (caller-saved first)
    REGS = ["eax", "ebx", "ecx", "edx", "esi", "edi", "r8d", "r9d", "r10d", "r11d"]

    def __init__(self, ir_instructions):
        self.ir       = ir_instructions
        self.asm      = []          # output lines
        self.reg_map  = {}          # var_name -> register
        self.stack    = {}          # var_name -> stack offset
        self.sp_off   = 0           # current stack pointer offset
        self.free_regs= list(self.REGS)
        self.used_regs= {}          # var -> reg
        self.in_func  = False
        self.func_name= None

    # ── register allocator (linear scan, simple) ──────────────────

    def alloc_reg(self, var):
        """Give var a register. Spill to stack if none free."""
        if var in self.used_regs:
            return self.used_regs[var]
        if self.free_regs:
            reg = self.free_regs.pop(0)
            self.used_regs[var] = reg
            return reg
        # spill: evict first allocated var to stack
        victim, vreg = next(iter(self.used_regs.items()))
        self._spill(victim, vreg)
        del self.used_regs[victim]
        self.used_regs[var] = vreg
        return vreg

    def _spill(self, var, reg):
        self.sp_off += 4
        self.stack[var] = self.sp_off
        self.emit(f"    mov    DWORD [rbp-{self.sp_off}], {reg}   ; spill {var}")

    def resolve(self, operand):
        """Return the asm operand string for an IR value."""
        s = str(operand)
        # numeric literal
        try:
            float(s)
            return s
        except (ValueError, TypeError):
            pass
        if s in self.used_regs:
            return self.used_regs[s]
        if s in self.stack:
            return f"DWORD [rbp-{self.stack[s]}]"
        # unknown — treat as immediate 0 (safe fallback)
        return s

    def free_temp(self, var):
        """Release a temp register back to free pool."""
        s = str(var)
        if s.startswith("t") and s[1:].isdigit() and s in self.used_regs:
            self.free_regs.insert(0, self.used_regs.pop(s))

    # ── emitters ──────────────────────────────────────────────────

    def emit(self, line=""):
        self.asm.append(line)

    def emit_header(self):
        self.emit("; ═══════════════════════════════════════════")
        self.emit("; Generated x86-64 Assembly (NASM syntax)")
        self.emit("; Mini Compiler — Tier 3 Code Generator")
        self.emit("; ═══════════════════════════════════════════")
        self.emit()
        self.emit("global  main")
        self.emit("extern  printf")
        self.emit()
        self.emit("section .data")
        self.emit('    fmt_int  db  "%d", 10, 0   ; printf format')
        self.emit('    fmt_flt  db  "%f", 10, 0')
        self.emit()
        self.emit("section .text")

    def emit_func_prologue(self, name):
        self.emit()
        self.emit(f"{name}:")
        self.emit(f"    push   rbp")
        self.emit(f"    mov    rbp, rsp")
        self.emit(f"    sub    rsp, 128        ; local variable space")

    def emit_func_epilogue(self, name):
        self.emit(f".{name}_exit:")
        self.emit(f"    mov    rsp, rbp")
        self.emit(f"    pop    rbp")
        self.emit(f"    ret")

    # ── CMP op → jmp suffix ───────────────────────────────────────

    CMP_JUMP = {
        "<":  "jl",  ">":  "jg",
        "<=": "jle", ">=": "jge",
        "==": "je",  "!=": "jne",
    }

    # ── main translation loop ─────────────────────────────────────

    def generate(self):
        self.emit_header()

        for instr in self.ir:
            op = instr.op

            # ── function boundaries ───────────────────────────────
            if op == "func_begin":
                self.in_func   = True
                self.func_name = instr.result
                self.used_regs = {}
                self.free_regs = list(self.REGS)
                self.stack     = {}
                self.sp_off    = 0
                self.emit_func_prologue(instr.result)

            elif op == "func_end":
                self.emit_func_epilogue(instr.result)
                self.in_func = False

            elif op == "param":
                # params arrive in rdi, rsi, rdx, rcx, r8, r9
                param_regs = ["edi","esi","edx","ecx","r8d","r9d"]
                idx = sum(1 for v in self.used_regs)
                reg = self.alloc_reg(instr.arg1)
                if idx < len(param_regs):
                    self.emit(f"    mov    {reg}, {param_regs[idx]}   ; param {instr.arg1}")

            # ── labels & jumps ────────────────────────────────────
            elif op == "label":
                self.emit(f".{instr.result}:")

            elif op == "goto":
                self.emit(f"    jmp    .{instr.result}")

            elif op == "ifnot":
                cond = self.resolve(instr.arg1)
                self.emit(f"    cmp    {cond}, 0")
                self.emit(f"    je     .{instr.result}")

            # ── assignment ────────────────────────────────────────
            elif op == "assign":
                dst = self.alloc_reg(instr.result)
                src = self.resolve(instr.arg1)
                if src == dst:
                    pass
                elif src.startswith("DWORD"):
                    self.emit(f"    mov    {dst}, {src}")
                else:
                    try:
                        float(src)
                        self.emit(f"    mov    {dst}, {src}")
                    except ValueError:
                        self.emit(f"    mov    {dst}, {src}")

            # ── arithmetic ────────────────────────────────────────
            elif op in ("+", "-", "*", "/", "%"):
                dst  = self.alloc_reg(instr.result)
                lft  = self.resolve(instr.arg1)
                rgt  = self.resolve(instr.arg2)

                if op == "+":
                    self.emit(f"    mov    {dst}, {lft}")
                    self.emit(f"    add    {dst}, {rgt}")
                elif op == "-":
                    self.emit(f"    mov    {dst}, {lft}")
                    self.emit(f"    sub    {dst}, {rgt}")
                elif op == "*":
                    self.emit(f"    mov    eax, {lft}")
                    self.emit(f"    imul   eax, {rgt}")
                    self.emit(f"    mov    {dst}, eax")
                elif op in ("/", "%"):
                    self.emit(f"    mov    eax, {lft}")
                    self.emit(f"    cdq                  ; sign-extend eax→edx:eax")
                    self.emit(f"    mov    ecx, {rgt}")
                    self.emit(f"    idiv   ecx")
                    if op == "/":
                        self.emit(f"    mov    {dst}, eax  ; quotient")
                    else:
                        self.emit(f"    mov    {dst}, edx  ; remainder")

                self.free_temp(instr.arg1)
                self.free_temp(instr.arg2)

            # ── comparisons ───────────────────────────────────────
            elif op in ("<", ">", "<=", ">=", "==", "!="):
                dst = self.alloc_reg(instr.result)
                lft = self.resolve(instr.arg1)
                rgt = self.resolve(instr.arg2)
                jmp = self.CMP_JUMP[op]
                lbl_true = f"_cmp_{len(self.asm)}_true"
                lbl_done = f"_cmp_{len(self.asm)}_done"
                self.emit(f"    cmp    {lft}, {rgt}")
                self.emit(f"    {jmp:<6} .{lbl_true}")
                self.emit(f"    mov    {dst}, 0")
                self.emit(f"    jmp    .{lbl_done}")
                self.emit(f".{lbl_true}:")
                self.emit(f"    mov    {dst}, 1")
                self.emit(f".{lbl_done}:")

            # ── unary neg ─────────────────────────────────────────
            elif op == "neg":
                dst = self.alloc_reg(instr.result)
                src = self.resolve(instr.arg1)
                self.emit(f"    mov    {dst}, {src}")
                self.emit(f"    neg    {dst}")

            # ── print (calls printf) ──────────────────────────────
            elif op == "print":
                val = self.resolve(instr.arg1)
                self.emit(f"    ; --- print {instr.arg1} ---")
                self.emit(f"    lea    rdi, [rel fmt_int]")
                self.emit(f"    mov    esi, {val}")
                self.emit(f"    xor    eax, eax")
                self.emit(f"    call   printf")

            # ── return ────────────────────────────────────────────
            elif op == "return":
                val = self.resolve(instr.arg1)
                self.emit(f"    mov    eax, {val}     ; return value")
                self.emit(f"    jmp    .{self.func_name}_exit")

            # ── function call ─────────────────────────────────────
            elif op == "call":
                arg_regs = ["edi","esi","edx","ecx","r8d","r9d"]
                for i, arg in enumerate(instr.arg2 or []):
                    v = self.resolve(arg)
                    if i < len(arg_regs):
                        self.emit(f"    mov    {arg_regs[i]}, {v}")
                self.emit(f"    call   {instr.arg1}")
                dst = self.alloc_reg(instr.result)
                self.emit(f"    mov    {dst}, eax     ; capture return")

            # ── arrays ───────────────────────────────────────────
            elif op == "array_decl":
                self.emit(f"    ; ARRAY {instr.result}[{instr.arg1}] on stack")
                self.sp_off += int(instr.arg1) * 4
                self.stack[instr.result] = self.sp_off

            elif op == "array_store":
                idx  = self.resolve(instr.arg1)
                val  = self.resolve(instr.arg2)
                base = self.stack.get(instr.result, 0)
                tmp  = "ecx"
                self.emit(f"    mov    {tmp}, {idx}")
                self.emit(f"    imul   {tmp}, 4")
                self.emit(f"    neg    {tmp}")
                self.emit(f"    add    {tmp}, rbp")
                self.emit(f"    sub    {tmp}, {base - int(instr.arg1)*4 if isinstance(instr.arg1, int) else base}")
                self.emit(f"    mov    eax, {val}")
                self.emit(f"    mov    DWORD [{tmp}], eax")

            elif op == "array_load":
                dst  = self.alloc_reg(instr.result)
                idx  = self.resolve(instr.arg2)
                base = self.stack.get(instr.arg1, 0)
                self.emit(f"    mov    ecx, {idx}")
                self.emit(f"    imul   ecx, 4")
                self.emit(f"    lea    rdx, [rbp-{base}]")
                self.emit(f"    mov    {dst}, DWORD [rdx+rcx]")

        return "\n".join(self.asm)