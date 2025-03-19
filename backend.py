from flask import Flask, render_template, request, redirect, session
import sqlite3
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = "expense_tracker_secret"  # Required for session management

def init_db():
    """Initialize the database and create the expenses table if not exists."""
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 amount REAL,
                 category TEXT,
                 date TEXT)''')
    conn.commit()
    conn.close()



def generate_chart(expenses_by_category, dark_mode=False):
    """Generate bar and pie charts based on dark mode settings."""
    categories = list(expenses_by_category.keys())
    amounts = [sum(exp[2] for exp in expenses) for expenses in expenses_by_category.values()]

    # Define colors for Dark Mode or Light Mode
    if dark_mode:
        plt.style.use("dark_background")
        colors = ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff']
        text_color = "white"
    else:
        plt.style.use("default")
        colors = ['blue', 'green', 'red', 'purple', 'orange']
        text_color = "black"

   
    
    # Generate bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(categories, amounts, color=colors)
    ax.set_xlabel("Categories", color=text_color)
    ax.set_ylabel("Total Expenses", color=text_color)
    ax.set_title("Expenses by Category", color=text_color)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)

    # Save bar chart to base64
    bar_io = io.BytesIO()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(bar_io, format='png', transparent=True)
    bar_io.seek(0)
    bar_base64 = base64.b64encode(bar_io.getvalue()).decode()

    # Generate pie chart
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(amounts, labels=categories, autopct='%1.1f%%', colors=colors, textprops={'color': text_color})
    ax.set_title("Expense Distribution", color=text_color)

    # Save pie chart to base64
    pie_io = io.BytesIO()
    plt.savefig(pie_io, format='png', transparent=True)
    pie_io.seek(0)
    pie_base64 = base64.b64encode(pie_io.getvalue()).decode()

    return bar_base64, pie_base64




@app.route('/')
def index():
    """Display all expenses, search, and filter by category."""
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    # Fetch unique categories
    c.execute("SELECT DISTINCT LOWER(category) FROM expenses")
    categories = sorted([row[0] for row in c.fetchall()])

    # Get search query, selected category, and dark mode status
    search_query = request.args.get('search', '').strip().lower()
    selected_category = request.args.get('category', 'All').lower()
    dark_mode = session.get("dark_mode", False)

    # Start with the base query
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    # Apply category filter if a specific category is selected
    if selected_category != 'all':
        query += " AND LOWER(category) = ?"
        params.append(selected_category)

    # Apply search filter if a search query is provided
    if search_query:
        query += " AND (LOWER(name) LIKE ? OR LOWER(category) LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    # Execute query
    c.execute(query, params)
    expenses = c.fetchall()

    # Calculate total amount
    total_amount = sum(expense[2] for expense in expenses)

    # Group expenses by category
    expenses_by_category = {}
    for expense in expenses:
        category = expense[3].lower()
        if category not in expenses_by_category:
            expenses_by_category[category] = []
        expenses_by_category[category].append(expense)

    conn.close()

    # Generate charts
    bar_chart, pie_chart = generate_chart(expenses_by_category, dark_mode)

    return render_template('index.html', 
                           expenses_by_category=expenses_by_category, 
                           categories=categories, 
                           selected_category=selected_category,
                           total_amount=total_amount,
                           bar_chart=bar_chart,
                           pie_chart=pie_chart,
                           dark_mode=dark_mode,
                           search_query=search_query)

@app.route('/delete/<int:id>')
def delete_expense(id):
    """Delete an expense from the database."""
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/toggle-dark-mode')
def toggle_dark_mode():
    """Toggle between dark and light mode."""
    session["dark_mode"] = not session.get("dark_mode", False)
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    

    
  
 