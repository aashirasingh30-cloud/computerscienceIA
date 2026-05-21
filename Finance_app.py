# ============================================
# FINANCETRACKER PRO — IB SL CS IA
# v3 — Home + Dashboard + Transactions (Fixed)
# ============================================
#
# Dependencies:
#   pip install matplotlib pandas
#
# ============================================

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import rcParams
from datetime import datetime

rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.spines.top'] = False
rcParams['axes.spines.right'] = False

# ──────────────────────────────────────────
# COLOUR PALETTE
# ──────────────────────────────────────────
C = {
    "bg":          "#0f172a",
    "surface":     "#1e293b",
    "surface2":    "#273449",
    "border":      "#334155",
    "accent":      "#38bdf8",
    "green":       "#4ade80",
    "red":         "#f87171",
    "yellow":      "#fbbf24",
    "text":        "#f1f5f9",
    "muted":       "#94a3b8",
    "white":       "#ffffff",
    "btn":         "#38bdf8",
    "btn_hover":   "#0ea5e9",
    "chart_bg":    "#1e293b",
}

PIE_COLOURS = ["#38bdf8", "#4ade80", "#fbbf24", "#f87171",
               "#a78bfa", "#fb923c", "#34d399", "#f472b6"]

# ──────────────────────────────────────────
# DATA
# ──────────────────────────────────────────
transactions = []
_txn_id_counter = 0

EXCHANGE_RATES = {
    "USD": 1.00,
    "EUR": 0.92,
    "GBP": 0.78,
    "AED": 3.67,
    "INR": 83.00,
}

CURRENCY_OPTIONS = {
    "USD ($)":    ("USD", "$"),
    "EUR (€)":    ("EUR", "€"),
    "GBP (£)":    ("GBP", "£"),
    "AED (د.إ)": ("AED", "د.إ"),
    "INR (₹)":   ("INR", "₹"),
}

SAMPLE_MONTHS           = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
SAMPLE_MONTHLY_INCOME   = [3200, 2800, 3500, 2900, 3800, 3400]
SAMPLE_MONTHLY_EXPENSES = [2500, 2200, 2600, 2100, 3000, 2700]

EXPENSE_CATEGORIES = [
    "Food & Dining", "Shopping", "Transportation", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel", "Freelance", "Other"
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other"]

# ──────────────────────────────────────────
# ROOT WINDOW
# ──────────────────────────────────────────
root = tk.Tk()
root.title("FinanceTracker PRO")
root.geometry("1280x860")
root.minsize(1000, 720)
root.configure(bg=C["bg"])
root.option_add("*Font", "Helvetica 10")

selected_currency_var = tk.StringVar(root, value="USD ($)")

# ──────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────
def get_currency():
    return CURRENCY_OPTIONS[selected_currency_var.get()]

def to_display(usd_amount):
    code, _ = get_currency()
    return usd_amount * EXCHANGE_RATES[code]

def to_usd(display_amount):
    code, _ = get_currency()
    return display_amount / EXCHANGE_RATES[code]

def fmt(amount):
    _, sym = get_currency()
    return f"{sym}{amount:,.2f}"

def today_str():
    return datetime.now().strftime("%d/%m/%Y")

def next_id():
    global _txn_id_counter
    _txn_id_counter += 1
    return _txn_id_counter


# ──────────────────────────────────────────
# WIDGET HELPERS
# ──────────────────────────────────────────
def label(parent, text, size=10, weight="normal", color=None, **kw):
    return tk.Label(
        parent, text=text,
        bg=parent["bg"], fg=color or C["text"],
        font=("Helvetica", size, weight), **kw,
    )

def card(parent, **kw):
    return tk.Frame(
        parent, bg=C["surface"],
        highlightthickness=1,
        highlightbackground=C["border"], **kw,
    )

def entry_widget(parent, width=22, **kw):
    return tk.Entry(
        parent, width=width,
        bg=C["surface2"], fg=C["text"],
        insertbackground=C["text"],
        relief="flat", bd=0,
        font=("Helvetica", 11),
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"], **kw,
    )

def btn(parent, text, command, color=None, width=None):
    bg_col = color or C["btn"]
    b = tk.Button(
        parent, text=text, command=command,
        bg=bg_col, fg=C["bg"],
        activebackground=C["btn_hover"],
        activeforeground=C["bg"],
        font=("Helvetica", 10, "bold"),
        relief="flat", bd=0, padx=16, pady=9,
        cursor="hand2", width=width or 0,
    )
    b.bind("<Enter>", lambda e: b.config(bg=C["btn_hover"]))
    b.bind("<Leave>", lambda e: b.config(bg=bg_col))
    return b


# ══════════════════════════════════════════
# FRAME STACK (all frames live here)
# ══════════════════════════════════════════
home_frame  = tk.Frame(root, bg=C["bg"])
main_frame  = tk.Frame(root, bg=C["bg"])
txn_page    = tk.Frame(root, bg=C["bg"])   # standalone Transactions page

for f in (home_frame, main_frame, txn_page):
    f.place(relx=0, rely=0, relwidth=1, relheight=1)


def show_frame(frame):
    frame.lift()


# ══════════════════════════════════════════
# ░░  HOME / SPLASH SCREEN  ░░
# ══════════════════════════════════════════
def build_home():
    bg_canvas = tk.Canvas(home_frame, bg=C["bg"], highlightthickness=0)
    bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    def draw_grid(event=None):
        bg_canvas.delete("grid")
        w, h = bg_canvas.winfo_width(), bg_canvas.winfo_height()
        for x in range(0, w, 60):
            bg_canvas.create_line(x, 0, x, h, fill="#1a2744", tags="grid")
        for y in range(0, h, 60):
            bg_canvas.create_line(0, y, w, y, fill="#1a2744", tags="grid")

    bg_canvas.bind("<Configure>", draw_grid)

    centre = tk.Frame(home_frame, bg=C["bg"])
    centre.place(relx=0.5, rely=0.5, anchor="center")

    tk.Frame(centre, bg=C["accent"], height=3, width=80).pack(pady=(0, 24))

    logo_row = tk.Frame(centre, bg=C["bg"])
    logo_row.pack()
    tk.Label(logo_row, text="◈", bg=C["bg"],
             fg=C["accent"], font=("Helvetica", 48, "bold")).pack(side="left")
    tk.Label(logo_row, text=" FinanceTracker", bg=C["bg"],
             fg=C["white"], font=("Helvetica", 40, "bold")).pack(side="left")
    tk.Label(logo_row, text=" PRO", bg=C["bg"],
             fg=C["accent"], font=("Helvetica", 40, "bold")).pack(side="left")

    tk.Label(centre, text="Your intelligent personal finance dashboard",
             bg=C["bg"], fg=C["muted"], font=("Helvetica", 13)).pack(pady=(10, 4))
    tk.Label(centre, text="IB SL Computer Science  •  Internal Assessment",
             bg=C["bg"], fg=C["border"], font=("Helvetica", 10)).pack(pady=(0, 40))

    pills_row = tk.Frame(centre, bg=C["bg"])
    pills_row.pack(pady=(0, 50))

    features = [
        ("↑↓", "Track Income & Expenses"),
        ("◎",  "Net Balance Analytics"),
        ("⊞",  "Transaction History"),
        ("◑",  "Multi-Currency Support"),
    ]
    for icon, text_val in features:
        pill = tk.Frame(pills_row, bg=C["surface"],
                        highlightthickness=1, highlightbackground=C["border"])
        pill.pack(side="left", padx=8, ipadx=14, ipady=10)
        tk.Label(pill, text=icon, bg=C["surface"],
                 fg=C["accent"], font=("Helvetica", 16, "bold")).pack()
        tk.Label(pill, text=text_val, bg=C["surface"],
                 fg=C["muted"], font=("Helvetica", 9)).pack()

    enter_btn = tk.Button(
        centre, text="  Enter Dashboard  →",
        command=lambda: show_frame(main_frame),
        bg=C["accent"], fg=C["bg"],
        font=("Helvetica", 13, "bold"),
        relief="flat", bd=0, padx=32, pady=14, cursor="hand2",
    )
    enter_btn.pack()
    enter_btn.bind("<Enter>", lambda e: enter_btn.config(bg=C["btn_hover"]))
    enter_btn.bind("<Leave>", lambda e: enter_btn.config(bg=C["accent"]))

    tk.Label(home_frame,
             text="FinanceTracker PRO  •  IB SL CS IA  •  All amounts stored in USD",
             bg=C["bg"], fg=C["border"],
             font=("Helvetica", 8)).place(relx=0.5, rely=0.97, anchor="center")


# ══════════════════════════════════════════
# ░░  SHARED HEADER BUILDER  ░░
# ══════════════════════════════════════════
def build_header(parent, active_tab="dashboard"):
    """Builds a top nav bar. active_tab: 'dashboard' or 'transactions'"""
    header = tk.Frame(parent, bg=C["surface"],
                      highlightthickness=1, highlightbackground=C["border"])
    header.pack(fill="x", side="top")
    header.grid_columnconfigure(1, weight=1)

    # Logo
    logo_f = tk.Frame(header, bg=C["surface"])
    logo_f.pack(side="left", padx=24, pady=12)
    tk.Label(logo_f, text="◈", bg=C["surface"],
             fg=C["accent"], font=("Helvetica", 20, "bold")).pack(side="left")
    tk.Label(logo_f, text="  FinanceTracker", bg=C["surface"],
             fg=C["white"], font=("Helvetica", 15, "bold")).pack(side="left")
    tk.Label(logo_f, text=" PRO", bg=C["surface"],
             fg=C["accent"], font=("Helvetica", 15, "bold")).pack(side="left")

    # Right side controls
    right_f = tk.Frame(header, bg=C["surface"])
    right_f.pack(side="right", padx=24, pady=12)

    # Currency selector
    tk.Label(right_f, text="Currency  ", bg=C["surface"],
             fg=C["muted"], font=("Helvetica", 10)).pack(side="left")
    currency_combo = ttk.Combobox(
        right_f, textvariable=selected_currency_var,
        values=list(CURRENCY_OPTIONS.keys()),
        state="readonly", width=13, style="Dark.TCombobox",
        font=("Helvetica", 10),
    )
    currency_combo.pack(side="left", padx=(0, 16))
    currency_combo.bind("<<ComboboxSelected>>", lambda _: refresh_all())

    # Home button
    tk.Button(
        right_f, text="⌂  Home",
        command=lambda: show_frame(home_frame),
        bg=C["surface2"], fg=C["muted"],
        font=("Helvetica", 9), relief="flat", bd=0,
        padx=10, pady=5, cursor="hand2",
    ).pack(side="left")

    # Nav tabs (center-ish)
    nav_f = tk.Frame(header, bg=C["surface"])
    nav_f.pack(side="left", padx=30, pady=8)

    def _nav_btn(text, cmd, is_active):
        bg = C["accent"] if is_active else C["surface2"]
        fg = C["bg"] if is_active else C["muted"]
        b = tk.Button(nav_f, text=text, command=cmd,
                      bg=bg, fg=fg,
                      font=("Helvetica", 10, "bold"),
                      relief="flat", bd=0, padx=20, pady=7, cursor="hand2")
        b.pack(side="left", padx=4)
        return b

    _nav_btn("📊  Dashboard",    lambda: (show_frame(main_frame), refresh_all()),
             active_tab == "dashboard")
    _nav_btn("💳  Transactions", lambda: (show_frame(txn_page), refresh_txn_page()),
             active_tab == "transactions")

    return header


# ══════════════════════════════════════════
# ░░  MAIN APP (DASHBOARD)  ░░
# ══════════════════════════════════════════
def build_main_frame():
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    build_header(main_frame, active_tab="dashboard")

    # ── Summary Cards ──
    cards_outer = tk.Frame(main_frame, bg=C["bg"])
    cards_outer.pack(fill="x", padx=20, pady=(18, 0))
    for i in range(4):
        cards_outer.grid_columnconfigure(i, weight=1)

    def _make_summary_card(parent, col, icon, title, color):
        f = card(parent, padx=20, pady=16)
        f.grid(row=0, column=col, padx=8, sticky="ew")
        top = tk.Frame(f, bg=C["surface"])
        top.pack(fill="x")
        tk.Label(top, text=icon, bg=C["surface"],
                 fg=color, font=("Helvetica", 18)).pack(side="left")
        tk.Label(top, text=f"  {title}", bg=C["surface"],
                 fg=C["muted"], font=("Helvetica", 10, "bold")).pack(side="left", pady=(4, 0))
        val = tk.Label(f, text="$0.00", bg=C["surface"],
                       fg=color, font=("Helvetica", 22, "bold"))
        val.pack(anchor="w", pady=(6, 2))
        sub = tk.Label(f, text="—", bg=C["surface"],
                       fg=C["muted"], font=("Helvetica", 9))
        sub.pack(anchor="w")
        return val, sub

    global income_val, income_sub, expense_val, expense_sub
    global balance_val, balance_sub, txn_val, txn_sub

    income_val,  income_sub  = _make_summary_card(cards_outer, 0, "↑", "TOTAL INCOME",   C["green"])
    expense_val, expense_sub = _make_summary_card(cards_outer, 1, "↓", "TOTAL EXPENSES", C["red"])
    balance_val, balance_sub = _make_summary_card(cards_outer, 2, "◎", "NET BALANCE",    C["yellow"])
    txn_val,     txn_sub     = _make_summary_card(cards_outer, 3, "⊞", "TRANSACTIONS",   C["accent"])

    # ── View Transactions shortcut ──
    go_txn_bar = tk.Frame(main_frame, bg=C["bg"])
    go_txn_bar.pack(fill="x", padx=20, pady=(10, 0))
    go_btn = tk.Button(
        go_txn_bar,
        text="💳  View Transaction History →",
        command=lambda: (show_frame(txn_page), refresh_txn_page()),
        bg=C["surface"], fg=C["accent"],
        font=("Helvetica", 10, "bold"),
        relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
        highlightthickness=1, highlightbackground=C["border"],
    )
    go_btn.pack(side="right")
    go_btn.bind("<Enter>", lambda e: go_btn.config(bg=C["surface2"]))
    go_btn.bind("<Leave>", lambda e: go_btn.config(bg=C["surface"]))

    # ── Content area: left panel + charts ──
    content = tk.Frame(main_frame, bg=C["bg"])
    content.pack(fill="both", expand=True, padx=20, pady=12)
    content.grid_columnconfigure(1, weight=1)
    content.grid_rowconfigure(0, weight=1)

    # Left panel (add income / expense)
    left_panel = tk.Frame(content, bg=C["bg"])
    left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 14))

    # Income card
    inc_card = card(left_panel, padx=20, pady=18)
    inc_card.pack(fill="x", pady=(0, 12))

    label(inc_card, "Add Income", 13, "bold", C["green"]).pack(anchor="w")
    tk.Frame(inc_card, bg=C["border"], height=1).pack(fill="x", pady=8)
    label(inc_card, "Amount", color=C["muted"]).pack(anchor="w")
    global income_entry, income_desc_entry, income_cat_var
    income_entry = entry_widget(inc_card, width=26)
    income_entry.pack(fill="x", pady=(3, 8))
    label(inc_card, "Category", color=C["muted"]).pack(anchor="w")
    income_cat_var = tk.StringVar(root, value=INCOME_CATEGORIES[0])
    ttk.Combobox(inc_card, textvariable=income_cat_var,
                 values=INCOME_CATEGORIES, state="readonly", width=24,
                 style="Dark.TCombobox", font=("Helvetica", 10)).pack(fill="x", pady=(3, 8))
    label(inc_card, "Description (optional)", color=C["muted"]).pack(anchor="w")
    income_desc_entry = entry_widget(inc_card, width=26)
    income_desc_entry.pack(fill="x", pady=(3, 10))
    inc_btn = btn(inc_card, "＋  Add Income", add_income, color=C["green"])
    inc_btn.pack(fill="x")

    # Expense card
    exp_card = card(left_panel, padx=20, pady=18)
    exp_card.pack(fill="x", pady=(0, 12))

    label(exp_card, "Add Expense", 13, "bold", C["red"]).pack(anchor="w")
    tk.Frame(exp_card, bg=C["border"], height=1).pack(fill="x", pady=8)
    label(exp_card, "Amount", color=C["muted"]).pack(anchor="w")
    global expense_amount_entry, expense_desc_entry, category_var
    expense_amount_entry = entry_widget(exp_card, width=26)
    expense_amount_entry.pack(fill="x", pady=(3, 8))
    label(exp_card, "Category", color=C["muted"]).pack(anchor="w")
    category_var = tk.StringVar(root, value=EXPENSE_CATEGORIES[0])
    ttk.Combobox(exp_card, textvariable=category_var,
                 values=EXPENSE_CATEGORIES, state="readonly", width=24,
                 style="Dark.TCombobox", font=("Helvetica", 10)).pack(fill="x", pady=(3, 8))
    label(exp_card, "Description (optional)", color=C["muted"]).pack(anchor="w")
    expense_desc_entry = entry_widget(exp_card, width=26)
    expense_desc_entry.pack(fill="x", pady=(3, 10))
    btn(exp_card, "＋  Add Expense", add_expense, color=C["red"]).pack(fill="x")

    # Quick actions
    qa_card = card(left_panel, padx=20, pady=18)
    qa_card.pack(fill="x")
    label(qa_card, "Quick Actions", 11, "bold").pack(anchor="w", pady=(0, 10))
    btn(qa_card, "↺  Refresh Charts", refresh_charts).pack(fill="x", pady=(0, 6))
    btn(qa_card, "✕  Clear All Data", clear_all, color=C["border"]).pack(fill="x")

    # Right panel — charts
    right_panel = card(content)
    right_panel.grid(row=0, column=1, sticky="nsew")
    right_panel.grid_rowconfigure(1, weight=1)
    right_panel.grid_columnconfigure(0, weight=1)

    label(right_panel, "Analytics", 13, "bold").grid(
        row=0, column=0, sticky="w", padx=20, pady=(16, 4))

    global fig, ax_line, ax_pie, chart_canvas
    fig = Figure(figsize=(8, 5), dpi=100)
    fig.patch.set_facecolor(C["chart_bg"])
    ax_line = fig.add_subplot(121)
    ax_pie  = fig.add_subplot(122)

    chart_canvas = FigureCanvasTkAgg(fig, master=right_panel)
    chart_widget = chart_canvas.get_tk_widget()
    chart_widget.configure(bg=C["surface"])
    chart_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))

    # Status bar
    status_frame = tk.Frame(main_frame, bg=C["surface"],
                             highlightthickness=1, highlightbackground=C["border"])
    status_frame.pack(fill="x", side="bottom")
    global status_var
    status_var = tk.StringVar(root, value="Ready")
    tk.Label(status_frame, textvariable=status_var,
             bg=C["surface"], fg=C["muted"],
             font=("Helvetica", 9), anchor="w").pack(side="left", padx=16, pady=5)
    tk.Label(status_frame,
             text="IB SL CS IA  •  FinanceTracker PRO  •  v3",
             bg=C["surface"], fg=C["border"],
             font=("Helvetica", 9)).pack(side="right", padx=16)

    # Keyboard shortcuts
    income_entry.bind("<Return>", lambda _: add_income())
    expense_amount_entry.bind("<Return>", lambda _: expense_desc_entry.focus_set())
    expense_desc_entry.bind("<Return>", lambda _: add_expense())


# ══════════════════════════════════════════
# ░░  TRANSACTIONS PAGE  ░░
# ══════════════════════════════════════════
def build_txn_page():
    """Builds the standalone full-screen Transactions page."""

    build_header(txn_page, active_tab="transactions")

    # ── Page title bar ──
    title_bar = tk.Frame(txn_page, bg=C["bg"])
    title_bar.pack(fill="x", padx=28, pady=(20, 0))

    left_title = tk.Frame(title_bar, bg=C["bg"])
    left_title.pack(side="left")
    tk.Label(left_title, text="Transactions", bg=C["bg"],
             fg=C["white"], font=("Helvetica", 22, "bold")).pack(anchor="w")
    tk.Label(left_title, text="Track every financial movement", bg=C["bg"],
             fg=C["muted"], font=("Helvetica", 10)).pack(anchor="w")

    add_btn = tk.Button(
        title_bar, text="＋  Add Transaction",
        command=open_add_transaction_dialog,
        bg=C["accent"], fg=C["bg"],
        font=("Helvetica", 10, "bold"),
        relief="flat", bd=0, padx=18, pady=10,
        cursor="hand2",
    )
    add_btn.pack(side="right")
    add_btn.bind("<Enter>", lambda e: add_btn.config(bg=C["btn_hover"]))
    add_btn.bind("<Leave>", lambda e: add_btn.config(bg=C["accent"]))

    # ── Summary cards ──
    cards_row = tk.Frame(txn_page, bg=C["bg"])
    cards_row.pack(fill="x", padx=20, pady=(16, 0))
    for i in range(3):
        cards_row.grid_columnconfigure(i, weight=1)

    global txn_page_inc_val, txn_page_exp_val, txn_page_bal_val

    def _mini_card(parent, col, icon, title, color):
        f = card(parent, padx=18, pady=14)
        f.grid(row=0, column=col, padx=8, sticky="ew")
        row_f = tk.Frame(f, bg=C["surface"])
        row_f.pack(fill="x")
        # Icon circle
        ic = tk.Label(row_f, text=icon, bg=C["surface2"],
                      fg=color, font=("Helvetica", 14, "bold"),
                      width=3, pady=4)
        ic.pack(side="left")
        info = tk.Frame(row_f, bg=C["surface"])
        info.pack(side="left", padx=12)
        tk.Label(info, text=title, bg=C["surface"],
                 fg=C["muted"], font=("Helvetica", 9, "bold")).pack(anchor="w")
        val = tk.Label(info, text="$0.00", bg=C["surface"],
                       fg=color, font=("Helvetica", 18, "bold"))
        val.pack(anchor="w")
        return val

    txn_page_inc_val = _mini_card(cards_row, 0, "↑", "TOTAL INCOME",   C["green"])
    txn_page_exp_val = _mini_card(cards_row, 1, "↓", "TOTAL EXPENSES", C["red"])
    txn_page_bal_val = _mini_card(cards_row, 2, "▣", "NET BALANCE",    C["yellow"])

    # ── Recent Transactions section ──
    tbl_outer = card(txn_page)
    tbl_outer.pack(fill="both", expand=True, padx=28, pady=16)
    tbl_outer.grid_rowconfigure(2, weight=1)
    tbl_outer.grid_columnconfigure(0, weight=1)

    # Section heading + toolbar
    top_bar = tk.Frame(tbl_outer, bg=C["surface"])
    top_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))

    tk.Label(top_bar, text="Recent Transactions", bg=C["surface"],
             fg=C["white"], font=("Helvetica", 13, "bold")).pack(side="left")

    # Filter / search controls (right side)
    ctrl_f = tk.Frame(top_bar, bg=C["surface"])
    ctrl_f.pack(side="right")

    global txn_filter_var, txn_search_var
    txn_filter_var = tk.StringVar(root, value="All")
    txn_search_var = tk.StringVar(root)

    tk.Label(ctrl_f, text="Filter:", bg=C["surface"],
             fg=C["muted"], font=("Helvetica", 9)).pack(side="left", padx=(0, 4))
    filter_cb = ttk.Combobox(ctrl_f, textvariable=txn_filter_var,
                              values=["All", "Income", "Expense"],
                              state="readonly", width=9,
                              style="Dark.TCombobox", font=("Helvetica", 9))
    filter_cb.pack(side="left", padx=(0, 10))
    filter_cb.bind("<<ComboboxSelected>>", lambda _: refresh_txn_page())

    tk.Label(ctrl_f, text="Search:", bg=C["surface"],
             fg=C["muted"], font=("Helvetica", 9)).pack(side="left", padx=(0, 4))
    s_entry = tk.Entry(ctrl_f, textvariable=txn_search_var,
                       bg=C["surface2"], fg=C["text"],
                       insertbackground=C["text"],
                       relief="flat", bd=0, font=("Helvetica", 9),
                       highlightthickness=1,
                       highlightbackground=C["border"],
                       highlightcolor=C["accent"], width=18)
    s_entry.pack(side="left", padx=(0, 6))
    s_entry.bind("<Return>", lambda _: refresh_txn_page())

    tk.Button(ctrl_f, text="🔍", command=refresh_txn_page,
              bg=C["surface2"], fg=C["accent"],
              font=("Helvetica", 9), relief="flat", bd=0,
              padx=6, pady=4, cursor="hand2").pack(side="left", padx=(0, 4))
    tk.Button(ctrl_f, text="✕ Clear",
              command=lambda: (txn_search_var.set(""), txn_filter_var.set("All"), refresh_txn_page()),
              bg=C["surface2"], fg=C["muted"],
              font=("Helvetica", 9), relief="flat", bd=0,
              padx=6, pady=4, cursor="hand2").pack(side="left")

    # Separator
    tk.Frame(tbl_outer, bg=C["border"], height=1).grid(
        row=1, column=0, sticky="ew", padx=0, pady=(10, 0))

    # Treeview
    COLS     = ("Date", "Type", "Category", "Description", "Amount", "Actions")
    COL_WIDTHS = (110,   90,    140,         240,           110,      80)

    tree_frame = tk.Frame(tbl_outer, bg=C["surface"])
    tree_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    global txn_tree2
    txn_tree2 = ttk.Treeview(
        tree_frame,
        columns=COLS,
        show="headings",
        selectmode="browse",
        style="Finance.Treeview",
    )

    col_anchors = {"Amount": "e", "Actions": "center"}
    for col, w in zip(COLS, COL_WIDTHS):
        txn_tree2.heading(col, text=col.upper(),
                          command=lambda c=col: sort_txn2(c))
        txn_tree2.column(col, width=w, anchor=col_anchors.get(col, "w"), minwidth=40)

    scroll2 = ttk.Scrollbar(tree_frame, orient="vertical", command=txn_tree2.yview)
    txn_tree2.configure(yscrollcommand=scroll2.set)
    txn_tree2.grid(row=0, column=0, sticky="nsew")
    scroll2.grid(row=0, column=1, sticky="ns")

    txn_tree2.tag_configure("income",      background="#1a2e1a", foreground=C["green"])
    txn_tree2.tag_configure("expense",     background="#2e1a1a", foreground=C["red"])
    txn_tree2.tag_configure("income_alt",  background="#192b19", foreground=C["green"])
    txn_tree2.tag_configure("expense_alt", background="#2b1919", foreground=C["red"])

    # Bind delete on row selection via right-click or Delete key
    txn_tree2.bind("<Delete>", lambda _: delete_selected_txn2())
    txn_tree2.bind("<Double-1>", on_txn_double_click)

    # Footer summary
    global txn2_footer_label
    footer_f = tk.Frame(tbl_outer, bg=C["surface"],
                         highlightthickness=1, highlightbackground=C["border"])
    footer_f.grid(row=3, column=0, sticky="ew")
    txn2_footer_label = tk.Label(footer_f, text="",
                                  bg=C["surface"], fg=C["muted"],
                                  font=("Helvetica", 9), anchor="w")
    txn2_footer_label.pack(side="left", padx=14, pady=6)

    # Delete selected button in footer
    tk.Button(footer_f, text="🗑  Delete Selected",
              command=delete_selected_txn2,
              bg=C["surface"], fg=C["red"],
              font=("Helvetica", 9, "bold"), relief="flat", bd=0,
              padx=10, pady=5, cursor="hand2").pack(side="right", padx=10)


_sort2_state = {"col": "Date", "reverse": True}


def sort_txn2(col):
    if _sort2_state["col"] == col:
        _sort2_state["reverse"] = not _sort2_state["reverse"]
    else:
        _sort2_state["col"] = col
        _sort2_state["reverse"] = False
    refresh_txn_page()


def refresh_txn_page():
    """Refresh the standalone Transactions page table and summary cards."""
    _, sym = get_currency()
    code, _ = get_currency()
    rate = EXCHANGE_RATES[code]

    # Update summary cards
    total_inc = to_display(sum(t["amount_usd"] for t in transactions if t["type"] == "Income"))
    total_exp = to_display(sum(t["amount_usd"] for t in transactions if t["type"] == "Expense"))
    net = total_inc - total_exp
    txn_page_inc_val.config(text=fmt(total_inc))
    txn_page_exp_val.config(text=fmt(total_exp))
    txn_page_bal_val.config(text=fmt(net), fg=C["green"] if net >= 0 else C["red"])

    # Clear table
    for row in txn_tree2.get_children():
        txn_tree2.delete(row)

    ftype  = txn_filter_var.get()
    search = txn_search_var.get().strip().lower()

    visible = []
    for t in transactions:
        if ftype != "All" and t["type"] != ftype:
            continue
        haystack = (t["category"] + t["description"] + t["type"]).lower()
        if search and search not in haystack:
            continue
        visible.append(t)

    # Sort
    col = _sort2_state["col"]
    rev = _sort2_state["reverse"]
    key_map = {
        "Date":        lambda t: t["date"],
        "Type":        lambda t: t["type"],
        "Category":    lambda t: t["category"],
        "Description": lambda t: t["description"],
        "Amount":      lambda t: t["amount_usd"],
        "Actions":     lambda t: t["id"],
    }
    visible.sort(key=key_map.get(col, key_map["Date"]), reverse=rev)

    shown_inc = shown_exp = 0.0
    for i, t in enumerate(visible):
        disp = t["amount_usd"] * rate
        if t["type"] == "Expense":
            amt_str = f"-{sym}{disp:,.2f}"
            shown_exp += disp
            tag_base = "expense"
        else:
            amt_str = f"+{sym}{disp:,.2f}"
            shown_inc += disp
            tag_base = "income"
        tag = tag_base if i % 2 == 0 else tag_base + "_alt"

        txn_tree2.insert("", "end",
                         iid=str(t["id"]),
                         values=(t["date"], t["type"], t["category"],
                                 t["description"] or "—", amt_str, "🗑 Delete"),
                         tags=(tag,))

    net_shown = shown_inc - shown_exp
    txn2_footer_label.config(
        text=(f"Showing {len(visible)} record(s)   |   "
              f"Income: {sym}{shown_inc:,.2f}   "
              f"Expenses: {sym}{shown_exp:,.2f}   "
              f"Net: {sym}{net_shown:,.2f}")
    )


def on_txn_double_click(event):
    """Delete row on double-click of the Actions column."""
    region = txn_tree2.identify_region(event.x, event.y)
    col    = txn_tree2.identify_column(event.x)
    if region == "cell" and col == "#6":   # Actions column
        delete_selected_txn2()


def delete_selected_txn2():
    sel = txn_tree2.selection()
    if not sel:
        messagebox.showinfo("No Selection",
                            "Please select a transaction to delete.",
                            parent=root)
        return
    txn_id = int(sel[0])
    if not messagebox.askyesno("Delete Transaction",
                                f"Delete transaction #{txn_id}?",
                                parent=root):
        return
    global transactions
    transactions = [x for x in transactions if x["id"] != txn_id]
    refresh_all()
    refresh_txn_page()
    set_status(f"Transaction #{txn_id} deleted.")


# ── Add Transaction Dialog ──
def open_add_transaction_dialog():
    dlg = tk.Toplevel(root)
    dlg.title("Add Transaction")
    dlg.geometry("420x480")
    dlg.resizable(False, False)
    dlg.configure(bg=C["bg"])
    dlg.grab_set()

    tk.Label(dlg, text="Add Transaction", bg=C["bg"],
             fg=C["white"], font=("Helvetica", 16, "bold")).pack(pady=(24, 4))
    tk.Label(dlg, text="Record a new income or expense", bg=C["bg"],
             fg=C["muted"], font=("Helvetica", 10)).pack(pady=(0, 20))

    form = tk.Frame(dlg, bg=C["bg"])
    form.pack(padx=32, fill="x")

    def lbl(t):
        tk.Label(form, text=t, bg=C["bg"], fg=C["muted"],
                 font=("Helvetica", 10)).pack(anchor="w", pady=(8, 2))

    # Type
    lbl("Transaction Type")
    type_var = tk.StringVar(dlg, value="Expense")
    type_row = tk.Frame(form, bg=C["bg"])
    type_row.pack(fill="x")
    for t_val in ("Income", "Expense"):
        tk.Radiobutton(
            type_row, text=t_val, variable=type_var, value=t_val,
            bg=C["bg"], fg=C["text"], selectcolor=C["surface2"],
            activebackground=C["bg"], activeforeground=C["accent"],
            font=("Helvetica", 10), cursor="hand2",
        ).pack(side="left", padx=(0, 20))

    # Amount
    lbl("Amount")
    amt_e = entry_widget(form, width=36)
    amt_e.pack(fill="x")

    # Category — updates based on type
    lbl("Category")
    cat_var_dlg = tk.StringVar(dlg, value=EXPENSE_CATEGORIES[0])
    cat_cb = ttk.Combobox(form, textvariable=cat_var_dlg,
                           values=EXPENSE_CATEGORIES, state="readonly",
                           width=34, style="Dark.TCombobox", font=("Helvetica", 10))
    cat_cb.pack(fill="x")

    def update_categories(*_):
        if type_var.get() == "Income":
            cat_cb["values"] = INCOME_CATEGORIES
            cat_var_dlg.set(INCOME_CATEGORIES[0])
        else:
            cat_cb["values"] = EXPENSE_CATEGORIES
            cat_var_dlg.set(EXPENSE_CATEGORIES[0])
    type_var.trace_add("write", update_categories)

    # Description
    lbl("Description (optional)")
    desc_e = entry_widget(form, width=36)
    desc_e.pack(fill="x")

    def do_add():
        raw = amt_e.get().strip()
        if not raw:
            messagebox.showerror("Missing Value", "Please enter an amount.", parent=dlg)
            amt_e.focus_set(); return
        try:
            amount = float(raw)
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter a positive number.", parent=dlg)
            amt_e.focus_set(); return

        usd = to_usd(amount)
        txn = {
            "id":          next_id(),
            "date":        today_str(),
            "type":        type_var.get(),
            "category":    cat_var_dlg.get(),
            "description": desc_e.get().strip(),
            "amount_usd":  usd,
        }
        transactions.append(txn)
        refresh_all()
        refresh_txn_page()
        _, sym = get_currency()
        set_status(f"✓ {txn['type']} of {sym}{amount:,.2f} added.")
        dlg.destroy()

    tk.Frame(form, bg=C["border"], height=1).pack(fill="x", pady=16)
    b = tk.Button(form, text="＋  Save Transaction", command=do_add,
                  bg=C["accent"], fg=C["bg"],
                  font=("Helvetica", 11, "bold"),
                  relief="flat", bd=0, padx=20, pady=10, cursor="hand2")
    b.pack(fill="x")
    b.bind("<Enter>", lambda e: b.config(bg=C["btn_hover"]))
    b.bind("<Leave>", lambda e: b.config(bg=C["accent"]))

    desc_e.bind("<Return>", lambda _: do_add())


# ══════════════════════════════════════════
# CORE LOGIC
# ══════════════════════════════════════════
def set_status(msg):
    status_var.set(msg)
    root.after(3000, lambda: status_var.set("Ready"))


def refresh_summary():
    code, sym = get_currency()
    total_inc = to_display(sum(r["amount_usd"] for r in transactions if r["type"] == "Income"))
    total_exp = to_display(sum(r["amount_usd"] for r in transactions if r["type"] == "Expense"))
    balance   = total_inc - total_exp
    txns      = len(transactions)

    income_val.config(text=fmt(total_inc))
    expense_val.config(text=fmt(total_exp))
    balance_val.config(text=fmt(balance),
                       fg=C["green"] if balance >= 0 else C["red"])
    txn_val.config(text=str(txns))

    inc_count = sum(1 for r in transactions if r["type"] == "Income")
    exp_count = sum(1 for r in transactions if r["type"] == "Expense")
    income_sub.config(text=f"{inc_count} entr{'y' if inc_count == 1 else 'ies'}")
    expense_sub.config(text=f"{exp_count} entr{'y' if exp_count == 1 else 'ies'}")
    pct = (total_exp / total_inc * 100) if total_inc else 0
    balance_sub.config(text=f"{pct:.1f}% of income spent")
    txn_sub.config(text="total records")


def refresh_charts():
    ax_line.clear()
    ax_pie.clear()

    for ax in (ax_line, ax_pie):
        ax.set_facecolor(C["chart_bg"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for sp in ax.spines.values():
            sp.set_color(C["border"])

    ax_line.plot(SAMPLE_MONTHS, SAMPLE_MONTHLY_INCOME,
                 marker="o", linewidth=2, color=C["green"],
                 label="Income", markersize=5)
    ax_line.plot(SAMPLE_MONTHS, SAMPLE_MONTHLY_EXPENSES,
                 marker="o", linewidth=2, color=C["red"],
                 label="Expenses", markersize=5)
    ax_line.fill_between(SAMPLE_MONTHS, SAMPLE_MONTHLY_INCOME,
                          SAMPLE_MONTHLY_EXPENSES, alpha=0.08, color=C["green"])
    ax_line.set_title("Income vs Expenses Trend",
                       color=C["text"], fontsize=10, pad=10)
    ax_line.legend(facecolor=C["surface"], labelcolor=C["muted"],
                   fontsize=8, framealpha=0.6)

    exp_txns = [r for r in transactions if r["type"] == "Expense"]
    if exp_txns:
        import pandas as pd
        df   = pd.DataFrame(exp_txns)
        cats = df.groupby("category")["amount_usd"].sum()
        wedges, texts, autotexts = ax_pie.pie(
            cats, labels=cats.index,
            autopct="%1.1f%%",
            colors=PIE_COLOURS[:len(cats)],
            startangle=90,
            wedgeprops={"linewidth": 1.5, "edgecolor": C["chart_bg"]},
        )
    else:
        wedges, texts, autotexts = ax_pie.pie(
            [40, 25, 20, 15],
            labels=["Bills", "Food", "Shopping", "Transport"],
            autopct="%1.1f%%",
            colors=PIE_COLOURS[:4],
            startangle=90,
            wedgeprops={"linewidth": 1.5, "edgecolor": C["chart_bg"]},
        )

    for t in texts:     t.set_color(C["muted"]);  t.set_fontsize(8)
    for at in autotexts: at.set_color(C["text"]); at.set_fontsize(7)

    ax_pie.set_title("Expenses by Category", color=C["text"], fontsize=10, pad=10)
    fig.tight_layout(pad=2.0)
    chart_canvas.draw()


def refresh_all():
    refresh_summary()
    refresh_charts()


def add_income():
    raw  = income_entry.get().strip()
    desc = income_desc_entry.get().strip()
    cat  = income_cat_var.get()
    if not raw:
        messagebox.showerror("Missing Value", "Please enter an income amount.", parent=root)
        income_entry.focus_set(); return
    try:
        amount = float(raw)
        if amount <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a positive number.", parent=root)
        income_entry.focus_set(); return

    usd = to_usd(amount)
    transactions.append({
        "id": next_id(), "date": today_str(),
        "type": "Income", "category": cat,
        "description": desc, "amount_usd": usd,
    })
    income_entry.delete(0, tk.END)
    income_desc_entry.delete(0, tk.END)
    refresh_all()
    _, sym = get_currency()
    set_status(f"✓ Income of {sym}{amount:,.2f} added.")


def add_expense():
    raw_amt  = expense_amount_entry.get().strip()
    category = category_var.get()
    desc     = expense_desc_entry.get().strip()

    if not raw_amt:
        messagebox.showerror("Missing Value", "Please enter an expense amount.", parent=root)
        expense_amount_entry.focus_set(); return
    try:
        amount = float(raw_amt)
        if amount <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a positive number.", parent=root)
        expense_amount_entry.focus_set(); return

    usd = to_usd(amount)
    transactions.append({
        "id": next_id(), "date": today_str(),
        "type": "Expense", "category": category,
        "description": desc, "amount_usd": usd,
    })
    expense_amount_entry.delete(0, tk.END)
    expense_desc_entry.delete(0, tk.END)
    refresh_all()
    _, sym = get_currency()
    set_status(f"✓ Expense of {sym}{amount:,.2f} ({category}) added.")


def clear_all():
    if not transactions:
        set_status("Nothing to clear."); return
    if messagebox.askyesno("Clear Data",
                            "This will delete ALL records.\nContinue?",
                            parent=root):
        transactions.clear()
        refresh_all()
        refresh_txn_page()
        set_status("All data cleared.")


# ══════════════════════════════════════════
# STYLE CONFIG
# ══════════════════════════════════════════
style = ttk.Style()
style.theme_use("clam")
style.configure("Dark.TCombobox",
                fieldbackground=C["surface2"],
                background=C["surface2"],
                foreground=C["text"],
                arrowcolor=C["accent"],
                bordercolor=C["border"],
                selectbackground=C["surface2"],
                selectforeground=C["text"])
style.map("Dark.TCombobox",
          fieldbackground=[("readonly", C["surface2"])],
          foreground=[("readonly", C["text"])])

style.configure("Finance.Treeview",
                background=C["surface"],
                foreground=C["text"],
                fieldbackground=C["surface"],
                borderwidth=0,
                font=("Helvetica", 10),
                rowheight=36)
style.configure("Finance.Treeview.Heading",
                background=C["surface2"],
                foreground=C["muted"],
                font=("Helvetica", 9, "bold"),
                borderwidth=0)
style.map("Finance.Treeview",
          background=[("selected", C["surface2"])],
          foreground=[("selected", C["accent"])])


# ══════════════════════════════════════════
# PLACEHOLDER GLOBALS (set by builders)
# ══════════════════════════════════════════
income_val = expense_val = balance_val = txn_val = None
income_sub = expense_sub = balance_sub = txn_sub = None
income_entry = income_desc_entry = income_cat_var = None
expense_amount_entry = expense_desc_entry = category_var = None
fig = ax_line = ax_pie = chart_canvas = None
status_var = None
txn_page_inc_val = txn_page_exp_val = txn_page_bal_val = None
txn_filter_var = txn_search_var = None
txn_tree2 = None
txn2_footer_label = None


# ══════════════════════════════════════════
# BUILD & LAUNCH
# ══════════════════════════════════════════
build_home()
build_main_frame()
build_txn_page()

refresh_all()
refresh_txn_page()

show_frame(home_frame)

root.mainloop()
