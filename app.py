# SmartSpend Full Code (Flask-based with SQLite)

from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import date, datetime
import os
from calendar import month_name

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_NAME = 'smartspend.db'

# ---------------------- DATABASE SETUP ----------------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS Income (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        yearly REAL,
                        monthly REAL,
                        weekly REAL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS Expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount REAL,
                        date TEXT,

                        description TEXT,
                        category TEXT,
                        timestamp TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS Goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        target_amount REAL,
                        is_active BOOLEAN,
                        created_at TEXT,
                        updated_at TEXT
                    )''')

# ---------------------- ROUTES ----------------------

@app.route('/')
def index():
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = sqlite3.connect('smartspend.db')
    c = conn.cursor()

    # Check if any user is already registered
    c.execute("SELECT * FROM users")
    user = c.fetchone()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not user:
            # First time setup
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()
            return redirect('/home')
        else:
            # Standard login
            if email == user[1] and password == user[2]:
                conn.close()
                return redirect('/home')
            else:
                flash("Incorrect email or password")
                return redirect('/login')

    conn.close()
    return render_template('login.html', setup=not user)

@app.route('/settings', methods=['GET'])
def settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email FROM Users LIMIT 1")
    user = c.fetchone()
    conn.close()
    if user:
        current_email = user[0]
    else:
        current_email = ''
    return render_template('settings.html', current_email=current_email)

@app.route('/update-settings', methods=['POST'])
def update_settings():
    new_email = request.form['email']
    new_password = request.form['password']

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check if new email is already taken by another user (though only one user exists)
    c.execute("SELECT id FROM Users WHERE email = ? LIMIT 1", (new_email,))
    existing_user = c.fetchone()

    if existing_user and new_email != new_email:
        flash("Email is already in use.")
        conn.close()
        return redirect('/settings')

    # Update user email and password
    c.execute("UPDATE Users SET email = ?, password = ? WHERE id = 1", (new_email, new_password))
    conn.commit()
    conn.close()

    flash("Settings updated successfully.")
    return redirect('/settings')

@app.route('/home')
def home():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT yearly FROM Income ORDER BY id DESC LIMIT 1')
    result = c.fetchone()
    yearly = result[0] if result else None
    monthly = round(yearly / 12, 2) if yearly else None
    weekly = round(yearly / 52, 2) if yearly else None

    # Exclude saving category from total_week and total_month
    c.execute('SELECT SUM(amount) FROM Expenses WHERE date >= date("now", "-7 day") AND category != "saving"')
    total_week = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = strftime("%Y-%m", "now") AND category != "saving"')
    total_month = c.fetchone()[0] or 0

    c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving"')
    total_saved = c.fetchone()[0] or 0

    # Fetch category summaries for the last 7 days (week)
    c.execute('SELECT category, SUM(amount) FROM Expenses WHERE date >= date("now", "-7 day") AND category != "saving" GROUP BY category')
    week_category_summary = c.fetchall()

    # Fetch category summaries for the current month
    c.execute('SELECT category, SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = strftime("%Y-%m", "now") AND category != "saving" GROUP BY category')
    month_category_summary = c.fetchall()

    # Fetch active saving goal
    c.execute('SELECT name, target_amount FROM Goals WHERE is_active = 1 LIMIT 1')
    active_goal = c.fetchone()
    active_goal_name = active_goal[0] if active_goal else None
    active_goal_target = active_goal[1] if active_goal else None

    conn.close()
    return render_template('home.html', yearly=yearly, monthly=monthly, weekly=weekly,
                           total_week=total_week, total_month=total_month, total_saved=total_saved,
                           week_category_summary=week_category_summary,
                           month_category_summary=month_category_summary,
                           active_goal_name=active_goal_name,
                           active_goal_target=active_goal_target)

@app.route('/set-income', methods=['POST'])
def set_income():
    income = float(request.form['income'])
    monthly = round(income / 12, 2)
    weekly = round(income / 52, 2)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO Income (yearly, monthly, weekly) VALUES (?, ?, ?)', (income, monthly, weekly))
    conn.commit()
    conn.close()
    return redirect('/home')

from datetime import date

@app.route('/add')
def add_expense():
    categories = [
        'Groceries', 'Transport', 'Entertainment', 'Utilities', 'Shopping', 'Health', 'Dining', 'Education',
        'Travel', 'Personal Care', 'Insurance', 'Taxes', 'Gifts', 'Charity', 'Subscriptions', 'Home Improvement',
        'Automotive', 'Childcare', 'Pet Care', 'Mortgage', 'Miscellaneous', 'Other'
    ]
    keywords_map = {
        "bus,uber,fuel,petrol,train,metro,taxi,bike": "Transport",
        "grocery,aldi,coles,woolworths,supermarket,market": "Groceries",
        "movie,cinema,netflix,spotify,concert,theater": "Entertainment",
        "electricity,water,internet,phone,bill,gas": "Utilities",
        "clothes,shopping,amazon,ebay,apparel": "Shopping",
        "doctor,pharmacy,hospital,medicine,clinic": "Health",
        "restaurant,cafe,coffee,food,dining,meal": "Dining",
        "school,university,books,education,course": "Education",
        "flight,hotel,airbnb,travel,tour,vacation": "Travel",
        "haircut,spa,beauty,personal care": "Personal Care",
        "insurance,health insurance,car insurance,home insurance": "Insurance",
        "tax,taxes,income tax": "Taxes",
        "gift,present,birthday,anniversary": "Gifts",
        "charity,donation": "Charity",
        "subscription,netflix,spotify,amazon prime": "Subscriptions",
        "home improvement,repair,maintenance": "Home Improvement",
        "car,automotive,auto,repair,fuel": "Automotive",
        "childcare,baby,kids": "Childcare",
        "pet,vet,pet care": "Pet Care",
        "mortgage,home loan,property loan": "Mortgage",
        "misc,other,miscellaneous": "Miscellaneous"
    }
    from datetime import date as dt_date
    return render_template(
        'add.html',
        categories=categories,
        keywords_to_categories=keywords_map,
        today=dt_date.today().isoformat()  # <-- This matches the template
    )


@app.route('/save-expense', methods=['POST'])
def save_expense():
    amount = float(request.form['amount'])
    date = request.form['date']
    description = request.form['description']
    category = request.form['category']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO Expenses (amount, date, description, category, timestamp) VALUES (?, ?, ?, ?, ?)',
              (amount, date, description, category, timestamp))
    conn.commit()
    conn.close()
    return redirect('/home')

@app.route('/summary')
def summary():
    view_mode = request.args.get('view', 'monthly')
    selected_period_label = request.args.get('period')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get all distinct months and weeks
    c.execute('SELECT DISTINCT strftime("%Y-%m", date) FROM Expenses ORDER BY date DESC')
    month_keys = [row[0] for row in c.fetchall()]
    c.execute('SELECT DISTINCT strftime("%Y-%W", date) FROM Expenses ORDER BY date DESC')
    week_keys = [row[0] for row in c.fetchall()]

    # Prepare periods for month and week
    month_periods = [month_name[int(m.split('-')[1])] + " " + m.split('-')[0] for m in month_keys]  # e.g., July 2025
    week_periods = [f"Week {int(w.split('-')[1])} {w.split('-')[0]}" for w in week_keys]  # e.g., Week 29 2025

    # Default period (first available)
    if not selected_period_label:
        if view_mode == 'monthly' and month_keys:
            selected_period_label = month_periods[0]
        elif view_mode == 'weekly' and week_keys:
            selected_period_label = week_periods[0]

    # Match the label to query period
    if view_mode == 'monthly':
        periods = month_periods
        if selected_period_label in periods:
            idx = periods.index(selected_period_label)
            query_period = month_keys[idx]
        else:
            query_period = datetime.now().strftime('%Y-%m')
            selected_period_label = month_name[int(query_period.split('-')[1])] + " " + query_period.split('-')[0]
    else:
        periods = week_periods
        if selected_period_label in periods:
            idx = periods.index(selected_period_label)
            query_period = week_keys[idx]
        else:
            query_period = datetime.now().strftime('%Y-%W')
            selected_period_label = f"Week {int(query_period.split('-')[1])} {query_period.split('-')[0]}"

    # ---------------- Expenses ------------------
    try:
        if view_mode == 'monthly':
            c.execute('SELECT * FROM Expenses WHERE strftime("%Y-%m", date) = ? ORDER BY date DESC', (query_period,))
        else:
            c.execute('SELECT * FROM Expenses WHERE strftime("%Y-%W", date) = ? ORDER BY date DESC', (query_period,))
        expenses = c.fetchall()

        # ---------------- Category Summary ------------------
        if view_mode == 'monthly':
            c.execute('SELECT category, SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = ? GROUP BY category', (query_period,))
        else:
            c.execute('SELECT category, SUM(amount) FROM Expenses WHERE strftime("%Y-%W", date) = ? GROUP BY category', (query_period,))
        summary_data = c.fetchall()

        # ---------------- Totals ------------------
        if view_mode == 'monthly':
            c.execute('SELECT SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = ?', (query_period,))
            total_spent = c.fetchone()[0] or 0
            c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving" AND strftime("%Y-%m", date) = ?', (query_period,))
            total_saved = c.fetchone()[0] or 0
        else:
            c.execute('SELECT SUM(amount) FROM Expenses WHERE strftime("%Y-%W", date) = ?', (query_period,))
            total_spent = c.fetchone()[0] or 0
            c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving" AND strftime("%Y-%W", date) = ?', (query_period,))
            total_saved = c.fetchone()[0] or 0

        # ---------------- Saving Goal % ------------------
        c.execute('SELECT target_amount FROM Goals WHERE is_active = 1')
        goal = c.fetchone()
        saving_percent = 0
        if goal and goal[0] > 0:
            saving_percent = int(round((total_saved / goal[0]) * 100))
            saving_percent = max(0, min(saving_percent, 100))
    except Exception as e:
        # Log error and set defaults to avoid template errors
        print(f"Error fetching summary data: {e}")
        expenses = []
        summary_data = []
        total_spent = 0
        total_saved = 0
        saving_percent = 0

    conn.close()

    # Convert total_spent and total_saved to float to avoid TypeError in template
    try:
        total_spent = float(total_spent)
    except (TypeError, ValueError):
        total_spent = 0.0
    try:
        total_saved = float(total_saved)
    except (TypeError, ValueError):
        total_saved = 0.0

    # Convert summary_data amounts to float
    summary_data = [(cat, float(tot) if tot is not None else 0.0) for cat, tot in summary_data]

    # Convert expenses amounts to float (amount is at index 1)
    expenses = [(
        exp[0],  # id
        float(exp[1]) if exp[1] is not None else 0.0,  # amount
        exp[2],  # date
        exp[3],  # description
        exp[4],  # category
        exp[5]   # timestamp
    ) for exp in expenses]

    return render_template(
        'summary.html',
        expenses=expenses,
        summary_data=summary_data,
        total_spent=total_spent,
        total_saved=total_saved,
        saving_percent=saving_percent,
        periods=periods,
        selected_period=selected_period_label,
        view_mode=view_mode
    )

@app.route('/saving')
def saving():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM Goals')
    goals_raw = c.fetchall()

    goals = []
    for goal in goals_raw:
        goal_id = goal[0]
        target_amount = goal[2]

        # Calculate progress: sum of expenses for this goal (assuming category "saving" and description contains goal name)
        c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving" AND description = ?', (goal[1],))
        progress = c.fetchone()[0] or 0.0

        remaining = target_amount - progress
        if remaining < 0:
            remaining = 0.0

        # Append goal tuple with remaining as 5th element (index 4)
        # Original goal tuple: (id, name, target_amount, is_active, created_at, updated_at)
        # New tuple: (id, name, target_amount, is_active, remaining, created_at, updated_at)
        new_goal = (goal[0], goal[1], goal[2], goal[3], remaining, goal[4], goal[5])
        goals.append(new_goal)

    conn.close()
    return render_template('saving.html', goals=goals)

@app.route('/add-goal', methods=['POST'])
def add_goal():
    name = request.form['goal_name']
    target = float(request.form['target'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO Goals (name, target_amount, is_active, created_at) VALUES (?, ?, ?, ?)',
              (name, target, False, now))
    conn.commit()
    conn.close()
    return redirect('/saving')

@app.route('/set-active/<int:goal_id>', methods=['POST'])
def set_active(goal_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE Goals SET is_active = 0')
    c.execute('UPDATE Goals SET is_active = 1 WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    return redirect('/saving')

@app.route('/add-saving-expense', methods=['POST'])
def add_saving_expense():
    amount = float(request.form['amount'])
    date_val = request.form['date']
    description = request.form.get('description', '')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name FROM Goals WHERE is_active = 1 LIMIT 1')
    active_goal = c.fetchone()
    goal_name = active_goal[0] if active_goal else 'No Active Goal'

    c.execute('INSERT INTO Expenses (amount, date, description, category, timestamp) VALUES (?, ?, ?, ?, ?)',
              (amount, date_val, goal_name if description == '' else description, 'saving', timestamp))
    conn.commit()
    conn.close()
    return redirect('/saving')

@app.route('/update-goal/<int:goal_id>', methods=['POST'])
def update_goal(goal_id):
    new_name = request.form['updated_name']
    new_target = float(request.form['updated_target'])
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE Goals SET name = ?, target_amount = ?, updated_at = ? WHERE id = ?',
              (new_name, new_target, now, goal_id))
    conn.commit()
    conn.close()
    return redirect('/saving')

@app.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM Goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    flash("Goal deleted successfully!")
    return redirect('/saving')

@app.route('/update-income', methods=['POST'])
def update_income():
    income = float(request.form['income'])
    monthly = round(income / 12, 2)
    weekly = round(income / 52, 2)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Update the latest income record
    c.execute('SELECT id FROM Income ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    if row:
        c.execute('UPDATE Income SET yearly=?, monthly=?, weekly=? WHERE id=?', (income, monthly, weekly, row[0]))
    else:
        c.execute('INSERT INTO Income (yearly, monthly, weekly) VALUES (?, ?, ?)', (income, monthly, weekly))
    conn.commit()
    conn.close()
    return redirect('/home')

@app.route('/edit-expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if request.method == 'POST':
        amount = float(request.form['amount'])
        date_val = request.form['date']
        description = request.form['description']
        category = request.form['category']
        c.execute('UPDATE Expenses SET amount=?, date=?, description=?, category=? WHERE id=?',
                  (amount, date_val, description, category, expense_id))
        conn.commit()
        conn.close()
        return redirect('/summary')
    else:
        c.execute('SELECT * FROM Expenses WHERE id=?', (expense_id,))
        expense = c.fetchone()
        conn.close()
        categories = ['Groceries','Transport','Entertainment','Utilities','Shopping','Other','saving']
        return render_template('edit_expense.html', expense=expense, categories=categories)

@app.route('/delete-expense/<int:expense_id>')
def delete_expense(expense_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM Expenses WHERE id=?', (expense_id,))
    conn.commit()
    conn.close()
    return redirect('/summary')

from flask import send_file
from io import BytesIO
from fpdf import FPDF

@app.route('/export-report')
def export_report():
    view_mode = request.args.get('view', 'monthly')
    selected_period_label = request.args.get('period')

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get all distinct months and weeks
    c.execute('SELECT DISTINCT strftime("%Y-%m", date) FROM Expenses ORDER BY date DESC')
    month_keys = [row[0] for row in c.fetchall()]
    c.execute('SELECT DISTINCT strftime("%Y-%W", date) FROM Expenses ORDER BY date DESC')
    week_keys = [row[0] for row in c.fetchall()]

    # Prepare periods for month and week
    month_periods = [month_name[int(m.split("-")[1])] + " " + m.split("-")[0] for m in month_keys]  # e.g., July 2025
    week_periods = [f"Week {int(w.split('-')[1])} {w.split('-')[0]}" for w in week_keys]  # e.g., Week 29 2025

    # Default period (first available)
    if not selected_period_label:
        if view_mode == 'monthly' and month_keys:
            selected_period_label = month_periods[0]
        elif view_mode == 'weekly' and week_keys:
            selected_period_label = week_periods[0]

    # Match the label to query period
    if view_mode == 'monthly':
        periods = month_periods
        if selected_period_label in periods:
            idx = periods.index(selected_period_label)
            query_period = month_keys[idx]
        else:
            query_period = datetime.now().strftime('%Y-%m')
            selected_period_label = month_name[int(query_period.split('-')[1])] + " " + query_period.split('-')[0]
    else:
        periods = week_periods
        if selected_period_label in periods:
            idx = periods.index(selected_period_label)
            query_period = week_keys[idx]
        else:
            query_period = datetime.now().strftime('%Y-%W')
            selected_period_label = f"Week {int(query_period.split('-')[1])} {query_period.split('-')[0]}"

    # Fetch expenses and summary data
    try:
        if view_mode == 'monthly':
            c.execute('SELECT date, amount, category FROM Expenses WHERE strftime("%Y-%m", date) = ? ORDER BY date DESC', (query_period,))
        else:
            c.execute('SELECT date, amount, category FROM Expenses WHERE strftime("%Y-%W", date) = ? ORDER BY date DESC', (query_period,))
        expenses = c.fetchall()

        if view_mode == 'monthly':
            c.execute('SELECT category, SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = ? GROUP BY category', (query_period,))
        else:
            c.execute('SELECT category, SUM(amount) FROM Expenses WHERE strftime("%Y-%W", date) = ? GROUP BY category', (query_period,))
        summary_data = c.fetchall()

        if view_mode == 'monthly':
            c.execute('SELECT SUM(amount) FROM Expenses WHERE strftime("%Y-%m", date) = ?', (query_period,))
            total_spent = c.fetchone()[0] or 0
            c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving" AND strftime("%Y-%m", date) = ?', (query_period,))
            total_saved = c.fetchone()[0] or 0
        else:
            c.execute('SELECT SUM(amount) FROM Expenses WHERE strftime("%Y-%W", date) = ?', (query_period,))
            total_spent = c.fetchone()[0] or 0
            c.execute('SELECT SUM(amount) FROM Expenses WHERE category = "saving" AND strftime("%Y-%W", date) = ?', (query_period,))
            total_saved = c.fetchone()[0] or 0

        c.execute('SELECT target_amount FROM Goals WHERE is_active = 1')
        goal = c.fetchone()
        saving_percent = 0
        if goal and goal[0] > 0:
            saving_percent = int(round((total_saved / goal[0]) * 100))
            saving_percent = max(0, min(saving_percent, 100))
    except Exception as e:
        print(f"Error fetching export data: {e}")
        expenses = []
        summary_data = []
        total_spent = 0
        total_saved = 0
        saving_percent = 0

    conn.close()

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"SmartSpend Report - {selected_period_label}", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Expenses:", ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 8, "Date", 1)
    pdf.cell(40, 8, "Amount", 1)
    pdf.cell(60, 8, "Category", 1)
    pdf.ln()

    for exp in expenses:
        pdf.cell(50, 8, exp[0], 1)
        pdf.cell(40, 8, f"${exp[1]:.2f}", 1)
        pdf.cell(60, 8, exp[2], 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Category Summary:", ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(80, 8, "Category", 1)
    pdf.cell(40, 8, "Summary Cost", 1)
    pdf.ln()

    for cat, tot in summary_data:
        pdf.cell(80, 8, cat, 1)
        pdf.cell(40, 8, f"${tot:.2f}", 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Totals:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Total spent in this time period: ${total_spent:.2f}", ln=True)
    pdf.cell(0, 8, f"Total saved in this time period: ${total_saved:.2f}", ln=True)
    pdf.cell(0, 8, f"Saving Goal Progress: {saving_percent}%", ln=True)

    # Output PDF to memory buffer
    pdf_output = BytesIO()
    pdf_output_str = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_output_str)
    pdf_output.seek(0)

    return send_file(pdf_output, as_attachment=True, download_name=f"SmartSpend_Report_{selected_period_label.replace(' ', '_')}.pdf", mimetype="application/pdf")

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
    app.run(debug=True)
