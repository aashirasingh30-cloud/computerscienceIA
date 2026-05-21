# ============================================
# FINANCE TRACKER PRO EDITION
# Fully Fixed & Optimized Stable Version
# ============================================

# Required Libraries:
# pip install matplotlib pandas

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ============================================
# MAIN WINDOW
# ============================================

root = tk.Tk()
root.title("FinanceTracker PRO")
root.geometry("1200x850")
root.configure(bg="#f3f4f6")

# Prevent UI freezing glitches
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# ============================================
# DATA STORAGE
# ============================================

income = []
expenses = []

BASE_CURRENCY = "USD"

# ============================================
# EXCHANGE RATES
# ============================================

exchange_rates = {
    "USD": 1,
    "EUR": 0.92,
    "GBP": 0.78,
    "AED": 3.67,
    "INR": 83.0
}

currencies = {
    "USD ($)": ("USD", "$"),
    "EUR (€)": ("EUR", "€"),
    "GBP (£)": ("GBP", "£"),
    "AED (د.إ)": ("AED", "د.إ"),
    "INR (₹)": ("INR", "₹")
}

selected_currency = tk.StringVar(value="USD ($)")

# ============================================
# SAMPLE CHART DATA
# ============================================

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

monthly_income = [3200, 2800, 3500, 2900, 3800, 3400]
monthly_expenses = [2500, 2200, 2600, 2100, 3000, 2700]

# ============================================
# HELPER FUNCTIONS
# ============================================

def convert_from_usd(amount, target_currency):
    return amount * exchange_rates[target_currency]


def get_selected_currency():
    return currencies[selected_currency.get()]


# ============================================
# UPDATE SUMMARY
# ============================================

def update_summary():

    currency_code, symbol = get_selected_currency()

    total_income_usd = sum(income)

    total_expenses_usd = sum(
        item["amount"] for item in expenses
    )

    balance_usd = total_income_usd - total_expenses_usd

    total_income = convert_from_usd(
        total_income_usd,
        currency_code
    )

    total_expenses = convert_from_usd(
        total_expenses_usd,
        currency_code
    )

    balance = convert_from_usd(
        balance_usd,
        currency_code
    )

    income_label.config(
        text=f"{symbol}{total_income:,.2f}"
    )

    expense_label.config(
        text=f"{symbol}{total_expenses:,.2f}"
    )

    balance_label.config(
        text=f"{symbol}{balance:,.2f}"
    )

    update_charts()


# ============================================
# CURRENCY CHANGED
# ============================================

def currency_changed(event=None):
    update_summary()


# ============================================
# ADD INCOME
# ============================================

def add_income():

    amount_text = income_entry.get().strip()

    if amount_text == "":
        messagebox.showerror(
            "Error",
            "Please enter income amount"
        )
        return

    try:

        amount = float(amount_text)

        currency_code, _ = get_selected_currency()

        usd_amount = amount / exchange_rates[currency_code]

        income.append(usd_amount)

        income_entry.delete(0, tk.END)

        update_summary()

    except ValueError:

        messagebox.showerror(
            "Error",
            "Please enter a valid number"
        )


# ============================================
# ADD EXPENSE
# ============================================

def add_expense():

    amount_text = expense_amount_entry.get().strip()
    category = expense_category_entry.get().strip()

    if amount_text == "":
        messagebox.showerror(
            "Error",
            "Please enter expense amount"
        )
        return

    if category == "":
        messagebox.showerror(
            "Error",
            "Please enter expense category"
        )
        return

    try:

        amount = float(amount_text)

        currency_code, _ = get_selected_currency()

        usd_amount = amount / exchange_rates[currency_code]

        expenses.append({
            "amount": usd_amount,
            "category": category
        })

        expense_amount_entry.delete(0, tk.END)
        expense_category_entry.delete(0, tk.END)

        update_summary()

    except ValueError:

        messagebox.showerror(
            "Error",
            "Please enter a valid number"
        )


# ============================================
# CREATE SUMMARY CARDS
# ============================================

def create_card(parent, title, color):

    frame = tk.Frame(
        parent,
        bg="white",
        width=250,
        height=120,
        highlightthickness=1,
        highlightbackground="#e5e7eb"
    )

    frame.pack_propagate(False)

    tk.Label(
        frame,
        text=title,
        bg="white",
        fg="gray",
        font=("Helvetica", 11, "bold")
    ).pack(pady=(15, 5))

    value_label = tk.Label(
        frame,
        text="$0.00",
        bg="white",
        fg=color,
        font=("Helvetica", 20, "bold")
    )

    value_label.pack()

    return frame, value_label


# ============================================
# STYLED BUTTON
# ============================================

def styled_button(parent, text, command):

    return tk.Button(
        parent,
        text=text,
        command=command,
        bg="#0f172a",
        fg="white",
        activebackground="#1e293b",
        activeforeground="white",
        font=("Helvetica", 10, "bold"),
        relief="flat",
        padx=14,
        pady=8,
        cursor="hand2",
        borderwidth=0
    )


# ============================================
# HEADER
# ============================================

header = tk.Frame(
    root,
    bg="white",
    height=70
)

header.pack(fill="x")

tk.Label(
    header,
    text="FinanceTracker PRO",
    bg="white",
    fg="#111827",
    font=("Helvetica", 20, "bold")
).pack(
    side="left",
    padx=20,
    pady=20
)

currency_menu = ttk.Combobox(
    header,
    textvariable=selected_currency,
    values=list(currencies.keys()),
    state="readonly",
    width=15,
    font=("Helvetica", 10)
)

currency_menu.pack(
    side="right",
    padx=20,
    pady=15
)

currency_menu.bind(
    "<<ComboboxSelected>>",
    currency_changed
)

# ============================================
# DASHBOARD TITLE
# ============================================

title_frame = tk.Frame(
    root,
    bg="#f3f4f6"
)

title_frame.pack(
    fill="x",
    padx=20,
    pady=(20, 5)
)

tk.Label(
    title_frame,
    text="Financial Dashboard",
    bg="#f3f4f6",
    fg="#111827",
    font=("Helvetica", 24, "bold")
).pack(anchor="w")

tk.Label(
    title_frame,
    text="A comprehensive view of your finances",
    bg="#f3f4f6",
    fg="gray",
    font=("Helvetica", 11)
).pack(anchor="w")

# ============================================
# SUMMARY CARDS
# ============================================

cards_frame = tk.Frame(
    root,
    bg="#f3f4f6"
)

cards_frame.pack(pady=15)

income_card, income_label = create_card(
    cards_frame,
    "TOTAL INCOME",
    "#16a34a"
)

expense_card, expense_label = create_card(
    cards_frame,
    "TOTAL EXPENSES",
    "#dc2626"
)

balance_card, balance_label = create_card(
    cards_frame,
    "BALANCE",
    "#eab308"
)

income_card.grid(row=0, column=0, padx=15)
expense_card.grid(row=0, column=1, padx=15)
balance_card.grid(row=0, column=2, padx=15)

# ============================================
# INPUT SECTION
# ============================================

input_container = tk.Frame(
    root,
    bg="#f3f4f6"
)

input_container.pack(pady=20)

input_frame = tk.Frame(
    input_container,
    bg="white",
    padx=25,
    pady=25,
    highlightthickness=1,
    highlightbackground="#e5e7eb"
)

input_frame.pack()

# ============================================
# INCOME SECTION
# ============================================

tk.Label(
    input_frame,
    text="Add Income",
    bg="white",
    font=("Helvetica", 12, "bold")
).grid(
    row=0,
    column=0,
    sticky="w"
)

income_entry = tk.Entry(
    input_frame,
    width=28,
    font=("Helvetica", 11),
    relief="solid",
    bd=1
)

income_entry.grid(
    row=1,
    column=0,
    pady=10,
    padx=(0, 10)
)

styled_button(
    input_frame,
    "Add Income",
    add_income
).grid(
    row=1,
    column=1
)

# ============================================
# EXPENSE SECTION
# ============================================

tk.Label(
    input_frame,
    text="Add Expense",
    bg="white",
    font=("Helvetica", 12, "bold")
).grid(
    row=2,
    column=0,
    sticky="w",
    pady=(20, 5)
)

tk.Label(
    input_frame,
    text="Expense Amount",
    bg="white",
    fg="gray",
    font=("Helvetica", 10)
).grid(
    row=3,
    column=0,
    sticky="w"
)

expense_amount_entry = tk.Entry(
    input_frame,
    width=28,
    font=("Helvetica", 11),
    relief="solid",
    bd=1
)

expense_amount_entry.grid(
    row=4,
    column=0,
    pady=5,
    padx=(0, 10)
)

tk.Label(
    input_frame,
    text="Expense Category",
    bg="white",
    fg="gray",
    font=("Helvetica", 10)
).grid(
    row=5,
    column=0,
    sticky="w"
)

expense_category_entry = tk.Entry(
    input_frame,
    width=28,
    font=("Helvetica", 11),
    relief="solid",
    bd=1
)

expense_category_entry.grid(
    row=6,
    column=0,
    pady=5,
    padx=(0, 10)
)

styled_button(
    input_frame,
    "Add Expense",
    add_expense
).grid(
    row=4,
    column=1,
    rowspan=3,
    padx=15
)

# ============================================
# CHARTS SECTION
# ============================================

charts_frame = tk.Frame(
    root,
    bg="#f3f4f6"
)

charts_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

fig = Figure(
    figsize=(10, 5),
    dpi=100
)

fig.patch.set_facecolor("#f3f4f6")

ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

canvas = FigureCanvasTkAgg(
    fig,
    master=charts_frame
)

canvas_widget = canvas.get_tk_widget()

canvas_widget.pack(
    fill="both",
    expand=True
)

# ============================================
# UPDATE CHARTS
# ============================================

def update_charts():

    ax1.clear()
    ax2.clear()

    # Line Graph
    ax1.plot(
        months,
        monthly_income,
        marker="o",
        linewidth=2,
        label="Income"
    )

    ax1.plot(
        months,
        monthly_expenses,
        marker="o",
        linewidth=2,
        label="Expenses"
    )

    ax1.set_title(
        "Income vs Expenses Trend"
    )

    ax1.legend()

    # Pie Chart
    if len(expenses) > 0:

        df = pd.DataFrame(expenses)

        category_data = (
            df.groupby("category")["amount"]
            .sum()
        )

        ax2.pie(
            category_data,
            labels=category_data.index,
            autopct="%1.1f%%"
        )

    else:

        ax2.pie(
            [40, 25, 20, 15],
            labels=[
                "Bills",
                "Food",
                "Shopping",
                "Transport"
            ],
            autopct="%1.1f%%"
        )

    ax2.set_title(
        "Expenses by Category"
    )

    fig.tight_layout()

    canvas.draw()


# ============================================
# QUICK ACTIONS
# ============================================

quick_frame = tk.Frame(
    root,
    bg="#f3f4f6"
)

quick_frame.pack(
    fill="x",
    padx=20,
    pady=20
)

quick_card = tk.Frame(
    quick_frame,
    bg="white",
    padx=20,
    pady=20,
    highlightthickness=1,
    highlightbackground="#e5e7eb"
)

quick_card.pack(fill="x")

tk.Label(
    quick_card,
    text="Quick Actions",
    bg="white",
    font=("Helvetica", 14, "bold")
).pack(
    anchor="w",
    pady=(0, 15)
)

actions = tk.Frame(
    quick_card,
    bg="white"
)

actions.pack()

styled_button(
    actions,
    "Refresh Analytics",
    update_charts
).grid(
    row=0,
    column=0,
    padx=10
)

# ============================================
# ENTER KEY SUPPORT
# ============================================

income_entry.bind(
    "<Return>",
    lambda event: add_income()
)

expense_amount_entry.bind(
    "<Return>",
    lambda event: add_expense()
)

expense_category_entry.bind(
    "<Return>",
    lambda event: add_expense()
)

# ============================================
# INITIALIZE
# ============================================

update_summary()

# ============================================
# RUN APPLICATION
# ============================================

root.mainloop()
