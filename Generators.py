# generators.py
# Low-level instruction generator definitions.
#
# "base_cost"  : cost of the FIRST purchase; each subsequent purchase
#                costs base_cost * 1.15^owned (cookie-clicker style scaling).
# "increment"  : base instructions/sec contributed per owned unit
#                (before any multipliers are applied).
#
# Costs are tuned so that, playing normally, each new generator tier takes
# roughly 300 seconds of current income to afford the first copy.

GENERATORS = [
    {
        "name": "MOV",
        "label": "Buy MOV Unit",
        "base_cost": 10,
        "increment": 1,
        "info": (
            "MOV — Move / Register Copy\n\n"
            "ARM64:  mov x0, x1\n"
            "x86-64: mov rax, rbx\n\n"
            "Copies the value of one register into another.\n"
            "ARM64 encodes this as an alias of ORR with XZR.\n"
            "x86-64 has a dedicated MOV opcode."
        ),
    },
    {
        "name": "ADD",
        "label": "Buy ADD Unit",
        "base_cost": 100,
        "increment": 5,
        "info": (
            "ADD — Integer Addition\n\n"
            "ARM64:  add x0, x1, x2   ; x0 = x1 + x2\n"
            "x86-64: add rax, rbx     ; rax = rax + rbx\n\n"
            "ARM64 uses three explicit operands (destination separate).\n"
            "x86-64 uses two operands; destination is also a source."
        ),
    },
    {
        "name": "IF_INST",
        "label": "Buy IF Unit",
        "base_cost": 500,
        "increment": 20,
        "info": (
            "Conditional Branch\n\n"
            "ARM64:  b.eq label   (branch if equal)\n"
            "x86-64: je  label    (jump if equal)\n\n"
            "Both follow a compare instruction that sets flags.\n"
            "ARM64 condition codes: eq, ne, lt, gt, le, ge, etc.\n"
            "x86-64 uses the EFLAGS register for the same purpose."
        ),
    },
    {
        "name": "LOAD_STORE",
        "label": "Buy LOAD/STORE Unit",
        "base_cost": 2_000,
        "increment": 80,
        "info": (
            "LOAD / STORE — Memory Access\n\n"
            "ARM64:\n"
            "  ldr x0, [x1]    ; load  from address in x1\n"
            "  str x0, [x1]    ; store to  address in x1\n\n"
            "x86-64:\n"
            "  mov rax, [rbx]  ; load  from address in rbx\n"
            "  mov [rbx], rax  ; store to  address in rbx\n\n"
            "ARM64 (RISC) uses distinct LDR/STR opcodes.\n"
            "x86-64 (CISC) reuses MOV for both load and store."
        ),
    },
    {
        "name": "CMP",
        "label": "Buy CMP Unit",
        "base_cost": 8_000,
        "increment": 300,
        "info": (
            "CMP — Compare\n\n"
            "ARM64:  cmp x0, x1    ; sets condition flags\n"
            "x86-64: cmp rax, rbx  ; sets EFLAGS\n\n"
            "Performs subtraction and discards the result,\n"
            "keeping only the resulting flags for conditional branches."
        ),
    },
    {
        "name": "BRANCH",
        "label": "Buy BRANCH Unit",
        "base_cost": 30_000,
        "increment": 1_000,
        "info": (
            "BRANCH — Unconditional & Conditional Jump\n\n"
            "ARM64:\n"
            "  b  label     ; unconditional branch\n"
            "  b.eq label   ; branch if equal\n\n"
            "x86-64:\n"
            "  jmp label    ; unconditional jump\n"
            "  je  label    ; jump if equal\n\n"
            "ARM64 encodes the condition in the opcode suffix.\n"
            "x86-64 uses separate opcodes per condition."
        ),
    },
]