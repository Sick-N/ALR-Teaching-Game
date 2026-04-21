# main.py
# Instruction Clicker — main entry point.
#
# Architecture:
#   generators.py  — low-level generator definitions (name, cost, increment)
#   multipliers.py — high-level multiplier definitions (name, cost, effect info)
#   main.py        — all game state, logic, and UI
#
# ── Multiplier formula ───────────────────────────────────────────────────────
#   Each generator g has an individual multiplier  gen_mult[g]  (starts at 1).
#
#   Per-generator IPS (before global multipliers):
#       raw_ips[g] = owned[g] * base_increment[g] * gen_mult[g]
#
#   Total IPS:
#       base_sum = sum(raw_ips[g] for all g)
#       for_level = number of FOR_LOOP purchases
#       fc_level  = number of FUNCTION_CALL purchases
#       stack_mul = 10 ^ stack_prestige_count          (permanent)
#
#       TOTAL_IPS = (max(for_level,1) * base_sum) ^ (1 + fc_level)  * stack_mul
#
#   Click value uses the same TOTAL_MULTIPLIER applied to 1 base instruction.
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox
from Generators import GENERATORS
from Multipliers import MULTIPLIERS

# ---------------------------------------------------------------------------
# ── Game State ───────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

instructions: float = 0.0   # current instruction count (float for sub-tick acc.)

# Generator state  (keyed by generator name)
owned_counts: dict[str, int]   = {g["name"]: 0 for g in GENERATORS}
gen_mult:     dict[str, float] = {g["name"]: 1.0 for g in GENERATORS}

# High-level multiplier purchase counts
mult_counts: dict[str, int] = {m["name"]: 0 for m in MULTIPLIERS}

# Prestige (STACK) — permanent across resets within a session
stack_prestige: int = 0          # number of STACK purchases ever
stack_window: tk.Toplevel | None = None   # reference to the STACK status window

# Popup suppression  (reset on STACK prestige)
popup_view_counts: dict[str, int]  = {}   # views of each popup
popup_disabled:    dict[str, bool] = {}   # "don't show again" flags

# UI widget references (populated during build_ui)
label:        tk.Label
ips_label:    tk.Label
click_btn:    tk.Button
gen_rows:     dict[str, dict] = {}   # name → {frame, btn, count_lbl, mult_lbl}
mult_rows:    dict[str, dict] = {}   # name → {frame, btn, cost_lbl}

root: tk.Tk

# ---------------------------------------------------------------------------
# ── Derived / computed values ─────────────────────────────────────────────
# ---------------------------------------------------------------------------

def compute_total_multiplier() -> float:
    """Return the global multiplier applied on top of raw IPS / click."""
    for_level = mult_counts["FOR_LOOP"]
    fc_level  = mult_counts["FUNCTION_CALL"]
    for_mul   = max(for_level, 1)          # FOR_LOOP contributes ×level (min ×1)
    exponent  = 1 + fc_level
    stack_mul = 10 ** stack_prestige
    return (for_mul ** exponent) * stack_mul


def compute_raw_ips() -> float:
    """Sum of (owned × base_increment × gen_mult) for all generators."""
    total = 0.0
    for g in GENERATORS:
        n = g["name"]
        total += owned_counts[n] * g["increment"] * gen_mult[n]
    return total


def compute_total_ips() -> float:
    """Full IPS after all multipliers."""
    raw = compute_raw_ips()
    fc_level  = mult_counts["FUNCTION_CALL"]
    for_level = mult_counts["FOR_LOOP"]
    for_mul   = max(for_level, 1)
    exponent  = 1 + fc_level
    stack_mul = 10 ** stack_prestige
    # formula: (for_mul * raw_ips) ^ exponent * stack_mul
    # guard against negative base (shouldn't happen, but just in case)
    base = for_mul * raw
    if base < 0:
        base = 0.0
    return (base ** exponent) * stack_mul


def compute_click_value() -> float:
    """Instructions awarded for one manual click (1 base × global multiplier)."""
    return compute_total_multiplier()


def next_gen_cost(gen: dict) -> int:
    """Cookie-clicker style scaling: base_cost × 1.15^owned."""
    owned = owned_counts[gen["name"]]
    return int(gen["base_cost"] * (1.15 ** owned))


def next_mult_cost(mul: dict) -> int:
    """Multiplier upgrades cost × 2 per purchase (they are very powerful)."""
    count = mult_counts[mul["name"]]
    return int(mul["base_cost"] * (2 ** count))

# ---------------------------------------------------------------------------
# ── Display helpers ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def fmt(n: float) -> str:
    """Format large numbers with suffixes for readability."""
    if n < 1_000:
        return str(int(n))
    for val, suffix in [(1e15, "Q"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if n >= val:
            return f"{n/val:.2f}{suffix}"
    return str(int(n))


def update_display() -> None:
    """Refresh all dynamic UI text."""
    label.config(text=f"Instructions: {hex(int(instructions))}")
    ips_label.config(text=f"IPS: {fmt(compute_total_ips())}   "
                          f"Click: ×{fmt(compute_total_multiplier())}")

    # Generator rows
    for g in GENERATORS:
        n = g["name"]
        row = gen_rows[n]
        cost = next_gen_cost(g)
        can_afford = instructions >= cost
        row["btn"].config(
            text=f"{g['label']}  [{fmt(cost)}]",
            state="normal" if can_afford else "disabled",
        )
        row["count_lbl"].config(text=f"×{owned_counts[n]}")
        row["mult_lbl"].config(text=f"mult:{gen_mult[n]:.0f}")

    # Multiplier rows
    for m in MULTIPLIERS:
        n = m["name"]
        row = mult_rows[n]
        cost = next_mult_cost(m)
        can_afford = instructions >= cost
        lvl = mult_counts[n]
        row["btn"].config(
            text=f"{m['label']}  [Lv{lvl}] [{fmt(cost)}]",
            state="normal" if can_afford else "disabled",
        )

    # Stack window (if open)
    refresh_stack_window()


def refresh_stack_window() -> None:
    global stack_window
    if stack_window and stack_window.winfo_exists():
        # find the label inside and update it
        for widget in stack_window.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(
                    text=f"STACK Prestige Count: {stack_prestige}\n"
                         f"Permanent Multiplier: ×{10 ** stack_prestige:,}"
                )
                break

# ---------------------------------------------------------------------------
# ── Popup system ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def show_info_popup(name: str, info: str) -> None:
    popup = tk.Toplevel(root)
    popup.title("Architecture Info")
    tk.Label(popup, text=info, justify="left", padx=10, pady=10,
             font=("Courier", 10)).pack()

    suppress_var = tk.BooleanVar()
    if popup_view_counts.get(name, 0) >= 2:
        tk.Checkbutton(popup, text="Don't show again", variable=suppress_var).pack()

    def on_close() -> None:
        if suppress_var.get():
            popup_disabled[name] = True
        popup.destroy()

    tk.Button(popup, text="OK", command=on_close).pack(pady=5)

# ---------------------------------------------------------------------------
# ── Click handler ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def on_processor_click() -> None:
    global instructions
    instructions += compute_click_value() * 10000000000000000
    update_display()

# ---------------------------------------------------------------------------
# ── Generator purchase ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def buy_generator(gen: dict) -> None:
    global instructions
    cost = next_gen_cost(gen)
    if instructions < cost:
        return

    instructions -= cost
    owned_counts[gen["name"]] += 1

    popup_view_counts[gen["name"]] = popup_view_counts.get(gen["name"], 0) + 1
    update_display()

    if not popup_disabled.get(gen["name"], False):
        show_info_popup(gen["name"], gen["info"])

# ---------------------------------------------------------------------------
# ── Multiplier purchase & effects ─────────────────────────────────────────
# ---------------------------------------------------------------------------

def apply_multiplier_effect(name: str) -> None:
    """Apply the game-mechanic effect for each high-level construct purchase."""

    gen_names = [g["name"] for g in GENERATORS]   # ordered list

    if name == "IF_STATEMENT":
        # Odd purchase (1st, 3rd, …) → generators at ODD indices (1,3,5)
        # Even purchase (2nd, 4th, …) → generators at EVEN indices (0,2,4)
        purchase_num = mult_counts["IF_STATEMENT"]   # already incremented
        if purchase_num % 2 == 1:   # odd purchase number
            targets = gen_names[1::2]
        else:                        # even purchase number
            targets = gen_names[0::2]
        for n in targets:
            gen_mult[n] += 1

    elif name == "WHILE_LOOP":
        # Add the lowest current multiplier (min 1) to EVERY generator
        lowest = max(1, min(gen_mult.values()))
        for n in gen_names:
            gen_mult[n] += lowest

    elif name == "FOR_LOOP":
        # Level is tracked in mult_counts; formula already uses it
        pass   # effect is purely in compute_total_ips()

    elif name == "FUNCTION_CALL":
        # Exponent level tracked in mult_counts; formula uses it
        pass

    elif name == "PARAM_PASSING":
        # Set the lowest-multiplier generator to match the highest
        max_mult = max(gen_mult.values())
        min_name = min(gen_mult, key=lambda n: gen_mult[n])
        gen_mult[min_name] = max_mult

    elif name == "STACK":
        do_stack_prestige()


def do_stack_prestige() -> None:
    """Prestige reset: wipe everything, grant ×10 permanent bonus."""
    global instructions, stack_prestige, stack_window

    stack_prestige += 1

    # Reset generators
    for g in GENERATORS:
        owned_counts[g["name"]] = 0
        gen_mult[g["name"]] = 1.0

    # Reset non-STACK multiplier counts
    for m in MULTIPLIERS:
        if m["name"] != "STACK":
            mult_counts[m["name"]] = 0

    # Reset instructions
    instructions = 0.0

    # Reset popup suppression so the player has to re-check "don't show"
    popup_view_counts.clear()
    popup_disabled.clear()

    # Open / refresh the STACK status window
    open_stack_window()

    update_display()


def open_stack_window() -> None:
    global stack_window
    if stack_window and stack_window.winfo_exists():
        stack_window.destroy()

    stack_window = tk.Toplevel(root)
    stack_window.title("STACK Prestige")
    stack_window.resizable(False, False)

    tk.Label(
        stack_window,
        text=f"STACK Prestige Count: {stack_prestige}\n"
             f"Permanent Multiplier: ×{10 ** stack_prestige:,}",
        font=("Arial", 14, "bold"),
        padx=20, pady=20,
        fg="green",
    ).pack()

    tk.Label(
        stack_window,
        text="This bonus persists until you close the game.",
        font=("Arial", 9),
        padx=10, pady=5,
    ).pack()


def buy_multiplier(mul: dict) -> None:
    global instructions
    cost = next_mult_cost(mul)
    if instructions < cost:
        return

    instructions -= cost
    name = mul["name"]

    # Confirm the scary STACK prestige
    if name == "STACK":
        if not messagebox.askyesno(
            "Prestige Reset",
            "STACK will RESET all generators and upgrades!\n"
            "You will gain a permanent ×10 multiplier.\n\n"
            "Are you sure?",
        ):
            instructions += cost   # refund
            return

    mult_counts[name] += 1
    popup_view_counts[name] = popup_view_counts.get(name, 0) + 1

    apply_multiplier_effect(name)
    update_display()

    if not popup_disabled.get(name, False):
        show_info_popup(name, mul["info"])

# ---------------------------------------------------------------------------
# ── Auto-increment (1-second tick) ───────────────────────────────────────
# ---------------------------------------------------------------------------

def auto_increment() -> None:
    global instructions
    instructions += compute_total_ips()
    update_display()
    root.after(1000, auto_increment)

# ---------------------------------------------------------------------------
# ── UI construction ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def build_ui() -> None:
    global label, ips_label, click_btn, root
    root = tk.Tk()
    root.title("Instruction Clicker")

    processor_img = tk.PhotoImage(file="Processor.png")

    # ── Header ──────────────────────────────────────────────────────────────
    label = tk.Label(root, text="Instructions: 0x0", font=("Arial", 16))
    label.pack()

    ips_label = tk.Label(root, text="IPS: 0   Click: ×1", font=("Arial", 13))
    ips_label.pack()

    click_btn = tk.Button(root, image=processor_img, command=on_processor_click)
    click_btn.pack(pady=4)
    click_btn.image = processor_img   # prevent GC

    # ── Section label ────────────────────────────────────────────────────────
    tk.Label(root, text="─── Generators ───", font=("Arial", 11, "bold")).pack(pady=(6, 0))

    # ── Generator rows ───────────────────────────────────────────────────────
    for g in GENERATORS:
        frame = tk.Frame(root)
        frame.pack(pady=1, fill="x", padx=6)

        btn = tk.Button(
            frame,
            text=f"{g['label']}  [{g['base_cost']}]",
            width=36,
            anchor="w",
            command=lambda _g=g: buy_generator(_g),
        )
        btn.pack(side="left")

        count_lbl = tk.Label(frame, text="×0", width=5, anchor="e")
        count_lbl.pack(side="left")

        mult_lbl = tk.Label(frame, text="mult:1", width=8, anchor="w")
        mult_lbl.pack(side="left", padx=4)

        gen_rows[g["name"]] = {"frame": frame, "btn": btn,
                               "count_lbl": count_lbl, "mult_lbl": mult_lbl}

    # ── Section label ────────────────────────────────────────────────────────
    tk.Label(root, text="─── Multipliers ───", font=("Arial", 11, "bold")).pack(pady=(8, 0))

    # ── Multiplier rows ──────────────────────────────────────────────────────
    for m in MULTIPLIERS:
        frame = tk.Frame(root)
        frame.pack(pady=1, fill="x", padx=6)

        btn = tk.Button(
            frame,
            text=f"{m['label']}  [Lv0] [{m['base_cost']}]",
            width=44,
            anchor="w",
            command=lambda _m=m: buy_multiplier(_m),
        )
        btn.pack(side="left")

        mult_rows[m["name"]] = {"frame": frame, "btn": btn}

    return root, processor_img   # return img ref to keep alive

# ---------------------------------------------------------------------------
# ── Entry point ───────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root, _img = build_ui()
    update_display()
    auto_increment()
    root.mainloop()