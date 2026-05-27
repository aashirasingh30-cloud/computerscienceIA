# ============================================
# FINANCETRACKER PRO — IB SL CS IA
# v4.6 — macOS + Windows + Linux compatible
# ============================================
#
# Dependencies:
#   pip install matplotlib pandas requests
#
# Run:  python Finance_app_v46.py
#
# v4.6 Changes:
#  1. STOCK MARKET PAGE (page 4)
#     • "All Stocks" tab: live market overview table with
#       Symbol, Company, Price, Change %, Volume, Market Cap,
#       and a mini-chart icon; simulated prices that update
#       on "Refresh Data"
#     • "My Portfolio" tab: shows only the user's holdings
#       from the Investments page with Your Shares, Current
#       Price, Today's Change, Position Value, and a
#       Portfolio Summary section (total positions, portfolio
#       value, average return)
#     • Portfolio stocks are synced from investments[] in
#       real-time — adding/deleting holdings on the
#       Investments page is instantly reflected here
#     • Per-user portfolio persisted to
#       data/<username>_portfolio.json
#     • "Refresh Data" simulates a live price update with
#       small random fluctuations (±0–2 %) on every stock
#     • Mini price-history sparkline popup when the chart
#       icon is clicked in the All Stocks tab
#
# v4.5 Changes (carried forward):
#  1. LOGIN / SIGNUP SYSTEM
#  2. Per-user transaction isolation
#  3. Investments page
# ============================================

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import rcParams
from datetime import datetime, timedelta
import platform
import random
import json
import os
import hashlib
import time

rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.spines.top']   = False
rcParams['axes.spines.right'] = False

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# ──────────────────────────────────────────
# FILE PATHS
# ──────────────────────────────────────────
DATA_DIR         = "financetracker_data"
USERS_FILE       = os.path.join(DATA_DIR, "users.json")
LAST_USER_FILE   = os.path.join(DATA_DIR, "last_user.txt")

os.makedirs(DATA_DIR, exist_ok=True)


# ──────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────
def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()

def _random_salt() -> str:
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def register_user(username: str, email: str, full_name: str, password: str) -> tuple:
    users = load_users()
    uname = username.strip().lower()
    if not uname:
        return False, "Username cannot be empty."
    if len(uname) < 3:
        return False, "Username must be at least 3 characters."
    if not uname.isalnum() and not all(c.isalnum() or c in "_-" for c in uname):
        return False, "Username may only contain letters, numbers, _ and -."
    if uname in users:
        return False, "Username already exists. Please choose another."
    if not email.strip() or "@" not in email or "." not in email:
        return False, "Please enter a valid email address."
    if not full_name.strip():
        return False, "Full name cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    salt = _random_salt()
    users[uname] = {
        "email":     email.strip(),
        "full_name": full_name.strip(),
        "salt":      salt,
        "password":  _hash_password(password, salt),
        "created":   datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    save_users(users)
    return True, "Account created successfully!"

def verify_login(username: str, password: str) -> tuple:
    users = load_users()
    uname = username.strip().lower()
    if uname not in users:
        return False, "Username not found."
    record = users[uname]
    if record["password"] != _hash_password(password, record["salt"]):
        return False, "Incorrect password."
    return True, users[uname]["full_name"]

def save_last_user(username: str):
    try:
        with open(LAST_USER_FILE, "w", encoding="utf-8") as f:
            f.write(username.strip().lower())
    except IOError:
        pass

def load_last_user() -> str:
    if not os.path.exists(LAST_USER_FILE):
        return ""
    try:
        with open(LAST_USER_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except IOError:
        return ""

def clear_last_user():
    try:
        if os.path.exists(LAST_USER_FILE):
            os.remove(LAST_USER_FILE)
    except IOError:
        pass


# ──────────────────────────────────────────
# PER-USER PERSISTENCE
# ──────────────────────────────────────────
def _user_txn_file(username: str) -> str:
    return os.path.join(DATA_DIR, f"{username.strip().lower()}_transactions.json")

def load_user_transactions(username: str) -> list:
    fpath = _user_txn_file(username)
    if not os.path.exists(fpath):
        return []
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_user_transactions(username: str, txns: list):
    fpath = _user_txn_file(username)
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(txns, f, indent=2)
    except IOError:
        pass


# ──────────────────────────────────────────
# COLOUR PALETTE
# ──────────────────────────────────────────
C = {
    "bg":        "#0f172a",
    "surface":   "#1e293b",
    "surface2":  "#273449",
    "border":    "#334155",
    "accent":    "#38bdf8",
    "purple":    "#a78bfa",
    "green":     "#4ade80",
    "red":       "#f87171",
    "yellow":    "#fbbf24",
    "text":      "#f1f5f9",
    "muted":     "#94a3b8",
    "white":     "#ffffff",
    "btn_hover": "#0ea5e9",
    "chart_bg":  "#1e293b",
}

PIE_COLOURS = ["#38bdf8","#4ade80","#fbbf24","#f87171",
               "#a78bfa","#fb923c","#34d399","#f472b6"]

# ──────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────
current_user      = None
current_full_name = None

# ──────────────────────────────────────────
# DATA
# ──────────────────────────────────────────
transactions    = []
investments     = []
_txn_id_counter = 0
_inv_id_counter = 0

EXCHANGE_RATES = {
    "USD":1.00,"EUR":0.92,"GBP":0.78,"AED":3.67,"INR":83.00,
}
CURRENCY_OPTIONS = {
    "USD ($)":   ("USD","$"),
    "EUR (€)":   ("EUR","€"),
    "GBP (£)":   ("GBP","£"),
    "AED (د.إ)":("AED","د.إ"),
    "INR (₹)":  ("INR","₹"),
}

SAMPLE_MONTHS           = ["Jan","Feb","Mar","Apr","May","Jun"]
SAMPLE_MONTHLY_INCOME   = [3200,2800,3500,2900,3800,3400]
SAMPLE_MONTHLY_EXPENSES = [2500,2200,2600,2100,3000,2700]

EXPENSE_CATEGORIES = [
    "Food & Dining","Shopping","Transportation","Bills & Utilities",
    "Entertainment","Health","Education","Travel","Freelance","Other",
]
INCOME_CATEGORIES = ["Salary","Freelance","Investment","Gift","Other"]

_SAMPLE_INVESTMENTS = [
    {"symbol":"AAPL","name":"Apple Inc.",            "shares":10,"buy_price":165.50,"cur_price":175.50},
    {"symbol":"MSFT","name":"Microsoft Corporation", "shares":5, "buy_price":410.00,"cur_price":425.80},
    {"symbol":"GOOGL","name":"Alphabet Inc.",        "shares":8, "buy_price":135.00,"cur_price":141.20},
]

# ──────────────────────────────────────────
# STOCK MARKET DATA
# ──────────────────────────────────────────
# Base prices — "Refresh Data" applies small random fluctuations
_MARKET_STOCKS = [
    {"symbol":"AAPL",  "name":"Apple Inc.",            "price":173.83, "change_pct":-0.95, "change_abs":-1.67, "volume":28229187, "mktcap":"$153.53B"},
    {"symbol":"GOOGL", "name":"Alphabet Inc.",         "price":138.37, "change_pct":-2.01, "change_abs":-2.83, "volume":44355302, "mktcap":"$89.09B"},
    {"symbol":"MSFT",  "name":"Microsoft Corporation", "price":426.24, "change_pct": 0.10, "change_abs": 0.44, "volume":32963959, "mktcap":"$328.18B"},
    {"symbol":"AMZN",  "name":"Amazon.com Inc.",       "price":188.05, "change_pct": 1.49, "change_abs": 2.75, "volume":21570369, "mktcap":"$216.36B"},
    {"symbol":"TSLA",  "name":"Tesla Inc.",            "price":240.67, "change_pct": 0.93, "change_abs": 2.22, "volume":29891440, "mktcap":"$577.65B"},
    {"symbol":"META",  "name":"Meta Platforms Inc.",   "price":519.87, "change_pct": 0.19, "change_abs": 0.97, "volume":58470179, "mktcap":"$719.63B"},
    {"symbol":"NVDA",  "name":"NVIDIA Corporation",    "price":882.97, "change_pct": 0.28, "change_abs": 2.47, "volume":29047316, "mktcap":"$443.32B"},
    {"symbol":"JPM",   "name":"JPMorgan Chase & Co.",  "price":203.75, "change_pct": 2.00, "change_abs": 4.00, "volume":31363125, "mktcap":"$104.56B"},
    {"symbol":"V",     "name":"Visa Inc.",             "price":283.33, "change_pct": 1.77, "change_abs": 4.93, "volume":55369004, "mktcap":"$440.49B"},
    {"symbol":"WMT",   "name":"Walmart Inc.",          "price": 68.00, "change_pct":-0.37, "change_abs":-0.25, "volume":47045863, "mktcap":"$65.52B"},
    {"symbol":"JNJ",   "name":"Johnson & Johnson",     "price":152.44, "change_pct":-0.14, "change_abs":-0.21, "volume":18230411, "mktcap":"$367.82B"},
    {"symbol":"UNH",   "name":"UnitedHealth Group",    "price":520.10, "change_pct": 0.65, "change_abs": 3.37, "volume":3924556,  "mktcap":"$479.31B"},
    {"symbol":"XOM",   "name":"Exxon Mobil Corp.",     "price":115.78, "change_pct":-0.54, "change_abs":-0.63, "volume":22107890, "mktcap":"$462.15B"},
    {"symbol":"BAC",   "name":"Bank of America Corp.", "price": 38.12, "change_pct": 0.87, "change_abs": 0.33, "volume":49321067, "mktcap":"$300.44B"},
    {"symbol":"PG",    "name":"Procter & Gamble Co.",  "price":163.55, "change_pct": 0.22, "change_abs": 0.36, "volume":9841233,  "mktcap":"$385.76B"},
]

# Live working copy (mutated on Refresh Data)
market_stocks = [dict(s) for s in _MARKET_STOCKS]


# ══════════════════════════════════════════
# ROOT WINDOW
# ══════════════════════════════════════════
root = tk.Tk()
root.title("FinanceTracker PRO")
root.geometry("1280x920")
root.minsize(1060,760)
root.configure(bg=C["bg"])

selected_currency_var = tk.StringVar(root, value="USD ($)")
status_var            = tk.StringVar(root, value="Ready")

def _focus_handler(event):
    try:
        w = event.widget
        if w and w.winfo_exists():
            w.focus_set()
    except Exception:
        pass

root.bind_all("<ButtonPress-1>",   _focus_handler, add="+")
root.bind_all("<ButtonRelease-1>", _focus_handler, add="+")


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────
def get_currency():
    return CURRENCY_OPTIONS[selected_currency_var.get()]

def to_display(usd):
    code,_ = get_currency()
    return usd * EXCHANGE_RATES[code]

def to_usd(display):
    code,_ = get_currency()
    return display / EXCHANGE_RATES[code]

def fmt(amount):
    _,sym = get_currency()
    return f"{sym}{amount:,.2f}"

def today_str():
    return datetime.now().strftime("%d/%m/%Y")

def next_txn_id():
    global _txn_id_counter
    _txn_id_counter += 1
    return _txn_id_counter

def next_inv_id():
    global _inv_id_counter
    _inv_id_counter += 1
    return _inv_id_counter

def set_status(msg):
    status_var.set(msg)
    root.after(3000, lambda: status_var.set("Ready"))


# ──────────────────────────────────────────
# STYLE SETUP
# ──────────────────────────────────────────
style = ttk.Style(root)
style.theme_use("clam")

style.configure("Dark.TCombobox",
                fieldbackground=C["surface2"], background=C["surface2"],
                foreground=C["text"], arrowcolor=C["accent"],
                bordercolor=C["border"], selectbackground=C["surface2"],
                selectforeground=C["text"], padding=4)
style.map("Dark.TCombobox",
          fieldbackground=[("readonly",C["surface2"])],
          foreground=[("readonly",C["text"])])

def _reg(name, bg, fg, hbg, hfg=None, pad=(16,9)):
    hfg = hfg or fg
    style.configure(name, font=("Helvetica",10,"bold"),
                    background=bg, foreground=fg,
                    borderwidth=0, focusthickness=0,
                    relief="flat", padding=pad)
    style.map(name,
              background=[("!disabled","active",hbg),("!disabled","pressed",hbg),
                          ("active",hbg),("pressed",hbg)],
              foreground=[("!disabled","active",hfg),("!disabled","pressed",hfg),
                          ("active",hfg),("pressed",hfg)])

_reg("Accent.TButton",      C["accent"],   C["bg"],    C["btn_hover"])
_reg("Green.TButton",       C["green"],    C["bg"],    "#22c55e")
_reg("Red.TButton",         C["red"],      C["bg"],    "#ef4444")
_reg("Purple.TButton",      C["purple"],   C["bg"],    "#8b5cf6")
_reg("Muted.TButton",       C["surface2"], C["muted"], C["border"], C["text"])
_reg("Ghost.TButton",       C["surface2"], C["muted"], C["border"], C["text"], (8,4))
_reg("NavActive.TButton",   C["accent"],   C["bg"],    C["btn_hover"],          (20,7))
_reg("NavInactive.TButton", C["surface2"], C["muted"], C["border"], C["text"], (20,7))

style.configure("Finance.Treeview",
                background=C["surface"], foreground=C["text"],
                fieldbackground=C["surface"], borderwidth=0,
                font=("Helvetica",10), rowheight=40)
style.configure("Finance.Treeview.Heading",
                background=C["surface2"], foreground=C["muted"],
                font=("Helvetica",9,"bold"), borderwidth=0, relief="flat")
style.map("Finance.Treeview",
          background=[("selected",C["surface2"])],
          foreground=[("selected",C["accent"])])

style.configure("Market.Treeview",
                background=C["surface"], foreground=C["text"],
                fieldbackground=C["surface"], borderwidth=0,
                font=("Helvetica",10), rowheight=44)
style.configure("Market.Treeview.Heading",
                background=C["surface2"], foreground=C["muted"],
                font=("Helvetica",9,"bold"), borderwidth=0, relief="flat")
style.map("Market.Treeview",
          background=[("selected",C["surface2"])],
          foreground=[("selected",C["accent"])])


# ──────────────────────────────────────────
# WIDGET FACTORIES
# ──────────────────────────────────────────
def make_label(parent, text, size=10, weight="normal", color=None, **kw):
    bg = parent.cget("bg") if hasattr(parent,"cget") else C["bg"]
    return tk.Label(parent, text=text, bg=bg,
                    fg=color or C["text"],
                    font=("Helvetica",size,weight), **kw)

def make_card(parent, **kw):
    return tk.Frame(parent, bg=C["surface"],
                    highlightthickness=1, highlightbackground=C["border"], **kw)

def make_entry(parent, width=22, show=None, **kw):
    ht = 0 if IS_MAC else 1
    kwargs = dict(bg=C["surface2"], fg=C["text"],
                  insertbackground=C["text"],
                  relief="flat", bd=2,
                  font=("Helvetica",11),
                  highlightthickness=ht,
                  highlightbackground=C["border"],
                  highlightcolor=C["accent"], **kw)
    if show is not None:
        kwargs["show"] = show
    e = tk.Entry(parent, width=width, **kwargs)
    e.bind("<ButtonPress-1>",   lambda ev: e.focus_set(), add="+")
    e.bind("<ButtonRelease-1>", lambda ev: e.focus_set(), add="+")
    return e

def make_sep(parent):
    return tk.Frame(parent, bg=C["border"], height=1)

def make_btn(parent, text, command, style_name="Accent.TButton"):
    _running = [False]
    _last_ms = [0]
    def _safe_command(_cmd=command):
        now_ms = int(time.time() * 1000)
        if _running[0] or (now_ms - _last_ms[0]) < 400:
            return
        _running[0] = True
        _last_ms[0] = now_ms
        try:
            _cmd()
        finally:
            _running[0] = False
    b = ttk.Button(parent, text=text, command=_safe_command, style=style_name)
    return b

def make_combobox(parent, textvariable, values, width=24, font_size=10, **kw):
    cb = ttk.Combobox(parent, textvariable=textvariable,
                      values=values, state="readonly",
                      width=width, style="Dark.TCombobox",
                      font=("Helvetica",font_size), **kw)
    cb.bind("<ButtonPress-1>",   lambda e: cb.focus_set(), add="+")
    cb.bind("<ButtonRelease-1>", lambda e: cb.focus_set(), add="+")
    cb.configure(postcommand=lambda: cb.update_idletasks())
    return cb


# ══════════════════════════════════════════
# FRAME STACK
# ══════════════════════════════════════════
home_frame   = tk.Frame(root, bg=C["bg"])
auth_frame   = tk.Frame(root, bg=C["bg"])
main_frame   = tk.Frame(root, bg=C["bg"])
txn_page     = tk.Frame(root, bg=C["bg"])
inv_page     = tk.Frame(root, bg=C["bg"])
market_page  = tk.Frame(root, bg=C["bg"])

_current_frame = None

def show_frame(frame):
    global _current_frame
    if _current_frame is not None:
        _current_frame.place_forget()
    frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    frame.lift()
    frame.focus_set()
    _current_frame = frame


# ══════════════════════════════════════════
# NAV HELPERS
# ══════════════════════════════════════════
def _go_dashboard():
    show_frame(main_frame)
    refresh_all()

def _go_transactions():
    show_frame(txn_page)
    refresh_txn_page()

def _go_investments():
    show_frame(inv_page)
    refresh_inv_page()

def _go_market():
    show_frame(market_page)
    refresh_market_page()

def _go_home():
    show_frame(home_frame)

def _go_auth():
    show_frame(auth_frame)
    _auth_on_show()

def _do_logout():
    global current_user, current_full_name, transactions, investments
    global _txn_id_counter, _inv_id_counter
    current_user      = None
    current_full_name = None
    transactions      = []
    investments       = []
    _txn_id_counter   = 0
    _inv_id_counter   = 0
    clear_last_user()
    _go_auth()
    set_status("Logged out.")


# ══════════════════════════════════════════
# INTERACTIVE CHART STATE
# ══════════════════════════════════════════
_detail_label      = None
_hover_annotation  = None
_selected_marker   = None
_line_income_obj   = None
_line_expense_obj  = None
_pie_wedges        = []
_pie_labels_data   = []
_chart_months      = []
_chart_income_pts  = []
_chart_expense_pts = []

_inv_detail_label = None
_inv_hover_ann    = None
_inv_sel_marker   = None
_inv_line_obj     = None
_inv_chart_dates  = []
_inv_chart_values = []
_inv_fig          = None
_inv_ax           = None
_inv_canvas       = None


def _get_monthly_data():
    if not transactions:
        return SAMPLE_MONTHS, SAMPLE_MONTHLY_INCOME, SAMPLE_MONTHLY_EXPENSES
    df = pd.DataFrame(transactions)
    df["_dt"]    = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["_month"] = df["_dt"].dt.to_period("M")
    df           = df.dropna(subset=["_month"])
    code,_ = get_currency()
    rate   = EXCHANGE_RATES[code]
    if df["_month"].nunique() < 2:
        inc = df[df["type"]=="Income"]["amount_usd"].sum()*rate
        exp = df[df["type"]=="Expense"]["amount_usd"].sum()*rate
        months = list(SAMPLE_MONTHS); income = list(SAMPLE_MONTHLY_INCOME)
        exps   = list(SAMPLE_MONTHLY_EXPENSES)
        if inc or exp:
            months[0]="Now"; income[0]=round(inc,2); exps[0]=round(exp,2)
        return months, income, exps
    grouped = (df.groupby(["_month","type"])["amount_usd"]
                 .sum().unstack(fill_value=0).sort_index())
    months = [str(p) for p in grouped.index]
    income = [round(v*rate,2) for v in grouped.get("Income", pd.Series([0]*len(months))).values]
    exps   = [round(v*rate,2) for v in grouped.get("Expense",pd.Series([0]*len(months))).values]
    return months, income, exps


def _show_detail(text):
    if _detail_label:
        _detail_label.config(text=text)

def _show_inv_detail(text):
    if _inv_detail_label:
        _inv_detail_label.config(text=text)


def _on_pick(event):
    global _selected_marker
    _,sym = get_currency()
    artist = event.artist
    if artist in (_line_income_obj, _line_expense_obj):
        idx = event.ind[0]
        if idx >= len(_chart_months): return
        month = _chart_months[idx]
        inc_v = _chart_income_pts[idx]  if idx < len(_chart_income_pts)  else 0
        exp_v = _chart_expense_pts[idx] if idx < len(_chart_expense_pts) else 0
        net   = inc_v - exp_v
        savings = (net/inc_v*100) if inc_v else 0
        if idx > 0:
            pi = _chart_income_pts[idx-1]  if (idx-1)<len(_chart_income_pts)  else 0
            pe = _chart_expense_pts[idx-1] if (idx-1)<len(_chart_expense_pts) else 0
            ti = ("▲" if inc_v>=pi else "▼")+f" {sym}{abs(inc_v-pi):,.0f} MoM"
            te = ("▲" if exp_v>=pe else "▼")+f" {sym}{abs(exp_v-pe):,.0f} MoM"
        else:
            ti = te = "— first period"
        if _selected_marker:
            try: _selected_marker.remove()
            except: pass
        y = inc_v if artist is _line_income_obj else exp_v
        sc = ax_line.scatter([idx],[y],s=160,facecolors="none",
                             edgecolors=C["accent"],linewidths=2.5,zorder=5)
        _selected_marker = sc
        fig.canvas.draw_idle()
        nd = "🟢" if net>=0 else "🔴"
        _show_detail(
            f"📅 {month}  ·  Income: {sym}{inc_v:,.2f} ({ti})  ·  "
            f"Expenses: {sym}{exp_v:,.2f} ({te})  ·  "
            f"Net: {nd} {sym}{net:,.2f}  ·  Savings: {savings:.1f}%"
        )
        set_status(f"📅 {month} — Net {sym}{net:,.2f} | Savings {savings:.1f}%")

    elif artist in _pie_wedges:
        try: idx = _pie_wedges.index(artist)
        except ValueError: return
        if idx >= len(_pie_labels_data): return
        cat = _pie_labels_data[idx]
        exp_txns = [t for t in transactions if t["type"]=="Expense"]
        if not exp_txns: return
        code,_ = get_currency(); rate = EXCHANGE_RATES[code]
        df = pd.DataFrame(exp_txns)
        tots  = df.groupby("category")["amount_usd"].sum()
        grand = tots.sum()
        amt   = tots.get(cat,0)
        cnt   = len([t for t in exp_txns if t["category"]==cat])
        pct   = (amt/grand*100) if grand else 0
        avg   = (amt/cnt) if cnt else 0
        _show_detail(
            f"🍕 {cat}  ·  Total: {sym}{amt*rate:,.2f} ({pct:.1f}%)  ·  "
            f"Txns: {cnt}  ·  Avg: {sym}{avg*rate:,.2f}"
        )
        set_status(f"{cat} — {pct:.1f}% | {sym}{amt*rate:,.2f}")


def _on_hover(event):
    global _hover_annotation
    if event.inaxes != ax_line or not _chart_months:
        if _hover_annotation:
            try: _hover_annotation.remove()
            except: pass
            _hover_annotation = None
            fig.canvas.draw_idle()
        return
    xdata = event.xdata
    if xdata is None: return
    idx = max(0, min(int(round(xdata)), len(_chart_months)-1))
    inc_v = _chart_income_pts[idx]  if idx < len(_chart_income_pts)  else 0
    exp_v = _chart_expense_pts[idx] if idx < len(_chart_expense_pts) else 0
    _,sym = get_currency()
    if _hover_annotation:
        try: _hover_annotation.remove()
        except: pass
    _hover_annotation = ax_line.annotate(
        f"{_chart_months[idx]}\n↑ {sym}{inc_v:,.0f}\n↓ {sym}{exp_v:,.0f}",
        xy=(idx, max(inc_v,exp_v)), xytext=(12,12), textcoords="offset points",
        fontsize=7.5, color=C["text"],
        bbox=dict(boxstyle="round,pad=0.45",fc=C["surface2"],ec=C["accent"],lw=1.3,alpha=0.93),
        arrowprops=dict(arrowstyle="->",color=C["accent"],lw=1.2)
    )
    fig.canvas.draw_idle()


def _on_inv_pick(event):
    global _inv_sel_marker
    if event.artist is not _inv_line_obj: return
    idx = event.ind[0]
    if idx >= len(_inv_chart_dates): return
    date_lbl = _inv_chart_dates[idx]
    val      = _inv_chart_values[idx]
    _,sym    = get_currency()
    chg = val - _inv_chart_values[idx-1] if idx>0 else 0
    chg_pct = (chg/_inv_chart_values[idx-1]*100) if idx>0 and _inv_chart_values[idx-1] else 0
    start = _inv_chart_values[0] if _inv_chart_values else val
    cum_ret = ((val-start)/start*100) if start else 0
    arrow = "▲" if chg>=0 else "▼"
    if _inv_sel_marker:
        try: _inv_sel_marker.remove()
        except: pass
    sc = _inv_ax.scatter([idx],[val],s=160,facecolors="none",
                         edgecolors=C["purple"],linewidths=2.5,zorder=5)
    _inv_sel_marker = sc
    _inv_fig.canvas.draw_idle()
    _show_inv_detail(
        f"📅 {date_lbl}  ·  Portfolio Value: {sym}{val:,.2f}  ·  "
        f"Daily change: {arrow} {sym}{abs(chg):,.2f} ({chg_pct:+.2f}%)  ·  "
        f"Cumulative return: {cum_ret:+.2f}%"
    )
    set_status(f"Portfolio {date_lbl}: {sym}{val:,.2f} | {chg_pct:+.2f}%")


def _on_inv_hover(event):
    global _inv_hover_ann
    if event.inaxes != _inv_ax or not _inv_chart_dates:
        if _inv_hover_ann:
            try: _inv_hover_ann.remove()
            except: pass
            _inv_hover_ann = None
            _inv_fig.canvas.draw_idle()
        return
    xdata = event.xdata
    if xdata is None: return
    idx = max(0, min(int(round(xdata)), len(_inv_chart_dates)-1))
    val  = _inv_chart_values[idx]
    _,sym = get_currency()
    if _inv_hover_ann:
        try: _inv_hover_ann.remove()
        except: pass
    _inv_hover_ann = _inv_ax.annotate(
        f"{_inv_chart_dates[idx]}\n{sym}{val:,.2f}",
        xy=(idx,val), xytext=(10,10), textcoords="offset points",
        fontsize=7.5, color=C["text"],
        bbox=dict(boxstyle="round,pad=0.4",fc=C["surface2"],ec=C["purple"],lw=1.2,alpha=0.92),
        arrowprops=dict(arrowstyle="->",color=C["purple"],lw=1)
    )
    _inv_fig.canvas.draw_idle()


# ══════════════════════════════════════════
# HOME / SPLASH
# ══════════════════════════════════════════
def build_home():
    bg_canvas = tk.Canvas(home_frame, bg=C["bg"], highlightthickness=0)
    bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    def draw_grid(e=None):
        bg_canvas.delete("grid")
        w,h = bg_canvas.winfo_width(), bg_canvas.winfo_height()
        for x in range(0,w,60): bg_canvas.create_line(x,0,x,h,fill="#1a2744",tags="grid")
        for y in range(0,h,60): bg_canvas.create_line(0,y,w,y,fill="#1a2744",tags="grid")
    bg_canvas.bind("<Configure>", draw_grid)

    centre = tk.Frame(home_frame, bg=C["bg"])
    centre.place(relx=0.5, rely=0.5, anchor="center")
    tk.Frame(centre, bg=C["accent"], height=3, width=80).pack(pady=(0,24))

    logo_row = tk.Frame(centre, bg=C["bg"])
    logo_row.pack()
    tk.Label(logo_row, text="◈",  bg=C["bg"], fg=C["accent"],
             font=("Helvetica",48,"bold")).pack(side="left")
    tk.Label(logo_row, text=" FinanceTracker", bg=C["bg"], fg=C["white"],
             font=("Helvetica",40,"bold")).pack(side="left")
    tk.Label(logo_row, text=" PRO", bg=C["bg"], fg=C["accent"],
             font=("Helvetica",40,"bold")).pack(side="left")

    tk.Label(centre, text="Your intelligent personal finance dashboard",
             bg=C["bg"], fg=C["muted"], font=("Helvetica",13)).pack(pady=(10,4))
    tk.Label(centre, text="IB SL Computer Science  •  Internal Assessment",
             bg=C["bg"], fg=C["border"], font=("Helvetica",10)).pack(pady=(0,40))

    pills_row = tk.Frame(centre, bg=C["bg"])
    pills_row.pack(pady=(0,50))
    for icon, feat in [("↑↓","Track Income & Expenses"),("◎","Net Balance Analytics"),
                       ("⊞","Transaction History"),("◑","Multi-Currency"),
                       ("📈","Investments"),("📊","Stock Market")]:
        pill = tk.Frame(pills_row, bg=C["surface"],
                        highlightthickness=1, highlightbackground=C["border"])
        pill.pack(side="left", padx=6, ipadx=12, ipady=10)
        tk.Label(pill, text=icon, bg=C["surface"], fg=C["accent"],
                 font=("Helvetica",16,"bold")).pack()
        tk.Label(pill, text=feat, bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",8)).pack()

    ttk.Button(centre, text="  Get Started  →",
               command=_go_auth, style="Accent.TButton"
               ).pack(pady=(0,0), ipadx=16, ipady=5)

    tk.Label(home_frame,
             text="FinanceTracker PRO  •  IB SL CS IA  •  All amounts stored in USD",
             bg=C["bg"], fg=C["border"],
             font=("Helvetica",8)).place(relx=0.5, rely=0.97, anchor="center")


# ══════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════
_login_user_entry   = None
_login_pass_entry   = None
_login_remember_var = None
_auth_mode_var      = None
_auth_panels        = {}

def _auth_on_show():
    if _login_user_entry is None:
        return
    remembered = load_last_user()
    if remembered:
        _login_user_entry.delete(0, tk.END)
        _login_user_entry.insert(0, remembered)
        if _login_remember_var:
            _login_remember_var.set(True)


def _password_strength(password: str) -> tuple:
    if len(password) == 0:
        return "", C["muted"]
    score = 0
    if len(password) >= 8:  score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password): score += 1
    labels = {0:"Weak",1:"Weak",2:"Fair",3:"Good",4:"Strong"}
    colors = {0:C["red"],1:C["red"],2:C["yellow"],3:C["green"],4:C["accent"]}
    return f"Strength: {labels[score]}", colors[score]


def build_auth_frame():
    global _login_user_entry, _login_pass_entry, _login_remember_var
    global _auth_mode_var, _auth_panels

    bg_cv = tk.Canvas(auth_frame, bg=C["bg"], highlightthickness=0)
    bg_cv.place(relx=0, rely=0, relwidth=1, relheight=1)
    def _draw(e=None):
        bg_cv.delete("g")
        w,h = bg_cv.winfo_width(), bg_cv.winfo_height()
        for x in range(0,w,60): bg_cv.create_line(x,0,x,h,fill="#1a2744",tags="g")
        for y in range(0,h,60): bg_cv.create_line(0,y,w,y,fill="#1a2744",tags="g")
    bg_cv.bind("<Configure>", _draw)

    wrapper = tk.Frame(auth_frame, bg=C["bg"])
    wrapper.place(relx=0.5, rely=0.5, anchor="center")

    logo_r = tk.Frame(wrapper, bg=C["bg"]); logo_r.pack(pady=(0,6))
    tk.Label(logo_r, text="◈",  bg=C["bg"], fg=C["accent"],
             font=("Helvetica",28,"bold")).pack(side="left")
    tk.Label(logo_r, text=" FinanceTracker", bg=C["bg"], fg=C["white"],
             font=("Helvetica",22,"bold")).pack(side="left")
    tk.Label(logo_r, text=" PRO", bg=C["bg"], fg=C["accent"],
             font=("Helvetica",22,"bold")).pack(side="left")

    tk.Label(wrapper, text="IB SL Computer Science  •  Internal Assessment",
             bg=C["bg"], fg=C["border"], font=("Helvetica",9)).pack(pady=(0,22))

    _auth_mode_var = tk.StringVar(value="login")
    tab_row = tk.Frame(wrapper, bg=C["surface"],
                       highlightthickness=1, highlightbackground=C["border"])
    tab_row.pack(fill="x")

    def _switch(mode):
        _auth_mode_var.set(mode)
        for k, panel in _auth_panels.items():
            if k == mode:
                panel.pack(fill="x")
            else:
                panel.pack_forget()
        login_tab.config(style="NavActive.TButton"   if mode=="login"  else "NavInactive.TButton")
        signup_tab.config(style="NavActive.TButton"  if mode=="signup" else "NavInactive.TButton")

    login_tab  = ttk.Button(tab_row, text="  🔑  Log In  ",
                             command=lambda: _switch("login"),
                             style="NavActive.TButton")
    signup_tab = ttk.Button(tab_row, text="  ✏️  Sign Up  ",
                             command=lambda: _switch("signup"),
                             style="NavInactive.TButton")
    login_tab.pack(side="left", fill="x", expand=True, ipady=5)
    signup_tab.pack(side="left", fill="x", expand=True, ipady=5)

    card = make_card(wrapper, padx=32, pady=28)
    card.pack(fill="x")
    card.configure(width=460)

    # LOGIN PANEL
    login_panel = tk.Frame(card, bg=C["surface"])
    _auth_panels["login"] = login_panel

    tk.Label(login_panel, text="Welcome back", bg=C["surface"], fg=C["white"],
             font=("Helvetica",16,"bold")).pack(anchor="w", pady=(0,4))
    tk.Label(login_panel, text="Sign in to your account to continue",
             bg=C["surface"], fg=C["muted"], font=("Helvetica",10)).pack(anchor="w", pady=(0,18))

    tk.Label(login_panel, text="Username", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",10)).pack(anchor="w")
    _login_user_entry = make_entry(login_panel, width=38)
    _login_user_entry.pack(fill="x", pady=(3,10))

    tk.Label(login_panel, text="Password", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",10)).pack(anchor="w")
    _login_pass_entry = make_entry(login_panel, width=38, show="•")
    _login_pass_entry.pack(fill="x", pady=(3,8))

    opts_row = tk.Frame(login_panel, bg=C["surface"]); opts_row.pack(fill="x", pady=(0,16))
    _login_remember_var = tk.BooleanVar(value=False)
    tk.Checkbutton(opts_row, text="Remember Me", variable=_login_remember_var,
                   bg=C["surface"], fg=C["muted"], selectcolor=C["surface2"],
                   activebackground=C["surface"], activeforeground=C["accent"],
                   font=("Helvetica",9)).pack(side="left")

    login_err = tk.Label(login_panel, text="", bg=C["surface"], fg=C["red"],
                         font=("Helvetica",9), wraplength=380, justify="left")
    login_err.pack(anchor="w", pady=(0,4))

    def do_login():
        username = _login_user_entry.get().strip()
        password = _login_pass_entry.get()
        ok, result = verify_login(username, password)
        if not ok:
            login_err.config(text=f"⚠  {result}")
            _login_pass_entry.delete(0, tk.END)
            return
        login_err.config(text="")
        if _login_remember_var.get():
            save_last_user(username)
        else:
            clear_last_user()
        _on_successful_login(username.strip().lower(), result)

    make_btn(login_panel, "  Log In  →", do_login, "Accent.TButton"
             ).pack(fill="x", ipady=5)

    make_sep(login_panel).pack(fill="x", pady=16)
    no_acc = tk.Frame(login_panel, bg=C["surface"]); no_acc.pack()
    tk.Label(no_acc, text="Don't have an account?  ", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",9)).pack(side="left")
    lnk = tk.Label(no_acc, text="Sign Up", bg=C["surface"], fg=C["accent"],
                   font=("Helvetica",9,"underline"), cursor="hand2")
    lnk.pack(side="left")
    lnk.bind("<Button-1>", lambda e: _switch("signup"))

    _login_user_entry.bind("<Return>", lambda e: _login_pass_entry.focus_set())
    _login_pass_entry.bind("<Return>", lambda e: do_login())

    # SIGNUP PANEL
    signup_panel = tk.Frame(card, bg=C["surface"])
    _auth_panels["signup"] = signup_panel

    tk.Label(signup_panel, text="Create your account", bg=C["surface"], fg=C["white"],
             font=("Helvetica",16,"bold")).pack(anchor="w", pady=(0,4))
    tk.Label(signup_panel, text="Join FinanceTracker PRO — it's free",
             bg=C["surface"], fg=C["muted"], font=("Helvetica",10)).pack(anchor="w", pady=(0,18))

    def _fl(txt):
        tk.Label(signup_panel, text=txt, bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",10)).pack(anchor="w")

    _fl("Full Name")
    su_name_e = make_entry(signup_panel, width=38)
    su_name_e.pack(fill="x", pady=(3,10))

    _fl("Email Address")
    su_email_e = make_entry(signup_panel, width=38)
    su_email_e.pack(fill="x", pady=(3,10))

    _fl("Username  (letters, numbers, _ or -)")
    su_user_e = make_entry(signup_panel, width=38)
    su_user_e.pack(fill="x", pady=(3,10))

    _fl("Password  (min 6 characters)")
    su_pass_e = make_entry(signup_panel, width=38, show="•")
    su_pass_e.pack(fill="x", pady=(3,4))

    pw_strength_lbl = tk.Label(signup_panel, text="", bg=C["surface"],
                                fg=C["muted"], font=("Helvetica",8))
    pw_strength_lbl.pack(anchor="w", pady=(0,6))

    def _on_pw_change(*_):
        txt, col = _password_strength(su_pass_e.get())
        pw_strength_lbl.config(text=txt, fg=col)
    su_pass_e.bind("<KeyRelease>", _on_pw_change)

    _fl("Confirm Password")
    su_pass2_e = make_entry(signup_panel, width=38, show="•")
    su_pass2_e.pack(fill="x", pady=(3,8))

    signup_err = tk.Label(signup_panel, text="", bg=C["surface"], fg=C["red"],
                           font=("Helvetica",9), wraplength=380, justify="left")
    signup_err.pack(anchor="w", pady=(0,4))

    def do_signup():
        full_name = su_name_e.get().strip()
        email     = su_email_e.get().strip()
        username  = su_user_e.get().strip()
        password  = su_pass_e.get()
        confirm   = su_pass2_e.get()
        if password != confirm:
            signup_err.config(text="⚠  Passwords do not match.")
            su_pass2_e.delete(0, tk.END)
            su_pass2_e.focus_set()
            return
        ok, msg = register_user(username, email, full_name, password)
        if not ok:
            signup_err.config(text=f"⚠  {msg}")
            return
        signup_err.config(text="")
        _on_successful_login(username.strip().lower(), full_name)

    make_btn(signup_panel, "  Create Account  →", do_signup, "Green.TButton"
             ).pack(fill="x", ipady=5)

    make_sep(signup_panel).pack(fill="x", pady=16)
    have_acc = tk.Frame(signup_panel, bg=C["surface"]); have_acc.pack()
    tk.Label(have_acc, text="Already have an account?  ", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",9)).pack(side="left")
    lnk2 = tk.Label(have_acc, text="Log In", bg=C["surface"], fg=C["accent"],
                    font=("Helvetica",9,"underline"), cursor="hand2")
    lnk2.pack(side="left")
    lnk2.bind("<Button-1>", lambda e: _switch("login"))

    su_name_e.bind("<Return>",  lambda e: su_email_e.focus_set())
    su_email_e.bind("<Return>", lambda e: su_user_e.focus_set())
    su_user_e.bind("<Return>",  lambda e: su_pass_e.focus_set())
    su_pass_e.bind("<Return>",  lambda e: su_pass2_e.focus_set())
    su_pass2_e.bind("<Return>", lambda e: do_signup())

    back_row = tk.Frame(wrapper, bg=C["bg"]); back_row.pack(pady=(12,0))
    make_btn(back_row, "← Back to Home", _go_home, "Ghost.TButton").pack()

    login_panel.pack(fill="x")


def _on_successful_login(username: str, full_name: str):
    global current_user, current_full_name, transactions, investments
    global _txn_id_counter, _inv_id_counter

    current_user      = username
    current_full_name = full_name

    raw = load_user_transactions(username)
    transactions = raw
    if raw:
        _txn_id_counter = max(t["id"] for t in raw)
    else:
        _txn_id_counter = 0

    investments     = []
    _inv_id_counter = 0
    for s in _SAMPLE_INVESTMENTS:
        investments.append({"id": next_inv_id(), **s})

    root.title(f"FinanceTracker PRO  —  {full_name}")

    refresh_all()
    refresh_txn_page()
    refresh_inv_page()
    refresh_market_page()

    show_frame(main_frame)
    set_status(f"Welcome back, {full_name}! 👋")


# ══════════════════════════════════════════
# SHARED HEADER
# ══════════════════════════════════════════
def build_header(parent, active_tab="dashboard"):
    header = tk.Frame(parent, bg=C["surface"],
                      highlightthickness=1, highlightbackground=C["border"])
    header.pack(fill="x", side="top")

    logo_f = tk.Frame(header, bg=C["surface"])
    logo_f.pack(side="left", padx=24, pady=12)
    tk.Label(logo_f, text="◈",               bg=C["surface"], fg=C["accent"],
             font=("Helvetica",20,"bold")).pack(side="left")
    tk.Label(logo_f, text="  FinanceTracker", bg=C["surface"], fg=C["white"],
             font=("Helvetica",15,"bold")).pack(side="left")
    tk.Label(logo_f, text=" PRO",             bg=C["surface"], fg=C["accent"],
             font=("Helvetica",15,"bold")).pack(side="left")

    nav_f = tk.Frame(header, bg=C["surface"])
    nav_f.pack(side="left", padx=20, pady=8)

    def nav_style(tab): return "NavActive.TButton" if active_tab==tab else "NavInactive.TButton"
    make_btn(nav_f, "📊  Dashboard",    _go_dashboard,    nav_style("dashboard")   ).pack(side="left", padx=3)
    make_btn(nav_f, "💳  Transactions", _go_transactions, nav_style("transactions")).pack(side="left", padx=3)
    make_btn(nav_f, "📈  Investments",  _go_investments,  nav_style("investments") ).pack(side="left", padx=3)
    make_btn(nav_f, "📉  Stock Market", _go_market,       nav_style("market")      ).pack(side="left", padx=3)

    right_f = tk.Frame(header, bg=C["surface"])
    right_f.pack(side="right", padx=24, pady=12)

    make_btn(right_f, "⇤  Logout", _do_logout, "Ghost.TButton").pack(side="left", padx=(0,12))

    user_badge = tk.Label(right_f,
                          text=f"👤  {current_full_name or 'Guest'}",
                          bg=C["surface2"], fg=C["accent"],
                          font=("Helvetica",9,"bold"),
                          padx=10, pady=4,
                          relief="flat",
                          highlightthickness=1,
                          highlightbackground=C["border"])
    user_badge.pack(side="left", padx=(0,12))

    tk.Label(right_f, text="Currency", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",10)).pack(side="left", padx=(0,6))
    cb = make_combobox(right_f, textvariable=selected_currency_var,
                       values=list(CURRENCY_OPTIONS.keys()), width=13)
    cb.pack(side="left")
    cb.bind("<<ComboboxSelected>>", lambda _: refresh_all())
    return header


# ══════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════
income_val = expense_val = balance_val = txn_val = None
income_sub = expense_sub = balance_sub = txn_sub = None
income_entry = income_desc_entry = income_cat_var = None
expense_amount_entry = expense_desc_entry = category_var = None
fig = ax_line = ax_pie = chart_canvas = None


def build_main_frame():
    global income_val, income_sub, expense_val, expense_sub
    global balance_val, balance_sub, txn_val, txn_sub
    global income_entry, income_desc_entry, income_cat_var
    global expense_amount_entry, expense_desc_entry, category_var
    global fig, ax_line, ax_pie, chart_canvas, _detail_label

    build_header(main_frame, active_tab="dashboard")

    cards_outer = tk.Frame(main_frame, bg=C["bg"])
    cards_outer.pack(fill="x", padx=20, pady=(18,0))
    for i in range(4): cards_outer.grid_columnconfigure(i, weight=1)

    def _sc(parent, col, icon, title, color):
        f = make_card(parent, padx=20, pady=16)
        f.grid(row=0, column=col, padx=8, sticky="ew")
        top = tk.Frame(f, bg=C["surface"]); top.pack(fill="x")
        tk.Label(top, text=icon, bg=C["surface"], fg=color,
                 font=("Helvetica",18)).pack(side="left")
        tk.Label(top, text=f"  {title}", bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",10,"bold")).pack(side="left", pady=(4,0))
        val = tk.Label(f, text="$0.00", bg=C["surface"], fg=color,
                       font=("Helvetica",22,"bold"))
        val.pack(anchor="w", pady=(6,2))
        sub = tk.Label(f, text="—", bg=C["surface"], fg=C["muted"],
                       font=("Helvetica",9))
        sub.pack(anchor="w")
        return val, sub

    income_val,  income_sub  = _sc(cards_outer, 0, "↑", "TOTAL INCOME",   C["green"])
    expense_val, expense_sub = _sc(cards_outer, 1, "↓", "TOTAL EXPENSES", C["red"])
    balance_val, balance_sub = _sc(cards_outer, 2, "◎", "NET BALANCE",    C["yellow"])
    txn_val,     txn_sub     = _sc(cards_outer, 3, "⊞", "TRANSACTIONS",   C["accent"])

    shortcut_bar = tk.Frame(main_frame, bg=C["bg"])
    shortcut_bar.pack(fill="x", padx=20, pady=(10,0))
    make_btn(shortcut_bar, "💳  View Transaction History →",
             _go_transactions, "Ghost.TButton").pack(side="right")

    content = tk.Frame(main_frame, bg=C["bg"])
    content.pack(fill="both", expand=True, padx=20, pady=12)
    content.grid_columnconfigure(1, weight=1)
    content.grid_rowconfigure(0, weight=1)

    left_panel = tk.Frame(content, bg=C["bg"])
    left_panel.grid(row=0, column=0, sticky="ns", padx=(0,14))

    inc_card = make_card(left_panel, padx=20, pady=18)
    inc_card.pack(fill="x", pady=(0,12))
    make_label(inc_card, "Add Income", 13, "bold", C["green"]).pack(anchor="w")
    make_sep(inc_card).pack(fill="x", pady=8)
    make_label(inc_card, "Amount", color=C["muted"]).pack(anchor="w")
    income_entry = make_entry(inc_card, width=26)
    income_entry.pack(fill="x", pady=(3,8))
    make_label(inc_card, "Category", color=C["muted"]).pack(anchor="w")
    income_cat_var = tk.StringVar(root, value=INCOME_CATEGORIES[0])
    make_combobox(inc_card, textvariable=income_cat_var,
                  values=INCOME_CATEGORIES, width=24).pack(fill="x", pady=(3,8))
    make_label(inc_card, "Description (optional)", color=C["muted"]).pack(anchor="w")
    income_desc_entry = make_entry(inc_card, width=26)
    income_desc_entry.pack(fill="x", pady=(3,10))
    make_btn(inc_card, "＋  Add Income", add_income, "Green.TButton").pack(fill="x", ipady=2)

    exp_card = make_card(left_panel, padx=20, pady=18)
    exp_card.pack(fill="x", pady=(0,12))
    make_label(exp_card, "Add Expense", 13, "bold", C["red"]).pack(anchor="w")
    make_sep(exp_card).pack(fill="x", pady=8)
    make_label(exp_card, "Amount", color=C["muted"]).pack(anchor="w")
    expense_amount_entry = make_entry(exp_card, width=26)
    expense_amount_entry.pack(fill="x", pady=(3,8))
    make_label(exp_card, "Category", color=C["muted"]).pack(anchor="w")
    category_var = tk.StringVar(root, value=EXPENSE_CATEGORIES[0])
    make_combobox(exp_card, textvariable=category_var,
                  values=EXPENSE_CATEGORIES, width=24).pack(fill="x", pady=(3,8))
    make_label(exp_card, "Description (optional)", color=C["muted"]).pack(anchor="w")
    expense_desc_entry = make_entry(exp_card, width=26)
    expense_desc_entry.pack(fill="x", pady=(3,10))
    make_btn(exp_card, "＋  Add Expense", add_expense, "Red.TButton").pack(fill="x", ipady=2)

    qa_card = make_card(left_panel, padx=20, pady=18)
    qa_card.pack(fill="x")
    make_label(qa_card, "Quick Actions", 11, "bold").pack(anchor="w", pady=(0,10))
    make_btn(qa_card, "↺  Refresh Charts", refresh_charts, "Accent.TButton").pack(fill="x", ipady=2, pady=(0,6))
    make_btn(qa_card, "✕  Clear All Data", clear_all,      "Muted.TButton" ).pack(fill="x", ipady=2)

    right_panel = make_card(content)
    right_panel.grid(row=0, column=1, sticky="nsew")
    right_panel.grid_rowconfigure(1, weight=1)
    right_panel.grid_rowconfigure(2, weight=0)
    right_panel.grid_columnconfigure(0, weight=1)

    make_label(right_panel, "Analytics  —  click any point or wedge for details",
               13, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(16,4))

    fig = Figure(figsize=(8,4.5), dpi=100)
    fig.patch.set_facecolor(C["chart_bg"])
    ax_line = fig.add_subplot(121)
    ax_pie  = fig.add_subplot(122)

    chart_canvas = FigureCanvasTkAgg(fig, master=right_panel)
    cw = chart_canvas.get_tk_widget()
    cw.configure(bg=C["surface"], takefocus=0)
    cw.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,4))

    detail_frame = tk.Frame(right_panel, bg=C["surface2"],
                            highlightthickness=1, highlightbackground=C["border"])
    detail_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,10))
    _detail_label = tk.Label(detail_frame,
        text="💡  Click any data point on the line chart or a wedge on the pie chart to see detailed analytics.",
        bg=C["surface2"], fg=C["muted"], font=("Helvetica",9),
        anchor="w", justify="left", wraplength=680)
    _detail_label.pack(fill="x", padx=12, pady=8)

    status_bar = tk.Frame(main_frame, bg=C["surface"],
                          highlightthickness=1, highlightbackground=C["border"])
    status_bar.pack(fill="x", side="bottom")
    tk.Label(status_bar, textvariable=status_var, bg=C["surface"], fg=C["muted"],
             font=("Helvetica",9), anchor="w").pack(side="left", padx=16, pady=5)
    tk.Label(status_bar, text="IB SL CS IA  •  FinanceTracker PRO  •  v4.6",
             bg=C["surface"], fg=C["border"],
             font=("Helvetica",9)).pack(side="right", padx=16)

    income_entry.bind("<Return>",         lambda e: add_income())
    expense_amount_entry.bind("<Return>", lambda e: expense_desc_entry.focus_set())
    expense_desc_entry.bind("<Return>",   lambda e: add_expense())

    fig.canvas.mpl_connect("pick_event",          _on_pick)
    fig.canvas.mpl_connect("motion_notify_event", _on_hover)


# ══════════════════════════════════════════
# TRANSACTIONS PAGE
# ══════════════════════════════════════════
txn_page_inc_val = txn_page_exp_val = txn_page_bal_val = None
txn_filter_var = txn_search_var = None
txn_tree2 = None
txn2_footer_label = None
_sort2_state = {"col":"Date","reverse":True}


def build_txn_page():
    global txn_page_inc_val, txn_page_exp_val, txn_page_bal_val
    global txn_filter_var, txn_search_var, txn_tree2, txn2_footer_label

    build_header(txn_page, active_tab="transactions")

    title_bar = tk.Frame(txn_page, bg=C["bg"])
    title_bar.pack(fill="x", padx=28, pady=(20,0))
    left_title = tk.Frame(title_bar, bg=C["bg"])
    left_title.pack(side="left")
    tk.Label(left_title, text="Transactions", bg=C["bg"], fg=C["white"],
             font=("Helvetica",22,"bold")).pack(anchor="w")
    tk.Label(left_title, text="Track every financial movement", bg=C["bg"],
             fg=C["muted"], font=("Helvetica",10)).pack(anchor="w")
    make_btn(title_bar, "＋  Add Transaction",
             open_add_transaction_dialog, "Accent.TButton"
             ).pack(side="right", ipadx=6, ipady=4)

    cards_row = tk.Frame(txn_page, bg=C["bg"])
    cards_row.pack(fill="x", padx=20, pady=(16,0))
    for i in range(3): cards_row.grid_columnconfigure(i, weight=1)

    def _mc(parent, col, icon, title, color):
        f = make_card(parent, padx=18, pady=14)
        f.grid(row=0, column=col, padx=8, sticky="ew")
        row_f = tk.Frame(f, bg=C["surface"]); row_f.pack(fill="x")
        tk.Label(row_f, text=icon, bg=C["surface2"], fg=color,
                 font=("Helvetica",14,"bold"), width=3, pady=4).pack(side="left")
        info = tk.Frame(row_f, bg=C["surface"]); info.pack(side="left", padx=12)
        tk.Label(info, text=title, bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",9,"bold")).pack(anchor="w")
        val = tk.Label(info, text="$0.00", bg=C["surface"], fg=color,
                       font=("Helvetica",18,"bold"))
        val.pack(anchor="w")
        return val

    txn_page_inc_val = _mc(cards_row, 0, "↑", "TOTAL INCOME",   C["green"])
    txn_page_exp_val = _mc(cards_row, 1, "↓", "TOTAL EXPENSES", C["red"])
    txn_page_bal_val = _mc(cards_row, 2, "▣", "NET BALANCE",    C["yellow"])

    tbl_outer = make_card(txn_page)
    tbl_outer.pack(fill="both", expand=True, padx=28, pady=16)
    tbl_outer.grid_rowconfigure(2, weight=1)
    tbl_outer.grid_columnconfigure(0, weight=1)

    top_bar = tk.Frame(tbl_outer, bg=C["surface"])
    top_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,0))
    tk.Label(top_bar, text="Recent Transactions", bg=C["surface"], fg=C["white"],
             font=("Helvetica",13,"bold")).pack(side="left")

    ctrl_f = tk.Frame(top_bar, bg=C["surface"])
    ctrl_f.pack(side="right")
    txn_filter_var = tk.StringVar(root, value="All")
    txn_search_var = tk.StringVar(root)

    tk.Label(ctrl_f, text="Filter:", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",9)).pack(side="left", padx=(0,4))
    filter_cb = make_combobox(ctrl_f, textvariable=txn_filter_var,
                              values=["All","Income","Expense"], width=9, font_size=9)
    filter_cb.pack(side="left", padx=(0,10))
    filter_cb.bind("<<ComboboxSelected>>", lambda e: refresh_txn_page())

    tk.Label(ctrl_f, text="Search:", bg=C["surface"], fg=C["muted"],
             font=("Helvetica",9)).pack(side="left", padx=(0,4))
    s_entry = tk.Entry(ctrl_f, textvariable=txn_search_var,
                       bg=C["surface2"], fg=C["text"],
                       insertbackground=C["text"], relief="flat", bd=2,
                       font=("Helvetica",9),
                       highlightthickness=0 if IS_MAC else 1,
                       highlightbackground=C["border"],
                       highlightcolor=C["accent"], width=18)
    s_entry.pack(side="left", padx=(0,6))
    s_entry.bind("<ButtonPress-1>",   lambda e: s_entry.focus_set(), add="+")
    s_entry.bind("<ButtonRelease-1>", lambda e: s_entry.focus_set(), add="+")
    s_entry.bind("<Return>", lambda e: refresh_txn_page())

    make_btn(ctrl_f, "🔍 Search", refresh_txn_page, "Ghost.TButton").pack(side="left", padx=(0,4))
    make_btn(ctrl_f, "✕ Clear",
             lambda: (txn_search_var.set(""), txn_filter_var.set("All"), refresh_txn_page()),
             "Ghost.TButton").pack(side="left")

    make_sep(tbl_outer).grid(row=1, column=0, sticky="ew", pady=(10,0))

    COLS       = ("Date","Type","Category","Description","Amount","Actions")
    COL_WIDTHS = (110,    90,    140,        240,          110,     80)

    tree_frame = tk.Frame(tbl_outer, bg=C["surface"])
    tree_frame.grid(row=2, column=0, sticky="nsew")
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    txn_tree2 = ttk.Treeview(tree_frame, columns=COLS, show="headings",
                              selectmode="browse", style="Finance.Treeview")
    col_anchors = {"Amount":"e","Actions":"center"}
    for col, w in zip(COLS, COL_WIDTHS):
        txn_tree2.heading(col, text=col.upper(), command=lambda c=col: sort_txn2(c))
        txn_tree2.column(col, width=w, anchor=col_anchors.get(col,"w"), minwidth=40)

    scroll2 = ttk.Scrollbar(tree_frame, orient="vertical", command=txn_tree2.yview)
    txn_tree2.configure(yscrollcommand=scroll2.set)
    txn_tree2.grid(row=0, column=0, sticky="nsew")
    scroll2.grid(row=0, column=1, sticky="ns")

    txn_tree2.tag_configure("income",      background="#1a2e1a", foreground=C["green"])
    txn_tree2.tag_configure("expense",     background="#2e1a1a", foreground=C["red"])
    txn_tree2.tag_configure("income_alt",  background="#192b19", foreground=C["green"])
    txn_tree2.tag_configure("expense_alt", background="#2b1919", foreground=C["red"])

    txn_tree2.bind("<Delete>",    lambda e: delete_selected_txn2())
    txn_tree2.bind("<BackSpace>", lambda e: delete_selected_txn2())
    txn_tree2.bind("<Double-1>",  on_txn_double_click)

    footer_f = tk.Frame(tbl_outer, bg=C["surface"],
                        highlightthickness=1, highlightbackground=C["border"])
    footer_f.grid(row=3, column=0, sticky="ew")
    txn2_footer_label = tk.Label(footer_f, text="",
                                  bg=C["surface"], fg=C["muted"],
                                  font=("Helvetica",9), anchor="w")
    txn2_footer_label.pack(side="left", padx=14, pady=6)
    make_btn(footer_f, "🗑  Delete Selected",
             delete_selected_txn2, "Red.TButton").pack(side="right", padx=10, pady=4)


def sort_txn2(col):
    if _sort2_state["col"]==col: _sort2_state["reverse"] = not _sort2_state["reverse"]
    else: _sort2_state["col"]=col; _sort2_state["reverse"]=False
    refresh_txn_page()


def refresh_txn_page():
    if txn_tree2 is None: return
    _,sym   = get_currency()
    code,_  = get_currency()
    rate    = EXCHANGE_RATES[code]
    total_inc = to_display(sum(t["amount_usd"] for t in transactions if t["type"]=="Income"))
    total_exp = to_display(sum(t["amount_usd"] for t in transactions if t["type"]=="Expense"))
    net       = total_inc - total_exp
    txn_page_inc_val.config(text=fmt(total_inc))
    txn_page_exp_val.config(text=fmt(total_exp))
    txn_page_bal_val.config(text=fmt(net), fg=C["green"] if net>=0 else C["red"])

    for row in txn_tree2.get_children(): txn_tree2.delete(row)
    ftype  = txn_filter_var.get()
    search = txn_search_var.get().strip().lower()
    visible = []
    for t in transactions:
        if ftype!="All" and t["type"]!=ftype: continue
        if search and search not in (t["category"]+t["description"]+t["type"]).lower(): continue
        visible.append(t)
    key_map = {
        "Date":lambda t:t["date"], "Type":lambda t:t["type"],
        "Category":lambda t:t["category"], "Description":lambda t:t["description"],
        "Amount":lambda t:t["amount_usd"], "Actions":lambda t:t["id"],
    }
    visible.sort(key=key_map.get(_sort2_state["col"],key_map["Date"]),
                 reverse=_sort2_state["reverse"])
    shown_inc = shown_exp = 0.0
    for i, t in enumerate(visible):
        disp = t["amount_usd"]*rate
        if t["type"]=="Expense":
            amt_str=f"-{sym}{disp:,.2f}"; shown_exp+=disp; tag_base="expense"
        else:
            amt_str=f"+{sym}{disp:,.2f}"; shown_inc+=disp; tag_base="income"
        tag = tag_base if i%2==0 else tag_base+"_alt"
        txn_tree2.insert("","end",iid=str(t["id"]),
                         values=(t["date"],t["type"],t["category"],
                                 t["description"] or "—",amt_str,"✕ Delete"),
                         tags=(tag,))
    net_shown = shown_inc-shown_exp
    txn2_footer_label.config(
        text=(f"Showing {len(visible)} record(s)   |   "
              f"Income: {sym}{shown_inc:,.2f}   "
              f"Expenses: {sym}{shown_exp:,.2f}   "
              f"Net: {sym}{net_shown:,.2f}"))


def on_txn_double_click(event):
    if txn_tree2.identify_region(event.x,event.y)=="cell" and \
       txn_tree2.identify_column(event.x)=="#6":
        delete_selected_txn2()


def delete_selected_txn2():
    global transactions
    sel = txn_tree2.selection()
    if not sel:
        messagebox.showinfo("No Selection","Please select a transaction to delete.",parent=root)
        return
    txn_id = int(sel[0])
    if not messagebox.askyesno("Delete Transaction",f"Delete transaction #{txn_id}?",parent=root):
        return
    transactions = [x for x in transactions if x["id"]!=txn_id]
    if current_user:
        save_user_transactions(current_user, transactions)
    refresh_all(); refresh_txn_page()
    set_status(f"Transaction #{txn_id} deleted.")


def open_add_transaction_dialog():
    dlg = tk.Toplevel(root)
    dlg.title("Add Transaction")
    dlg.geometry("440x500")
    dlg.resizable(False,False)
    dlg.configure(bg=C["bg"])
    root.update_idletasks()
    rx = root.winfo_x()+root.winfo_width()//2-220
    ry = root.winfo_y()+root.winfo_height()//2-250
    dlg.geometry(f"440x500+{rx}+{ry}")
    dlg.wait_visibility()
    dlg.grab_set()
    dlg.focus_set()
    dlg.bind_all("<ButtonPress-1>",
                 lambda e: e.widget.focus_set() if e.widget.winfo_exists() else None, add="+")

    tk.Label(dlg, text="Add Transaction", bg=C["bg"], fg=C["white"],
             font=("Helvetica",16,"bold")).pack(pady=(24,4))
    tk.Label(dlg, text="Record a new income or expense", bg=C["bg"], fg=C["muted"],
             font=("Helvetica",10)).pack(pady=(0,16))

    form = tk.Frame(dlg, bg=C["bg"]); form.pack(padx=32, fill="x")

    def fl(t):
        tk.Label(form, text=t, bg=C["bg"], fg=C["muted"],
                 font=("Helvetica",10)).pack(anchor="w", pady=(8,2))

    fl("Transaction Type")
    type_var = tk.StringVar(dlg, value="Expense")
    type_row = tk.Frame(form, bg=C["bg"]); type_row.pack(fill="x", pady=(0,4))
    for tv in ("Income","Expense"):
        tk.Radiobutton(type_row, text=tv, variable=type_var, value=tv,
                       bg=C["bg"], fg=C["text"], selectcolor=C["surface2"],
                       activebackground=C["bg"], activeforeground=C["accent"],
                       font=("Helvetica",10)).pack(side="left", padx=(0,24))

    fl("Amount")
    amt_e = make_entry(form, width=36); amt_e.pack(fill="x")

    fl("Category")
    cat_var_dlg = tk.StringVar(dlg, value=EXPENSE_CATEGORIES[0])
    cat_cb = make_combobox(form, textvariable=cat_var_dlg,
                           values=EXPENSE_CATEGORIES, width=34)
    cat_cb.pack(fill="x")

    def update_cats(*_):
        if type_var.get()=="Income":
            cat_cb["values"]=INCOME_CATEGORIES; cat_var_dlg.set(INCOME_CATEGORIES[0])
        else:
            cat_cb["values"]=EXPENSE_CATEGORIES; cat_var_dlg.set(EXPENSE_CATEGORIES[0])
    type_var.trace_add("write", update_cats)

    fl("Description (optional)")
    desc_e = make_entry(form, width=36); desc_e.pack(fill="x")

    def do_add():
        raw = amt_e.get().strip()
        if not raw:
            messagebox.showerror("Missing Value","Please enter an amount.",parent=dlg)
            amt_e.focus_set(); return
        try:
            amount = float(raw)
            if amount<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input","Please enter a positive number.",parent=dlg)
            amt_e.focus_set(); return
        usd = to_usd(amount)
        txn = {"id":next_txn_id(),"date":today_str(),"type":type_var.get(),
               "category":cat_var_dlg.get(),"description":desc_e.get().strip(),
               "amount_usd":usd}
        transactions.append(txn)
        if current_user:
            save_user_transactions(current_user, transactions)
        refresh_all(); refresh_txn_page()
        _,sym = get_currency()
        set_status(f"✓ {txn['type']} of {sym}{amount:,.2f} added.")
        dlg.destroy()

    make_sep(form).pack(fill="x", pady=16)
    make_btn(form,"＋  Save Transaction",do_add,"Accent.TButton").pack(fill="x",ipady=4)
    desc_e.bind("<Return>", lambda e: do_add())
    amt_e.focus_set()


# ══════════════════════════════════════════
# INVESTMENTS PAGE
# ══════════════════════════════════════════
inv_port_val_lbl  = None
inv_pl_lbl        = None
inv_ret_lbl       = None
inv_holdings_tree = None
_inv_sort_state   = {"col":"Symbol","reverse":False}


def build_inv_page():
    global inv_port_val_lbl, inv_pl_lbl, inv_ret_lbl
    global inv_holdings_tree, _inv_detail_label
    global _inv_fig, _inv_ax, _inv_canvas

    build_header(inv_page, active_tab="investments")

    outer = tk.Frame(inv_page, bg=C["bg"])
    outer.pack(fill="both", expand=True)
    canvas_scroll = tk.Canvas(outer, bg=C["bg"], highlightthickness=0)
    vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas_scroll.yview)
    canvas_scroll.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas_scroll.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas_scroll, bg=C["bg"])
    inner_win = canvas_scroll.create_window((0,0), window=inner, anchor="nw")

    def _on_configure(e):
        canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
    def _on_canvas_resize(e):
        canvas_scroll.itemconfig(inner_win, width=e.width)
    inner.bind("<Configure>", _on_configure)
    canvas_scroll.bind("<Configure>", _on_canvas_resize)

    def _scroll(e):
        delta = -1*(e.delta//120) if IS_WIN else (-1 if e.num==4 else 1)
        canvas_scroll.yview_scroll(int(delta), "units")
    canvas_scroll.bind_all("<MouseWheel>", _scroll)
    canvas_scroll.bind_all("<Button-4>",   _scroll)
    canvas_scroll.bind_all("<Button-5>",   _scroll)

    title_bar = tk.Frame(inner, bg=C["bg"])
    title_bar.pack(fill="x", padx=28, pady=(20,0))
    left_t = tk.Frame(title_bar, bg=C["bg"]); left_t.pack(side="left")
    tk.Label(left_t, text="Investment Portfolio", bg=C["bg"], fg=C["white"],
             font=("Helvetica",22,"bold")).pack(anchor="w")
    tk.Label(left_t, text="Your path to financial growth", bg=C["bg"],
             fg=C["muted"], font=("Helvetica",10)).pack(anchor="w")
    make_btn(title_bar,"＋  Add Investment",
             open_add_investment_dialog,"Purple.TButton"
             ).pack(side="right", ipadx=6, ipady=4)

    cards_row = tk.Frame(inner, bg=C["bg"])
    cards_row.pack(fill="x", padx=28, pady=(20,0))
    for i in range(3): cards_row.grid_columnconfigure(i, weight=1)

    def _ic(parent, col, label, color):
        f = make_card(parent, padx=22, pady=18)
        f.grid(row=0, column=col, padx=8, sticky="ew")
        tk.Label(f, text=label, bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",10)).pack(anchor="w")
        val = tk.Label(f, text="$0.00", bg=C["surface"], fg=color,
                       font=("Helvetica",24,"bold"))
        val.pack(anchor="w", pady=(6,0))
        return val

    inv_port_val_lbl = _ic(cards_row, 0, "Portfolio Value",   C["text"])
    inv_pl_lbl       = _ic(cards_row, 1, "Total Profit/Loss", C["green"])
    inv_ret_lbl      = _ic(cards_row, 2, "Return Percentage", C["green"])

    chart_card = make_card(inner)
    chart_card.pack(fill="x", padx=28, pady=(20,0))

    make_label(chart_card, "Portfolio Performance  —  click any point for analytics",
               12, "bold").pack(anchor="w", padx=20, pady=(16,4))

    _inv_fig = Figure(figsize=(10,3.2), dpi=100)
    _inv_fig.patch.set_facecolor(C["chart_bg"])
    _inv_ax = _inv_fig.add_subplot(111)

    _inv_canvas = FigureCanvasTkAgg(_inv_fig, master=chart_card)
    icw = _inv_canvas.get_tk_widget()
    icw.configure(bg=C["surface"], takefocus=0)
    icw.pack(fill="x", padx=10, pady=(0,4))

    inv_detail_frame = tk.Frame(chart_card, bg=C["surface2"],
                                highlightthickness=1, highlightbackground=C["border"])
    inv_detail_frame.pack(fill="x", padx=10, pady=(0,12))
    _inv_detail_label = tk.Label(inv_detail_frame,
        text="💡  Click any point on the chart to see date, portfolio value, daily change, and cumulative return.",
        bg=C["surface2"], fg=C["muted"], font=("Helvetica",9),
        anchor="w", justify="left", wraplength=900)
    _inv_detail_label.pack(fill="x", padx=12, pady=8)

    _inv_fig.canvas.mpl_connect("pick_event",          _on_inv_pick)
    _inv_fig.canvas.mpl_connect("motion_notify_event", _on_inv_hover)

    hold_card = make_card(inner)
    hold_card.pack(fill="x", padx=28, pady=(20,0))
    hold_card.grid_columnconfigure(0, weight=1)

    make_label(hold_card, "Your Holdings", 13, "bold").pack(anchor="w", padx=20, pady=(16,8))
    make_sep(hold_card).pack(fill="x")

    HCOLS = ("Symbol","Name","Shares","Purchase Price","Current Price","Total Value","Profit/Loss","Actions")
    HWIDS = (80,       200,   70,      120,             120,            110,          130,           70)
    htf = tk.Frame(hold_card, bg=C["surface"])
    htf.pack(fill="x")
    htf.grid_columnconfigure(0, weight=1)

    inv_holdings_tree = ttk.Treeview(htf, columns=HCOLS, show="headings",
                                     selectmode="browse", style="Finance.Treeview",
                                     height=8)
    h_anchors = {"Shares":"center","Purchase Price":"e","Current Price":"e",
                 "Total Value":"e","Profit/Loss":"e","Actions":"center"}
    for col,w in zip(HCOLS,HWIDS):
        inv_holdings_tree.heading(col, text=col.upper(),
                                  command=lambda c=col: _sort_holdings(c))
        inv_holdings_tree.column(col, width=w,
                                 anchor=h_anchors.get(col,"w"), minwidth=40)

    hscroll = ttk.Scrollbar(htf, orient="vertical", command=inv_holdings_tree.yview)
    inv_holdings_tree.configure(yscrollcommand=hscroll.set)
    inv_holdings_tree.grid(row=0, column=0, sticky="nsew")
    hscroll.grid(row=0, column=1, sticky="ns")

    inv_holdings_tree.tag_configure("profit",     foreground=C["green"])
    inv_holdings_tree.tag_configure("loss",       foreground=C["red"])
    inv_holdings_tree.tag_configure("profit_alt", background=C["surface2"], foreground=C["green"])
    inv_holdings_tree.tag_configure("loss_alt",   background=C["surface2"], foreground=C["red"])

    inv_holdings_tree.bind("<Delete>",    lambda e: _delete_holding())
    inv_holdings_tree.bind("<BackSpace>", lambda e: _delete_holding())
    inv_holdings_tree.bind("<Double-1>",  _on_holding_dbl_click)

    hold_footer = tk.Frame(hold_card, bg=C["surface"],
                           highlightthickness=1, highlightbackground=C["border"])
    hold_footer.pack(fill="x")
    make_btn(hold_footer,"🗑  Delete Selected",_delete_holding,"Red.TButton"
             ).pack(side="right", padx=10, pady=6)
    make_btn(hold_footer,"📉  View in Stock Market",_go_market,"Ghost.TButton"
             ).pack(side="left", padx=10, pady=6)

    share_card = make_card(inner)
    share_card.pack(fill="x", padx=28, pady=(20,28))

    make_label(share_card, "Share Holdings", 13, "bold").pack(anchor="w", padx=20, pady=(16,4))
    tk.Label(share_card,
             text="Share your portfolio performance or view it on the Stock Market page.",
             bg=C["surface"], fg=C["muted"],
             font=("Helvetica",10)).pack(anchor="w", padx=20, pady=(0,16))

    sh_btn_row = tk.Frame(share_card, bg=C["surface"])
    sh_btn_row.pack(fill="x", padx=20, pady=(0,20))
    make_btn(sh_btn_row,"📊  View Stock Market",_go_market,"Accent.TButton").pack(side="left", padx=(0,10))


def _sort_holdings(col):
    if _inv_sort_state["col"]==col: _inv_sort_state["reverse"]=not _inv_sort_state["reverse"]
    else: _inv_sort_state["col"]=col; _inv_sort_state["reverse"]=False
    refresh_inv_page()


def _on_holding_dbl_click(event):
    if inv_holdings_tree.identify_region(event.x,event.y)=="cell" and \
       inv_holdings_tree.identify_column(event.x)=="#8":
        _delete_holding()


def _delete_holding():
    global investments
    sel = inv_holdings_tree.selection()
    if not sel:
        messagebox.showinfo("No Selection","Please select a holding to delete.",parent=root)
        return
    inv_id = int(sel[0])
    h = next((x for x in investments if x["id"]==inv_id), None)
    name = h["symbol"] if h else f"#{inv_id}"
    if not messagebox.askyesno("Delete Holding",f"Remove {name} from your portfolio?",parent=root):
        return
    investments = [x for x in investments if x["id"]!=inv_id]
    refresh_inv_page()
    set_status(f"Holding {name} removed.")


def open_add_investment_dialog():
    dlg = tk.Toplevel(root)
    dlg.title("Add Investment")
    dlg.geometry("420x460")
    dlg.resizable(False,False)
    dlg.configure(bg=C["bg"])
    root.update_idletasks()
    rx = root.winfo_x()+root.winfo_width()//2-210
    ry = root.winfo_y()+root.winfo_height()//2-230
    dlg.geometry(f"420x460+{rx}+{ry}")
    dlg.wait_visibility()
    dlg.grab_set()
    dlg.focus_set()
    dlg.bind_all("<ButtonPress-1>",
                 lambda e: e.widget.focus_set() if e.widget.winfo_exists() else None, add="+")

    tk.Label(dlg, text="Add Investment", bg=C["bg"], fg=C["white"],
             font=("Helvetica",16,"bold")).pack(pady=(24,4))
    tk.Label(dlg, text="Add a stock or asset to your portfolio", bg=C["bg"], fg=C["muted"],
             font=("Helvetica",10)).pack(pady=(0,16))

    form = tk.Frame(dlg, bg=C["bg"]); form.pack(padx=32, fill="x")

    fields = {}
    for label, key in [("Ticker Symbol (e.g. AAPL)","symbol"),
                        ("Company Name","name"),
                        ("Number of Shares","shares"),
                        ("Purchase Price per Share ($)","buy_price"),
                        ("Current Price per Share ($)","cur_price")]:
        tk.Label(form, text=label, bg=C["bg"], fg=C["muted"],
                 font=("Helvetica",10)).pack(anchor="w", pady=(8,2))
        e = make_entry(form, width=36); e.pack(fill="x")
        fields[key] = e

    def do_add():
        sym  = fields["symbol"].get().strip().upper()
        name = fields["name"].get().strip()
        if not sym:
            messagebox.showerror("Missing Value","Please enter a ticker symbol.",parent=dlg)
            fields["symbol"].focus_set(); return
        if not name:
            messagebox.showerror("Missing Value","Please enter the company name.",parent=dlg)
            fields["name"].focus_set(); return
        try:
            shares    = float(fields["shares"].get().strip())
            buy_price = float(fields["buy_price"].get().strip())
            cur_price = float(fields["cur_price"].get().strip())
            if shares<=0 or buy_price<=0 or cur_price<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Shares, purchase price, and current price must be positive numbers.",
                                 parent=dlg)
            return
        investments.append({
            "id": next_inv_id(), "symbol":sym, "name":name,
            "shares":shares, "buy_price":buy_price, "cur_price":cur_price,
        })
        refresh_inv_page()
        set_status(f"✓ {sym} added to portfolio.")
        dlg.destroy()

    make_sep(form).pack(fill="x", pady=16)
    make_btn(form,"＋  Add to Portfolio",do_add,"Purple.TButton").pack(fill="x",ipady=4)
    fields["symbol"].focus_set()


def _build_portfolio_history():
    if not investments:
        return [], []
    code,_ = get_currency()
    rate   = EXCHANGE_RATES[code]
    total  = sum(h["shares"]*h["cur_price"] for h in investments) * rate
    dates  = []
    values = []
    base   = total * 0.97
    random.seed(42)
    today  = datetime.now()
    for i in range(30):
        d = today - timedelta(days=29-i)
        dates.append(d.strftime("%b %d"))
        noise = random.uniform(-0.008, 0.010)
        base  = base * (1+noise)
        values.append(round(base, 2))
    values[-1] = round(total, 2)
    return dates, values


def refresh_inv_page():
    global _inv_chart_dates, _inv_chart_values
    global _inv_line_obj, _inv_sel_marker, _inv_hover_ann

    if inv_holdings_tree is None: return
    code,_ = get_currency()
    rate   = EXCHANGE_RATES[code]
    _,sym  = get_currency()

    for row in inv_holdings_tree.get_children():
        inv_holdings_tree.delete(row)

    total_val = pl_total = 0.0
    sort_key_map = {
        "Symbol":        lambda h: h["symbol"],
        "Name":          lambda h: h["name"],
        "Shares":        lambda h: h["shares"],
        "Purchase Price":lambda h: h["buy_price"],
        "Current Price": lambda h: h["cur_price"],
        "Total Value":   lambda h: h["shares"]*h["cur_price"],
        "Profit/Loss":   lambda h: h["shares"]*(h["cur_price"]-h["buy_price"]),
        "Actions":       lambda h: h["id"],
    }
    sorted_inv = sorted(investments,
                        key=sort_key_map.get(_inv_sort_state["col"], sort_key_map["Symbol"]),
                        reverse=_inv_sort_state["reverse"])

    for i, h in enumerate(sorted_inv):
        tv   = h["shares"] * h["cur_price"] * rate
        pl   = h["shares"] * (h["cur_price"] - h["buy_price"]) * rate
        pl_p = ((h["cur_price"]-h["buy_price"])/h["buy_price"]*100) if h["buy_price"] else 0
        total_val += tv
        pl_total  += pl
        pl_str = f"{sym}{pl:,.2f}  ({pl_p:+.2f}%)"
        tag    = ("profit" if pl>=0 else "loss") + ("_alt" if i%2 else "")
        inv_holdings_tree.insert("","end", iid=str(h["id"]),
            values=(h["symbol"], h["name"],
                    f"{h['shares']:g}",
                    f"{sym}{h['buy_price']*rate:,.2f}",
                    f"{sym}{h['cur_price']*rate:,.2f}",
                    f"{sym}{tv:,.2f}", pl_str, "🗑"),
            tags=(tag,))

    cost_total = sum(h["shares"]*h["buy_price"]*rate for h in investments)
    ret_pct    = (pl_total/cost_total*100) if cost_total else 0
    pl_color   = C["green"] if pl_total>=0 else C["red"]
    inv_port_val_lbl.config(text=f"{sym}{total_val:,.2f}", fg=C["text"])
    inv_pl_lbl.config(  text=f"{sym}{pl_total:,.2f}", fg=pl_color)
    inv_ret_lbl.config( text=f"{ret_pct:+.2f}%",       fg=pl_color)

    _inv_ax.clear()
    _inv_sel_marker = None
    _inv_hover_ann  = None

    _inv_ax.set_facecolor(C["chart_bg"])
    _inv_ax.tick_params(colors=C["muted"], labelsize=7.5)
    for sp in _inv_ax.spines.values(): sp.set_color(C["border"])
    _inv_ax.grid(True, linestyle="--", alpha=0.25, color=C["border"])

    dates, values = _build_portfolio_history()
    _inv_chart_dates  = dates
    _inv_chart_values = values

    if dates:
        x_idx = list(range(len(dates)))
        _inv_line_obj, = _inv_ax.plot(
            x_idx, values,
            marker="o", linewidth=2, color=C["purple"],
            markersize=4, picker=8, zorder=3
        )
        _inv_ax.fill_between(x_idx, values,
                              alpha=0.12, color=C["purple"])
        step = max(1, len(dates)//10)
        _inv_ax.set_xticks(x_idx[::step])
        _inv_ax.set_xticklabels(dates[::step], fontsize=7, color=C["muted"],
                                 rotation=20, ha="right")
        _inv_ax.set_title("30-Day Portfolio Performance  (click a point)",
                           color=C["text"], fontsize=9.5, pad=8)

    _inv_fig.tight_layout(pad=1.8)
    _inv_canvas.draw()


# ══════════════════════════════════════════
# STOCK MARKET PAGE
# ══════════════════════════════════════════
_market_tab_var       = None   # "all" | "portfolio"
_market_all_tree      = None
_market_port_tree     = None
_market_port_frame    = None
_market_all_frame     = None
_port_total_lbl       = None
_port_positions_lbl   = None
_port_avg_ret_lbl     = None
_market_sort_state    = {"col": "Symbol", "reverse": False}
_port_sort_state      = {"col": "Symbol", "reverse": False}

# Sparkline popup state
_spark_window         = None


def _simulate_price_update():
    """Apply small random ±0–2 % fluctuations to market_stocks."""
    random.seed(int(time.time()))
    for s in market_stocks:
        factor      = random.uniform(-0.02, 0.02)
        old_price   = s["price"]
        s["price"]  = round(old_price * (1 + factor), 2)
        s["change_abs"] = round(s["price"] - old_price + s["change_abs"], 2)
        s["change_pct"] = round(s["change_abs"] / (s["price"] - s["change_abs"]) * 100
                                if (s["price"] - s["change_abs"]) != 0 else 0, 2)
        s["volume"] = int(s["volume"] * random.uniform(0.97, 1.03))


def _get_market_price(symbol: str) -> float:
    """Return the current simulated market price for a symbol (or 0 if unknown)."""
    for s in market_stocks:
        if s["symbol"] == symbol.upper():
            return s["price"]
    return 0.0


def _get_market_change_pct(symbol: str) -> float:
    for s in market_stocks:
        if s["symbol"] == symbol.upper():
            return s["change_pct"]
    return 0.0


def _open_sparkline(symbol: str, company: str):
    """Show a 30-day simulated price history popup for a stock."""
    global _spark_window
    if _spark_window and _spark_window.winfo_exists():
        _spark_window.destroy()

    _spark_window = tk.Toplevel(root)
    _spark_window.title(f"{symbol} — Price History")
    _spark_window.geometry("520x340")
    _spark_window.resizable(False, False)
    _spark_window.configure(bg=C["bg"])
    root.update_idletasks()
    rx = root.winfo_x() + root.winfo_width()//2 - 260
    ry = root.winfo_y() + root.winfo_height()//2 - 170
    _spark_window.geometry(f"520x340+{rx}+{ry}")

    # Generate 30-day history
    base_price = _get_market_price(symbol)
    if base_price == 0:
        base_price = 100.0
    random.seed(hash(symbol) % 9999)
    today   = datetime.now()
    prices  = []
    dates   = []
    p       = base_price * 0.95
    for i in range(30):
        d = today - timedelta(days=29-i)
        dates.append(d.strftime("%b %d"))
        p = round(p * (1 + random.uniform(-0.015, 0.018)), 2)
        prices.append(p)
    prices[-1] = base_price

    sf = Figure(figsize=(5, 2.8), dpi=100)
    sf.patch.set_facecolor(C["bg"])
    ax = sf.add_subplot(111)
    ax.set_facecolor(C["surface"])
    color = C["green"] if prices[-1] >= prices[0] else C["red"]
    ax.plot(range(len(prices)), prices, linewidth=2, color=color)
    ax.fill_between(range(len(prices)), prices, alpha=0.15, color=color)
    step = max(1, len(dates)//6)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels(dates[::step], fontsize=7, color=C["muted"], rotation=20, ha="right")
    ax.tick_params(colors=C["muted"], labelsize=7.5)
    for sp in ax.spines.values(): sp.set_color(C["border"])
    ax.set_title(f"{symbol}  —  {company}  (30-day)", color=C["text"], fontsize=9)
    sf.tight_layout(pad=1.5)

    tk.Label(_spark_window, text=f"{symbol}  ·  {company}",
             bg=C["bg"], fg=C["white"], font=("Helvetica",13,"bold")).pack(pady=(14,4))
    pct_chg = ((prices[-1]-prices[0])/prices[0]*100) if prices[0] else 0
    clr = C["green"] if pct_chg >= 0 else C["red"]
    arrow = "▲" if pct_chg >= 0 else "▼"
    tk.Label(_spark_window,
             text=f"${prices[-1]:,.2f}   {arrow} {pct_chg:+.2f}% over 30 days",
             bg=C["bg"], fg=clr, font=("Helvetica",10)).pack()
    sc = FigureCanvasTkAgg(sf, master=_spark_window)
    sc.get_tk_widget().configure(bg=C["bg"], takefocus=0)
    sc.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(4,10))
    sc.draw()


def build_market_page():
    global _market_tab_var, _market_all_tree, _market_port_tree
    global _market_port_frame, _market_all_frame
    global _port_total_lbl, _port_positions_lbl, _port_avg_ret_lbl

    build_header(market_page, active_tab="market")

    # ── Title bar ──
    title_bar = tk.Frame(market_page, bg=C["bg"])
    title_bar.pack(fill="x", padx=28, pady=(20,0))
    left_t = tk.Frame(title_bar, bg=C["bg"]); left_t.pack(side="left")
    tk.Label(left_t, text="Stock Market", bg=C["bg"], fg=C["white"],
             font=("Helvetica",22,"bold")).pack(anchor="w")
    tk.Label(left_t, text="Monitor the pulse of global markets", bg=C["bg"],
             fg=C["muted"], font=("Helvetica",10)).pack(anchor="w")
    make_btn(title_bar, "↺  Refresh Data",
             _do_refresh_market, "Accent.TButton").pack(side="right", ipadx=6, ipady=4)

    # ── Tab strip ──
    _market_tab_var = tk.StringVar(value="all")
    tab_bar = tk.Frame(market_page, bg=C["bg"])
    tab_bar.pack(fill="x", padx=28, pady=(16,0))

    tab_btn_all  = [None]
    tab_btn_port = [None]

    def _switch_tab(mode):
        _market_tab_var.set(mode)
        if mode == "all":
            _market_all_frame.pack(fill="both", expand=True)
            _market_port_frame.pack_forget()
            tab_btn_all[0].config(style="NavActive.TButton")
            tab_btn_port[0].config(style="NavInactive.TButton")
        else:
            _market_port_frame.pack(fill="both", expand=True)
            _market_all_frame.pack_forget()
            tab_btn_all[0].config(style="NavInactive.TButton")
            tab_btn_port[0].config(style="NavActive.TButton")
            _refresh_portfolio_tab()

    tab_strip = tk.Frame(tab_bar, bg=C["surface"],
                         highlightthickness=1, highlightbackground=C["border"])
    tab_strip.pack(side="left")

    btn_all  = ttk.Button(tab_strip, text="  📋  All Stocks  ",
                          command=lambda: _switch_tab("all"),
                          style="NavActive.TButton")
    btn_port = ttk.Button(tab_strip, text="  💼  My Portfolio  ",
                          command=lambda: _switch_tab("portfolio"),
                          style="NavInactive.TButton")
    btn_all.pack(side="left", ipady=5, padx=(0,0))
    btn_port.pack(side="left", ipady=5)
    tab_btn_all[0]  = btn_all
    tab_btn_port[0] = btn_port

    # ── Live dot ──
    dot_frame = tk.Frame(tab_bar, bg=C["bg"]); dot_frame.pack(side="left", padx=14)
    tk.Canvas(dot_frame, width=8, height=8, bg=C["bg"],
              highlightthickness=0).pack(side="left")
    tk.Label(dot_frame, text="● LIVE", bg=C["bg"], fg=C["green"],
             font=("Helvetica",8,"bold")).pack(side="left")
    tk.Label(dot_frame, text="  Simulated market data",
             bg=C["bg"], fg=C["muted"], font=("Helvetica",8)).pack(side="left")

    # ── Content area ──
    content_area = tk.Frame(market_page, bg=C["bg"])
    content_area.pack(fill="both", expand=True, padx=28, pady=(12,16))

    # ══ ALL STOCKS panel ══
    _market_all_frame = tk.Frame(content_area, bg=C["bg"])

    all_card = make_card(_market_all_frame)
    all_card.pack(fill="both", expand=True)
    all_card.grid_rowconfigure(1, weight=1)
    all_card.grid_columnconfigure(0, weight=1)

    hdr_f = tk.Frame(all_card, bg=C["surface"])
    hdr_f.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,8))
    tk.Label(hdr_f, text="Market Overview", bg=C["surface"], fg=C["white"],
             font=("Helvetica",13,"bold")).pack(side="left")
    tk.Label(hdr_f, text=f"  {len(market_stocks)} stocks", bg=C["surface"],
             fg=C["muted"], font=("Helvetica",9)).pack(side="left")

    make_sep(all_card).grid(row=0, column=0, sticky="sew", padx=0, pady=(50,0))

    ALL_COLS  = ("Symbol","Company","Price","Change","Volume","Market Cap","Chart")
    ALL_WIDTHS= (90,       260,      100,    110,     110,     110,         60)
    tree_wrap = tk.Frame(all_card, bg=C["surface"])
    tree_wrap.grid(row=1, column=0, sticky="nsew")
    tree_wrap.grid_rowconfigure(0, weight=1)
    tree_wrap.grid_columnconfigure(0, weight=1)

    _market_all_tree = ttk.Treeview(tree_wrap, columns=ALL_COLS, show="headings",
                                    selectmode="browse", style="Market.Treeview")
    anchors = {"Price":"e","Change":"e","Volume":"e","Market Cap":"e","Chart":"center"}
    for col, w in zip(ALL_COLS, ALL_WIDTHS):
        _market_all_tree.heading(col, text=col.upper(),
                                  command=lambda c=col: _sort_market_all(c))
        _market_all_tree.column(col, width=w, anchor=anchors.get(col,"w"), minwidth=40)

    mscroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=_market_all_tree.yview)
    _market_all_tree.configure(yscrollcommand=mscroll.set)
    _market_all_tree.grid(row=0, column=0, sticky="nsew")
    mscroll.grid(row=0, column=1, sticky="ns")

    _market_all_tree.tag_configure("up",     foreground=C["green"])
    _market_all_tree.tag_configure("down",   foreground=C["red"])
    _market_all_tree.tag_configure("up_alt", background=C["surface2"], foreground=C["green"])
    _market_all_tree.tag_configure("down_alt", background=C["surface2"], foreground=C["red"])

    _market_all_tree.bind("<Double-1>", _on_market_tree_click)
    _market_all_tree.bind("<Return>",   lambda e: _on_chart_click_selected())

    all_footer = tk.Frame(all_card, bg=C["surface"],
                          highlightthickness=1, highlightbackground=C["border"])
    all_footer.grid(row=2, column=0, sticky="ew")
    tk.Label(all_footer,
             text="Double-click a row or click 📈 in the Chart column to view 30-day price history.",
             bg=C["surface"], fg=C["muted"], font=("Helvetica",8), anchor="w"
             ).pack(side="left", padx=14, pady=6)

    # ══ MY PORTFOLIO panel ══
    _market_port_frame = tk.Frame(content_area, bg=C["bg"])

    port_card = make_card(_market_port_frame)
    port_card.pack(fill="both", expand=True)
    port_card.grid_rowconfigure(1, weight=1)
    port_card.grid_columnconfigure(0, weight=1)

    port_hdr = tk.Frame(port_card, bg=C["surface"])
    port_hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,8))
    tk.Label(port_hdr, text="Your Portfolio Stocks", bg=C["surface"], fg=C["white"],
             font=("Helvetica",13,"bold")).pack(side="left")
    tk.Label(port_hdr, text="  Current market prices for your investments",
             bg=C["surface"], fg=C["muted"], font=("Helvetica",9)).pack(side="left")

    make_sep(port_card).grid(row=0, column=0, sticky="sew", padx=0, pady=(50,0))

    PORT_COLS  = ("Symbol","Company","Your Shares","Current Price","Today's Change","Position Value")
    PORT_WIDTHS= (90,       260,      100,          120,            130,             130)
    ptree_wrap = tk.Frame(port_card, bg=C["surface"])
    ptree_wrap.grid(row=1, column=0, sticky="nsew")
    ptree_wrap.grid_rowconfigure(0, weight=1)
    ptree_wrap.grid_columnconfigure(0, weight=1)

    _market_port_tree = ttk.Treeview(ptree_wrap, columns=PORT_COLS, show="headings",
                                      selectmode="browse", style="Market.Treeview")
    p_anchors = {"Your Shares":"center","Current Price":"e","Today's Change":"e","Position Value":"e"}
    for col, w in zip(PORT_COLS, PORT_WIDTHS):
        _market_port_tree.heading(col, text=col.upper(),
                                   command=lambda c=col: _sort_portfolio_tab(c))
        _market_port_tree.column(col, width=w, anchor=p_anchors.get(col,"w"), minwidth=40)

    pscroll = ttk.Scrollbar(ptree_wrap, orient="vertical", command=_market_port_tree.yview)
    _market_port_tree.configure(yscrollcommand=pscroll.set)
    _market_port_tree.grid(row=0, column=0, sticky="nsew")
    pscroll.grid(row=0, column=1, sticky="ns")

    _market_port_tree.tag_configure("up",      foreground=C["green"])
    _market_port_tree.tag_configure("down",    foreground=C["red"])
    _market_port_tree.tag_configure("up_alt",  background=C["surface2"], foreground=C["green"])
    _market_port_tree.tag_configure("down_alt",background=C["surface2"], foreground=C["red"])

    # Portfolio summary card
    summary_card = make_card(_market_port_frame, padx=24, pady=20)
    summary_card.pack(fill="x", pady=(12,0))
    tk.Label(summary_card, text="Portfolio Summary", bg=C["surface"], fg=C["white"],
             font=("Helvetica",12,"bold")).pack(anchor="w", pady=(0,12))
    make_sep(summary_card).pack(fill="x", pady=(0,14))
    stats_row = tk.Frame(summary_card, bg=C["surface"]); stats_row.pack(fill="x")
    for i in range(3): stats_row.grid_columnconfigure(i, weight=1)

    def _stat(col, label):
        f = tk.Frame(stats_row, bg=C["surface"]); f.grid(row=0, column=col, sticky="w")
        tk.Label(f, text=label, bg=C["surface"], fg=C["muted"],
                 font=("Helvetica",9)).pack(anchor="w")
        val = tk.Label(f, text="—", bg=C["surface"], fg=C["text"],
                       font=("Helvetica",18,"bold"))
        val.pack(anchor="w", pady=(4,0))
        return val

    _port_positions_lbl = _stat(0, "Total Positions")
    _port_total_lbl     = _stat(1, "Current Portfolio Value")
    _port_avg_ret_lbl   = _stat(2, "Average Return")

    # Start with All Stocks visible
    _market_all_frame.pack(fill="both", expand=True)


def _sort_market_all(col):
    if _market_sort_state["col"] == col:
        _market_sort_state["reverse"] = not _market_sort_state["reverse"]
    else:
        _market_sort_state["col"] = col
        _market_sort_state["reverse"] = False
    _refresh_all_stocks_tab()


def _sort_portfolio_tab(col):
    if _port_sort_state["col"] == col:
        _port_sort_state["reverse"] = not _port_sort_state["reverse"]
    else:
        _port_sort_state["col"] = col
        _port_sort_state["reverse"] = False
    _refresh_portfolio_tab()


def _refresh_all_stocks_tab():
    if _market_all_tree is None: return
    _,sym  = get_currency()
    code,_ = get_currency()
    rate   = EXCHANGE_RATES[code]

    for row in _market_all_tree.get_children():
        _market_all_tree.delete(row)

    sort_funcs = {
        "Symbol":     lambda s: s["symbol"],
        "Company":    lambda s: s["name"],
        "Price":      lambda s: s["price"],
        "Change":     lambda s: s["change_pct"],
        "Volume":     lambda s: s["volume"],
        "Market Cap": lambda s: s["mktcap"],
        "Chart":      lambda s: s["symbol"],
    }
    sf = sort_funcs.get(_market_sort_state["col"], sort_funcs["Symbol"])
    sorted_stocks = sorted(market_stocks, key=sf, reverse=_market_sort_state["reverse"])

    for i, s in enumerate(sorted_stocks):
        price_disp = s["price"] * rate
        chg_abs    = s["change_abs"] * rate
        chg_pct    = s["change_pct"]
        arrow      = "▲" if chg_pct >= 0 else "▼"
        chg_str    = f"{arrow} {chg_pct:+.2f}%  {sym}{abs(chg_abs):,.2f}"
        tag_base   = "up" if chg_pct >= 0 else "down"
        tag        = tag_base + ("_alt" if i % 2 else "")
        vol_str    = f"{s['volume']:,}"
        # Recalculate mktcap display
        mktcap_str = s["mktcap"]
        _market_all_tree.insert("", "end", iid=s["symbol"],
            values=(s["symbol"], s["name"],
                    f"{sym}{price_disp:,.2f}",
                    chg_str,
                    vol_str,
                    mktcap_str,
                    "📈"),
            tags=(tag,))


def _refresh_portfolio_tab():
    if _market_port_tree is None: return
    _,sym  = get_currency()
    code,_ = get_currency()
    rate   = EXCHANGE_RATES[code]

    for row in _market_port_tree.get_children():
        _market_port_tree.delete(row)

    if not investments:
        if _port_positions_lbl:
            _port_positions_lbl.config(text="0", fg=C["muted"])
            _port_total_lbl.config(text=f"{sym}0.00", fg=C["muted"])
            _port_avg_ret_lbl.config(text="0.00%", fg=C["muted"])
        return

    sort_funcs = {
        "Symbol":         lambda h: h["symbol"],
        "Company":        lambda h: h["name"],
        "Your Shares":    lambda h: h["shares"],
        "Current Price":  lambda h: h["cur_price"],
        "Today's Change": lambda h: _get_market_change_pct(h["symbol"]),
        "Position Value": lambda h: h["shares"] * h["cur_price"],
    }
    sf = sort_funcs.get(_port_sort_state["col"], sort_funcs["Symbol"])
    sorted_inv = sorted(investments, key=sf, reverse=_port_sort_state["reverse"])

    total_val = 0.0
    total_ret_pct_sum = 0.0

    for i, h in enumerate(sorted_inv):
        # Use market price if the symbol exists in market data
        mkt_price   = _get_market_price(h["symbol"])
        cur_price   = mkt_price if mkt_price > 0 else h["cur_price"]
        chg_pct     = _get_market_change_pct(h["symbol"]) if mkt_price > 0 else 0.0
        pos_val     = h["shares"] * cur_price * rate
        total_val  += pos_val
        total_ret_pct_sum += chg_pct

        arrow    = "▲" if chg_pct >= 0 else "▼"
        chg_str  = f"{arrow} {chg_pct:+.2f}%"
        tag_base = "up" if chg_pct >= 0 else "down"
        tag      = tag_base + ("_alt" if i % 2 else "")

        _market_port_tree.insert("", "end", iid=str(h["id"]),
            values=(h["symbol"], h["name"],
                    f"{h['shares']:g}",
                    f"{sym}{cur_price*rate:,.2f}",
                    chg_str,
                    f"{sym}{pos_val:,.2f}"),
            tags=(tag,))

    avg_ret = total_ret_pct_sum / len(investments) if investments else 0
    ret_color = C["green"] if avg_ret >= 0 else C["red"]

    if _port_positions_lbl:
        _port_positions_lbl.config(text=str(len(investments)), fg=C["text"])
        _port_total_lbl.config(text=f"{sym}{total_val:,.2f}", fg=C["text"])
        _port_avg_ret_lbl.config(text=f"{avg_ret:+.2f}%", fg=ret_color)


def _on_market_tree_click(event):
    """Double-click or Chart column click opens sparkline."""
    region = _market_all_tree.identify_region(event.x, event.y)
    col_id = _market_all_tree.identify_column(event.x)
    item   = _market_all_tree.identify_row(event.y)
    if not item: return
    # col #7 is Chart
    if region == "cell":
        symbol  = item  # iid is symbol
        company = next((s["name"] for s in market_stocks if s["symbol"]==symbol), symbol)
        _open_sparkline(symbol, company)


def _on_chart_click_selected():
    sel = _market_all_tree.selection()
    if not sel: return
    symbol  = sel[0]
    company = next((s["name"] for s in market_stocks if s["symbol"]==symbol), symbol)
    _open_sparkline(symbol, company)


def _do_refresh_market():
    _simulate_price_update()
    _refresh_all_stocks_tab()
    if _market_tab_var and _market_tab_var.get() == "portfolio":
        _refresh_portfolio_tab()
    set_status("📈  Market data refreshed.")


def refresh_market_page():
    _refresh_all_stocks_tab()
    if _market_tab_var and _market_tab_var.get() == "portfolio":
        _refresh_portfolio_tab()


# ══════════════════════════════════════════
# CORE LOGIC
# ══════════════════════════════════════════
def refresh_summary():
    total_inc = to_display(sum(r["amount_usd"] for r in transactions if r["type"]=="Income"))
    total_exp = to_display(sum(r["amount_usd"] for r in transactions if r["type"]=="Expense"))
    balance   = total_inc-total_exp
    txns      = len(transactions)
    income_val.config(text=fmt(total_inc))
    expense_val.config(text=fmt(total_exp))
    balance_val.config(text=fmt(balance), fg=C["green"] if balance>=0 else C["red"])
    txn_val.config(text=str(txns))
    inc_count = sum(1 for r in transactions if r["type"]=="Income")
    exp_count = sum(1 for r in transactions if r["type"]=="Expense")
    income_sub.config(text=f"{inc_count} entr{'y' if inc_count==1 else 'ies'}")
    expense_sub.config(text=f"{exp_count} entr{'y' if exp_count==1 else 'ies'}")
    pct = (total_exp/total_inc*100) if total_inc else 0
    balance_sub.config(text=f"{pct:.1f}% of income spent")
    txn_sub.config(text="total records")


def refresh_charts():
    global _line_income_obj, _line_expense_obj
    global _pie_wedges, _pie_labels_data
    global _chart_months, _chart_income_pts, _chart_expense_pts
    global _selected_marker, _hover_annotation

    ax_line.clear(); ax_pie.clear()
    _selected_marker = None; _hover_annotation = None

    for ax in (ax_line, ax_pie):
        ax.set_facecolor(C["chart_bg"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for sp in ax.spines.values(): sp.set_color(C["border"])

    months, income_data, expense_data = _get_monthly_data()
    _chart_months      = months
    _chart_income_pts  = income_data
    _chart_expense_pts = expense_data
    x_idx = list(range(len(months)))

    _line_income_obj, = ax_line.plot(
        x_idx, income_data, marker="o", linewidth=2.2,
        color=C["green"], label="Income", markersize=7, picker=8, zorder=3)
    _line_expense_obj, = ax_line.plot(
        x_idx, expense_data, marker="o", linewidth=2.2,
        color=C["red"], label="Expenses", markersize=7, picker=8, zorder=3)
    ax_line.fill_between(x_idx, income_data, expense_data, alpha=0.08, color=C["green"])
    ax_line.set_xticks(x_idx)
    ax_line.set_xticklabels(months, fontsize=7.5, color=C["muted"], rotation=20, ha="right")
    ax_line.set_title("Income vs Expenses  (click a point)",
                       color=C["text"], fontsize=9.5, pad=8)
    ax_line.legend(facecolor=C["surface"], labelcolor=C["muted"],
                   fontsize=8, framealpha=0.6)

    exp_txns = [r for r in transactions if r["type"]=="Expense"]
    if exp_txns:
        df   = pd.DataFrame(exp_txns)
        cats = df.groupby("category")["amount_usd"].sum()
        _pie_labels_data = list(cats.index)
        wedges,texts,autotexts = ax_pie.pie(
            cats, labels=cats.index, autopct="%1.1f%%",
            colors=PIE_COLOURS[:len(cats)], startangle=90,
            wedgeprops={"linewidth":1.5,"edgecolor":C["chart_bg"]})
    else:
        sc = ["Bills","Food","Shopping","Transport"]
        _pie_labels_data = sc
        wedges,texts,autotexts = ax_pie.pie(
            [40,25,20,15], labels=sc, autopct="%1.1f%%",
            colors=PIE_COLOURS[:4], startangle=90,
            wedgeprops={"linewidth":1.5,"edgecolor":C["chart_bg"]})

    _pie_wedges = list(wedges)
    for w in _pie_wedges: w.set_picker(True)
    for t in texts: t.set_color(C["muted"]); t.set_fontsize(7.5)
    for at in autotexts: at.set_color(C["text"]); at.set_fontsize(7)
    ax_pie.set_title("Expenses by Category  (click a wedge)",
                      color=C["text"], fontsize=9.5, pad=8)
    fig.tight_layout(pad=2.0)
    chart_canvas.draw()


def refresh_all():
    if income_val is None: return
    refresh_summary()
    refresh_charts()


def add_income():
    raw  = income_entry.get().strip()
    desc = income_desc_entry.get().strip()
    cat  = income_cat_var.get()
    if not raw:
        messagebox.showerror("Missing Value","Please enter an income amount.",parent=root)
        income_entry.focus_set(); return
    try:
        amount = float(raw)
        if amount<=0: raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input","Please enter a positive number.",parent=root)
        income_entry.focus_set(); return
    transactions.append({
        "id":next_txn_id(),"date":today_str(),"type":"Income",
        "category":cat,"description":desc,"amount_usd":to_usd(amount),
    })
    income_entry.delete(0,tk.END)
    income_desc_entry.delete(0,tk.END)
    if current_user:
        save_user_transactions(current_user, transactions)
    refresh_all()
    _,sym = get_currency()
    set_status(f"✓ Income of {sym}{amount:,.2f} added.")


def add_expense():
    raw_amt  = expense_amount_entry.get().strip()
    category = category_var.get()
    desc     = expense_desc_entry.get().strip()
    if not raw_amt:
        messagebox.showerror("Missing Value","Please enter an expense amount.",parent=root)
        expense_amount_entry.focus_set(); return
    try:
        amount = float(raw_amt)
        if amount<=0: raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input","Please enter a positive number.",parent=root)
        expense_amount_entry.focus_set(); return
    transactions.append({
        "id":next_txn_id(),"date":today_str(),"type":"Expense",
        "category":category,"description":desc,"amount_usd":to_usd(amount),
    })
    expense_amount_entry.delete(0,tk.END)
    expense_desc_entry.delete(0,tk.END)
    if current_user:
        save_user_transactions(current_user, transactions)
    refresh_all()
    _,sym = get_currency()
    set_status(f"✓ Expense of {sym}{amount:,.2f} ({category}) added.")


def clear_all():
    if not transactions: set_status("Nothing to clear."); return
    if messagebox.askyesno("Clear Data","This will delete ALL records.\nContinue?",parent=root):
        transactions.clear()
        if current_user:
            save_user_transactions(current_user, transactions)
        refresh_all(); refresh_txn_page()
        _show_detail("💡  All data cleared.")
        set_status("All data cleared.")


# ══════════════════════════════════════════
# BUILD & LAUNCH
# ══════════════════════════════════════════
build_home()
build_auth_frame()
build_main_frame()
build_txn_page()
build_inv_page()
build_market_page()

refresh_all()
refresh_txn_page()
refresh_inv_page()
refresh_market_page()

show_frame(home_frame)
root.mainloop()
