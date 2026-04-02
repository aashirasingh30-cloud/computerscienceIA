"""
Personal Finance Manager - IB Computer Science SL IA
Criterion B - Design: Basic Application Structure
Author: [Your Name]
Date: 2026

Modules used:
    - tkinter   : GUI framework
    - ttk       : Themed widgets (Notebook, Treeview, etc.)
    - sqlite3   : Data persistence
    - matplotlib: Charts and graphs
    - datetime  : Date handling
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import random  # used to simulate stock prices

# Matplotlib embedded inside Tkinter
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ===========================================================================
# COLOUR CONSTANTS  (centralised theme - easy to update)
# ===========================================================================
BG_DARK   = "#0f1117"   # main window background
BG_CARD   = "#1a1d27"   # card / frame background
BG_TAB    = "#12151e"   # notebook tab area
ACCENT    = "#4f8ef7"   # primary blue accent
ACCENT2   = "#3dd68c"   # green (profit / income)
DANGER    = "#f75f5f"   # red (loss / expense)
TEXT_MAIN = "#e8eaf0"   # primary text
TEXT_DIM  = "#6b7280"   # muted / secondary text
BORDER    = "#2a2d3a"   # subtle border colour

FONT_H1   = ("Helvetica", 22, "bold")
FONT_H2   = ("Helvetica", 14, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SMALL= ("Helvetica", 9)


# ===========================================================================
# DATABASE MANAGER  (Criterion B - Data Storage Design)
# ===========================================================================
class DataManager:
    """
    Handles all SQLite read / write operations.
    Tables:
        transactions  - income and expense records
        investments   - portfolio holdings
        savings_goals - user-defined savings targets
        stocks        - stocks the user tracks
    """

    def __init__(self, db_path="finance_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    # ---- Schema creation -----------------------------------------------
    def _create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,
                category    TEXT    NOT NULL,
                description TEXT,
                amount      REAL    NOT NULL,
                type        TEXT    NOT NULL   -- 'Income' or 'Expense'
            );

            CREATE TABLE IF NOT EXISTS investments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL,
                ticker       TEXT,
                quantity     REAL    NOT NULL,
                buy_price    REAL    NOT NULL,
                current_price REAL   NOT NULL,
                date_bought  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS savings_goals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name       TEXT    NOT NULL,
                target_amount   REAL    NOT NULL,
                saved_amount    REAL    NOT NULL DEFAULT 0,
                monthly_contrib REAL    NOT NULL DEFAULT 0,
                deadline        TEXT
            );

            CREATE TABLE IF NOT EXISTS stocks (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT    NOT NULL UNIQUE,
                name   TEXT    NOT NULL
            );
        """)
        self.conn.commit()

    # ---- Transaction CRUD ----------------------------------------------
    def add_transaction(self, date, category, description, amount, t_type):
        self.cursor.execute(
            "INSERT INTO transactions (date, category, description, amount, type) "
            "VALUES (?, ?, ?, ?, ?)",
            (date, category, description, amount, t_type)
        )
        self.conn.commit()

    def get_transactions(self):
        self.cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
        return self.cursor.fetchall()

    def get_totals(self):
        """Returns (total_income, total_expenses)."""
        self.cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='Income'"
        )
        income = self.cursor.fetchone()[0] or 0.0

        self.cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE type='Expense'"
        )
        expenses = self.cursor.fetchone()[0] or 0.0
        return income, expenses

    # ---- Investment CRUD -----------------------------------------------
    def add_investment(self, name, ticker, quantity, buy_price,
                       current_price, date_bought):
        self.cursor.execute(
            "INSERT INTO investments "
            "(name, ticker, quantity, buy_price, current_price, date_bought) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, ticker, quantity, buy_price, current_price, date_bought)
        )
        self.conn.commit()

    def get_investments(self):
        self.cursor.execute("SELECT * FROM investments")
        return self.cursor.fetchall()

    # ---- Savings goal CRUD --------------------------------------------
    def add_savings_goal(self, name, target, saved, monthly, deadline):
        self.cursor.execute(
            "INSERT INTO savings_goals "
            "(goal_name, target_amount, saved_amount, monthly_contrib, deadline) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, target, saved, monthly, deadline)
        )
        self.conn.commit()

    def get_savings_goals(self):
        self.cursor.execute("SELECT * FROM savings_goals")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


# ===========================================================================
# STOCK TRACKER  (simulates live prices; replace with API call if desired)
# ===========================================================================
class StockTracker:
    """
    Simulates stock market data.
    In a real deployment, replace _fetch_price() with a
    yfinance / Alpha Vantage API call.
    """
    DEMO_STOCKS = {
        "AAPL": ("Apple Inc.",         182.50),
        "TSLA": ("Tesla Inc.",          248.30),
        "GOOGL":("Alphabet Inc.",      2800.00),
        "AMZN": ("Amazon.com Inc.",    3400.00),
        "MSFT": ("Microsoft Corp.",     415.00),
        "NVDA": ("NVIDIA Corp.",        880.00),
    }

    def get_price(self, ticker: str) -> float:
        """Return simulated current price with ±2 % random variation."""
        base = self.DEMO_STOCKS.get(ticker, ("Unknown", 100.0))[1]
        variation = random.uniform(-0.02, 0.02)
        return round(base * (1 + variation), 2)

    def get_all_market_data(self) -> list[dict]:
        """Return list of dicts with ticker, name, price, change %."""
        data = []
        for ticker, (name, base) in self.DEMO_STOCKS.items():
            price  = self.get_price(ticker)
            change = round(((price - base) / base) * 100, 2)
            data.append({
                "ticker": ticker,
                "name":   name,
                "price":  price,
                "change": change
            })
        return data


# ===========================================================================
# MAIN APPLICATION  (Criterion B - Overall Structure)
# ===========================================================================
class FinanceApp(tk.Tk):
    """
    Root Tkinter window.
    Builds the ttk.Notebook and wires all tab frames together.
    """

    def __init__(self):
        super().__init__()
        self.title("Personal Finance Manager")
        self.geometry("1200x750")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Shared data layer
        self.db      = DataManager()
        self.stocks  = StockTracker()

        # Style configuration
        self._configure_styles()

        # Header bar
        self._build_header()

        # Notebook (tab container)
        self.notebook = ttk.Notebook(self, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Create each tab
        self.tab_dashboard    = DashboardTab(self.notebook, self)
        self.tab_transactions = TransactionsTab(self.notebook, self)
        self.tab_investments  = InvestmentsTab(self.notebook, self)
        self.tab_stocks       = StocksTab(self.notebook, self)
        self.tab_savings      = SavingsGoalTab(self.notebook, self)
        self.tab_charts       = ChartsTab(self.notebook, self)

        self.notebook.add(self.tab_dashboard,    text="  📊 Dashboard  ")
        self.notebook.add(self.tab_transactions, text="  💳 Transactions  ")
        self.notebook.add(self.tab_investments,  text="  📈 Investments  ")
        self.notebook.add(self.tab_stocks,       text="  🏦 Stocks  ")
        self.notebook.add(self.tab_savings,      text="  🎯 Savings Goal  ")
        self.notebook.add(self.tab_charts,       text="  📉 Charts  ")

        # Refresh dashboard on tab switch
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Cleanup on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- Style setup --------------------------------------------------
    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Custom.TNotebook",
                        background=BG_TAB,
                        borderwidth=0)
        style.configure("Custom.TNotebook.Tab",
                        background=BG_CARD,
                        foreground=TEXT_DIM,
                        padding=[14, 8],
                        font=FONT_BODY)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", BG_DARK)],
                  foreground=[("selected", ACCENT)])

        style.configure("Card.TFrame",
                        background=BG_CARD,
                        relief="flat")
        style.configure("TLabel",
                        background=BG_CARD,
                        foreground=TEXT_MAIN,
                        font=FONT_BODY)
        style.configure("Treeview",
                        background=BG_CARD,
                        foreground=TEXT_MAIN,
                        fieldbackground=BG_CARD,
                        rowheight=28,
                        font=FONT_BODY)
        style.configure("Treeview.Heading",
                        background=BG_DARK,
                        foreground=ACCENT,
                        font=("Helvetica", 10, "bold"))
        style.configure("TEntry",
                        fieldbackground=BG_DARK,
                        foreground=TEXT_MAIN,
                        insertcolor=TEXT_MAIN)
        style.configure("TCombobox",
                        fieldbackground=BG_DARK,
                        foreground=TEXT_MAIN)

    # ---- Header bar ---------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self, bg=BG_CARD, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header,
                 text="💰  Personal Finance Manager",
                 bg=BG_CARD, fg=TEXT_MAIN,
                 font=FONT_H1).pack(side="left", padx=24, pady=10)

        date_str = datetime.date.today().strftime("%d %B %Y")
        tk.Label(header,
                 text=date_str,
                 bg=BG_CARD, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="right", padx=24)

    # ---- Tab-change handler ------------------------------------------
    def _on_tab_changed(self, event):
        selected = self.notebook.select()
        tab_text = self.notebook.tab(selected, "text")
        if "Dashboard" in tab_text:
            self.tab_dashboard.refresh()
        if "Charts" in tab_text:
            self.tab_charts.refresh()

    # ---- Clean shutdown ----------------------------------------------
    def _on_close(self):
        self.db.close()
        self.destroy()


# ===========================================================================
# HELPER: rounded card frame
# ===========================================================================
def make_card(parent, title="", padx=12, pady=12):
    """Returns a labelled frame styled as a dark card."""
    card = tk.LabelFrame(parent,
                         text=f"  {title}  " if title else "",
                         bg=BG_CARD,
                         fg=ACCENT,
                         font=("Helvetica", 10, "bold"),
                         bd=1, relief="solid",
                         highlightbackground=BORDER)
    card.pack(fill="both", expand=True, padx=padx, pady=pady)
    return card


# ===========================================================================
# TAB 1 – DASHBOARD
# ===========================================================================
class DashboardTab(tk.Frame):
    """
    Shows summary KPI cards: Balance, Income, Expenses, Savings.
    Auto-refreshes when the tab is selected.
    """

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="Overview", bg=BG_DARK,
                 fg=TEXT_DIM, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(self, text="Financial Summary", bg=BG_DARK,
                 fg=TEXT_MAIN, font=FONT_H2).pack(anchor="w", padx=20)

        # KPI row
        self.kpi_frame = tk.Frame(self, bg=BG_DARK)
        self.kpi_frame.pack(fill="x", padx=16, pady=16)

        self.kpi_labels = {}
        kpis = [
            ("balance",  "💰 Balance",     ACCENT),
            ("income",   "📥 Total Income", ACCENT2),
            ("expenses", "📤 Expenses",     DANGER),
            ("savings",  "🏦 Net Savings",  ACCENT2),
        ]
        for col, (key, label, colour) in enumerate(kpis):
            card = tk.Frame(self.kpi_frame, bg=BG_CARD,
                            bd=1, relief="solid",
                            highlightbackground=BORDER)
            card.grid(row=0, column=col, padx=8, sticky="nsew")
            self.kpi_frame.columnconfigure(col, weight=1)

            tk.Label(card, text=label, bg=BG_CARD,
                     fg=TEXT_DIM, font=FONT_SMALL).pack(anchor="w", padx=14, pady=(14, 2))
            val_label = tk.Label(card, text="$0.00", bg=BG_CARD,
                                 fg=colour, font=FONT_H1)
            val_label.pack(anchor="w", padx=14, pady=(0, 14))
            self.kpi_labels[key] = val_label

        # Recent transactions preview
        recent_card = make_card(self, title="Recent Transactions")
        cols = ("Date", "Category", "Description", "Amount", "Type")
        self.tree = ttk.Treeview(recent_card, columns=cols,
                                 show="headings", height=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.refresh()

    def refresh(self):
        income, expenses = self.app.db.get_totals()
        balance = income - expenses
        savings = balance  # simplified; adjust with savings goal data

        self.kpi_labels["income"].config(text=f"${income:,.2f}")
        self.kpi_labels["expenses"].config(text=f"${expenses:,.2f}")
        self.kpi_labels["balance"].config(text=f"${balance:,.2f}")
        self.kpi_labels["savings"].config(text=f"${savings:,.2f}")

        # Populate recent transactions treeview
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.app.db.get_transactions()[:10]:
            _, date, cat, desc, amt, t_type = record
            colour_tag = "income" if t_type == "Income" else "expense"
            prefix = "+" if t_type == "Income" else "-"
            self.tree.insert("", "end",
                             values=(date, cat, desc,
                                     f"{prefix}${amt:,.2f}", t_type),
                             tags=(colour_tag,))
        self.tree.tag_configure("income",  foreground=ACCENT2)
        self.tree.tag_configure("expense", foreground=DANGER)


# ===========================================================================
# TAB 2 – TRANSACTIONS
# ===========================================================================
class TransactionsTab(tk.Frame):
    """
    Input form to add income / expense records.
    Displays all transactions in a Treeview table.
    """

    CATEGORIES_INCOME  = ["Salary", "Freelance", "Dividends",
                          "Gift", "Other Income"]
    CATEGORIES_EXPENSE = ["Food", "Rent", "Transport", "Healthcare",
                          "Entertainment", "Utilities", "Education",
                          "Clothing", "Other Expense"]

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        # ---- Input form -----------------------------------------------
        form_card = make_card(self, title="Add Transaction")

        fields = tk.Frame(form_card, bg=BG_CARD)
        fields.pack(fill="x", padx=12, pady=8)

        # Date
        tk.Label(fields, text="Date (YYYY-MM-DD):", bg=BG_CARD,
                 fg=TEXT_MAIN, font=FONT_BODY).grid(row=0, column=0,
                                                     padx=8, pady=6, sticky="w")
        self.entry_date = ttk.Entry(fields, width=18)
        self.entry_date.insert(0, str(datetime.date.today()))
        self.entry_date.grid(row=0, column=1, padx=8, sticky="ew")

        # Type (Income / Expense)
        tk.Label(fields, text="Type:", bg=BG_CARD,
                 fg=TEXT_MAIN, font=FONT_BODY).grid(row=0, column=2,
                                                     padx=8, sticky="w")
        self.combo_type = ttk.Combobox(fields,
                                        values=["Income", "Expense"],
                                        state="readonly", width=12)
        self.combo_type.current(0)
        self.combo_type.grid(row=0, column=3, padx=8, sticky="ew")
        self.combo_type.bind("<<ComboboxSelected>>", self._update_categories)

        # Category
        tk.Label(fields, text="Category:", bg=BG_CARD,
                 fg=TEXT_MAIN, font=FONT_BODY).grid(row=1, column=0,
                                                     padx=8, pady=6, sticky="w")
        self.combo_category = ttk.Combobox(fields,
                                            values=self.CATEGORIES_INCOME,
                                            state="readonly", width=20)
        self.combo_category.current(0)
        self.combo_category.grid(row=1, column=1, padx=8, sticky="ew")

        # Description
        tk.Label(fields, text="Description:", bg=BG_CARD,
                 fg=TEXT_MAIN, font=FONT_BODY).grid(row=1, column=2,
                                                     padx=8, sticky="w")
        self.entry_desc = ttk.Entry(fields, width=22)
        self.entry_desc.grid(row=1, column=3, padx=8, sticky="ew")

        # Amount
        tk.Label(fields, text="Amount ($):", bg=BG_CARD,
                 fg=TEXT_MAIN, font=FONT_BODY).grid(row=2, column=0,
                                                     padx=8, pady=6, sticky="w")
        self.entry_amount = ttk.Entry(fields, width=18)
        self.entry_amount.grid(row=2, column=1, padx=8, sticky="ew")

        # Add button
        tk.Button(fields, text="  ➕  Add Transaction  ",
                  bg=ACCENT, fg="white",
                  font=FONT_BODY, relief="flat", cursor="hand2",
                  command=self._add_transaction).grid(row=2, column=3,
                                                       padx=8, pady=6,
                                                       sticky="ew")

        for col in range(4):
            fields.columnconfigure(col, weight=1)

        # ---- Transactions table --------------------------------------
        table_card = make_card(self, title="All Transactions")
        cols = ("ID", "Date", "Category", "Description", "Amount", "Type")
        self.tree = ttk.Treeview(table_card, columns=cols,
                                 show="headings", height=16)
        widths = (40, 110, 130, 200, 100, 90)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        scroll = ttk.Scrollbar(table_card, orient="vertical",
                               command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll.pack(side="right", fill="y")

        self._load_table()

    # ---- Helpers ------------------------------------------------------
    def _update_categories(self, event=None):
        if self.combo_type.get() == "Income":
            self.combo_category.configure(values=self.CATEGORIES_INCOME)
        else:
            self.combo_category.configure(values=self.CATEGORIES_EXPENSE)
        self.combo_category.current(0)

    def _add_transaction(self):
        date     = self.entry_date.get().strip()
        t_type   = self.combo_type.get()
        category = self.combo_category.get()
        desc     = self.entry_desc.get().strip()
        try:
            amount = float(self.entry_amount.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a number.")
            return
        if not date or amount <= 0:
            messagebox.showerror("Input Error", "Please fill all fields correctly.")
            return

        self.app.db.add_transaction(date, category, desc, amount, t_type)
        self._load_table()
        self.entry_amount.delete(0, "end")
        self.entry_desc.delete(0, "end")

    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.app.db.get_transactions():
            rec_id, date, cat, desc, amt, t_type = record
            prefix = "+" if t_type == "Income" else "-"
            tag    = "income" if t_type == "Income" else "expense"
            self.tree.insert("", "end",
                             values=(rec_id, date, cat, desc,
                                     f"{prefix}${amt:,.2f}", t_type),
                             tags=(tag,))
        self.tree.tag_configure("income",  foreground=ACCENT2)
        self.tree.tag_configure("expense", foreground=DANGER)


# ===========================================================================
# TAB 3 – INVESTMENTS & PORTFOLIO
# ===========================================================================
class InvestmentsTab(tk.Frame):
    """
    Tracks investment holdings, current value, and profit / loss.
    """

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        # ---- Input form -----------------------------------------------
        form_card = make_card(self, title="Add Investment")
        fields = tk.Frame(form_card, bg=BG_CARD)
        fields.pack(fill="x", padx=12, pady=8)

        labels = ["Investment Name", "Ticker Symbol",
                  "Quantity", "Buy Price ($)",
                  "Current Price ($)", "Date Bought"]
        self.entries = {}
        for i, lbl in enumerate(labels):
            row, col = divmod(i, 3)
            tk.Label(fields, text=lbl + ":", bg=BG_CARD,
                     fg=TEXT_MAIN, font=FONT_BODY).grid(
                         row=row*2, column=col, padx=8, pady=4, sticky="w")
            entry = ttk.Entry(fields, width=18)
            if lbl == "Date Bought":
                entry.insert(0, str(datetime.date.today()))
            entry.grid(row=row*2+1, column=col, padx=8, pady=2, sticky="ew")
            self.entries[lbl] = entry
        for col in range(3):
            fields.columnconfigure(col, weight=1)

        tk.Button(fields, text="  ➕  Add Investment  ",
                  bg=ACCENT2, fg=BG_DARK,
                  font=FONT_BODY, relief="flat", cursor="hand2",
                  command=self._add_investment).grid(
                      row=4, column=0, columnspan=3, pady=10, sticky="ew", padx=8)

        # ---- Portfolio table -----------------------------------------
        table_card = make_card(self, title="Portfolio Holdings")
        cols = ("Name", "Ticker", "Qty", "Buy Price",
                "Current Price", "Total Value", "Profit / Loss")
        self.tree = ttk.Treeview(table_card, columns=cols,
                                 show="headings", height=14)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")
        scroll = ttk.Scrollbar(table_card, orient="vertical",
                               command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll.pack(side="right", fill="y")

        self._load_table()

    def _add_investment(self):
        try:
            name    = self.entries["Investment Name"].get().strip()
            ticker  = self.entries["Ticker Symbol"].get().strip().upper()
            qty     = float(self.entries["Quantity"].get())
            buy_p   = float(self.entries["Buy Price ($)"].get())
            cur_p   = float(self.entries["Current Price ($)"].get())
            date_b  = self.entries["Date Bought"].get().strip()
        except ValueError:
            messagebox.showerror("Input Error",
                                 "Quantity and prices must be numeric.")
            return
        if not name:
            messagebox.showerror("Input Error", "Investment name required.")
            return
        self.app.db.add_investment(name, ticker, qty, buy_p, cur_p, date_b)
        self._load_table()

    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.app.db.get_investments():
            _, name, ticker, qty, buy_p, cur_p, date_b = record
            total_val = qty * cur_p
            pnl       = (cur_p - buy_p) * qty
            tag       = "profit" if pnl >= 0 else "loss"
            self.tree.insert("", "end",
                             values=(name, ticker,
                                     f"{qty:.2f}",
                                     f"${buy_p:,.2f}",
                                     f"${cur_p:,.2f}",
                                     f"${total_val:,.2f}",
                                     f"{'+'if pnl>=0 else ''}${pnl:,.2f}"),
                             tags=(tag,))
        self.tree.tag_configure("profit", foreground=ACCENT2)
        self.tree.tag_configure("loss",   foreground=DANGER)


# ===========================================================================
# TAB 4 – STOCKS
# ===========================================================================
class StocksTab(tk.Frame):
    """
    Displays simulated live stock market data.
    Refreshes every 10 seconds automatically.
    """

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()
        self._auto_refresh()

    def _build(self):
        header_row = tk.Frame(self, bg=BG_DARK)
        header_row.pack(fill="x", padx=16, pady=12)
        tk.Label(header_row, text="Live Market (Simulated)",
                 bg=BG_DARK, fg=TEXT_MAIN, font=FONT_H2).pack(side="left")
        tk.Button(header_row, text="🔄 Refresh",
                  bg=ACCENT, fg="white", relief="flat",
                  cursor="hand2", font=FONT_BODY,
                  command=self._load_market).pack(side="right")

        card = make_card(self, title="Market Overview")
        cols = ("Ticker", "Company Name", "Price ($)", "Change (%)")
        self.tree = ttk.Treeview(card, columns=cols,
                                 show="headings", height=18)
        widths = (100, 280, 130, 130)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self._load_market()

    def _load_market(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for stock in self.app.stocks.get_all_market_data():
            chg   = stock["change"]
            tag   = "up" if chg >= 0 else "down"
            arrow = "▲" if chg >= 0 else "▼"
            self.tree.insert("", "end",
                             values=(stock["ticker"],
                                     stock["name"],
                                     f"${stock['price']:,.2f}",
                                     f"{arrow} {abs(chg):.2f}%"),
                             tags=(tag,))
        self.tree.tag_configure("up",   foreground=ACCENT2)
        self.tree.tag_configure("down", foreground=DANGER)

    def _auto_refresh(self):
        self._load_market()
        self.after(10000, self._auto_refresh)   # refresh every 10 s


# ===========================================================================
# TAB 5 – SAVINGS GOAL
# ===========================================================================
class SavingsGoalTab(tk.Frame):
    """
    Set savings targets. Calculates progress % and months to reach goal.

    Algorithm (Criterion B - Pseudocode equivalent):
        months_needed = (target - saved) / monthly_contribution
        progress_pct  = (saved / target) * 100
    """

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        form_card = make_card(self, title="Add Savings Goal")
        fields = tk.Frame(form_card, bg=BG_CARD)
        fields.pack(fill="x", padx=12, pady=8)

        field_defs = [
            ("Goal Name",                 0, 0),
            ("Target Amount ($)",          0, 2),
            ("Already Saved ($)",          1, 0),
            ("Monthly Contribution ($)",   1, 2),
            ("Deadline (YYYY-MM-DD)",      2, 0),
        ]
        self.goal_entries = {}
        for lbl, row, col in field_defs:
            tk.Label(fields, text=lbl + ":", bg=BG_CARD,
                     fg=TEXT_MAIN, font=FONT_BODY).grid(
                         row=row*2, column=col, padx=8, pady=4, sticky="w")
            e = ttk.Entry(fields, width=22)
            e.grid(row=row*2+1, column=col, padx=8, sticky="ew", pady=2)
            self.goal_entries[lbl] = e
        for c in range(4):
            fields.columnconfigure(c, weight=1)

        tk.Button(fields, text="  🎯  Set Goal  ",
                  bg=ACCENT, fg="white", relief="flat",
                  cursor="hand2", font=FONT_BODY,
                  command=self._add_goal).grid(
                      row=6, column=0, columnspan=4, pady=10,
                      sticky="ew", padx=8)

        table_card = make_card(self, title="My Savings Goals")
        cols = ("Goal", "Target", "Saved", "Progress %",
                "Monthly", "Months Left", "Deadline")
        self.tree = ttk.Treeview(table_card, columns=cols,
                                 show="headings", height=12)
        widths = (160, 110, 110, 100, 110, 100, 120)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self._load_goals()

    def _add_goal(self):
        try:
            name    = self.goal_entries["Goal Name"].get().strip()
            target  = float(self.goal_entries["Target Amount ($)"].get())
            saved   = float(self.goal_entries["Already Saved ($)"].get())
            monthly = float(self.goal_entries["Monthly Contribution ($)"].get())
            deadline= self.goal_entries["Deadline (YYYY-MM-DD)"].get().strip()
        except ValueError:
            messagebox.showerror("Input Error", "Amounts must be numeric.")
            return
        if not name or target <= 0:
            messagebox.showerror("Input Error", "Goal name and target required.")
            return
        self.app.db.add_savings_goal(name, target, saved, monthly, deadline)
        self._load_goals()

    def _load_goals(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.app.db.get_savings_goals():
            _, name, target, saved, monthly, deadline = record
            progress = (saved / target * 100) if target > 0 else 0
            remaining = target - saved
            months_left = (remaining / monthly) if monthly > 0 else float("inf")
            months_str = (f"{months_left:.1f}" if monthly > 0 else "N/A")
            self.tree.insert("", "end",
                             values=(name,
                                     f"${target:,.2f}",
                                     f"${saved:,.2f}",
                                     f"{progress:.1f}%",
                                     f"${monthly:,.2f}",
                                     months_str,
                                     deadline))


# ===========================================================================
# TAB 6 – CHARTS & GRAPHS
# ===========================================================================
class ChartsTab(tk.Frame):
    """
    Embeds Matplotlib charts inside Tkinter using FigureCanvasTkAgg.
    Charts shown:
        1. Expenses by category  (pie chart)
        2. Income vs Expenses    (bar chart)
        3. Portfolio value       (horizontal bar)
    """

    def __init__(self, parent, app: FinanceApp):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="Charts & Graphs", bg=BG_DARK,
                 fg=TEXT_MAIN, font=FONT_H2).pack(anchor="w",
                                                   padx=20, pady=12)

        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=16)

        for label, cmd in [
            ("📊 Expenses by Category", self._chart_expenses_pie),
            ("📈 Income vs Expenses",    self._chart_income_vs_expenses),
            ("💼 Portfolio Value",       self._chart_portfolio),
        ]:
            tk.Button(btn_frame, text=label,
                      bg=BG_CARD, fg=TEXT_MAIN,
                      activebackground=ACCENT, activeforeground="white",
                      relief="flat", cursor="hand2", font=FONT_BODY,
                      padx=12, pady=6,
                      command=cmd).pack(side="left", padx=6)

        # Chart canvas area
        self.chart_frame = tk.Frame(self, bg=BG_DARK)
        self.chart_frame.pack(fill="both", expand=True, padx=16, pady=12)
        self._canvas = None

        # Default chart on load
        self._chart_income_vs_expenses()

    def _clear_canvas(self):
        if self._canvas:
            self._canvas.get_tk_widget().destroy()
            plt.close("all")

    def _embed(self, fig):
        self._clear_canvas()
        self._canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---- Chart generators --------------------------------------------
    def _chart_expenses_pie(self):
        records = self.app.db.get_transactions()
        cat_totals = {}
        for _, _, cat, _, amt, t_type in records:
            if t_type == "Expense":
                cat_totals[cat] = cat_totals.get(cat, 0) + amt
        if not cat_totals:
            messagebox.showinfo("No Data", "No expense records found.")
            return

        fig, ax = plt.subplots(figsize=(8, 5),
                               facecolor=BG_CARD)
        ax.set_facecolor(BG_CARD)
        wedge_colors = [ACCENT, ACCENT2, DANGER, "#f7c94f",
                        "#af7ef8", "#f87171", "#34d399"]
        ax.pie(cat_totals.values(),
               labels=cat_totals.keys(),
               autopct="%1.1f%%",
               colors=wedge_colors[:len(cat_totals)],
               textprops={"color": TEXT_MAIN})
        ax.set_title("Expenses by Category",
                     color=TEXT_MAIN, fontsize=13, fontweight="bold")
        self._embed(fig)

    def _chart_income_vs_expenses(self):
        income, expenses = self.app.db.get_totals()
        fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG_CARD)
        ax.set_facecolor(BG_CARD)
        bars = ax.bar(["Income", "Expenses"],
                      [income, expenses],
                      color=[ACCENT2, DANGER],
                      width=0.4, edgecolor=BORDER)
        ax.set_ylabel("Amount ($)", color=TEXT_MAIN)
        ax.set_title("Income vs Expenses",
                     color=TEXT_MAIN, fontsize=13, fontweight="bold")
        ax.tick_params(colors=TEXT_MAIN)
        ax.spines[:].set_color(BORDER)
        for bar, val in zip(bars, [income, expenses]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + (max(income, expenses) * 0.02),
                    f"${val:,.0f}",
                    ha="center", color=TEXT_MAIN, fontsize=11)
        self._embed(fig)

    def _chart_portfolio(self):
        records = self.app.db.get_investments()
        if not records:
            messagebox.showinfo("No Data", "No investments recorded.")
            return
        names  = [r[1] for r in records]
        values = [r[3] * r[5] for r in records]    # qty * current_price

        fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG_CARD)
        ax.set_facecolor(BG_CARD)
        colors = [ACCENT2 if (r[5]-r[4])>=0 else DANGER for r in records]
        ax.barh(names, values, color=colors, edgecolor=BORDER)
        ax.set_xlabel("Current Value ($)", color=TEXT_MAIN)
        ax.set_title("Portfolio Holdings Value",
                     color=TEXT_MAIN, fontsize=13, fontweight="bold")
        ax.tick_params(colors=TEXT_MAIN)
        ax.spines[:].set_color(BORDER)
        self._embed(fig)

    def refresh(self):
        """Called when tab is switched to."""
        self._chart_income_vs_expenses()


# ===========================================================================
# ENTRY POINT
# ===========================================================================
if __name__ == "__main__":
    app = FinanceApp()
    app.mainloop()
