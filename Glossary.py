# Glossary.py
# Reference data for the Glossary dropdown button in main.py.
#
# Public API (imported by main.py):
#   ARM64_GLOSSARY  — list of {"name": str, "info": str}
#   X86_GLOSSARY    — list of {"name": str, "info": str}
#   GENERATOR_NAMES — set of generator names whose info comes from Generators.py
#
# Entries whose "name" matches a generator name in GENERATOR_NAMES will show
# that generator's "info" string instead of a Glossary entry — main.py handles
# the lookup.  All other entries carry their own "info" text here.

# Names of generators so main.py can redirect to generator info.
# These entries appear in both glossary lists but have no "info" here.
GENERATOR_NAMES = {"MOV", "ADD", "IF_INST", "LOAD_STORE", "CMP", "BRANCH"}

# ---------------------------------------------------------------------------
# ARM64 (AArch64) Glossary
# ---------------------------------------------------------------------------
ARM64_GLOSSARY = [

    # ── General-Purpose Registers ───────────────────────────────────────────

    {
        "name": "X0–X7  (Arguments / Return)",
        "info": (
            "ARM64 Registers: X0–X7\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit\n\n"
            "PRIMARY ROLE:\n"
            "  • X0–X7  — first 8 integer/pointer function arguments.\n"
            "  • X0     — also holds the integer return value.\n"
            "  • X0–X1  — hold a 128-bit return value (two 64-bit halves).\n\n"
            "CALLEE-SAVED?  No — CALLER must save these before a call\n"
            "               if it still needs their values afterwards.\n\n"
            "32-BIT ALIAS:  W0–W7  (lower 32 bits; upper 32 zeroed on write)\n\n"
            "EXAMPLE:\n"
            "  ; Call strlen(my_string)\n"
            "  ldr  x0, =my_string    ; argument 1 in X0\n"
            "  bl   strlen\n"
            "  ; return value now in X0\n\n"
            "x86-64 EQUIVALENT:\n"
            "  RDI, RSI, RDX, RCX, R8, R9  (first 6 args, System V ABI)\n"
            "  RAX = return value"
        ),
    },
    {
        "name": "X8–X17  (Scratch / IP0–IP1)",
        "info": (
            "ARM64 Registers: X8–X17\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit\n\n"
            "PRIMARY ROLES:\n"
            "  X8   — indirect result register (large struct return address)\n"
            "          and the syscall number register in Linux ABI.\n"
            "  X9–X15  — general scratch registers (caller-saved).\n"
            "  X16 (IP0) — first intra-procedure-call scratch register.\n"
            "              Linker uses it for long-range branch veneers.\n"
            "  X17 (IP1) — second intra-procedure-call scratch register.\n\n"
            "CALLEE-SAVED?  No — all caller-saved (volatile).\n\n"
            "EXAMPLE:\n"
            "  ; Linux syscall: write(1, buf, len)\n"
            "  mov  x8, #64          ; syscall number for write\n"
            "  mov  x0, #1           ; fd = stdout\n"
            "  ldr  x1, =buf\n"
            "  mov  x2, #13\n"
            "  svc  #0               ; invoke kernel\n\n"
            "x86-64 EQUIVALENT:\n"
            "  R10–R11 (scratch), RAX = syscall number"
        ),
    },
    {
        "name": "X18–X28  (Callee-Saved)",
        "info": (
            "ARM64 Registers: X18–X28\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit\n\n"
            "PRIMARY ROLE:\n"
            "  X18     — platform register (OS/ABI reserved; avoid in user\n"
            "             code on Windows/iOS). Used as shadow call stack\n"
            "             pointer in some security configurations.\n"
            "  X19–X28 — callee-saved general-purpose registers.\n"
            "             A function that uses these MUST push them on\n"
            "             entry and pop them before returning.\n\n"
            "CALLEE-SAVED?  Yes (X19–X28) — the called function preserves them.\n\n"
            "EXAMPLE:\n"
            "  ; Save X19 before use, restore on return\n"
            "  stp  x19, x20, [sp, #-16]!\n"
            "  mov  x19, x0            ; preserve arg across calls\n"
            "  bl   some_function\n"
            "  add  x0, x19, x0        ; use saved value\n"
            "  ldp  x19, x20, [sp], #16\n"
            "  ret\n\n"
            "x86-64 EQUIVALENT:\n"
            "  RBX, RBP, R12–R15  (callee-saved under System V ABI)"
        ),
    },
    {
        "name": "X29  (FP — Frame Pointer)",
        "info": (
            "ARM64 Register: X29 / FP\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — dedicated Frame Pointer\n\n"
            "PURPOSE:\n"
            "  Points to the bottom of the current stack frame.\n"
            "  Stays CONSTANT while the function executes, unlike SP\n"
            "  which moves whenever data is pushed or popped.\n\n"
            "WHY IT MATTERS:\n"
            "  Debuggers walk a linked chain of saved FP values to\n"
            "  reconstruct the call stack (stack unwinding / backtraces).\n"
            "  Each frame: [saved FP | saved LR | local vars]\n\n"
            "TYPICAL PROLOGUE:\n"
            "  stp  x29, x30, [sp, #-16]!  ; save FP and LR\n"
            "  mov  x29, sp                 ; FP = current SP\n\n"
            "TYPICAL EPILOGUE:\n"
            "  ldp  x29, x30, [sp], #16    ; restore FP and LR\n"
            "  ret\n\n"
            "COMPILER NOTE:\n"
            "  -fomit-frame-pointer frees X29 as a scratch register\n"
            "  at the cost of losing reliable stack traces.\n\n"
            "x86-64 EQUIVALENT:  RBP (Base Pointer)"
        ),
    },
    {
        "name": "X30  (LR — Link Register)",
        "info": (
            "ARM64 Register: X30 / LR\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — dedicated Link Register\n\n"
            "PURPOSE:\n"
            "  Holds the RETURN ADDRESS written by the BL (Branch with\n"
            "  Link) instruction when a function is called.\n\n"
            "HOW IT WORKS:\n"
            "  bl   label    →  X30 = PC + 4 (next instruction address)\n"
            "                    PC  = label\n"
            "  ret           →  PC  = X30\n\n"
            "THE NON-LEAF PROBLEM:\n"
            "  If function A calls B (BL overwrites X30) and then calls\n"
            "  C, the original return-to-A address is LOST unless X30\n"
            "  was saved first.\n\n"
            "  Non-leaf functions MUST save X30 on the stack:\n"
            "  stp  x29, x30, [sp, #-16]!  ; save at function entry\n"
            "  …\n"
            "  ldp  x29, x30, [sp], #16    ; restore before ret\n"
            "  ret\n\n"
            "x86-64 EQUIVALENT:\n"
            "  No direct equivalent — CALL pushes the return address\n"
            "  onto the stack automatically; no register is used."
        ),
    },
    {
        "name": "SP  (X31 — Stack Pointer)",
        "info": (
            "ARM64 Register: SP / X31\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose, 64-bit — Stack Pointer\n\n"
            "PURPOSE:\n"
            "  Points to the CURRENT TOP of the call stack.\n"
            "  Moves downward (toward lower addresses) as the stack grows.\n\n"
            "RULES:\n"
            "  • SP must be 16-byte aligned at every function CALL.\n"
            "    (Violated alignment can cause hardware exceptions.)\n"
            "  • SP can only be used in load/store with certain forms\n"
            "    (not as a general arithmetic operand in most contexts).\n\n"
            "COMMON IDIOMS:\n"
            "  ; Allocate 32 bytes of stack space:\n"
            "  sub  sp, sp, #32\n\n"
            "  ; Pre-indexed store (allocate + store together):\n"
            "  stp  x29, x30, [sp, #-16]!   ; SP -= 16, then store\n\n"
            "  ; Post-indexed load (load + deallocate together):\n"
            "  ldp  x29, x30, [sp], #16     ; load, then SP += 16\n\n"
            "x86-64 EQUIVALENT:  RSP (Stack Pointer)\n"
            "  push rax   ≡   sub rsp,8  +  mov [rsp],rax\n"
            "  pop  rax   ≡   mov rax,[rsp]  +  add rsp,8"
        ),
    },
    {
        "name": "XZR / WZR  (Zero Register)",
        "info": (
            "ARM64 Register: XZR / WZR\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose — Hard-wired Zero Register\n\n"
            "PURPOSE:\n"
            "  • Reading XZR always returns 0.\n"
            "  • Writing to XZR silently discards the value.\n\n"
            "WHY IT EXISTS (RISC PHILOSOPHY):\n"
            "  Instead of adding extra 'clear', 'discard', or 'test'\n"
            "  opcodes, ARM64 uses XZR with existing instructions:\n\n"
            "  PSEUDO → REAL ENCODING:\n"
            "  mov  x0, x1   →  orr x0, xzr, x1    (copy)\n"
            "  cmp  x0, x1   →  subs xzr, x0, x1   (compare, discard)\n"
            "  tst  x0, x1   →  ands xzr, x0, x1   (bit-test, discard)\n"
            "  mov  x0, #0   →  movz x0, #0  or  orr x0,xzr,xzr\n\n"
            "  WZR = 32-bit alias (same register, 32-bit context).\n\n"
            "x86-64 EQUIVALENT:\n"
            "  x86-64 has NO zero register.\n"
            "  Zeroing idiom:  xor rax, rax  (preferred over mov rax,0)"
        ),
    },
    {
        "name": "PC  (Program Counter)",
        "info": (
            "ARM64 Register: PC (Program Counter)\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose, 64-bit\n\n"
            "PURPOSE:\n"
            "  Always holds the address of the CURRENTLY EXECUTING\n"
            "  instruction. Updated by the CPU after every instruction\n"
            "  fetch (PC += 4 normally; branches override it).\n\n"
            "ARM64 RESTRICTIONS:\n"
            "  • PC cannot be used as a general arithmetic operand\n"
            "    (unlike ARMv7/Thumb where MOV PC,Rn was common).\n"
            "  • PC-relative addressing is used for data/code access:\n"
            "    adr  x0, label    ; x0 = PC + offset-to-label\n"
            "    adrp x0, label    ; x0 = page address of label (±4 GB)\n\n"
            "BRANCH EFFECT:\n"
            "  b  label   →  PC = label  (PC-relative, ±128 MB)\n"
            "  br x0      →  PC = x0     (absolute, via register)\n\n"
            "x86-64 EQUIVALENT:  RIP (Instruction Pointer)\n"
            "  RIP-relative addressing:  mov rax, [rip + offset]"
        ),
    },
    {
        "name": "PSTATE / NZCV  (Flags)",
        "info": (
            "ARM64: PSTATE / NZCV Condition Flags\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Processor state bits (not a general register)\n\n"
            "THE FOUR FLAGS:\n"
            "  N — Negative  : set when the result's sign bit is 1\n"
            "                  (result interpreted as a signed number < 0)\n"
            "  Z — Zero      : set when the result is exactly 0\n"
            "  C — Carry     : set on unsigned overflow or borrow\n"
            "  V — oVerflow  : set on signed overflow\n\n"
            "HOW FLAGS ARE SET:\n"
            "  • CMP  x0, x1   (alias: SUBS xzr, x0, x1)\n"
            "  • CMN  x0, x1   (compare negative — sets on x0+x1)\n"
            "  • ADDS, SUBS, ANDS, ANDS with 'S' suffix\n"
            "  • TST  x0, x1   (alias: ANDS xzr, x0, x1)\n\n"
            "HOW FLAGS ARE READ:\n"
            "  Conditional branch suffixes:\n"
            "  EQ (Z=1)   NE (Z=0)   LT (N≠V)   GE (N=V)\n"
            "  LE (Z=1 or N≠V)       GT (Z=0 and N=V)\n"
            "  LO (C=0)   HS/CS (C=1)   HI (C=1,Z=0)   LS (C=0 or Z=1)\n\n"
            "x86-64 EQUIVALENT:  EFLAGS register\n"
            "  ZF=Zero  SF=Sign  CF=Carry  OF=Overflow  PF=Parity  AF=Aux\n"
            "  (6 flags + legacy bits; ARM's 4-bit NZCV is a cleaner design)"
        ),
    },
    {
        "name": "V0–V31  (SIMD / FP Registers)",
        "info": (
            "ARM64 Registers: V0–V31\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  128-bit SIMD / Floating-point registers\n\n"
            "NAMING ALIASES (all the same physical register):\n"
            "  Bx   —   8-bit  (byte)\n"
            "  Hx   —  16-bit  (half-precision float)\n"
            "  Sx   —  32-bit  (single-precision float)\n"
            "  Dx   —  64-bit  (double-precision float)\n"
            "  Qx   — 128-bit  (full SIMD vector)\n"
            "  Vx   — 128-bit  (vector lane access: V0.4S = 4×32-bit lanes)\n\n"
            "COMMON USES:\n"
            "  • Floating-point arithmetic (FADD, FMUL, FDIV, FSQRT…)\n"
            "  • SIMD (single instruction, multiple data) for image, audio,\n"
            "    crypto, and ML workloads.\n"
            "  • Argument passing: first 8 FP/SIMD args in V0–V7.\n\n"
            "EXAMPLES:\n"
            "  fadd d0, d1, d2     ; double: d0 = d1 + d2\n"
            "  fmul s0, s1, s2     ; float:  s0 = s1 × s2\n"
            "  add  v0.4s, v1.4s, v2.4s  ; 4 × int32 add in parallel\n\n"
            "x86-64 EQUIVALENT:\n"
            "  XMM0–XMM15 (128-bit SSE)\n"
            "  YMM0–YMM15 (256-bit AVX)\n"
            "  ZMM0–ZMM31 (512-bit AVX-512)"
        ),
    },

    # ── Key Instructions (non-generator entries) ────────────────────────────

    {
        "name": "MOV  →  see Generator info",
        "info": "__GENERATOR__:MOV",
    },
    {
        "name": "ADD  →  see Generator info",
        "info": "__GENERATOR__:ADD",
    },
    {
        "name": "SUB  (Subtract)",
        "info": (
            "ARM64 Instruction: SUB / SUBS\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Subtract one register or immediate from another.\n\n"
            "SYNTAX:\n"
            "  sub  x0, x1, x2          ; x0 = x1 - x2\n"
            "  sub  x0, x1, #10         ; x0 = x1 - 10\n"
            "  subs x0, x1, x2          ; same + sets NZCV flags\n"
            "  sub  x0, x1, x2, lsl #2  ; x0 = x1 - (x2 << 2)\n\n"
            "SAME 3-OPERAND PATTERN AS ADD:\n"
            "  Destination is always separate — sources are not modified.\n"
            "  'S' suffix opts in to flag-setting.\n\n"
            "KEY PSEUDO-INSTRUCTIONS BUILT ON SUBS:\n"
            "  cmp x0, x1   ≡   subs xzr, x0, x1   (discard result)\n"
            "  neg x0, x1   ≡   sub  x0, xzr, x1   (negate)\n\n"
            "x86-64 EQUIVALENT:\n"
            "  sub rax, rbx    ; rax = rax - rbx  (2-operand, destructive)\n"
            "  Always sets flags. No opt-out."
        ),
    },
    {
        "name": "MUL / MADD  (Multiply)",
        "info": (
            "ARM64 Instructions: MUL / MADD / SMULH / UMULH\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Integer multiplication.\n\n"
            "SYNTAX:\n"
            "  mul   x0, x1, x2         ; x0 = x1 × x2  (low 64 bits)\n"
            "  madd  x0, x1, x2, x3     ; x0 = x3 + (x1 × x2)  (fused)\n"
            "  msub  x0, x1, x2, x3     ; x0 = x3 - (x1 × x2)  (fused sub)\n"
            "  smulh x0, x1, x2         ; x0 = high 64 bits (signed)\n"
            "  umulh x0, x1, x2         ; x0 = high 64 bits (unsigned)\n\n"
            "NOTES:\n"
            "  • MUL is an alias for MADD with X3 = XZR.\n"
            "  • MADD is the ARM64 fused multiply-add — one instruction,\n"
            "    no intermediate rounding, important for DSP and ML.\n"
            "  • MUL does NOT set flags (no MULS variant).\n\n"
            "x86-64 EQUIVALENT:\n"
            "  imul rax, rbx          ; signed: rax = rax × rbx\n"
            "  imul rax, rbx, 10      ; rax = rbx × 10  (3-operand form)\n"
            "  mul  rbx               ; unsigned: RDX:RAX = RAX × RBX"
        ),
    },
    {
        "name": "LDR / STR  →  see Generator info",
        "info": "__GENERATOR__:LOAD_STORE",
    },
    {
        "name": "LDP / STP  (Load/Store Pair)",
        "info": (
            "ARM64 Instructions: LDP / STP\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Transfer TWO registers to/from memory in a single instruction.\n"
            "  Critical for efficient function prologues and epilogues.\n\n"
            "SYNTAX:\n"
            "  ldp  x0, x1, [sp]          ; load x0=*sp, x1=*(sp+8)\n"
            "  ldp  x0, x1, [sp, #16]     ; load with immediate offset\n"
            "  ldp  x29, x30, [sp], #16   ; post-index: load then SP+=16\n\n"
            "  stp  x29, x30, [sp, #-16]! ; pre-index: SP-=16 then store\n"
            "  stp  x0, x1, [sp]          ; store pair at current SP\n\n"
            "ADDRESSING MODES:\n"
            "  [base]         — unsigned offset (compile-time)\n"
            "  [base, #imm]   — signed offset\n"
            "  [base, #imm]!  — pre-indexed  (SP updated BEFORE access)\n"
            "  [base], #imm   — post-indexed (SP updated AFTER access)\n\n"
            "WHY IT MATTERS:\n"
            "  x86-64 needs TWO separate MOV/PUSH instructions to do the\n"
            "  same thing. LDP/STP halve the number of memory ops in\n"
            "  function call overhead.\n\n"
            "x86-64 EQUIVALENT:\n"
            "  No single equivalent. Closest:  push rbp / push rbx"
        ),
    },
    {
        "name": "CMP  →  see Generator info",
        "info": "__GENERATOR__:CMP",
    },
    {
        "name": "B / BL / BLR  →  see Generator info",
        "info": "__GENERATOR__:BRANCH",
    },
    {
        "name": "CBZ / CBNZ  (Compare-and-Branch Zero)",
        "info": (
            "ARM64 Instructions: CBZ / CBNZ\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Test a register against zero AND branch — in ONE instruction.\n"
            "  Eliminates the need for a preceding CMP #0.\n\n"
            "SYNTAX:\n"
            "  cbz  x0, label    ; if x0 == 0, branch to label\n"
            "  cbnz x0, label    ; if x0 != 0, branch to label\n\n"
            "  ; 32-bit forms:\n"
            "  cbz  w0, label    ; test lower 32 bits only\n\n"
            "RANGE:  ±1 MB (21-bit offset) — smaller than B (±128 MB).\n"
            "        Use B.EQ/B.NE for longer jumps.\n\n"
            "COMMON PATTERNS:\n"
            "  ; Null pointer check:\n"
            "  cbz  x0, null_error\n\n"
            "  ; Loop while not zero:\n"
            "  cbnz x0, loop_top\n\n"
            "x86-64 EQUIVALENT:\n"
            "  test rax, rax     ; set ZF\n"
            "  jz   label        ; branch if zero\n"
            "  (always two instructions on x86-64)"
        ),
    },
    {
        "name": "TBZ / TBNZ  (Test Bit and Branch)",
        "info": (
            "ARM64 Instructions: TBZ / TBNZ\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Test a SPECIFIC bit in a register and branch — one instruction,\n"
            "  no need for a separate TST or AND.\n\n"
            "SYNTAX:\n"
            "  tbz  x0, #3, label   ; branch if bit 3 of x0 is 0\n"
            "  tbnz x0, #3, label   ; branch if bit 3 of x0 is 1\n\n"
            "  Bit number:  0 (LSB) through 63 (MSB).\n"
            "  RANGE:  ±32 KB (14-bit offset).\n\n"
            "COMMON PATTERNS:\n"
            "  ; Check the sign bit (bit 63):\n"
            "  tbnz x0, #63, is_negative\n\n"
            "  ; Check a status flag in a flags word:\n"
            "  tbz  w0, #FLAG_BIT, not_set\n\n"
            "x86-64 EQUIVALENT:\n"
            "  test rax, (1 << 3)   ; isolate bit 3\n"
            "  jz   label           ; branch if zero\n"
            "  (always two instructions on x86-64)"
        ),
    },
    {
        "name": "ADRP / ADR  (Address Register)",
        "info": (
            "ARM64 Instructions: ADRP / ADR\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Compute a PC-relative address into a register without\n"
            "  accessing memory — used to load addresses of globals,\n"
            "  string literals, and functions.\n\n"
            "SYNTAX:\n"
            "  adr  x0, label       ; x0 = PC + offset-to-label  (±1 MB)\n"
            "  adrp x0, label       ; x0 = page address of label  (±4 GB)\n\n"
            "  ; Load the full address of a global:\n"
            "  adrp x0, my_var      ; x0 = page base (4 KB page)\n"
            "  add  x0, x0, :lo12:my_var  ; add page offset\n"
            "  ; Now x0 = exact address of my_var\n\n"
            "WHY ADRP EXISTS:\n"
            "  ARM instructions are fixed 32 bits wide — a 64-bit absolute\n"
            "  address won't fit. ADRP encodes a ±4 GB page offset in 21\n"
            "  bits; the 12-bit page offset is added separately.\n\n"
            "x86-64 EQUIVALENT:\n"
            "  lea rax, [rip + offset]   ; RIP-relative addressing\n"
            "  mov rax, QWORD PTR [rip + my_var]"
        ),
    },
    {
        "name": "RET  (Return from function)",
        "info": (
            "ARM64 Instruction: RET\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Return from a function by jumping to the address\n"
            "  stored in the Link Register (X30 by default).\n\n"
            "SYNTAX:\n"
            "  ret              ; PC = X30  (the common form)\n"
            "  ret  x1          ; PC = X1   (explicit register)\n\n"
            "HOW IT DIFFERS FROM 'BR X30':\n"
            "  Functionally identical, but the CPU knows RET is a return.\n"
            "  Branch predictors use a dedicated Return Address Stack (RAS)\n"
            "  to speculatively predict where RET will jump — significant\n"
            "  performance win in deep call chains.\n\n"
            "LEAF vs NON-LEAF:\n"
            "  Leaf function (calls nothing):  just use RET — X30 still\n"
            "    holds the return address from BL.\n"
            "  Non-leaf function: MUST restore X30 from stack before RET:\n"
            "    ldp  x29, x30, [sp], #16\n"
            "    ret\n\n"
            "x86-64 EQUIVALENT:\n"
            "  ret   ; pops return address from stack into RIP"
        ),
    },
    {
        "name": "SVC  (System Call)",
        "info": (
            "ARM64 Instruction: SVC (Supervisor Call)\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Trap into the OS kernel to perform privileged operations\n"
            "  (file I/O, memory allocation, process control, etc.).\n\n"
            "SYNTAX:\n"
            "  svc  #0          ; invoke kernel (immediate is ignored by Linux)\n\n"
            "LINUX ARM64 CALLING CONVENTION:\n"
            "  X8  = syscall number\n"
            "  X0–X5 = arguments (up to 6)\n"
            "  X0  = return value after the call\n\n"
            "EXAMPLE — write(1, buf, 13):\n"
            "  mov  x8, #64          ; __NR_write\n"
            "  mov  x0, #1           ; fd = stdout\n"
            "  ldr  x1, =msg\n"
            "  mov  x2, #13          ; length\n"
            "  svc  #0\n\n"
            "x86-64 EQUIVALENT:\n"
            "  syscall               ; RAX = syscall number\n"
            "                        ; RDI, RSI, RDX, R10, R8, R9 = args"
        ),
    },
]

# ---------------------------------------------------------------------------
# x86-64 Glossary
# ---------------------------------------------------------------------------
X86_GLOSSARY = [

    # ── General-Purpose Registers ───────────────────────────────────────────

    {
        "name": "RAX  (Accumulator)",
        "info": (
            "x86-64 Register: RAX\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Accumulator\n\n"
            "PRIMARY ROLES:\n"
            "  • Return value for integer/pointer functions.\n"
            "  • Implicit operand in MUL, DIV, IMUL, IDIV.\n"
            "  • Syscall number in Linux (syscall instruction).\n"
            "  • Accumulator for string operations (REP STOSQ fills with RAX).\n\n"
            "SIZE ALIASES (same physical register):\n"
            "  RAX — 64-bit      EAX — 32-bit (writing zeroes upper 32)\n"
            "  AX  — 16-bit      AH  —  8-bit (bits 8-15)\n"
            "                    AL  —  8-bit (bits 0-7)\n\n"
            "CALLEE-SAVED?  No — caller-saved (volatile).\n\n"
            "COMMON IDIOM:\n"
            "  xor eax, eax    ; zero RAX — preferred over mov rax,0\n"
            "                  ; (smaller encoding + dependency break)\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X0 (return value), X8 (syscall number)"
        ),
    },
    {
        "name": "RBX  (Base Register)",
        "info": (
            "x86-64 Register: RBX\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Base register\n\n"
            "PRIMARY ROLE:\n"
            "  General scratch register. No special implied use in modern\n"
            "  x86-64 ABI, but historically used for base-indexed addressing.\n\n"
            "SIZE ALIASES:\n"
            "  RBX — 64-bit   EBX — 32-bit   BX — 16-bit\n"
            "  BH  —  8-bit (bits 8-15)       BL — 8-bit (bits 0-7)\n\n"
            "CALLEE-SAVED?  YES — a called function MUST preserve RBX.\n"
            "  The callee saves it on the stack and restores it before RET.\n\n"
            "WHY CALLEE-SAVED:\n"
            "  Gives the compiler a 'safe' register to hold long-lived\n"
            "  values across function calls without spilling to memory.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X19–X28 (callee-saved registers)"
        ),
    },
    {
        "name": "RCX  (Counter Register)",
        "info": (
            "x86-64 Register: RCX\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Counter\n\n"
            "PRIMARY ROLES:\n"
            "  • 4th integer argument in System V ABI (RDI,RSI,RDX,RCX…)\n"
            "  • Shift count for variable-count shifts:  shl rax, cl\n"
            "  • Loop counter for LOOP/REP instructions.\n"
            "  • JRCXZ — branch if RCX is zero (loop-ending idiom).\n\n"
            "SIZE ALIASES:\n"
            "  RCX — 64-bit   ECX — 32-bit   CX — 16-bit   CL / CH — 8-bit\n\n"
            "CALLEE-SAVED?  No — caller-saved (volatile).\n\n"
            "EXAMPLE:\n"
            "  mov  rcx, 8\n"
            "  shl  rax, cl      ; rax <<= 8  (shift by CL, not whole RCX)\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X3 (4th argument register)"
        ),
    },
    {
        "name": "RDX  (Data Register)",
        "info": (
            "x86-64 Register: RDX\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Data register\n\n"
            "PRIMARY ROLES:\n"
            "  • 3rd integer argument (System V ABI).\n"
            "  • High 64 bits of 128-bit MUL/IMUL result (RDX:RAX).\n"
            "  • Dividend high half for DIV/IDIV.\n"
            "  • 3rd return register for some ABIs.\n\n"
            "SIZE ALIASES:\n"
            "  RDX — 64-bit   EDX — 32-bit   DX — 16-bit   DL / DH — 8-bit\n\n"
            "CALLEE-SAVED?  No — caller-saved.\n\n"
            "EXAMPLE:\n"
            "  mov  rax, large_num\n"
            "  mul  rbx            ; result = RDX:RAX (128-bit product)\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X2 (3rd argument); UMULH/SMULH for 128-bit multiply high"
        ),
    },
    {
        "name": "RDI  (Destination Index)",
        "info": (
            "x86-64 Register: RDI\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Destination Index\n\n"
            "PRIMARY ROLES:\n"
            "  • 1st integer/pointer argument (System V AMD64 ABI).\n"
            "  • Destination pointer for REP string operations.\n\n"
            "SIZE ALIASES:\n"
            "  RDI — 64-bit   EDI — 32-bit   DI — 16-bit   DIL — 8-bit\n\n"
            "CALLEE-SAVED?  No — caller-saved.\n\n"
            "EXAMPLE:\n"
            "  ; printf(\"%s\", msg)\n"
            "  lea  rdi, [rip + fmt_str]   ; arg 1 = format string\n"
            "  lea  rsi, [rip + msg]        ; arg 2 = message\n"
            "  xor  eax, eax               ; 0 FP args (required by ABI)\n"
            "  call printf\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X0 (1st argument)"
        ),
    },
    {
        "name": "RSI  (Source Index)",
        "info": (
            "x86-64 Register: RSI\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — historical Source Index\n\n"
            "PRIMARY ROLES:\n"
            "  • 2nd integer/pointer argument (System V AMD64 ABI).\n"
            "  • Source pointer for REP string operations (MOVSB etc.).\n\n"
            "SIZE ALIASES:\n"
            "  RSI — 64-bit   ESI — 32-bit   SI — 16-bit   SIL — 8-bit\n\n"
            "CALLEE-SAVED?  No — caller-saved.\n\n"
            "ARM64 EQUIVALENT:  X1 (2nd argument)"
        ),
    },
    {
        "name": "RSP  (Stack Pointer)",
        "info": (
            "x86-64 Register: RSP\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose, 64-bit — Stack Pointer\n\n"
            "PURPOSE:\n"
            "  Always points to the current TOP of the call stack.\n"
            "  Stack grows DOWNWARD (toward lower addresses).\n\n"
            "ALIGNMENT RULE:\n"
            "  RSP must be 16-byte aligned just BEFORE a CALL instruction.\n"
            "  CALL pushes 8 bytes (return address), so inside the callee\n"
            "  RSP % 16 == 8 at function entry.\n\n"
            "PUSH / POP (implicit RSP modification):\n"
            "  push rax   ≡   sub rsp, 8  +  mov [rsp], rax\n"
            "  pop  rax   ≡   mov rax, [rsp]  +  add rsp, 8\n\n"
            "COMMON IDIOM (stack frame setup):\n"
            "  push rbp            ; save frame pointer\n"
            "  mov  rbp, rsp       ; establish frame\n"
            "  sub  rsp, 32        ; reserve 32 bytes for locals\n"
            "  …\n"
            "  leave               ; mov rsp,rbp + pop rbp\n"
            "  ret\n\n"
            "ARM64 EQUIVALENT:  SP (X31)"
        ),
    },
    {
        "name": "RBP  (Base Pointer / Frame Pointer)",
        "info": (
            "x86-64 Register: RBP\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — Base / Frame Pointer\n\n"
            "PURPOSE:\n"
            "  Traditionally points to the bottom of the current stack\n"
            "  frame. Stays constant while a function runs (unlike RSP).\n"
            "  Enables debuggers to walk the chain of stack frames.\n\n"
            "CALLEE-SAVED?  YES — must be preserved by the callee.\n\n"
            "MODERN NOTE:\n"
            "  With -fomit-frame-pointer, compilers skip RBP as a frame\n"
            "  pointer and use it as a general register instead (7 GPRs\n"
            "  become 8). Debug info is then encoded in .eh_frame / DWARF\n"
            "  instead of the RBP chain.\n\n"
            "TYPICAL PROLOGUE:\n"
            "  push rbp        ; save caller's frame pointer\n"
            "  mov  rbp, rsp   ; RBP = current stack top\n"
            "  sub  rsp, N     ; allocate N bytes for locals\n\n"
            "ARM64 EQUIVALENT:  X29 (Frame Pointer)"
        ),
    },
    {
        "name": "R8–R15  (Extended Registers)",
        "info": (
            "x86-64 Registers: R8–R15\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  General-purpose, 64-bit — introduced in x86-64 (AMD64)\n\n"
            "PRIMARY ROLES:\n"
            "  R8  — 5th integer argument (System V ABI)\n"
            "  R9  — 6th integer argument\n"
            "  R10 — scratch (caller-saved); syscall argument 4 in Linux\n"
            "  R11 — scratch (caller-saved); holds EFLAGS after SYSCALL\n"
            "  R12 — callee-saved general register\n"
            "  R13 — callee-saved general register\n"
            "  R14 — callee-saved general register\n"
            "  R15 — callee-saved general register\n\n"
            "SIZE ALIASES (e.g. for R8):\n"
            "  R8  — 64-bit   R8D — 32-bit   R8W — 16-bit   R8B — 8-bit\n\n"
            "HISTORICAL NOTE:\n"
            "  32-bit x86 (IA-32) only had 8 registers (EAX–EDI).\n"
            "  AMD doubled this to 16 when designing x86-64 — still fewer\n"
            "  than ARM64's 31 general-purpose registers.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  X4–X7 (args), X10–X17 (scratch), X19–X28 (callee-saved)"
        ),
    },
    {
        "name": "RIP  (Instruction Pointer)",
        "info": (
            "x86-64 Register: RIP\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose, 64-bit — Instruction Pointer (PC)\n\n"
            "PURPOSE:\n"
            "  Always holds the address of the NEXT instruction to execute.\n"
            "  Updated implicitly after every instruction decode.\n\n"
            "RIP-RELATIVE ADDRESSING (crucial for PIC/PIE):\n"
            "  Data and code are accessed relative to RIP:\n"
            "  mov  rax, [rip + my_global]  ; load global variable\n"
            "  lea  rdi, [rip + str_lit]    ; address of string literal\n\n"
            "  This makes code position-independent (ASLR-friendly)\n"
            "  without needing a GOT stub for simple accesses.\n\n"
            "CANNOT BE USED AS GENERAL OPERAND:\n"
            "  You cannot  mov rip, rax  to change the PC directly.\n"
            "  Control flow changes require JMP, CALL, or RET.\n\n"
            "ARM64 EQUIVALENT:  PC (Program Counter)\n"
            "  ARM uses ADRP + ADD for the equivalent of RIP-relative loads."
        ),
    },
    {
        "name": "EFLAGS  (Condition Flags)",
        "info": (
            "x86-64 Register: EFLAGS / RFLAGS\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  Special-purpose, 32/64-bit — Condition Flags register\n\n"
            "KEY FLAG BITS:\n"
            "  CF  (bit 0)  — Carry Flag      : unsigned overflow/borrow\n"
            "  PF  (bit 2)  — Parity Flag     : 1 if low byte has even parity\n"
            "  AF  (bit 4)  — Auxiliary Carry : BCD arithmetic (legacy)\n"
            "  ZF  (bit 6)  — Zero Flag       : result == 0\n"
            "  SF  (bit 7)  — Sign Flag       : result sign bit\n"
            "  OF  (bit 11) — Overflow Flag   : signed overflow\n"
            "  DF  (bit 10) — Direction Flag  : string op direction\n"
            "  IF  (bit 9)  — Interrupt Enable: hardware interrupts\n\n"
            "SET BY:  CMP, TEST, ADD, SUB, AND, OR, XOR, SHL …\n"
            "READ BY: JE, JNE, JL, JG, JB, JA …  and CMOVcc, SETcc\n\n"
            "LEGACY FLAGS:\n"
            "  PF and AF are inherited from the Intel 8086 (1978).\n"
            "  They appear in almost no modern code but hardware still\n"
            "  updates them on every arithmetic instruction.\n\n"
            "ARM64 EQUIVALENT:  PSTATE NZCV\n"
            "  4 clean flag bits: N(egative), Z(ero), C(arry), V(overflow)"
        ),
    },
    {
        "name": "XMM0–XMM15  (SSE Registers)",
        "info": (
            "x86-64 Registers: XMM0–XMM15\n"
            "══════════════════════════════════════════\n\n"
            "TYPE:  128-bit SIMD / floating-point registers (SSE)\n\n"
            "PRIMARY ROLES:\n"
            "  • Scalar floating-point (float: XMM as SS; double: XMM as SD)\n"
            "  • SIMD — 4×float, 2×double, or integer vectors per register\n"
            "  • First 8 FP/SIMD function arguments: XMM0–XMM7\n"
            "  • FP return value in XMM0\n\n"
            "SIZE EXTENSIONS:\n"
            "  YMM0–YMM15  — 256-bit (AVX, extends XMM)\n"
            "  ZMM0–ZMM31  — 512-bit (AVX-512)\n\n"
            "CALLEE-SAVED (System V): XMM6–XMM15 on Windows;\n"
            "  None callee-saved on Linux/macOS.\n\n"
            "EXAMPLES:\n"
            "  movss xmm0, [rip+pi]    ; load single float\n"
            "  addss xmm0, xmm1        ; scalar float add\n"
            "  addps xmm0, xmm1        ; 4 floats packed add\n"
            "  vaddps ymm0, ymm1, ymm2 ; 8 floats (AVX)\n\n"
            "ARM64 EQUIVALENT:  V0–V31 (S/D/Q registers)"
        ),
    },

    # ── Key Instructions ─────────────────────────────────────────────────────

    {
        "name": "MOV  →  see Generator info",
        "info": "__GENERATOR__:MOV",
    },
    {
        "name": "ADD  →  see Generator info",
        "info": "__GENERATOR__:ADD",
    },
    {
        "name": "SUB  (Subtract)",
        "info": (
            "x86-64 Instruction: SUB\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Subtract the source from the destination.\n\n"
            "SYNTAX:\n"
            "  sub  rax, rbx         ; rax = rax - rbx\n"
            "  sub  rax, 10          ; rax = rax - 10\n"
            "  sub  rax, [rbx]       ; rax = rax - *rbx  (memory operand!)\n\n"
            "NOTES:\n"
            "  • 2-operand, destructive — left register is overwritten.\n"
            "  • Always sets CF, ZF, SF, OF, PF flags.\n"
            "  • CMP rax, rbx is equivalent to SUB but result is discarded.\n\n"
            "COMMON USE:\n"
            "  sub  rsp, 32    ; allocate 32 bytes on the stack\n\n"
            "ARM64 EQUIVALENT:\n"
            "  sub  x0, x1, x2   ; 3-operand, non-destructive\n"
            "  subs x0, x1, x2   ; + flag-setting (opt-in)"
        ),
    },
    {
        "name": "IMUL / MUL  (Multiply)",
        "info": (
            "x86-64 Instructions: IMUL / MUL\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Integer multiplication.\n\n"
            "IMUL FORMS:\n"
            "  imul rax, rbx          ; rax = rax × rbx  (signed, 2-operand)\n"
            "  imul rax, rbx, 10      ; rax = rbx × 10   (3-operand!)\n"
            "  imul rbx               ; RDX:RAX = RAX × RBX (1-operand, 128-bit)\n\n"
            "MUL (unsigned, always 1-operand):\n"
            "  mul  rbx               ; RDX:RAX = RAX × RBX (unsigned)\n\n"
            "NOTES:\n"
            "  • 3-operand IMUL is the most convenient form for compilers.\n"
            "  • 1-operand forms produce a 128-bit result in RDX:RAX.\n"
            "  • MUL always uses RAX implicitly.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  mul  x0, x1, x2     ; low 64 bits\n"
            "  umulh x0, x1, x2   ; high 64 bits (unsigned)\n"
            "  madd x0, x1, x2, x3 ; fused multiply-add"
        ),
    },
    {
        "name": "LEA  (Load Effective Address)",
        "info": (
            "x86-64 Instruction: LEA\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Compute an address expression and store the RESULT in a\n"
            "  register — WITHOUT accessing memory.\n\n"
            "SYNTAX:\n"
            "  lea  rax, [rbx + rcx*4]      ; rax = rbx + rcx*4\n"
            "  lea  rax, [rip + my_global]   ; rax = address of my_global\n"
            "  lea  rax, [rax + 10]          ; rax = rax + 10  (cheap add)\n\n"
            "WHY IT EXISTS:\n"
            "  x86 addressing modes support: base + index×scale + displacement.\n"
            "  LEA reuses this hardware to perform arithmetic without a\n"
            "  memory access — a CISC trick that the compiler relies on\n"
            "  heavily for scaled array indexing.\n\n"
            "  lea rax, [rbx + rcx*8 + 24]   ; 3-component in ONE instruction!\n\n"
            "DOES NOT SET FLAGS — unlike ADD.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  add x0, x1, x2, lsl #3   ; scaled add (×8) in one instruction\n"
            "  adrp + add                 ; for address-of-global"
        ),
    },
    {
        "name": "PUSH / POP  (Stack Operations)",
        "info": (
            "x86-64 Instructions: PUSH / POP\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Push a value onto the stack or pop it off.\n\n"
            "PUSH:\n"
            "  push rax   ≡   sub rsp, 8  +  mov [rsp], rax\n"
            "  push 42    ; push immediate\n\n"
            "POP:\n"
            "  pop  rax   ≡   mov rax, [rsp]  +  add rsp, 8\n\n"
            "COMMON USES:\n"
            "  • Saving/restoring callee-saved registers:\n"
            "      push rbx\n"
            "      push r12\n"
            "      …\n"
            "      pop  r12\n"
            "      pop  rbx\n"
            "      ret\n"
            "  • Passing additional arguments (7th arg+) before CALL.\n\n"
            "NOTES:\n"
            "  • Stack grows downward — PUSH decrements RSP.\n"
            "  • No PUSH/POP equivalents on ARM64; compiler uses\n"
            "    STP/LDP with explicit SP adjustments.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  stp x0, x1, [sp, #-16]!   ; 'push' pair\n"
            "  ldp x0, x1, [sp], #16     ; 'pop' pair"
        ),
    },
    {
        "name": "CMP  →  see Generator info",
        "info": "__GENERATOR__:CMP",
    },
    {
        "name": "TEST  (Bit Test)",
        "info": (
            "x86-64 Instruction: TEST\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Compute bitwise AND of two operands, SET FLAGS, then\n"
            "  DISCARD the result. Used to test individual bits or\n"
            "  check if a register is zero.\n\n"
            "SYNTAX:\n"
            "  test rax, rbx      ; flags ← rax AND rbx (result discarded)\n"
            "  test rax, rax      ; canonical zero-check (ZF set if rax==0)\n"
            "  test rax, 0x80     ; is bit 7 set?\n\n"
            "WHY test rax, rax BEATS cmp rax, 0:\n"
            "  • No 64-bit immediate to encode — smaller instruction.\n"
            "  • CPUs recognise same-register TEST as a dependency-\n"
            "    breaking zero-check (better out-of-order scheduling).\n\n"
            "FLAGS SET:  ZF, SF, PF  (CF and OF are cleared to 0)\n\n"
            "ARM64 EQUIVALENT:\n"
            "  tst x0, x1     ; AND + flags, discard  (alias: ANDS xzr)\n"
            "  cbz x0, label  ; zero-check + branch in one instruction"
        ),
    },
    {
        "name": "JMP / Jcc  →  see Generator info",
        "info": "__GENERATOR__:BRANCH",
    },
    {
        "name": "CALL / RET  →  see Generator info",
        "info": "__GENERATOR__:BRANCH",
    },
    {
        "name": "XOR  (Exclusive OR)",
        "info": (
            "x86-64 Instruction: XOR\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Bitwise exclusive OR of two operands.\n\n"
            "SYNTAX:\n"
            "  xor  rax, rbx      ; rax = rax ^ rbx\n"
            "  xor  rax, 0xFF     ; rax = rax ^ 0xFF\n\n"
            "THE MOST IMPORTANT USE — ZERO IDIOM:\n"
            "  xor  eax, eax      ; RAX = 0  (preferred zero method!)\n\n"
            "  Why NOT  mov rax, 0:\n"
            "    xor eax, eax   encodes in 2 bytes (REX-free 32-bit form).\n"
            "    mov rax, 0     encodes in 7 bytes (64-bit immediate).\n"
            "    CPUs recognise XOR-same-reg and break false data dependencies.\n\n"
            "  Note: 32-bit XOR (xor eax,eax) zeroes the full 64-bit RAX —\n"
            "  writing a 32-bit register on x86-64 always zeroes bits 32-63.\n\n"
            "OTHER USES:\n"
            "  • Cryptographic operations (block cipher mixing)\n"
            "  • Toggle bits:  xor rax, (1<<5)  — flip bit 5\n\n"
            "ARM64 EQUIVALENT:\n"
            "  eor  x0, x1, x2   ; x0 = x1 ^ x2  (called EOR on ARM)"
        ),
    },
    {
        "name": "SHL / SHR / SAR  (Shift)",
        "info": (
            "x86-64 Instructions: SHL / SHR / SAR\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Shift register bits left or right.\n\n"
            "SYNTAX:\n"
            "  shl  rax, 3        ; rax <<= 3   (logical left, × 8)\n"
            "  shr  rax, 3        ; rax >>= 3   (logical right, ÷ 8 unsigned)\n"
            "  sar  rax, 3        ; rax >>= 3   (arithmetic right, sign-extends)\n\n"
            "  ; Variable shift — count MUST be in CL (low byte of RCX):\n"
            "  shl  rax, cl       ; rax <<= cl\n\n"
            "SHR vs SAR:\n"
            "  SHR fills with 0s (logical)   — use for unsigned divide by 2^n\n"
            "  SAR fills with sign bit (arith) — use for signed divide by 2^n\n\n"
            "SETS FLAGS:  CF gets the last bit shifted out; ZF, SF, PF updated.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  lsl  x0, x1, #3    ; logical shift left\n"
            "  lsr  x0, x1, #3    ; logical shift right (unsigned)\n"
            "  asr  x0, x1, #3    ; arithmetic shift right (signed)\n"
            "  lslv x0, x1, x2    ; variable shift (count in register, not CL)"
        ),
    },
    {
        "name": "NOP  (No Operation)",
        "info": (
            "x86-64 Instruction: NOP\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:  Do nothing — but still consume a decode slot and time.\n\n"
            "FORMS:\n"
            "  nop              ; 1-byte NOP (0x90 — originally XCHG AX,AX)\n"
            "  nop DWORD PTR [rax+rax*1+0]  ; multi-byte NOP (up to 15 bytes)\n\n"
            "WHY NOPs ARE USED:\n"
            "  • Alignment — pad code so hot loops start on cache-line\n"
            "    boundaries (16 or 64 bytes) for better instruction fetch.\n"
            "  • Timing slots in pipelines (legacy, rare in modern code).\n"
            "  • Patchable hooks — fill function prologues with NOPs so\n"
            "    profilers / debuggers can overwrite with JMP.\n"
            "  • PAUSE (rep nop) — used in spinloops to reduce CPU power\n"
            "    consumption and improve hyper-threading behavior.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  nop              ; one 32-bit NOP instruction\n"
            "  isb              ; instruction sync barrier (stronger)\n"
            "  Both architectures use NOP for alignment padding."
        ),
    },
    {
        "name": "SYSCALL  (System Call)",
        "info": (
            "x86-64 Instruction: SYSCALL\n"
            "══════════════════════════════════════════\n\n"
            "PURPOSE:\n"
            "  Trap into the OS kernel to perform privileged operations.\n"
            "  Replaces the older INT 0x80 (32-bit) method.\n\n"
            "LINUX CALLING CONVENTION (System V):\n"
            "  RAX  = syscall number\n"
            "  RDI, RSI, RDX, R10, R8, R9  = arguments (up to 6)\n"
            "  RAX  = return value (negative = error code)\n"
            "  RCX, R11 = CLOBBERED by SYSCALL (kernel uses them)\n\n"
            "EXAMPLE — write(1, buf, 13):\n"
            "  mov  rax, 1          ; __NR_write\n"
            "  mov  rdi, 1          ; fd = stdout\n"
            "  lea  rsi, [rip+msg]\n"
            "  mov  rdx, 13\n"
            "  syscall\n\n"
            "HOW IT WORKS:\n"
            "  SYSCALL saves RIP → RCX, RFLAGS → R11, then jumps to the\n"
            "  kernel entry point. SYSRET reverses this.\n\n"
            "ARM64 EQUIVALENT:\n"
            "  svc  #0    (Supervisor Call)\n"
            "  X8  = syscall number;  X0–X5 = arguments"
        ),
    },
]