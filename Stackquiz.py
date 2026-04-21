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

import tkinter as tk
from tkinter import messagebox
import random

# ---------------------------------------------------------------------------
# ── Question pool — 10 ARM64 vs x86-64 questions ─────────────────────────
# ---------------------------------------------------------------------------

QUIZ_QUESTIONS = [
    {
        "q": "In ARM64, MOV is a pseudo-instruction. What real opcode does\nthe assembler emit for a register-to-register MOV?",
        "options": ["MOVZ x0, x1", "ORR x0, xzr, x1", "ADD x0, xzr, x1", "LDR x0, [x1]"],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 has NO dedicated MOV opcode for reg-to-reg transfers.\n"
            "The assembler rewrites  mov x0, x1  as:\n"
            "  ORR x0, xzr, x1\n"
            "XZR is ARM's hard-wired zero register — OR-ing with zero\n"
            "simply copies the value. x86-64 has a real MOV opcode; ARM does not."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 has NO dedicated MOV opcode for reg-to-reg transfers.\n"
            "The assembler rewrites  mov x0, x1  as  ORR x0, xzr, x1.\n"
            "XZR is ARM's zero register — OR-ing with zero copies the value.\n"
            "x86-64 DOES have a real MOV opcode; ARM does not."
        ),
    },
    {
        "q": "ARM64's ADD uses 3 operands. What is the key advantage\nover x86-64's 2-operand ADD?",
        "options": [
            "It runs twice as fast on all hardware",
            "The destination is separate, so source registers are never overwritten",
            "It can add three numbers simultaneously",
            "It automatically sets the carry flag",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64:  add x0, x1, x2   — x0 = x1 + x2  (x1 and x2 unchanged)\n"
            "x86-64: add rax, rbx     — rax = rax + rbx  (rax overwritten)\n\n"
            "With 3 operands, compilers can freely reuse source registers\n"
            "without spilling them to the stack first."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "The 3-operand form means the destination is SEPARATE from sources.\n"
            "ARM64:  add x0, x1, x2  writes to x0 without touching x1 or x2.\n"
            "x86-64 ADD always overwrites its left operand.\n"
            "This lets compilers reuse registers without stack spills."
        ),
    },
    {
        "q": "x86-64 ADD always sets CPU flags. How does ARM64 handle\nflag-setting for its ADD instruction?",
        "options": [
            "ARM64 ADD never sets flags under any circumstances",
            "ARM64 sets flags only when the result overflows",
            "ARM64 uses a separate ADDS variant to opt IN to flag-setting",
            "ARM64 and x86-64 both always set flags — identical behaviour",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 separates the two behaviours:\n"
            "  add  x0, x1, x2   — adds, does NOT touch NZCV flags\n"
            "  adds x0, x1, x2   — adds AND sets NZCV flags\n\n"
            "x86-64 gives no choice — ADD always sets CF, ZF, SF, OF, PF.\n"
            "ARM lets you add without clobbering a prior comparison result."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 uses an 'S' suffix to OPT IN to flag-setting:\n"
            "  add  x0, x1, x2   — no flags touched\n"
            "  adds x0, x1, x2   — sets NZCV flags\n\n"
            "x86-64 ADD always sets flags — there is no opt-out."
        ),
    },
    {
        "q": "Which ARM64 instruction branches on a zero/non-zero check\nwithout needing a separate CMP first?",
        "options": ["B.EQ", "CBZ / CBNZ", "TST", "SUBS xzr, x0, #0"],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 CBZ / CBNZ:\n"
            "  cbz  x0, label   — branch if x0 == 0, no CMP needed!\n"
            "  cbnz x0, label   — branch if x0 != 0\n\n"
            "x86-64 has no equivalent — a separate CMP/TEST is always required.\n"
            "CBZ/CBNZ save an instruction in the common  if (x == 0)  pattern."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 has CBZ (Compare and Branch if Zero) and CBNZ (Non-Zero).\n"
            "  cbz x0, label  branches if x0 is zero — no prior CMP needed.\n\n"
            "B.EQ requires a CMP first. TST checks bits but doesn't branch.\n"
            "x86-64 has no single-instruction zero-check-and-branch equivalent."
        ),
    },
    {
        "q": "In x86-64, what is the idiomatic way to efficiently clear\na register to zero? (Compilers rarely use  mov rax, 0.)",
        "options": [
            "mov rax, 0",
            "xor rax, rax",
            "sub rax, rax is the only correct way",
            "ARM's XZR register handles this automatically",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "  xor rax, rax  is the canonical x86-64 zero idiom.\n"
            "It is shorter to encode (no immediate bytes) and faster to decode\n"
            "than  mov rax, 0. The CPU also recognises it as a zeroing idiom\n"
            "and can break false data dependencies.\n\n"
            "ARM64 uses XZR (the hard-wired zero register) instead."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "  xor rax, rax  is the correct answer.\n"
            "Shorter to encode than  mov rax, 0  (no immediate bytes),\n"
            "and the CPU treats it as a dependency-breaking zeroing idiom.\n\n"
            "ARM64 sidesteps this with XZR — a hard-wired zero register."
        ),
    },
    {
        "q": "ARM64 CMP is a pseudo-instruction. What real instruction\ndoes it map to, and where is the result stored?",
        "options": [
            "SUB x0, x0, x1  — result stored in x0",
            "SUBS xzr, x0, x1  — result discarded via XZR",
            "AND xzr, x0, x1  — bitwise compare stored in XZR",
            "It is a real opcode — same as x86-64 CMP",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 CMP is an alias for:  SUBS xzr, x0, x1\n"
            "  SUBS = subtract and set flags\n"
            "  xzr  = zero register — writes are silently discarded\n\n"
            "The subtraction result is thrown away; only NZCV flags are kept.\n"
            "x86-64 CMP is a genuine dedicated opcode, though logically the same."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 CMP maps to:  SUBS xzr, x0, x1\n"
            "The result is stored in XZR which discards it.\n"
            "The NZCV flags ARE set — that is the whole point.\n\n"
            "x86-64 CMP is a real dedicated opcode, not a pseudo-instruction."
        ),
    },
    {
        "q": "How does ARM64 express conditional branches\ncompared to x86-64?",
        "options": [
            "ARM64 has one opcode per condition (beq, bne, blt …) like x86-64's je/jne/jl",
            "ARM64 uses a single B opcode with a condition suffix (B.EQ, B.NE, B.LT …)",
            "ARM64 uses a flag register index as an operand to a generic BRANCH opcode",
            "ARM64 and x86-64 use identical branch mnemonics",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64:  B.EQ / B.NE / B.LT … — one base opcode B with a suffix.\n"
            "x86-64: JE / JNE / JL …     — every condition is its own opcode.\n\n"
            "ARM's approach means fewer unique mnemonics and a more regular\n"
            "encoding — consistent with RISC philosophy."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 uses ONE base opcode  B  with a condition SUFFIX:\n"
            "  B.EQ, B.NE, B.LT, B.GE …\n\n"
            "x86-64 gives every condition its own opcode: JE, JNE, JL, JGE …\n"
            "ARM's approach requires fewer mnemonics and is more regular."
        ),
    },
    {
        "q": "ARM64 is RISC; x86-64 is CISC. How does this affect\nmemory operands in arithmetic instructions?",
        "options": [
            "Both allow memory operands directly in arithmetic — same behaviour",
            "ARM64 allows memory operands; x86-64 requires a register load first",
            "ARM64 requires all arithmetic in registers; x86-64 can use memory operands directly",
            "Neither architecture supports memory operands in arithmetic",
        ],
        "answer": 2,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 (RISC): ALL arithmetic must work on registers.\n"
            "  ldr x1, [x2]     — load from memory first\n"
            "  add x0, x0, x1   — then add\n\n"
            "x86-64 (CISC): Arithmetic can take memory operands directly:\n"
            "  add rax, [rbx]   — rax += *(rbx), no separate load!\n\n"
            "ARM needs more instructions but each is simple to pipeline."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 is RISC: ALL arithmetic must operate on registers.\n"
            "You must  ldr  a value into a register before  add  can use it.\n\n"
            "x86-64 is CISC:  add rax, [rbx]  takes a memory address directly.\n"
            "More work per instruction but fewer instructions total."
        ),
    },
    {
        "q": "ARM64 NZCV vs x86-64 EFLAGS — which statement is correct?",
        "options": [
            "EFLAGS has 4 relevant bits; NZCV has 6 — ARM has more flags",
            "NZCV has 4 bits (N,Z,C,V); EFLAGS has 6 relevant bits including Parity and Aux Carry",
            "Both have exactly 4 flag bits — they are architecturally equivalent",
            "NZCV stands for: Null, Zero, Count, Valid",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 NZCV:  N=Negative, Z=Zero, C=Carry, V=oVerflow  (4 bits)\n\n"
            "x86-64 EFLAGS relevant bits:\n"
            "  CF, ZF, SF, OF, PF (Parity), AF (Aux Carry)  = 6 bits\n\n"
            "PF and AF are legacy x86 baggage rarely used in modern code.\n"
            "ARM's cleaner 4-bit NZCV reflects its more modern design."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 NZCV = 4 bits: Negative, Zero, Carry, oVerflow.\n"
            "x86-64 EFLAGS = 6 relevant bits: CF, ZF, SF, OF, PF, AF.\n\n"
            "The extra PF (Parity) and AF (Auxiliary Carry) are legacy x86\n"
            "features rarely needed in modern code."
        ),
    },
    {
        "q": "ARM64 has LDP and STP instructions. What do they do,\nand what is the x86-64 equivalent?",
        "options": [
            "LDP/STP do logic+data ops; x86-64 uses LODS/STOS",
            "LDP/STP load/store a PAIR of registers in one instruction; x86-64 needs two separate moves",
            "LDP/STP are 128-bit SIMD ops; x86-64 uses MOVAPS",
            "LDP/STP are pseudo-instructions for LDR/STR; x86-64 has exact equivalents",
        ],
        "answer": 1,
        "correct_exp": (
            "Correct!\n\n"
            "ARM64 LDP/STP (Load/Store Pair):\n"
            "  ldp x0, x1, [sp]  — load TWO registers in one instruction\n"
            "  stp x0, x1, [sp]  — store TWO registers in one instruction\n\n"
            "x86-64 has no single-instruction equivalent — two separate\n"
            "MOV/PUSH/POP operations are required. LDP/STP is a key\n"
            "efficiency win for function prologues and epilogues."
        ),
        "wrong_exp": (
            "Incorrect.\n\n"
            "ARM64 LDP = Load Pair, STP = Store Pair.\n"
            "  ldp x0, x1, [sp]  loads two registers from memory at once.\n"
            "  stp x0, x1, [sp]  stores two registers at once.\n\n"
            "x86-64 requires two separate instructions for the same effect.\n"
            "This makes ARM function call setup/teardown more efficient."
        ),
    },
]

# ---------------------------------------------------------------------------
# ── Quiz engine ───────────────────────────────────────────────────────────
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
    questions = random.sample(QUIZ_QUESTIONS, 3)
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
        text=f"Question {idx + 1} of {len(questions)}",
        font=("Arial", 9),
        fg="gray",
    ).pack()

    # ── Question text ─────────────────────────────────────────────────────
    tk.Label(
        win,
        text=q["q"],
        font=("Courier", 10),
        justify="left",
        wraplength=480,
        padx=14,
        pady=8,
    ).pack(anchor="w")

    # Reveal answer banner after 2 consecutive wrong attempts on this question
    if consecutive_wrong >= 2:
        tk.Label(
            win,
            text=f"💡 Answer: {q['options'][q['answer']]}",
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
            wraplength=460,
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
        wraplength=480,
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