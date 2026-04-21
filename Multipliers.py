# Multipliers.py
# High-level construct definitions — these act as MULTIPLIERS, not generators.
#
# "tooltip" : short game-mechanic description shown on hover.
#             No assembly content here — that lives in Generators.py.
# "base_cost": cost of the first purchase; doubles each subsequent purchase.
#
# The actual multiplier logic lives in main.py → apply_multiplier_effect().

MULTIPLIERS = [
    {
        "name": "IF_STATEMENT",
        "label": "Buy IF Statement",
        "base_cost": 100_000,
        "tooltip": (
            "IF Statement — Alternating +1 Multiplier\n"
            "─────────────────────────────────────────\n"
            "Raises the individual multiplier of alternating\n"
            "generator groups by +1 per purchase.\n\n"
            "  Purchase 1, 3, 5 … (ODD)\n"
            "    → ADD, LOAD/STORE, BRANCH  get +1 mult\n\n"
            "  Purchase 2, 4, 6 … (EVEN)\n"
            "    → MOV, IF_INST, CMP  get +1 mult\n\n"
            "Stacks with every purchase. Buy repeatedly to\n"
            "boost all generators over time."
        ),
    },
    {
        "name": "WHILE_LOOP",
        "label": "Buy WHILE Loop",
        "base_cost": 400_000,
        "tooltip": (
            "WHILE Loop — Additive Global Boost\n"
            "─────────────────────────────────────────\n"
            "Each purchase adds the lowest current generator\n"
            "multiplier (minimum +1) to EVERY generator.\n\n"
            "  Example: multipliers are [3, 5, 2, 8, 4, 6]\n"
            "    Lowest = 2  →  all multipliers get +2\n"
            "    Result:      [5, 7, 4, 10, 6, 8]\n\n"
            "Best bought after IF Statement has raised all\n"
            "generators to a similar level — the additive\n"
            "bonus is then applied across the board."
        ),
    },
    {
        "name": "FOR_LOOP",
        "label": "Buy FOR Loop",
        "base_cost": 1_500_000,
        "tooltip": (
            "FOR Loop — Independent Global Multiplier\n"
            "─────────────────────────────────────────\n"
            "Each level adds ×1 to the outer global multiplier.\n\n"
            "  Formula:  (FOR_level × raw_IPS) ^ (1 + FC_level)\n\n"
            "  FOR level 1 → ×1   (no change yet)\n"
            "  FOR level 2 → ×2   all output doubled\n"
            "  FOR level 3 → ×3   all output tripled\n\n"
            "Combines multiplicatively with FUNCTION CALL's\n"
            "exponent — buy FOR LOOP before FUNCTION CALL\n"
            "for maximum explosive scaling."
        ),
    },
    {
        "name": "FUNCTION_CALL",
        "label": "Buy FUNCTION CALL",
        "base_cost": 20_000_000,
        "tooltip": (
            "FUNCTION CALL — Exponential Boost  ⚠ Costly!\n"
            "─────────────────────────────────────────\n"
            "Each level raises the EXPONENT in the master\n"
            "formula by +1.\n\n"
            "  Formula:  (FOR_level × raw_IPS) ^ (1 + FC_level)\n\n"
            "  FC level 0 → exponent = 1  (linear, no bonus)\n"
            "  FC level 1 → exponent = 2  (everything squared!)\n"
            "  FC level 2 → exponent = 3  (everything cubed!)\n\n"
            "WARNING: This is intentionally very expensive.\n"
            "Make sure FOR Loop and generator multipliers are\n"
            "already high before buying — a large base raised\n"
            "to a higher exponent grows astronomically."
        ),
    },
    {
        "name": "PARAM_PASSING",
        "label": "Buy PARAM Passing",
        "base_cost": 600_000,
        "tooltip": (
            "PARAM Passing — Count Equaliser\n"
            "─────────────────────────────────────────\n"
            "Sets the OWNED COUNT of the LOWEST generator\n"
            "to match the count of the HIGHEST generator.\n\n"
            "  Example: owned counts are [10, 3, 10, 2, 8, 10]\n"
            "    Lowest = LOAD/STORE at 2\n"
            "    Highest = MOV/IF_INST/BRANCH at 10\n"
            "    Result: LOAD/STORE jumps to 10 owned\n\n"
            "Only one generator is equalised per purchase.\n"
            "Buy multiple times to bring all laggards up\n"
            "to the count of your top performers."
        ),
    },
    {
        "name": "STACK",
        "label": "Buy STACK (PRESTIGE)",
        "base_cost": 5_000_000,
        "tooltip": (
            "STACK — Prestige Reset  ⚠ Resets Everything!\n"
            "─────────────────────────────────────────\n"
            "RESETS:\n"
            "  • All generator owned counts → 0\n"
            "  • All generator multipliers  → 1\n"
            "  • All multiplier levels      → 0\n"
            "  • Current instruction count  → 0\n"
            "  • All 'don't show again' popup settings\n\n"
            "GRANTS (permanent, survives resets):\n"
            "  • ×10 STACK multiplier, stacking per prestige\n"
            "    1 prestige = ×10\n"
            "    2 prestiges = ×100\n"
            "    3 prestiges = ×1,000  etc.\n\n"
            "A STACK prestige window opens to track your\n"
            "permanent bonus. The reset is shown as a\n"
            "confirmation dialog — you will be asked twice."
        ),
    },
]