# main.py
# Instruction Clicker — main entry point.
#
# Architecture:
#   Generators.py  — low-level generator definitions (name, cost, increment, info)
#   Multipliers.py — high-level multiplier definitions (name, cost, tooltip)
#   main.py        — all game state, logic, and UI
#
# ── Multiplier formula ───────────────────────────────────────────────────────
#   Each generator g has an individual multiplier  gen_mult[g]  (starts at 1).
#
#   Per-generator IPS (before global multipliers):
#       raw_ips[g] = owned[g] * base_increment[g] * gen_mult[g]
#
#   Total IPS:
#       base_sum  = sum(raw_ips[g] for all g)
#       for_level = number of FOR_LOOP purchases
#       fc_level  = number of FUNCTION_CALL purchases
#       stack_mul = 10 ^ stack_prestige_count  (permanent)
#
#       TOTAL_IPS = (max(for_level,1) * base_sum) ^ (1 + fc_level) * stack_mul
#
#   Click value uses the same global multiplier applied to 1 base instruction.
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import messagebox
from Generators import GENERATORS
from Multipliers import MULTIPLIERS
from Stackquiz import start_stack_quiz
from Glossary import ARM64_GLOSSARY, X86_GLOSSARY, GENERATOR_NAMES

# ---------------------------------------------------------------------------
# ── Game State ───────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

instructions: float = 0.0   # current instruction count

# Generator state  (keyed by generator name)
owned_counts: dict[str, int]   = {g["name"]: 0 for g in GENERATORS}
gen_mult:     dict[str, float] = {g["name"]: 1.0 for g in GENERATORS}

# High-level multiplier purchase counts
mult_counts: dict[str, int] = {m["name"]: 0 for m in MULTIPLIERS}

# Prestige (STACK) — permanent across resets within a session
stack_prestige: int = 0
stack_window: tk.Toplevel | None = None

# Popup suppression for generator info windows (reset on STACK prestige)
popup_view_counts: dict[str, int]  = {}
popup_disabled:    dict[str, bool] = {}

# UI widget references (populated during build_ui)
label:     tk.Label
ips_label: tk.Label
click_btn: tk.Button
gen_rows:  dict[str, dict] = {}   # name → {frame, btn, count_lbl, mult_lbl}
mult_rows: dict[str, dict] = {}   # name → {frame, btn}

# Buy-quantity selector: positive int = fixed amount, -1 = MAX
buy_quantity: int = 1
qty_buttons:  dict[int, tk.Button] = {}   # quantity → button widget

root: tk.Tk

# ---------------------------------------------------------------------------
# ── Derived / computed values ─────────────────────────────────────────────
# ---------------------------------------------------------------------------

def compute_total_multiplier() -> float:
    """Global multiplier applied to click value and IPS."""
    for_level = mult_counts["FOR_LOOP"]
    fc_level  = mult_counts["FUNCTION_CALL"]
    for_mul   = max(for_level, 1)
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
    raw      = compute_raw_ips()
    for_level = mult_counts["FOR_LOOP"]
    fc_level  = mult_counts["FUNCTION_CALL"]
    for_mul   = max(for_level, 1)
    exponent  = 1 + fc_level
    stack_mul = 10 ** stack_prestige
    base = for_mul * raw
    if base < 0:
        base = 0.0
    return (base ** exponent) * stack_mul


def compute_click_value() -> float:
    """Instructions awarded for one manual click."""
    return compute_total_multiplier()


def next_gen_cost(gen: dict) -> int:
    """Cookie-clicker scaling: base_cost × 1.15^owned."""
    return int(gen["base_cost"] * (1.15 ** owned_counts[gen["name"]]))


def next_mult_cost(mul: dict) -> int:
    """Multiplier costs double each purchase."""
    return int(mul["base_cost"] * (2 ** mult_counts[mul["name"]]))


def cost_for_n(gen: dict, n: int) -> int:
    """Total cost of buying n more of a generator (geometric sum)."""
    base   = gen["base_cost"]
    owned  = owned_counts[gen["name"]]
    # sum_{i=0}^{n-1}  floor(base * 1.15^(owned+i))
    # Use closed-form for the geometric series then floor at end.
    # Exact integer sum to avoid float drift:
    total = 0
    for i in range(n):
        total += int(base * (1.15 ** (owned + i)))
    return total


def max_affordable(gen: dict) -> int:
    """How many of this generator can be bought with current instructions."""
    affordable = 0
    remaining  = instructions
    base       = gen["base_cost"]
    owned      = owned_counts[gen["name"]]
    while True:
        cost = int(base * (1.15 ** (owned + affordable)))
        if remaining < cost:
            break
        remaining -= cost
        affordable += 1
    return affordable


# ---------------------------------------------------------------------------
# ── Display helpers ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def fmt(n: float) -> str:
    """Format large numbers with K/M/B/T/Q suffixes."""
    if n < 1_000:
        return str(int(n))
    for val, suffix in [(1e15, "Q"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if n >= val:
            return f"{n/val:.2f}{suffix}"
    return str(int(n))


def fmt_ops(n: float) -> str:
    """Format the instruction counter with CPU operation suffixes (op/Kop/Mop…)."""
    if n < 1_000:
        return f"{int(n)} op"
    for val, suffix in [
        (1e18, "Eop"),
        (1e15, "Pop"),
        (1e12, "Top"),
        (1e9,  "Gop"),
        (1e6,  "Mop"),
        (1e3,  "Kop"),
    ]:
        if n >= val:
            return f"{n/val:.2f} {suffix}"
    return f"{int(n)} op"


def update_display() -> None:
    """Refresh all dynamic UI text."""
    label.config(text=f"Instructions: {fmt_ops(instructions)}")
    ips_label.config(
        text=f"IPS: {fmt(compute_total_ips())}   Click: ×{fmt(compute_total_multiplier())}"
    )

    # Generator rows
    for g in GENERATORS:
        n   = g["name"]
        row = gen_rows[n]

        if buy_quantity == -1:
            qty = max_affordable(g)
            if qty == 0:
                cost      = next_gen_cost(g)
                label_txt = f"{g['label']}  [MAX: {fmt(cost)}]"
                can_buy   = False
            else:
                cost      = cost_for_n(g, qty)
                label_txt = f"{g['label']}  [MAX×{qty}: {fmt(cost)}]"
                can_buy   = True
        else:
            qty       = buy_quantity
            cost      = cost_for_n(g, qty)
            label_txt = f"{g['label']}  [×{qty}: {fmt(cost)}]"
            can_buy   = instructions >= cost

        row["btn"].config(text=label_txt, state="normal" if can_buy else "disabled")
        row["count_lbl"].config(text=f"×{owned_counts[n]}")
        row["mult_lbl"].config(text=f"mult:{gen_mult[n]:.0f}")

    # Multiplier rows
    for m in MULTIPLIERS:
        n   = m["name"]
        row = mult_rows[n]
        cost = next_mult_cost(m)
        lvl  = mult_counts[n]
        row["btn"].config(
            text=f"{m['label']}  [Lv{lvl}] [{fmt(cost)}]",
            state="normal" if instructions >= cost else "disabled",
        )

    # Highlight active quantity button
    for qty_val, qbtn in qty_buttons.items():
        if qty_val == buy_quantity:
            qbtn.config(relief="sunken", bg="#a0c8ff")
        else:
            qbtn.config(relief="raised", bg="SystemButtonFace")

    refresh_stack_window()


def refresh_stack_window() -> None:
    global stack_window
    if stack_window and stack_window.winfo_exists():
        for widget in stack_window.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(
                    text=f"STACK Prestige Count: {stack_prestige}\n"
                         f"Permanent Multiplier: ×{10 ** stack_prestige:,}"
                )
                break

# ---------------------------------------------------------------------------
# ── Hover tooltip system ──────────────────────────────────────────────────
# ---------------------------------------------------------------------------

class Tooltip:
    """
    Lightweight hover tooltip for any tkinter widget.
    Shows a small Toplevel window near the widget on <Enter>,
    destroys it on <Leave>.
    """

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget  = widget
        self.text    = text
        self._tip_win: tk.Toplevel | None = None

        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None) -> None:
        if self._tip_win or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 4
        y = self.widget.winfo_rooty()

        self._tip_win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)   # no title bar / frame
        tw.wm_geometry(f"+{x}+{y}")

        tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Courier", 9),
            padx=6,
            pady=4,
        ).pack()

    def _hide(self, event=None) -> None:
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None

# ---------------------------------------------------------------------------
# ── Generator info popup ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def show_info_popup(name: str, info: str) -> None:
    """Show teaching-aid popup for a generator instruction."""
    popup = tk.Toplevel(root)
    popup.title("Architecture Info")
    tk.Label(
        popup,
        text=info,
        justify="left",
        padx=10,
        pady=10,
        font=("Courier", 10),
    ).pack()

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
    instructions += compute_click_value()
    update_display()

# ---------------------------------------------------------------------------
# ── Generator purchase ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def buy_generator(gen: dict) -> None:
    """Buy the currently selected quantity of a generator."""
    global instructions
    name = gen["name"]

    if buy_quantity == -1:
        qty = max_affordable(gen)
    else:
        qty = buy_quantity

    if qty <= 0:
        return

    total_cost = cost_for_n(gen, qty)
    if instructions < total_cost:
        return

    instructions -= total_cost
    owned_counts[name] += qty
    popup_view_counts[name] = popup_view_counts.get(name, 0) + qty

    update_display()

    # Only show popup once per click regardless of quantity, and only when
    # buying 1 (showing a popup for 100× purchases would be spammy).
    if qty == 1 and not popup_disabled.get(name, False):
        show_info_popup(name, gen["info"])

# ---------------------------------------------------------------------------
# ── Multiplier purchase & effects ─────────────────────────────────────────
# ---------------------------------------------------------------------------

def apply_multiplier_effect(name: str) -> None:
    """Apply the game-mechanic effect for each high-level construct purchase."""
    gen_names = [g["name"] for g in GENERATORS]

    if name == "IF_STATEMENT":
        purchase_num = mult_counts["IF_STATEMENT"]   # already incremented
        targets = gen_names[1::2] if purchase_num % 2 == 1 else gen_names[0::2]
        for n in targets:
            gen_mult[n] += 1

    elif name == "WHILE_LOOP":
        lowest = max(1.0, min(gen_mult.values()))
        for n in gen_names:
            gen_mult[n] += lowest

    elif name == "FOR_LOOP":
        pass   # effect is purely in compute_total_ips()

    elif name == "FUNCTION_CALL":
        pass   # exponent tracked in mult_counts; formula uses it

    elif name == "PARAM_PASSING":
        max_owned = max(owned_counts.values())
        min_name  = min(owned_counts, key=lambda n: owned_counts[n])
        owned_counts[min_name] = max_owned

    elif name == "STACK":
        do_stack_prestige()


def do_stack_prestige() -> None:
    """Prestige reset: wipe everything, grant ×10 permanent bonus."""
    global instructions, stack_prestige

    stack_prestige += 1

    for g in GENERATORS:
        owned_counts[g["name"]] = 0
        gen_mult[g["name"]]     = 1.0

    for m in MULTIPLIERS:
        if m["name"] != "STACK":
            mult_counts[m["name"]] = 0

    instructions = 0.0
    popup_view_counts.clear()
    popup_disabled.clear()

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
        padx=20,
        pady=20,
        fg="green",
    ).pack()

    tk.Label(
        stack_window,
        text="This bonus persists until you close the game.",
        font=("Arial", 9),
        padx=10,
        pady=5,
    ).pack()


def buy_multiplier(mul: dict) -> None:
    global instructions
    cost = next_mult_cost(mul)
    if instructions < cost:
        return

    instructions -= cost
    name = mul["name"]

    if name == "STACK":
        # Pass instructions as a one-element list so StackQuiz can refund it.
        instructions_ref = [instructions]

        def on_passed():
            global instructions
            instructions = instructions_ref[0]   # pick up any refund writes
            mult_counts[mul["name"]] += 1
            apply_multiplier_effect(mul["name"])
            update_display()

        def on_cancel():
            global instructions
            instructions = instructions_ref[0] + cost   # refund
            update_display()

        start_stack_quiz(root, instructions_ref, on_passed, on_cancel)
        return   # quiz callbacks handle the rest

    mult_counts[name] += 1
    apply_multiplier_effect(name)
    update_display()
    # NOTE: No popup is shown for multipliers — hover tooltip handles info.

# ---------------------------------------------------------------------------
# ── Auto-increment (per-frame smooth tick, ~30 fps) ───────────────────────
# ---------------------------------------------------------------------------

_TICK_MS: int   = 33           # ~30 fps
_TICK_S:  float = _TICK_MS / 1000.0

def auto_increment() -> None:
    global instructions
    # Add the proportional fraction of IPS for this frame so that
    # total instructions/second stays correct regardless of tick rate.
    instructions += compute_total_ips() * _TICK_S
    update_display()
    root.after(_TICK_MS, auto_increment)


def set_buy_quantity(qty: int) -> None:
    """Switch the active buy-quantity and refresh the display."""
    global buy_quantity
    buy_quantity = qty
    update_display()


# ---------------------------------------------------------------------------
# ── UI construction ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ── Glossary system ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def _get_generator_info(gen_name: str) -> str | None:
    """Return the 'info' string from the matching GENERATOR entry, or None."""
    for g in GENERATORS:
        if g["name"] == gen_name:
            return g["info"]
    return None


def show_glossary_popup(entry_name: str, info: str) -> None:
    """
    Display a glossary entry in a scrollable popup window.
    If info starts with '__GENERATOR__:<name>', redirect to that generator's
    info string so the content is never duplicated.
    """
    # Redirect to generator info when flagged
    if info.startswith("__GENERATOR__:"):
        gen_name = info.split(":", 1)[1]
        gen_info = _get_generator_info(gen_name)
        if gen_info:
            info = gen_info

    popup = tk.Toplevel(root)
    popup.title(f"Glossary — {entry_name}")
    popup.resizable(True, True)

    # ── Scrollable text area ──────────────────────────────────────────────
    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True, padx=6, pady=6)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    text_widget = tk.Text(
        frame,
        wrap="word",
        font=("Courier", 10),
        width=64,
        height=24,
        yscrollcommand=scrollbar.set,
        relief="flat",
        padx=8,
        pady=6,
        state="normal",
        cursor="arrow",
    )
    text_widget.insert("1.0", info)
    text_widget.config(state="disabled")   # read-only
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)

    tk.Button(popup, text="Close", command=popup.destroy,
              font=("Arial", 9, "bold")).pack(pady=(0, 8))


def build_glossary_menu(parent_frame: tk.Frame) -> None:
    """
    Build the 'Glossary' menubutton with ARM64 and x86-64 submenus.
    Each entry opens a show_glossary_popup when clicked.
    Generator-overlapping entries are marked with '→ see Generator info'
    in their label but still open the full generator info panel.
    """
    menu_btn = tk.Menubutton(
        parent_frame,
        text="📖 Glossary",
        font=("Arial", 10, "bold"),
        relief="raised",
        bd=2,
        padx=6,
        pady=3,
        cursor="hand2",
    )
    menu_btn.pack(side="left", padx=4, pady=4)

    top_menu = tk.Menu(menu_btn, tearoff=0)
    menu_btn.config(menu=top_menu)

    for arch_label, entries in [("ARM64 (AArch64)", ARM64_GLOSSARY),
                                 ("x86-64 (Intel/AMD)", X86_GLOSSARY)]:
        sub = tk.Menu(top_menu, tearoff=0)
        top_menu.add_cascade(label=arch_label, menu=sub)

        for entry in entries:
            name = entry["name"]
            info = entry["info"]
            # Command must capture name and info by value via default args
            sub.add_command(
                label=name,
                command=lambda n=name, i=info: show_glossary_popup(n, i),
            )


def build_ui():
    global label, ips_label, click_btn, root

    root = tk.Tk()
    root.title("Instruction Clicker")

    processor_img = tk.PhotoImage(file="Processor.png")

    # ── Glossary toolbar (top-left) ──────────────────────────────────────────
    toolbar = tk.Frame(root, bd=1, relief="groove")
    toolbar.pack(fill="x", padx=2, pady=(2, 0))
    build_glossary_menu(toolbar)

    # ── Header ──────────────────────────────────────────────────────────────
    label = tk.Label(root, text="Instructions: 0x0", font=("Arial", 16))
    label.pack()

    # Tooltip mapping op-suffix → full name
    _OPS_TOOLTIP = (
        "op  = operation (< 1,000)\n"
        "Kop = Kilo-operation  (×1,000)\n"
        "Mop = Mega-operation  (×1,000,000)\n"
        "Gop = Giga-operation  (×1,000,000,000)\n"
        "Top = Tera-operation  (×1,000,000,000,000)\n"
        "Pop = Peta-operation  (×1,000,000,000,000,000)\n"
        "Eop = Exa-operation   (×1,000,000,000,000,000,000)"
    )
    Tooltip(label, _OPS_TOOLTIP)

    ips_label = tk.Label(root, text="IPS: 0   Click: ×1", font=("Arial", 13))
    ips_label.pack()

    click_btn = tk.Button(root, image=processor_img, command=on_processor_click)
    click_btn.pack(pady=4)
    click_btn.image = processor_img   # prevent GC

    # ── DEBUG ────────────────────────────────────────────────────────────────
    def debug_give_money() -> None:
        global instructions
        instructions += 1_000_000_000
        update_display()

    tk.Button(
        root,
        text="[DEBUG] +1 Billion Instructions",
        command=debug_give_money,
        fg="red",
        font=("Arial", 9, "italic"),
    ).pack(pady=(0, 4))

    # ── Generators section ───────────────────────────────────────────────────
    tk.Label(root, text="─── Generators ───", font=("Arial", 11, "bold")).pack(pady=(6, 0))

    # Quantity selector bar
    qty_frame = tk.Frame(root)
    qty_frame.pack(pady=(2, 4))
    tk.Label(qty_frame, text="Buy:", font=("Arial", 9)).pack(side="left", padx=(0, 4))
    for qty_val, qty_label in [(1, "1×"), (2, "2×"), (5, "5×"), (10, "10×"),
                                (25, "25×"), (100, "100×"), (-1, "MAX")]:
        btn = tk.Button(
            qty_frame,
            text=qty_label,
            width=4,
            font=("Arial", 8, "bold"),
            command=lambda q=qty_val: set_buy_quantity(q),
        )
        btn.pack(side="left", padx=1)
        qty_buttons[qty_val] = btn

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

        gen_rows[g["name"]] = {
            "frame": frame,
            "btn": btn,
            "count_lbl": count_lbl,
            "mult_lbl": mult_lbl,
        }

    # ── Multipliers section ──────────────────────────────────────────────────
    tk.Label(root, text="─── Multipliers ───", font=("Arial", 11, "bold")).pack(pady=(8, 0))

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

        # Attach hover tooltip with game-mechanic description
        Tooltip(btn, m["tooltip"])

        mult_rows[m["name"]] = {"frame": frame, "btn": btn}

    return root, processor_img


# ---------------------------------------------------------------------------
# ── Entry point ───────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root, _img = build_ui()
    update_display()
    auto_increment()
    root.mainloop()