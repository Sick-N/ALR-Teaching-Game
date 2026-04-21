# StackQuiz.py
# STACK prestige quiz — question pool and UI engine.
#
# Public API (imported by main.py):
#   start_stack_quiz(root, instructions_ref, on_quiz_passed, on_cancel)
#
# The caller passes:
#   root             — the tk.Tk root window (for Toplevel parenting)
#   instructions_ref — a mutable list [float] so this module can refund cost
#   on_quiz_passed() — called when all 3 questions are answered correctly
#   on_cancel()      — called when the player closes the quiz window early
#
# All tkinter imports are self-contained here; main.py only calls
# start_stack_quiz() and the two callbacks.
#
# Question pool covers all 6 generators (MOV, ADD, IF/Branch, LOAD/STORE,
# CMP, BRANCH) and all 6 high-level constructs (IF, WHILE, FOR, FUNCTION
# CALL, PARAM PASSING, STACK) — focussed on the meaningful ARM64 vs x86-64
# differences a student must understand for the research report.

import tkinter as tk
from tkinter import messagebox
import random

# ---------------------------------------------------------------------------
# ── Question pool ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------
# Each entry has:
#   "q"           — question text
#   "options"     — list of 4 answer strings (index 0-3)
#   "answer"      — int index of the correct option
#   "correct_exp" — shown after a correct answer
#   "wrong_exp"   — shown after a wrong answer (same content, different tone)
#   "category"    — tag used so the sampler can pick a spread of topics
# ---------------------------------------------------------------------------

QUIZ_QUESTIONS = [

    # ══════════════════════════════════════════════════════════════════════
    # MOV  ─ Move / Register Copy
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "MOV",
        "q": (
            "In ARM64, the assembler rewrites   mov x0, x1\n"
            "into a real opcode. Which opcode does it use?"
        ),
        "options": [
            "LDR x0, [x1]  — loads from memory address x1",
            "ORR x0, xzr, x1  — ORs x1 with the zero register into x0",
            "ADD x0, x1, #0  — adds zero to x1",
            "CPY x0, x1  — the real ARM64 copy opcode",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! ARM64 has no dedicated reg-to-reg MOV opcode.\n"
            "The assembler encodes   mov x0, x1   as:\n\n"
            "  ORR x0, xzr, x1\n\n"
            "XZR is ARM's hard-wired zero register — OR-ing anything\n"
            "with 0 just copies it. This keeps the instruction set\n"
            "small (RISC philosophy) while still giving programmers\n"
            "a convenient MOV alias."
        ),
        "wrong_exp": (
            "Not quite. ARM64 has no real MOV opcode for reg-to-reg.\n"
            "The assembler translates   mov x0, x1   into:\n\n"
            "  ORR x0, xzr, x1\n\n"
            "XZR is the hard-wired zero register. OR-ing any value\n"
            "with 0 is the same as copying it — a clean RISC trick."
        ),
    },

    {
        "category": "MOV",
        "q": (
            "x86-64 does NOT have a dedicated zero register.\n"
            "What is the canonical idiom to zero out RAX on x86-64?"
        ),
        "options": [
            "mov rax, 0  — move the immediate zero into rax",
            "sub rax, rax  — subtract rax from itself",
            "xor rax, rax  — XOR rax with itself (preferred by compilers)",
            "clr rax  — the x86 clear-register instruction",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct!   xor rax, rax   is the preferred zero idiom on x86-64.\n\n"
            "It is shorter to encode than   mov rax, 0   (no 64-bit\n"
            "immediate needed) and is specially recognised by modern\n"
            "CPUs to break the false dependency on the old rax value.\n\n"
            "ARM64 never needs this — its XZR register always reads as\n"
            "zero with zero encoding overhead."
        ),
        "wrong_exp": (
            "The canonical zero idiom on x86-64 is   xor rax, rax.\n\n"
            "It encodes more compactly than   mov rax, 0   (no 64-bit\n"
            "immediate) and CPUs recognise it as a dependency-breaker.\n"
            "ARM64 avoids the problem entirely with the XZR zero register."
        ),
    },

    {
        "category": "MOV",
        "q": (
            "On x86-64, MOV is described as 'heavily overloaded'.\n"
            "Which of the following can a single MOV instruction do?"
        ),
        "options": [
            "Only register-to-register copies",
            "Only memory loads (mem → reg)",
            "reg→reg, mem→reg, reg→mem, AND imm→reg under one mnemonic",
            "reg→reg copies and arithmetic shifts only",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct! x86-64 MOV is a single mnemonic that covers:\n\n"
            "  mov rax, rbx        ; reg → reg\n"
            "  mov rax, [rbx]      ; mem → reg  (load)\n"
            "  mov [rbx], rax      ; reg → mem  (store)\n"
            "  mov rax, 42         ; imm → reg\n\n"
            "This is classic CISC design — fewer mnemonics, more work\n"
            "per instruction. ARM64 splits these into separate opcodes\n"
            "(ORR/MOVZ for reg/imm, LDR for load, STR for store)."
        ),
        "wrong_exp": (
            "x86-64 MOV handles all four forms under one mnemonic:\n\n"
            "  reg→reg, mem→reg, reg→mem, and imm→reg.\n\n"
            "ARM64 separates these: ORR/MOVZ for copies, LDR for\n"
            "loads, STR for stores. That separation is the RISC\n"
            "principle — simple, uniform instruction forms."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # ADD  ─ Integer Addition
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "ADD",
        "q": (
            "What is the key operand-count difference between\n"
            "ARM64 ADD and x86-64 ADD?"
        ),
        "options": [
            "ARM64 uses 2 operands; x86-64 uses 3 operands",
            "ARM64 uses 3 operands (dest + 2 sources); x86-64 uses 2 (dest is also source 1)",
            "Both use 3 operands in the same way",
            "Both use 2 operands and always overwrite the left register",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  ARM64:   add x0, x1, x2   → x0 = x1 + x2\n"
            "           Destination is SEPARATE. x1 and x2 are unmodified.\n\n"
            "  x86-64:  add rax, rbx     → rax = rax + rbx\n"
            "           The destination is ALSO the first source — it is\n"
            "           always overwritten.\n\n"
            "ARM's 3-operand form lets compilers reuse source registers\n"
            "freely without needing to spill them to the stack first."
        ),
        "wrong_exp": (
            "ARM64 uses 3 operands:   add x0, x1, x2   (dest = src1 + src2)\n"
            "The destination is separate, so x1 and x2 are preserved.\n\n"
            "x86-64 uses 2:   add rax, rbx   (rax = rax + rbx)\n"
            "The left register is both the first source AND the destination\n"
            "— it is always overwritten."
        ),
    },

    {
        "category": "ADD",
        "q": (
            "ARM64 ADD does NOT set CPU flags by default.\n"
            "How does a programmer opt IN to flag-setting on ARM64?"
        ),
        "options": [
            "Use the F prefix:  fadd x0, x1, x2",
            "Use the S suffix:  adds x0, x1, x2",
            "Add a .flags qualifier:  add.flags x0, x1, x2",
            "Flags are always set — there is no opt-in",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! Appending S gives the flag-setting variant:\n\n"
            "  add  x0, x1, x2    ; no flags changed\n"
            "  adds x0, x1, x2    ; sets NZCV flags\n\n"
            "This opt-in design means you can perform arithmetic\n"
            "without accidentally overwriting flags from a previous\n"
            "CMP — very useful inside complex conditionals.\n\n"
            "x86-64 always sets CF/ZF/SF/OF on ADD with no opt-out."
        ),
        "wrong_exp": (
            "The S suffix enables flag-setting on ARM64:\n\n"
            "  add  x0, x1, x2    ; NZCV unchanged\n"
            "  adds x0, x1, x2    ; sets NZCV flags\n\n"
            "x86-64 has no equivalent choice — ADD always sets flags.\n"
            "ARM's opt-in approach prevents accidental flag clobbering."
        ),
    },

    {
        "category": "ADD",
        "q": (
            "ARM64 has a shifted-register form for ADD:\n\n"
            "  add x0, x1, x2, lsl #2\n\n"
            "What is the equivalent operation on x86-64?"
        ),
        "options": [
            "add rax, rbx, 2  — direct three-operand form",
            "lea rax, [rbx + rcx*4]  — Load Effective Address for scaled indexing",
            "shl rbx, 2  followed by  add rax, rbx  — two-step sequence",
            "mul rax, rcx  — multiply first, then add manually",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! x86-64 uses LEA (Load Effective Address):\n\n"
            "  lea rax, [rbx + rcx*4]  ; rax = rbx + rcx*4\n\n"
            "LEA computes an address expression without accessing memory.\n"
            "It is the standard workaround for scaled addition on x86-64\n"
            "since ADD itself cannot embed a shift.\n\n"
            "ARM64's single instruction   add x0, x1, x2, lsl #2\n"
            "is cleaner and uses one fewer opcode."
        ),
        "wrong_exp": (
            "x86-64's equivalent is LEA:\n\n"
            "  lea rax, [rbx + rcx*4]\n\n"
            "LEA computes an address-style expression (no memory access).\n"
            "It is the standard x86-64 workaround for scaled addition\n"
            "since ADD cannot embed a shift the way ARM64 can."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # IF_INST  ─ Conditional Branch (compiled if/else)
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "IF_INST",
        "q": (
            "ARM64 has a special branch instruction that checks\n"
            "a register against zero WITHOUT a preceding CMP.\n"
            "Which instruction is it?"
        ),
        "options": [
            "b.eq  — branch if equal (requires prior CMP)",
            "cbz  — Compare and Branch if Zero (no CMP needed)",
            "tst  — test bits and branch",
            "beqz — branch if zero (x86-64 only)",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! CBZ (Compare and Branch if Zero):\n\n"
            "  cbz  x0, label    ; if x0 == 0, jump to label\n"
            "  cbnz x0, label    ; if x0 != 0, jump to label\n\n"
            "This eliminates the   cmp x0, #0   instruction for the\n"
            "very common  if (x == 0)  pattern — saving a fetch,\n"
            "decode, and execute cycle.\n\n"
            "x86-64 has no equivalent; it always requires a separate\n"
            "CMP (or TEST) before a conditional jump."
        ),
        "wrong_exp": (
            "CBZ (Compare and Branch if Zero) lets ARM64 skip the CMP:\n\n"
            "  cbz  x0, label    ; branch if x0 == 0\n"
            "  cbnz x0, label    ; branch if x0 != 0\n\n"
            "x86-64 always needs a separate CMP or TEST before a\n"
            "conditional jump — two instructions instead of one."
        ),
    },

    {
        "category": "IF_INST",
        "q": (
            "On ARM64 the condition is a SUFFIX on one opcode (b.eq, b.lt …).\n"
            "How does x86-64 handle the same set of conditions?"
        ),
        "options": [
            "x86-64 also uses one opcode with a suffix: jmp.eq, jmp.lt …",
            "x86-64 gives every condition its OWN opcode: je, jne, jl, jge …",
            "x86-64 encodes the condition as a second register argument",
            "x86-64 uses EFLAGS directly as a branch target address",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! x86-64 has a separate mnemonic for every condition:\n\n"
            "  je   label   ; jump if Equal  (ZF=1)\n"
            "  jne  label   ; jump if Not Equal\n"
            "  jl   label   ; jump if Less Than (signed)\n"
            "  jge  label   ; jump if ≥\n"
            "  jb   label   ; jump if Below (unsigned)\n"
            "  ja   label   ; jump if Above (unsigned)\n\n"
            "ARM64 uses one base opcode B with a condition suffix:\n"
            "  b.eq, b.ne, b.lt, b.ge, b.lo, b.hi …\n\n"
            "Fewer mnemonics to memorise is a hallmark of RISC design."
        ),
        "wrong_exp": (
            "x86-64 has a separate opcode for every condition:\n"
            "je, jne, jl, jge, jb, ja … (more than a dozen variants).\n\n"
            "ARM64 uses one opcode — B — with a condition suffix:\n"
            "b.eq, b.ne, b.lt, b.ge …\n\n"
            "This is the RISC principle: one orthogonal instruction with\n"
            "a modifier, rather than many specialised opcodes."
        ),
    },

    {
        "category": "IF_INST",
        "q": (
            "Which register holds ARM64's condition flags (NZCV),\n"
            "and what does each letter stand for?"
        ),
        "options": [
            "EFLAGS — Execution, Function, Logic, Address, General, Stack",
            "CPSR — Carry, Parity, Sign, Register",
            "PSTATE — N=Negative, Z=Zero, C=Carry, V=oVerflow",
            "FLAGS64 — Not-set, Zero-set, Carry-set, Signed-set",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct! ARM64 stores condition flags in PSTATE (processor state):\n\n"
            "  N — Negative  (result had the sign bit set)\n"
            "  Z — Zero      (result was exactly zero)\n"
            "  C — Carry     (unsigned overflow / borrow)\n"
            "  V — oVerflow  (signed overflow)\n\n"
            "x86-64 stores similar info in the 32-bit EFLAGS register,\n"
            "but adds legacy bits like PF (Parity) and AF (Auxiliary\n"
            "Carry) rarely used in modern code — a sign of x86's age."
        ),
        "wrong_exp": (
            "ARM64 condition flags live in PSTATE:\n\n"
            "  N=Negative, Z=Zero, C=Carry, V=oVerflow\n\n"
            "x86-64 uses the 32-bit EFLAGS register with the same core\n"
            "four flags PLUS legacy bits (PF, AF) seldom used today.\n"
            "ARM's 4-bit NZCV is a cleaner, more modern design."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # LOAD/STORE  ─ Memory Access
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "LOAD_STORE",
        "q": (
            "ARM64 follows the RISC load/store architecture.\n"
            "What does this mean for arithmetic instructions?"
        ),
        "options": [
            "All arithmetic can read and write memory directly",
            "Arithmetic only works on registers; data must be loaded first",
            "Arithmetic instructions must be preceded by a NOP cycle",
            "Arithmetic uses 128-bit registers for all operations",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! In a RISC load/store architecture:\n\n"
            "  • ONLY LDR/STR touch memory.\n"
            "  • ALL arithmetic (ADD, SUB, AND …) operates on registers.\n\n"
            "To add a memory value you must:\n"
            "  ldr x1, [x2]      ; load *x2 into x1\n"
            "  add x0, x0, x1    ; now add\n\n"
            "x86-64 (CISC) can do both in one:\n"
            "  add rax, [rbx]    ; rax += *rbx\n\n"
            "More instructions total on ARM, but each is simple and\n"
            "easy for the CPU's pipeline to execute quickly."
        ),
        "wrong_exp": (
            "RISC means load/store only — arithmetic must use registers:\n\n"
            "  ARM64:  ldr x1, [x2]   then   add x0, x0, x1  (2 instr)\n"
            "  x86-64: add rax, [rbx]                         (1 instr)\n\n"
            "x86-64 CISC can embed a memory operand directly in ADD.\n"
            "ARM cannot — all operands must be in registers first."
        ),
    },

    {
        "category": "LOAD_STORE",
        "q": (
            "ARM64 has LDP/STP instructions. What do they do,\n"
            "and what is the x86-64 equivalent?"
        ),
        "options": [
            "Load/Store a single 128-bit value; x86-64 uses MOVDQU",
            "Load/Store a PAIR of 64-bit registers in one instruction; x86-64 needs two separate MOVs",
            "Load/Store with a predicate flag; x86-64 uses CMOV",
            "Long-distance PUSH/POP across functions; x86-64 has no equivalent",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! LDP and STP transfer a PAIR of registers:\n\n"
            "  ldp x0, x1, [sp]       ; load two 64-bit regs at once\n"
            "  stp x29, x30, [sp,-16] ; store frame pointer + link reg\n\n"
            "x86-64 needs two separate MOV instructions for the same\n"
            "effect. LDP/STP are critical in ARM64 function prologues\n"
            "and epilogues — they halve the number of memory accesses\n"
            "needed to save and restore registers."
        ),
        "wrong_exp": (
            "LDP/STP load or store a PAIR of 64-bit registers together:\n\n"
            "  ldp x0, x1, [sp]   ; two loads in one instruction\n\n"
            "x86-64 has no equivalent; it needs two separate MOVs.\n"
            "This pair-transfer is a key ARM64 efficiency win in\n"
            "function prologues and epilogues."
        ),
    },

    {
        "category": "LOAD_STORE",
        "q": (
            "On x86-64, which instruction loads a 64-bit value\n"
            "from memory at the address stored in RBX into RAX?"
        ),
        "options": [
            "ldr rax, rbx",
            "mov rax, rbx",
            "mov rax, [rbx]",
            "load rax, [rbx]",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct!   mov rax, [rbx]\n\n"
            "Square brackets denote a memory dereference in Intel syntax.\n"
            "So [rbx] means 'the 64-bit value at the address in RBX'.\n\n"
            "ARM64 uses a distinct opcode instead:\n"
            "  ldr x0, [x1]    ; load 64-bit from address in x1\n\n"
            "The ARM distinction is clearer — LDR vs STR always means\n"
            "memory access. On x86-64 the same MOV mnemonic covers\n"
            "both register copies and memory access."
        ),
        "wrong_exp": (
            "On x86-64 the answer is   mov rax, [rbx]\n\n"
            "Square brackets mean 'memory at that address' (Intel syntax).\n"
            "ARM64 uses a separate opcode:   ldr x0, [x1]\n\n"
            "ARM's dedicated LDR/STR opcodes make load vs copy\n"
            "immediately obvious in the code, unlike x86's overloaded MOV."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # CMP  ─ Compare / Set Flags
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "CMP",
        "q": (
            "CMP in ARM64 is described as a pseudo-instruction.\n"
            "What real opcode does the assembler emit for   cmp x0, x1?"
        ),
        "options": [
            "SUB x0, x0, x1    — subtract and store in x0",
            "SUBS xzr, x0, x1  — subtract with flags, discard result via XZR",
            "TST x0, x1        — bitwise test with flags",
            "AND xzr, x0, x1   — AND and discard",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!   cmp x0, x1   assembles to:\n\n"
            "  SUBS xzr, x0, x1\n\n"
            "SUBS = SUBtract with flag-Setting. XZR is the zero/discard\n"
            "register — the result is thrown away but the NZCV flags\n"
            "ARE set based on the subtraction.\n\n"
            "On x86-64, CMP is a REAL opcode (not a pseudo) that also\n"
            "subtracts and discards — the concept is identical, but the\n"
            "encoding mechanism differs."
        ),
        "wrong_exp": (
            "  cmp x0, x1   on ARM64 becomes:\n\n"
            "  SUBS xzr, x0, x1\n\n"
            "SUBS sets flags; XZR discards the subtraction result.\n"
            "x86-64 CMP is a real opcode doing the same logical\n"
            "operation — subtract, set flags, discard — but it is\n"
            "not a pseudo-instruction."
        ),
    },

    {
        "category": "CMP",
        "q": (
            "On x86-64,   test rax, rax   is preferred over   cmp rax, 0\n"
            "to check if RAX is zero. Why?"
        ),
        "options": [
            "TEST is more accurate and handles signed values better",
            "TEST encodes more compactly (no 64-bit immediate) and CPUs break the false dependency on RAX's old value",
            "CMP cannot compare against the immediate value 0",
            "TEST sets more flags, giving branches more information",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! Two reasons TEST rax, rax beats CMP rax, 0:\n\n"
            "  1. Encoding size —   cmp rax, 0   must encode a 64-bit\n"
            "     zero immediate. TEST has no immediate; shorter encoding.\n\n"
            "  2. Dependency breaking — modern CPUs recognise the\n"
            "     'same-register TEST' pattern and treat it as a zero-\n"
            "     check without a false input dependency on RAX.\n\n"
            "ARM64 avoids the issue entirely: CBZ/CBNZ do a zero-check\n"
            "AND branch in a single instruction without any CMP at all."
        ),
        "wrong_exp": (
            "  test rax, rax   is preferred for two reasons:\n\n"
            "  1. Shorter encoding — no 64-bit immediate to carry.\n"
            "  2. CPUs recognise same-register TEST as a dependency-\n"
            "     free zero check.\n\n"
            "ARM64 goes further: CBZ/CBNZ fold the zero-check AND\n"
            "the branch into one instruction, skipping CMP entirely."
        ),
    },

    {
        "category": "CMP",
        "q": (
            "ARM64 has a TST instruction. What does it do,\n"
            "and what is its x86-64 counterpart?"
        ),
        "options": [
            "TST performs a logical OR and sets flags; x86-64 uses OR",
            "TST performs AND and sets flags (discarding the result); x86-64 uses TEST",
            "TST is a no-op for timing; x86-64 uses PAUSE",
            "TST negates a register and sets flags; x86-64 uses NEG",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! TST is the bit-mask compare:\n\n"
            "  ARM64:  tst  x0, x1    ; (x0 AND x1) → flags, discard\n"
            "  x86-64: test rax, rbx  ; (rax AND rbx) → flags, discard\n\n"
            "Both compute a bitwise AND, set the Zero flag (and\n"
            "others), then throw the result away. Used for:\n\n"
            "  if (x & mask)  →  tst x0, #mask  then  b.ne label\n\n"
            "ARM TST is an alias for   ANDS xzr, x0, x1   (same XZR\n"
            "discard trick as CMP / SUBS xzr)."
        ),
        "wrong_exp": (
            "TST performs AND-and-discard, setting flags:\n\n"
            "  ARM64:  tst x0, x1    ; AND with flags, result discarded\n"
            "  x86-64: test rax, rbx ; same concept\n\n"
            "Used to check individual bits:   if (x & mask) …\n"
            "ARM TST is an alias for ANDS xzr — the XZR register\n"
            "discards the AND result while keeping the flags."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH  ─ Unconditional & Function-call Branches
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "BRANCH",
        "q": (
            "To CALL a subroutine (saving a return address),\n"
            "ARM64 uses BL and x86-64 uses CALL.\n"
            "Where does each architecture store the return address?"
        ),
        "options": [
            "Both push the return address onto the stack",
            "ARM64 saves it in the Link Register (X30/LR); x86-64 pushes it onto the stack",
            "ARM64 pushes it onto the stack; x86-64 saves it in RDI",
            "Both store it in a dedicated return-address register",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  ARM64:  bl  label\n"
            "          → stores return address in X30 (the Link Register)\n"
            "          → jumps to label\n"
            "          → return with:  ret  (reads X30 back into PC)\n\n"
            "  x86-64: call label\n"
            "          → PUSHES return address onto the stack (RSP -= 8)\n"
            "          → jumps to label\n"
            "          → return with:  ret  (POPs address from stack)\n\n"
            "ARM's register approach is faster for leaf functions\n"
            "(no memory write). Nested calls require saving X30 to\n"
            "the stack manually — a job the compiler handles."
        ),
        "wrong_exp": (
            "ARM64 BL saves the return address in X30 (Link Register).\n"
            "x86-64 CALL pushes it onto the stack (RSP -= 8).\n\n"
            "ARM's register approach avoids a memory write for leaf\n"
            "functions. For nested calls the compiler must explicitly\n"
            "save X30 to the stack via STP."
        ),
    },

    {
        "category": "BRANCH",
        "q": (
            "ARM64 has TBZ and TBNZ. What do they test,\n"
            "and does x86-64 have a direct equivalent?"
        ),
        "options": [
            "They test the top bit only; x86-64 JS/JNS are exact equivalents",
            "They test whether a SPECIFIC bit in a register is 0 or 1; x86-64 has no single-instruction equivalent",
            "They test whether two registers are equal; x86-64 uses CMPEQ",
            "They are timer-based branch instructions; x86-64 uses LOOP",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  tbz  x0, #3, label   ; branch if bit 3 of x0 is 0\n"
            "  tbnz x0, #3, label   ; branch if bit 3 of x0 is 1\n\n"
            "No CMP or TST needed — the test and branch happen in\n"
            "one instruction.\n\n"
            "x86-64 requires two instructions:\n"
            "  test rax, 8         ; isolate bit 3  (8 = 1<<3)\n"
            "  jz   label          ; branch if zero\n\n"
            "TBZ/TBNZ are especially useful for flag-field checking\n"
            "in tight loops and OS kernel code."
        ),
        "wrong_exp": (
            "TBZ/TBNZ test a specific numbered bit and branch:\n\n"
            "  tbz x0, #3, label   ; if bit 3 of x0 == 0, jump\n\n"
            "x86-64 needs two instructions (TEST + Jcc).\n"
            "ARM's single-instruction bit-test-and-branch removes a\n"
            "memory access and reduces instruction count in tight loops."
        ),
    },

    {
        "category": "BRANCH",
        "q": (
            "Which statement about branch RANGES is correct?"
        ),
        "options": [
            "ARM64 B can reach any address in the 64-bit address space",
            "ARM64 B (unconditional) has ±128 MB PC-relative range; x86-64 JMP near has ±2 GB",
            "x86-64 JMP near has a 16-bit range; ARM64 B has a 32-bit range",
            "Both architectures use absolute addresses for all branches",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  ARM64 B   : ±128 MB from the current PC\n"
            "  ARM64 BL  : ±128 MB (same encoding)\n"
            "  x86-64 JMP near : ±2 GB (32-bit signed displacement)\n\n"
            "For targets out of range, ARM uses an indirect branch:\n"
            "  ldr x16, =far_label   ; load absolute address\n"
            "  br  x16               ; branch to register\n\n"
            "All ARM64 branches are PC-relative, making code\n"
            "position-independent by default — important for shared\n"
            "libraries and ASLR security."
        ),
        "wrong_exp": (
            "ARM64 B has a ±128 MB PC-relative range.\n"
            "x86-64 near JMP has a ±2 GB range.\n\n"
            "ARM64 branches are ALWAYS PC-relative, making object\n"
            "code position-independent by default — a security and\n"
            "linking advantage. Long-range ARM64 calls use an\n"
            "indirect branch through a register (BR x16)."
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # HIGH-LEVEL CONSTRUCTS  ─ IF / WHILE / FOR / FUNCTION CALL / PARAM / STACK
    # ══════════════════════════════════════════════════════════════════════

    {
        "category": "IF_CONSTRUCT",
        "q": (
            "How is a basic IF-ELSE compiled to ARM64 assembly?\n\n"
            "  if (a == b) { doTrue(); } else { doFalse(); }"
        ),
        "options": [
            "ife a, b, true_label, false_label  — single opcode",
            "CMP then B.cond to the else branch, fall-through for if-body, B to skip else",
            "MOV the condition into a register then TEST and branch",
            "ARM64 uses predicated instructions, no branches needed",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! The typical ARM64 pattern:\n\n"
            "  cmp  x0, x1          ; a == b?\n"
            "  b.ne else_label      ; NOT equal → go to else\n"
            "  ; --- if-body (doTrue) ---\n"
            "  bl   doTrue\n"
            "  b    end_label       ; skip else\n"
            "else_label:\n"
            "  bl   doFalse\n"
            "end_label:\n\n"
            "x86-64 is structurally identical:\n"
            "  cmp rax, rbx\n"
            "  jne else_label\n"
            "  …\n\n"
            "The branch condition is usually inverted (branch on\n"
            "FALSE) so the 'true' body falls through naturally."
        ),
        "wrong_exp": (
            "IF-ELSE in ARM64:\n\n"
            "  cmp  x0, x1        ; compare\n"
            "  b.ne else_label    ; branch if NOT equal (inverse condition)\n"
            "  ; true body (fall-through)\n"
            "  b    end_label\n"
            "else_label:\n"
            "  ; false body\n"
            "end_label:\n\n"
            "The compiler inverts the condition so the true-branch\n"
            "falls through without an extra jump — same on x86-64."
        ),
    },

    {
        "category": "WHILE_CONSTRUCT",
        "q": (
            "A WHILE loop in assembly has three structural parts.\n"
            "Which list correctly describes them in order?"
        ),
        "options": [
            "Initialize counter → arithmetic body → increment",
            "Jump to body → compare at top → jump back unconditionally",
            "Test condition → exit branch if false → body → unconditional jump back to test",
            "Body → test → increment → restart",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct! A WHILE loop compiles to:\n\n"
            "loop_top:\n"
            "  cmp  x0, x1          ; 1. Test condition\n"
            "  b.ge loop_exit        ; 2. Exit branch if condition false\n"
            "  ; --- body ---\n"
            "  add  x0, x0, #1      ; 3. Body (with any increment)\n"
            "  b    loop_top         ; 4. Unconditional jump back\n"
            "loop_exit:\n\n"
            "The condition is checked BEFORE the body, so a while loop\n"
            "can execute zero times. Both ARM64 and x86-64 compile to\n"
            "this same logical pattern — only the mnemonics differ."
        ),
        "wrong_exp": (
            "WHILE loop structure in assembly:\n\n"
            "loop_top:\n"
            "  cmp  x0, x1        ; Test condition\n"
            "  b.ge loop_exit     ; Exit if false\n"
            "  ; body\n"
            "  b    loop_top      ; Jump back\n"
            "loop_exit:\n\n"
            "The test comes FIRST — a while loop can run 0 times.\n"
            "This structure is the same on ARM64 and x86-64."
        ),
    },

    {
        "category": "FOR_CONSTRUCT",
        "q": (
            "A FOR loop has three extra elements compared to a bare WHILE loop.\n"
            "What are they, and where do they appear in the assembly?"
        ),
        "options": [
            "A push, a pop, and a call — the loop sets up a stack frame",
            "Initialization (before the loop), a condition test (at the top), and an increment (at the bottom, before the back-jump)",
            "A start label, an end label, and a counter register — no structured layout",
            "Declaration, assignment, and return — mapped to three separate functions",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! FOR adds init + increment wrappers to a WHILE:\n\n"
            "  ; Initialization  (for i = 0)\n"
            "  mov  x0, #0\n"
            "loop_top:\n"
            "  ; Condition test  (i < n)\n"
            "  cmp  x0, x1\n"
            "  b.ge loop_exit\n"
            "  ; Body\n"
            "  …\n"
            "  ; Increment  (i++)\n"
            "  add  x0, x0, #1\n"
            "  b    loop_top\n"
            "loop_exit:\n\n"
            "The increment sits AFTER the body but BEFORE the back-\n"
            "branch. x86-64 is structurally identical — only the\n"
            "register names and branch mnemonics change."
        ),
        "wrong_exp": (
            "A FOR loop is a WHILE loop with:\n\n"
            "  1. Initialisation   — before the loop label\n"
            "  2. Condition test   — at the top of the loop\n"
            "  3. Increment        — at the BOTTOM, before the back-jump\n\n"
            "  mov  x0, #0          ; init\n"
            "loop: cmp x0,x1 / b.ge exit  ; test\n"
            "  ; body\n"
            "  add  x0, x0, #1     ; increment\n"
            "  b    loop"
        ),
    },

    {
        "category": "FUNCTION_CALL",
        "q": (
            "The ARM64 ABI passes the first 8 integer/pointer\n"
            "arguments in registers X0–X7. What does x86-64 Linux\n"
            "(System V AMD64 ABI) use for the first 6 arguments?"
        ),
        "options": [
            "RAX, RBX, RCX, RDX, RSI, RDI  — in that order",
            "RDI, RSI, RDX, RCX, R8, R9  — in that order",
            "R8, R9, R10, R11, R12, R13  — the extended registers only",
            "All arguments are passed on the stack in x86-64",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! x86-64 System V ABI (Linux/macOS):\n\n"
            "  Arg 1 → RDI\n"
            "  Arg 2 → RSI\n"
            "  Arg 3 → RDX\n"
            "  Arg 4 → RCX\n"
            "  Arg 5 → R8\n"
            "  Arg 6 → R9\n"
            "  Args 7+ → pushed onto the stack (right-to-left)\n\n"
            "ARM64 ABI uses X0–X7 for the first 8 args — more\n"
            "registers, fewer stack spills for functions with many\n"
            "parameters. Additional args go on the stack in both ABIs."
        ),
        "wrong_exp": (
            "x86-64 System V ABI argument registers:\n\n"
            "  RDI, RSI, RDX, RCX, R8, R9  (first 6 args)\n"
            "  Stack for arg 7+\n\n"
            "ARM64 uses X0–X7 (8 registers) before hitting the stack.\n"
            "More register args means fewer memory writes — a\n"
            "performance advantage for functions with many parameters."
        ),
    },

    {
        "category": "PARAM_PASSING",
        "q": (
            "In ARM64, what is the role of the Frame Pointer (X29 / FP)\n"
            "and how does it differ from the Stack Pointer (SP / X31)?"
        ),
        "options": [
            "FP and SP are the same register — just different names",
            "SP tracks the current top of the stack; FP points to the start of the current frame, enabling stack unwinding and debug info",
            "FP holds the return value; SP holds the first argument",
            "SP is only used in leaf functions; FP is used in all functions",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  SP (X31) — Stack Pointer: always points to the current\n"
            "    top of the stack. Moves with every push/pop (STP/LDP).\n\n"
            "  FP (X29) — Frame Pointer: saved to the stack at function\n"
            "    entry and points to the BOTTOM of the current frame.\n"
            "    Stays constant while the function runs — debuggers and\n"
            "    unwinders walk the chain of saved FPs to produce\n"
            "    a call stack trace.\n\n"
            "x86-64 equivalent: RBP (frame pointer), RSP (stack pointer)\n"
            "— the same conceptual split. Modern compilers can omit FP\n"
            "(-fomit-frame-pointer) to free an extra register."
        ),
        "wrong_exp": (
            "SP (X31) tracks the stack top — it moves with STP/LDP.\n"
            "FP (X29) is saved at function entry and anchors the frame.\n\n"
            "Debuggers walk the chain of saved FPs to build a call\n"
            "stack trace. x86-64 uses RSP/RBP for the same roles.\n"
            "Compilers can omit FP to reclaim an extra register."
        ),
    },

    {
        "category": "STACK_CONSTRUCT",
        "q": (
            "On ARM64, the stack must be 16-byte aligned at a CALL.\n"
            "Why is this alignment required?"
        ),
        "options": [
            "Purely a convention — alignment has no hardware effect on ARM64",
            "Required by the ABI so SIMD/FP loads (which need 16-byte alignment) and atomic ops work correctly across call boundaries",
            "Required because ARM64 only has 16-bit memory buses",
            "Required only for system calls, not regular function calls",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! 16-byte alignment is required by the ARM64 ABI for:\n\n"
            "  • SIMD / floating-point load-store (LDP/STP of Q-regs\n"
            "    operate on 16-byte pairs and need alignment).\n"
            "  • Atomic operations (LDXR/STXR exclusive access).\n"
            "  • ABI compatibility — unaligned SP can cause alignment\n"
            "    faults or silent data corruption on some memory types.\n\n"
            "x86-64 System V ABI also requires 16-byte alignment at\n"
            "the point of a CALL (RSP % 16 == 0 before the call,\n"
            "i.e. RSP % 16 == 8 inside the callee due to the pushed\n"
            "return address)."
        ),
        "wrong_exp": (
            "16-byte alignment is required because the ABI mandates it\n"
            "for SIMD/FP register saves and atomic operations.\n\n"
            "x86-64 has the same 16-byte alignment rule (RSP must be\n"
            "16-byte aligned just before a CALL).\n"
            "Violating alignment can cause faults or data corruption."
        ),
    },

    {
        "category": "STACK_CONSTRUCT",
        "q": (
            "A typical ARM64 function prologue saves X29 and X30.\n"
            "Why must X30 (the Link Register) be saved to the stack?"
        ),
        "options": [
            "X30 holds the current stack pointer and must be backed up",
            "BL overwrites X30 with the return address of the NEW call; saving it first preserves the ability to return to the CALLER",
            "X30 holds the first function argument and must not be lost",
            "X30 is callee-saved by convention but has no special hardware role",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct! X30 is the Link Register (LR):\n\n"
            "  • When the current function was called, BL stored the\n"
            "    return-to-caller address in X30.\n"
            "  • If this function calls ANOTHER function with BL,\n"
            "    X30 is OVERWRITTEN with the new return address.\n"
            "  • The old return address is gone — we can never return\n"
            "    to our own caller!\n\n"
            "So non-leaf functions save X30 first:\n"
            "  stp x29, x30, [sp, #-16]!\n\n"
            "x86-64 avoids this — CALL always pushes onto the stack,\n"
            "so each call's return address is automatically preserved."
        ),
        "wrong_exp": (
            "X30 holds the return address written by BL.\n"
            "If this function calls another via BL, X30 is overwritten\n"
            "and we lose the address needed to return to our caller.\n\n"
            "Non-leaf functions must save X30 first:\n"
            "  stp x29, x30, [sp, #-16]!\n\n"
            "x86-64 CALL always pushes to the stack, so each call's\n"
            "return address is preserved automatically."
        ),
    },

]


# ---------------------------------------------------------------------------
# ── Sampler — pick a spread of categories ────────────────────────────────
# ---------------------------------------------------------------------------

def _sample_questions(n: int = 3) -> list:
    """
    Return n questions, preferring variety across categories.
    Falls back to a simple random sample if n >= pool size.
    """
    if n >= len(QUIZ_QUESTIONS):
        return random.sample(QUIZ_QUESTIONS, n)

    # Group by category and pick from different groups where possible
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for q in QUIZ_QUESTIONS:
        groups[q["category"]].append(q)

    chosen = []
    categories = list(groups.keys())
    random.shuffle(categories)

    # One from each category until we have n
    for cat in categories:
        if len(chosen) >= n:
            break
        chosen.append(random.choice(groups[cat]))

    # Top up if needed (rare edge case)
    remaining = [q for q in QUIZ_QUESTIONS if q not in chosen]
    while len(chosen) < n and remaining:
        pick = random.choice(remaining)
        chosen.append(pick)
        remaining.remove(pick)

    random.shuffle(chosen)
    return chosen


# ---------------------------------------------------------------------------
# ── Public entry point ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def start_stack_quiz(
    root,
    instructions_ref: list,
    on_quiz_passed,
    on_cancel,
) -> None:
    """
    Entry point. Call this when the player attempts a STACK prestige.

    Parameters
    ----------
    root              tk.Tk root window (Toplevel parent).
    instructions_ref  A single-element list [float] wrapping the current
                      instruction count. This module writes back to [0]
                      to refund the cost on cancel.
    on_quiz_passed    No-arg callable — invoked when all 3 Qs are correct.
    on_cancel         No-arg callable — invoked when the player closes early
                      (after the refund has already been applied here).
    """
    questions = _sample_questions(3)
    _run_question(root, instructions_ref, questions,
                  idx=0, consecutive_wrong=0,
                  on_passed=on_quiz_passed, on_cancel=on_cancel)


# ---------------------------------------------------------------------------
# ── Internal helpers ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _run_question(root, instructions_ref, questions, idx,
                  consecutive_wrong, on_passed, on_cancel) -> None:
    """Render a single question window and wire up its callbacks."""

    if idx >= len(questions):
        on_passed()
        return

    q   = questions[idx]
    win = tk.Toplevel(root)
    win.title(f"STACK Prestige Quiz — Question {idx + 1} of {len(questions)}")
    win.resizable(False, False)
    win.grab_set()

    def _cancel():
        """Refund cost and notify caller that the quiz was abandoned."""
        win.grab_release()
        win.destroy()
        on_cancel()

    win.protocol("WM_DELETE_WINDOW", _cancel)

    # ── Header ───────────────────────────────────────────────────────────
    tk.Label(
        win,
        text="⚠  Answer to confirm STACK Prestige reset  ⚠",
        font=("Arial", 10, "bold"),
        fg="#cc4400",
        pady=6,
    ).pack()

    tk.Label(
        win,
        text=f"Question {idx + 1} of {len(questions)}  |  Topic: {q['category'].replace('_', ' ')}",
        font=("Arial", 9),
        fg="gray",
    ).pack()

    # ── Question text ─────────────────────────────────────────────────────
    tk.Label(
        win,
        text=q["q"],
        font=("Courier", 10),
        justify="left",
        wraplength=520,
        padx=14,
        pady=8,
    ).pack(anchor="w")

    # Reveal answer banner after 2 consecutive wrong attempts on this question
    if consecutive_wrong >= 2:
        tk.Label(
            win,
            text=f"💡 Hint: {q['options'][q['answer']]}",
            font=("Arial", 10, "italic"),
            fg="#005580",
            bg="#ddeeff",
            relief="groove",
            padx=8,
            pady=4,
        ).pack(fill="x", padx=14, pady=(0, 6))

    # ── Radio buttons ─────────────────────────────────────────────────────
    choice_var = tk.IntVar(value=-1)
    for i, opt in enumerate(q["options"]):
        tk.Radiobutton(
            win,
            text=opt,
            variable=choice_var,
            value=i,
            font=("Arial", 10),
            justify="left",
            anchor="w",
            wraplength=500,
            padx=20,
        ).pack(anchor="w", pady=2)

    # ── Submit ────────────────────────────────────────────────────────────
    def _submit():
        selected = choice_var.get()
        if selected == -1:
            messagebox.showwarning("No selection",
                                   "Please select an answer.", parent=win)
            return

        correct = (selected == q["answer"])
        win.grab_release()
        win.destroy()

        if correct:
            _show_feedback(
                root=root,
                title="✅ Correct!",
                text=q["correct_exp"],
                is_correct=True,
                next_fn=lambda: _run_question(
                    root, instructions_ref, questions,
                    idx=idx + 1, consecutive_wrong=0,
                    on_passed=on_passed, on_cancel=on_cancel,
                ),
            )
        else:
            _show_feedback(
                root=root,
                title="❌ Incorrect",
                text=q["wrong_exp"],
                is_correct=False,
                next_fn=lambda: _run_question(
                    root, instructions_ref, questions,
                    idx=idx, consecutive_wrong=consecutive_wrong + 1,
                    on_passed=on_passed, on_cancel=on_cancel,
                ),
            )

    tk.Button(
        win,
        text="Submit Answer",
        command=_submit,
        font=("Arial", 10, "bold"),
        bg="#226622",
        fg="white",
        activebackground="#338833",
        padx=10,
        pady=4,
    ).pack(pady=(8, 12))


def _show_feedback(root, title: str, text: str,
                   is_correct: bool, next_fn) -> None:
    """Modal popup explaining why an answer was right or wrong."""
    win    = tk.Toplevel(root)
    win.title(title)
    win.resizable(False, False)
    win.grab_set()

    colour = "#1a4d1a" if is_correct else "#4d1a1a"
    bg     = "#eeffee" if is_correct else "#ffeeee"

    tk.Label(
        win,
        text=title,
        font=("Arial", 13, "bold"),
        fg=colour,
        bg=bg,
        padx=12,
        pady=8,
    ).pack(fill="x")

    tk.Label(
        win,
        text=text,
        font=("Courier", 9),
        justify="left",
        wraplength=520,
        padx=14,
        pady=10,
        bg=bg,
    ).pack(fill="x")

    def _continue():
        win.grab_release()
        win.destroy()
        next_fn()

    win.protocol("WM_DELETE_WINDOW", _continue)

    tk.Button(
        win,
        text="Continue →",
        command=_continue,
        font=("Arial", 10, "bold"),
        bg=colour,
        fg="white",
        activebackground="#338833" if is_correct else "#883333",
        padx=10,
        pady=4,
    ).pack(pady=(0, 12))