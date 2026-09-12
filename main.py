import sqlite3
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
from flask import Flask, render_template, request, redirect
app = Flask(__name__)

@app.route("/ai-insights", methods=["GET", "POST"])
def ai_insights():
    answer = None

    if request.method == "POST":
        question = request.form["question"]

        connection = sqlite3.connect("spendwise.db")
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM expenses")
        expenses = cursor.fetchall()

        cursor.execute("SELECT category, amount FROM budget")
        budget_rows = cursor.fetchall()

        connection.close()

        expense_text = ""
        for expense in expenses:
            expense_text += f"Rs. {expense[1]} on {expense[2]} on {expense[3]} ({expense[4]})\n"

        budget_text = ""
        for category, amount in budget_rows:
            budget_text += f"{category}: Rs. {amount}\n"

        prompt = f"""You are a helpful personal finance assistant. Here is the user's expense data:

{expense_text}

Here is the user's budget:

{budget_text}

The user's question is: {question}

Give a short, clear, friendly answer based only on the data above."""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        answer = response.text

    return render_template("ai_insights.html", answer=answer) 
@app.route("/")
def home():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_result = cursor.fetchone()
    total_spent = total_result[0] if total_result[0] else 0

    cursor.execute("SELECT COUNT(*) FROM expenses")
    count_result = cursor.fetchone()
    total_count = count_result[0]

    cursor.execute("SELECT amount FROM budget WHERE category = 'total'")
    budget_result = cursor.fetchone()
    total_budget = budget_result[0] if budget_result else 0
    remaining_budget = total_budget - total_spent

    cursor.execute("SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY total DESC LIMIT 1")
    top_category_result = cursor.fetchone()
    highest_category = top_category_result[0] if top_category_result else "N/A"

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    chart_data = cursor.fetchall()
    chart_labels = [row[0] for row in chart_data]
    chart_values = [row[1] for row in chart_data]
    if total_spent > 0 and highest_category != "N/A":
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE category = ?", (highest_category,))
        top_amount = cursor.fetchone()[0]
        top_percent = round((top_amount / total_spent) * 100, 1)
        insight_text = f"{highest_category.title()} accounts for {top_percent}% of your current spending."
    else:
        insight_text = "Add some expenses to see personalized insights!"
    category_icons = {
        "food": "\U0001F354", "grocery": "\U0001F6D2", "groceries": "\U0001F6D2",
        "transport": "\U0001F697", "travel": "\u2708", "shopping": "\U0001F6CD",
        "bills": "\U0001F4A1", "rent": "\U0001F3E0", "health": "\U0001F48A",
         "entertainment": "\U0001F3AC", "education": "\U0001F4DA"
}
    
    recent_transactions = []
    for exp in expenses[-5:][::-1]:
        icon = category_icons.get(exp[2], "💰")
        recent_transactions.append({"id": exp[0], "amount": exp[1], "category": exp[2], "date": exp[3], "description": exp[4], "icon": icon})
    connection.close()

    return render_template("index.html", expenses=expenses, total_spent=total_spent, total_count=total_count, remaining_budget=remaining_budget, highest_category=highest_category, chart_labels=chart_labels, chart_values=chart_values , recent_transactions=recent_transactions , insight_text=insight_text)
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"].strip().lower()
        date = request.form["date"]
        description = request.form["description"]

        connection = sqlite3.connect("spendwise.db")
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
            (amount, category, date, description)
        )
        connection.commit()
        connection.close()

        return redirect("/")

    return render_template("add.html")
   
@app.route("/delete/<int:expense_id>")    
def delete(expense_id):
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    connection.commit()
    connection.close()

    return redirect("/")
@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id):
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"].strip().lower()
        date = request.form["date"]
        description = request.form["description"]

        cursor.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
            (amount, category, date, description, expense_id)
        )
        connection.commit()
        connection.close()

        return redirect("/")

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    expense = cursor.fetchone()
    connection.close()

    return render_template("edit.html", expense=expense)
@app.route("/summary")
def summary():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    results = cursor.fetchall()

    connection.close()

    grand_total = sum(total for category, total in results)

    return render_template("summary.html", results=results, grand_total=grand_total)
@app.route("/budget", methods=["GET", "POST"])
def budget():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    if request.method == "POST":
        total_budget = request.form["total"]
        food_budget = request.form["food"]
        transport_budget = request.form["transport"]
        bills_budget = request.form["bills"]
        other_budget = request.form["other"]

        budget_data = [
            ("total", total_budget),
            ("food", food_budget),
            ("transport", transport_budget),
            ("bills", bills_budget),
            ("other", other_budget)
        ]

        cursor.executemany(
            "INSERT OR REPLACE INTO budget (category, amount) VALUES (?, ?)",
            budget_data
        )
        connection.commit()

    cursor.execute("SELECT category, amount FROM budget")
    budget_rows = cursor.fetchall()
    budgets = {}
    for category, amount in budget_rows:
        budgets[category] = amount

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expense_rows = cursor.fetchall()
    spent = {}
    for category, total in expense_rows:
        spent[category] = total

    connection.close()

    total_spent = sum(spent.values())
    total_budget_value = budgets.get("total", 0)
    remaining = total_budget_value - total_spent

    category_status = []
    for category, budget_amount in budgets.items():
        if category == "total":
            continue
        used = spent.get(category, 0)
        percent = (used / budget_amount * 100) if budget_amount > 0 else 0
        category_status.append((category, used, budget_amount, percent))

    return render_template(
        "budget.html",
        budgets=budgets,
        total_spent=total_spent,
        total_budget=total_budget_value,
        remaining=remaining,
        category_status=category_status
    )
@app.route("/filter")
def filter_expenses():
    category = request.args.get("category", "")
    month = request.args.get("month", "")
    min_amount = request.args.get("min_amount", "")

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category.strip().lower())

    if month:
        query += " AND date LIKE ?"
        params.append(month + "%")

    if min_amount:
        query += " AND amount > ?"
        params.append(float(min_amount))

    cursor.execute(query, params)
    results = cursor.fetchall()

    connection.close()

    return render_template("filter.html", results=results, category=category, month=month, min_amount=min_amount)
@app.route("/dashboard")
def dashboard():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expense_rows = cursor.fetchall()

    spent = {}
    for category, total in expense_rows:
        spent[category] = total

    total_spent = sum(spent.values())

    cursor.execute("SELECT DISTINCT date FROM expenses")
    date_rows = cursor.fetchall()
    num_days = len(date_rows)
    average_daily = total_spent / num_days if num_days > 0 else 0

    highest_category = None
    highest_amount = 0
    for category, category_total in spent.items():
        if category_total > highest_amount:
            highest_amount = category_total
            highest_category = category

    cursor.execute("SELECT amount FROM budget WHERE category = 'total'")
    result = cursor.fetchone()
    total_budget = result[0] if result else 0

    connection.close()

    remaining = total_budget - total_spent
    budget_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

    max_amount = max(spent.values()) if spent else 1
    bar_data = []
    for category, category_total in spent.items():
        bar_width_percent = (category_total / max_amount) * 100
        bar_data.append((category, category_total, bar_width_percent))

    return render_template(
        "dashboard.html",
        total_spent=total_spent,
        highest_category=highest_category,
        highest_amount=highest_amount,
        average_daily=average_daily,
        remaining=remaining,
        budget_percent=budget_percent,
        bar_data=bar_data
    )
def create_table():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            date TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            category TEXT PRIMARY KEY,
            amount REAL
        )
    """)

    connection.commit()
    connection.close()
    print("Database and tables ready!\n")

def add_expense():
    amount = input("Enter amount spent: Rs. ")
    category = input("Enter category (Food/Transport/Bills/Other): ")
    category = category.strip().lower()
    date = input("Enter date (YYYY-MM-DD): ")
    description = input("Enter short description: ")

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
        (amount, category, date, description)
    )

    connection.commit()
    connection.close()

    print("Expense added successfully!\n")
def view_expenses():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()

    connection.close()

    if len(rows) == 0:
        print("No expenses found.\n")
        return

    print("\n--- All Expenses ---")
    for row in rows:
        expense_id, amount, category, date, description = row
        print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")
    print("---------------------\n")
def edit_expense():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()

    if len(rows) == 0:
        print("No expenses to edit.\n")
        connection.close()
        return

    print("\n--- All Expenses ---")
    for row in rows:
        expense_id, amount, category, date, description = row
        print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")
    print("---------------------\n")

    choice = input("Enter the ID of the expense to edit: ")

    if not choice.isdigit():
        print("Invalid choice.\n")
        connection.close()
        return

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (choice,))
    existing = cursor.fetchone()

    if existing is None:
        print("No expense found with that ID.\n")
        connection.close()
        return

    old_id, old_amount, old_category, old_date, old_description = existing

    print("Enter new details (leave blank to keep old value):")
    new_amount = input(f"Amount [{old_amount}]: ") or old_amount
    new_category = input(f"Category [{old_category}]: ") or old_category
    new_category = new_category.strip().lower()
    new_date = input(f"Date [{old_date}]: ") or old_date
    new_description = input(f"Description [{old_description}]: ") or old_description

    cursor.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
        (new_amount, new_category, new_date, new_description, choice)
    )
    connection.commit()
    connection.close()

    print("Expense updated successfully!\n")
    
def delete_expense():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()

    if len(rows) == 0:
        print("No expenses to delete.\n")
        connection.close()
        return

    print("\n--- All Expenses ---")
    for row in rows:
        expense_id, amount, category, date, description = row
        print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")
    print("---------------------\n")

    choice = input("Enter the ID of the expense to delete: ")

    if not choice.isdigit():
        print("Invalid choice.\n")
        connection.close()
        return

    cursor.execute("DELETE FROM expenses WHERE id = ?", (choice,))
    connection.commit()

    if cursor.rowcount == 0:
        print("No expense found with that ID.\n")
    else:
        print("Expense deleted successfully!\n")

    connection.close()


def show_summary():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    results = cursor.fetchall()

    connection.close()

    if len(results) == 0:
        print("No expenses found.\n")
        return

    grand_total = 0
    print("\n--- Monthly Summary ---")

    for category, total in results:
        grand_total += total

    print(f"Total Spent: Rs. {grand_total:.2f}")
    print("\nCategory Breakdown:")

    for category, total in results:
        print(f"{category}: Rs. {total:.2f}")
    print("-----------------------\n")
def set_budget():
    total_budget = input("Enter total monthly budget: Rs. ")
    food_budget = input("Enter Food budget: Rs. ")
    transport_budget = input("Enter Transport budget: Rs. ")
    bills_budget = input("Enter Bills budget: Rs. ")
    other_budget = input("Enter Other budget: Rs. ")

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    budget_data = [
        ("total", total_budget),
        ("food", food_budget),
        ("transport", transport_budget),
        ("bills", bills_budget),
        ("other", other_budget)
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO budget (category, amount) VALUES (?, ?)",
        budget_data
    )

    connection.commit()
    connection.close()

    print("Budget saved successfully!\n")

def check_budget():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, amount FROM budget")
    budget_rows = cursor.fetchall()
    budgets = {}
    for category, amount in budget_rows:
        budgets[category] = amount

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expense_rows = cursor.fetchall()
    spent = {}
    for category, total in expense_rows:
        spent[category] = total

    connection.close()

    total_spent = sum(spent.values())
    total_budget = budgets.get("total", 0)
    remaining = total_budget - total_spent

    print("\n--- Budget Status ---")
    print(f"Total Budget: Rs. {total_budget:.2f}")
    print(f"Spent: Rs. {total_spent:.2f}")
    print(f"Remaining: Rs. {remaining:.2f}")

    print("\nCategory-wise:")
    for category, budget_amount in budgets.items():
        if category == "total":
            continue

        used = spent.get(category, 0)
        percent = (used / budget_amount * 100) if budget_amount > 0 else 0

        warning = ""
        if percent >= 100:
            warning = " 🚨 Over budget!"
        elif percent >= 90:
            warning = " ⚠️ Almost over budget!"

        print(f"{category}: Rs. {used:.2f} / Rs. {budget_amount:.2f} ({percent:.1f}% used){warning}")
    print("----------------------\n")
def filter_by_category():
    search_category = input("Enter category to search: ")
    search_category = search_category.strip().lower()

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses WHERE category = ?", (search_category,))
    rows = cursor.fetchall()

    connection.close()

    print(f"\n--- Expenses in '{search_category}' ---")

    if len(rows) == 0:
        print("No expenses found in this category.")
    else:
        for row in rows:
            expense_id, amount, category, date, description = row
            print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")

    print("---------------------------------\n")

def filter_by_month():
    search_month = input("Enter month to search (YYYY-MM, e.g. 2026-09): ")
    search_month = search_month.strip()

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses WHERE date LIKE ?", (search_month + "%",))
    rows = cursor.fetchall()

    connection.close()

    print(f"\n--- Expenses in '{search_month}' ---")

    if len(rows) == 0:
        print("No expenses found for this month.")
    else:
        for row in rows:
            expense_id, amount, category, date, description = row
            print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")

    print("---------------------------------\n")
def filter_by_amount():
    min_amount = input("Show expenses above: Rs. ")
    min_amount = float(min_amount)

    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM expenses WHERE amount > ?", (min_amount,))
    rows = cursor.fetchall()

    connection.close()

    print(f"\n--- Expenses above Rs. {min_amount:.2f} ---")

    if len(rows) == 0:
        print("No expenses found above this amount.")
    else:
        for row in rows:
            expense_id, amount, category, date, description = row
            print(f"{expense_id}. Rs. {amount} | {category} | {date} | {description}")

    print("---------------------------------\n")
def show_dashboard():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expense_rows = cursor.fetchall()

    if len(expense_rows) == 0:
        print("No expenses found.\n")
        connection.close()
        return

    spent = {}
    for category, total in expense_rows:
        spent[category] = total

    total_spent = sum(spent.values())

    cursor.execute("SELECT DISTINCT date FROM expenses")
    date_rows = cursor.fetchall()
    num_days = len(date_rows)
    average_daily = total_spent / num_days if num_days > 0 else 0

    highest_category = None
    highest_amount = 0
    for category, category_total in spent.items():
        if category_total > highest_amount:
            highest_amount = category_total
            highest_category = category

    cursor.execute("SELECT amount FROM budget WHERE category = 'total'")
    result = cursor.fetchone()
    total_budget = result[0] if result else 0

    connection.close()

    remaining = total_budget - total_spent

    print("\n========== DASHBOARD ==========")
    print(f"Total Spent: Rs. {total_spent:.2f}")
    print(f"Highest Spending Category: {highest_category} (Rs. {highest_amount:.2f})")
    print(f"Average Daily Spending: Rs. {average_daily:.2f}")
    print(f"Remaining Budget: Rs. {remaining:.2f}")

    print("\nSpending by Category:")
    max_bar_length = 20
    max_category_amount = max(spent.values())

    for category, category_total in spent.items():
        bar_length = int((category_total / max_category_amount) * max_bar_length)
        bar = "█" * bar_length
        print(f"{category:<10} {bar} Rs. {category_total:.2f}")

    print("================================\n")

def show_insights():
    connection = sqlite3.connect("spendwise.db")
    cursor = connection.cursor()

    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expense_rows = cursor.fetchall()

    if len(expense_rows) == 0:
        print("No expenses found.\n")
        connection.close()
        return

    spent = {}
    for category, total in expense_rows:
        spent[category] = total

    total_spent = sum(spent.values())

    highest_category = None
    highest_amount = 0
    for category, category_total in spent.items():
        if category_total > highest_amount:
            highest_amount = category_total
            highest_category = category

    cursor.execute("SELECT amount FROM budget WHERE category = 'total'")
    result = cursor.fetchone()
    total_budget = result[0] if result else 0

    connection.close()

    budget_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0

    print("\n--- Spending Insights ---")

    if highest_category:
        percent_of_total = (highest_amount / total_spent * 100) if total_spent > 0 else 0
        print(f"'{highest_category}' is your highest spending category, making up {percent_of_total:.1f}% of your total spending.")

    if budget_percent >= 100:
        print(f"You have exceeded your monthly budget! ({budget_percent:.1f}% used)")
    elif budget_percent >= 80:
        print(f"You have used {budget_percent:.1f}% of your monthly budget — getting close to the limit.")
    else:
        print(f"You have used {budget_percent:.1f}% of your monthly budget so far.")

    print("--------------------------\n")

def main():
    while True:
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Edit Expenses")
        print("4. Delete Expense")
        print("5. Monthly Summary")
        print("6. Set Budget")
        print("7. Check Budget")
        print("8. Search by Category")
        print("9. Search by Month")
        print("10. Search by amount")
        print("11. Dashboard")
        print("12. Insights")
        print("13. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            edit_expense()
        elif choice == "4":
            delete_expense()
        elif choice == "5": 
            show_summary()
        elif choice == "6":
            set_budget()
        elif choice == "7":
            check_budget() 
        elif choice == "8": 
            filter_by_category()
        elif choice == "9": 
            filter_by_month()
        elif choice == "10": 
            filter_by_amount() 
        elif choice == "11": 
            show_dashboard() 
        elif choice == "12": 
            show_insights()  
        elif choice == "13":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.\n")

create_table()

if __name__ == "__main__":
    app.run(debug=True)
