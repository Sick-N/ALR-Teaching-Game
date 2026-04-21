# multipliers.py
# High-level construct definitions — these act as MULTIPLIERS, not generators.
#
# Each entry describes the upgrade's name, display label, base cost, and info
# text shown in the popup.  The actual multiplier *logic* lives in main.py
# inside apply_multiplier_effect().
#
# Cost guidance (tuned for ~300 s per purchase at the expected IPS when
# the player first reaches each tier):
#   IF_STATEMENT  ~  100,000   (reachable after several BRANCH units)
#   WHILE_LOOP    ~  400,000
#   FOR_LOOP      ~1,500,000
#   FUNCTION_CALL ~ 20,000,000  (intentionally very expensive — exponent)
#   PARAM_PASSING ~  600,000
#   STACK         ~5,000,000   (prestige reset — should feel weighty)

MULTIPLIERS = [
    {
        "name": "IF_STATEMENT",
        "label": "Buy IF Statement",
        "base_cost": 100_000,
        "info": (
            "IF Statement — Alternating Multiplier\n\n"
            "Each purchase raises the individual multiplier of\n"
            "alternating generator groups by +1:\n"
            "  Odd  purchases → generators 1, 3, 5 (ADD, LOAD/STORE, BRANCH)\n"
            "  Even purchases → generators 0, 2, 4 (MOV, IF_INST, CMP)\n\n"
            "Compiled pattern: CMP  →  conditional BRANCH\n\n"
            "ARM64:\n"
            "  cmp  x0, x1\n"
            "  b.ne else_label\n\n"
            "x86-64:\n"
            "  cmp  rax, rbx\n"
            "  jne  else_label"
        ),
    },
    {
        "name": "WHILE_LOOP",
        "label": "Buy WHILE Loop",
        "base_cost": 400_000,
        "info": (
            "WHILE Loop — Additive Global Boost\n\n"
            "Each purchase adds the lowest current generator multiplier\n"
            "(minimum +1) to EVERY generator's individual multiplier.\n\n"
            "Compiled pattern: condition  →  body  →  back-branch\n\n"
            "ARM64:\n"
            "loop_start:\n"
            "  cmp  x0, x1\n"
            "  b.ge loop_end\n"
            "  ; body ...\n"
            "  b    loop_start\n"
            "loop_end:\n\n"
            "x86-64:\n"
            "loop_start:\n"
            "  cmp  rax, rbx\n"
            "  jge  loop_end\n"
            "  ; body ...\n"
            "  jmp  loop_start\n"
            "loop_end:"
        ),
    },
    {
        "name": "FOR_LOOP",
        "label": "Buy FOR Loop",
        "base_cost": 1_500_000,
        "info": (
            "FOR Loop — Independent Global Multiplier\n\n"
            "Each level multiplies ALL output by an additional ×(level).\n"
            "Formula contribution:  FOR_LOOP_level  (in the outer multiply)\n\n"
            "Compilers lower a for-loop into a while-loop:\n"
            "  init → [check → body → update] → exit\n\n"
            "ARM64:\n"
            "  mov  x0, #0\n"
            "loop:\n"
            "  cmp  x0, x1\n"
            "  b.ge end\n"
            "  ; body ...\n"
            "  add  x0, x0, #1\n"
            "  b    loop\n"
            "end:\n\n"
            "x86-64 uses xor/inc/cmp/jge for the same pattern."
        ),
    },
    {
        "name": "FUNCTION_CALL",
        "label": "Buy FUNCTION CALL",
        "base_cost": 20_000_000,
        "info": (
            "FUNCTION CALL — Exponential Boost  ⚠ Very Expensive\n\n"
            "Each level raises the exponent in the master formula by 1.\n"
            "Formula:  total = (FOR_level × gen_mult) ^ (1 + FC_level)\n\n"
            "ARM64:  bl  func_label   ; Branch with Link → saves PC to x30\n"
            "        ret              ; return via link register\n\n"
            "x86-64: call func_label  ; pushes return address onto stack\n"
            "        ret              ; pops return address and jumps\n\n"
            "ARM64 stores the return address in x30 (link register).\n"
            "x86-64 stores it on the hardware stack."
        ),
    },
    {
        "name": "PARAM_PASSING",
        "label": "Buy PARAM Passing",
        "base_cost": 600_000,
        "info": (
            "Parameter Passing — Level Equaliser\n\n"
            "Sets the individual multiplier of the lowest generator\n"
            "to match that of the highest generator.\n\n"
            "ARM64 (AAPCS64):\n"
            "  Integer args → x0–x7  (8 registers)\n"
            "  Return value → x0\n\n"
            "x86-64 (System V AMD64):\n"
            "  Integer args → rdi, rsi, rdx, rcx, r8, r9\n"
            "  Return value → rax\n\n"
            "Extra arguments spill onto the stack."
        ),
    },
    {
        "name": "STACK",
        "label": "Buy STACK (PRESTIGE)",
        "base_cost": 5_000_000,
        "info": (
            "STACK — Prestige Reset  ⚠ Resets Everything!\n\n"
            "Resets ALL generators and multipliers to zero,\n"
            "clears all 'don't show again' popup preferences,\n"
            "and grants a permanent ×10 STACK multiplier\n"
            "(displayed in its own window).\n\n"
            "ARM64:\n"
            "  stp x29, x30, [sp, #-16]!  ; push fp & lr\n"
            "  ldp x29, x30, [sp], #16    ; pop  on return\n\n"
            "x86-64:\n"
            "  push rbp\n"
            "  mov  rbp, rsp\n"
            "  ; ...\n"
            "  pop  rbp\n"
            "  ret\n\n"
            "ARM64 uses store-pair/load-pair; x86-64 has PUSH/POP."
        ),
    },
]