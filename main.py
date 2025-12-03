import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import os
import shutil
import json
import csv

st.set_page_config(layout="wide", page_title="Finance Tracker")

# --- Data Loading and Caching ---
@st.cache_data
def load_transactions():
    """Reads transactions from the database file."""
    transactions = []
    try:
        if not os.path.exists("database/transactions.txt"):
            os.makedirs("database", exist_ok=True) # Ensure directory exists
            with open("database/transactions.txt", "w") as f: # Create if not exists
                pass
        with open("database/transactions.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    date_str, type, category, description, amount_str = parts
                    transactions.append({
                        "date": datetime.strptime(date_str, '%Y-%m-%d'),
                        "type": type,
                        "category": category,
                        "description": description,
                        "amount": int(amount_str)
                    })
    except FileNotFoundError:
        pass # Should not happen after creating the file
    except Exception as e:
        st.error(f"Error reading transactions: {e}")
    return transactions

@st.cache_data
def load_budgets():
    """Reads budgets from the database file."""
    budgets = {}
    try:
        if not os.path.exists("database/budgets.txt"):
            os.makedirs("database", exist_ok=True) # Ensure directory exists
            with open("database/budgets.txt", "w") as f: # Create if not exists
                pass
        with open("database/budgets.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    category, amount = parts
                    budgets[category] = int(amount)
    except FileNotFoundError:
        pass # Should not happen after creating the file
    except Exception as e:
        st.error(f"Error reading budgets: {e}")
    return budgets

# --- Helper Functions for Data Writing ---
def write_transaction_to_file(date, trans_type, category, description, amount_paisa):
    """Appends a new transaction to transactions.txt and clears cache."""
    with open("database/transactions.txt", "a") as f:
        f.write(f"{date.strftime('%Y-%m-%d')},{trans_type},{category},{description},{amount_paisa}\n")
    st.cache_data.clear()
    st.rerun() # Rerun to refresh displayed data

def write_budget_to_file(category, amount_paisa):
    """Appends a new budget to budgets.txt and clears cache."""
    # A more robust system would update existing budgets, but for this, we append.
    # To update, one would read all budgets, modify, then rewrite the file.
    with open("database/budgets.txt", "a") as f:
        f.write(f"{category},{amount_paisa}\n")
    st.cache_data.clear()
    st.rerun() # Rerun to refresh displayed data

# --- UI Pages ---

def dashboard_page():
    st.title("Dashboard")
    st.markdown("A quick overview of your financial health for the current month.")

    transactions = load_transactions()
    budgets = load_budgets()

    if not transactions:
        st.warning("No transaction data. Please add transactions or import data.")
        # Display placeholders for balance and budget if no transactions
        st.header("Current Month's Financial Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", "Rs. 0.00")
        col2.metric("Total Expense", "Rs. 0.00")
        col3.metric("Current Balance", "Rs. 0.00")
        st.markdown("---")
        st.header("Budget Status")
        st.info("No budgets have been set or no transactions to track against budgets.")
        st.markdown("---")
        st.header("Recent Transactions")
        st.info("No recent transactions.")
        return

    df = pd.DataFrame(transactions)
    df['amount'] = df['amount'] / 100
    df['date'] = pd.to_datetime(df['date'])
    
    current_month_df = df[df['date'].dt.month == datetime.now().month]

    # --- Balance Section ---
    st.header("Current Month's Financial Overview")
    if current_month_df.empty:
        st.info("No transactions recorded for the current month.")
        total_income = 0.0
        total_expense = 0.0
        balance = 0.0
    else:
        total_income = current_month_df[current_month_df['type'] == 'income']['amount'].sum()
        total_expense = current_month_df[current_month_df['type'] == 'expense']['amount'].sum()
        balance = total_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"Rs. {total_income:,.2f}")
    col2.metric("Total Expense", f"Rs. {total_expense:,.2f}")
    col3.metric("Current Balance", f"Rs. {balance:,.2f}")

    st.markdown("---")

    # --- Budget Status Section ---
    st.header("Budget Status")
    if not budgets:
        st.info("No budgets have been set.")
    else:
        num_budgets = len(budgets)
        cols_per_row = 3
        
        # Determine how many columns are actually needed, max 3 per row
        num_effective_cols = min(num_budgets, cols_per_row)
        if num_effective_cols == 0: # Handle case where budgets dict might be empty but not None
            st.info("No budgets have been set.")
            return

        budget_items = list(budgets.items())
        
        # Split budgets into rows
        for i in range(0, num_budgets, cols_per_row):
            current_row_budgets = budget_items[i : i + cols_per_row]
            cols = st.columns(len(current_row_budgets)) # Create columns for only this row's budgets
            
            for col_idx, (category, budget_amount_paisa) in enumerate(current_row_budgets):
                with cols[col_idx]:
                    budget_amount = budget_amount_paisa / 100
                    # Safely get spent amount, ensuring it's 0 if no expenses for category
                    spent = current_month_df[(current_month_df['category'] == category) & (current_month_df['type'] == 'expense')]['amount'].sum() if not current_month_df.empty else 0.0
                    utilization = (spent / budget_amount * 100) if budget_amount > 0 else 0
                    
                    st.subheader(category)
                    
                    st.write(f"Budget: Rs. {budget_amount:,.2f}")
                    st.write(f"Spent: Rs. {spent:,.2f}")

                    # Determine color for the progress bar
                    if utilization < 70:
                        progress_color_style = "#4CAF50" # Green
                    elif 70 <= utilization < 100:
                        progress_color_style = "#FFC107" # Amber
                    else:
                        progress_color_style = "#F44336" # Red
                    
                    st.markdown(f"""
                        <style>
                            .stProgress > div > div > div > div {{
                                background-color: {progress_color_style};
                            }}
                        </style>""", unsafe_allow_html=True)
                    st.progress(min(utilization / 100, 1.0))
                    st.write(f"Utilization: {utilization:.1f}%")

                    if utilization > 100:
                        st.error(f"Over budget by Rs. {spent - budget_amount:,.2f}!")
    
    st.markdown("---")
    
    # --- Recent Transactions Table ---
    st.header("Recent Transactions")
    if not df.empty:
        def style_type(series):
            return ['color: green' if val == 'income' else 'color: red' for val in series]
        st.dataframe(
            df.sort_values(by="date", ascending=False).head(10)
            .style.apply(style_type, subset=['type'])
            .format({"amount": "Rs. {:,.2f}"}),
            use_container_width=True
        )
    else:
        st.info("No transactions yet.")

def transactions_page():
    st.title("Manage Transactions")
    
    with st.expander("Add New Transaction", expanded=False):
        with st.form("new_transaction_form", clear_on_submit=True):
            trans_type = st.selectbox("Type", ["expense", "income"], key="trans_type_select")
            
            # Dynamically set categories based on transaction type
            if trans_type == "expense":
                category_choices = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]
            else:
                category_choices = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
            
            category = st.selectbox("Category", category_choices, key="trans_category_select")
            
            amount = st.number_input("Amount (Rs.)", min_value=0.01, step=0.01, format="%.2f", key="trans_amount_input")
            description = st.text_input("Description", key="trans_description_input")
            date = st.date_input("Date", datetime.now(), key="trans_date_input")
            
            submitted = st.form_submit_button("Add Transaction", key="add_trans_button")
            if submitted:
                write_transaction_to_file(date, trans_type, category, description, int(amount*100))
                st.success("Transaction added!")
                # st.rerun() is already in write_transaction_to_file


    st.header("All Transactions")
    transactions = load_transactions()
    if transactions:
        df = pd.DataFrame(transactions)
        df['amount'] = df['amount'] / 100
        df['date'] = pd.to_datetime(df['date'])
        
        def style_type(series):
            return ['color: green' if val == 'income' else 'color: red' for val in series]
            
        st.dataframe(
            df.sort_values(by="date", ascending=False)
            .style.apply(style_type, subset=['type'])
            .format({"amount": "Rs. {:,.2f}"}),
            use_container_width=True
        )
    else:
        st.info("No transactions yet.")


def budgets_page():
    st.title("Manage Budgets")
    
    with st.expander("Set New Budget", expanded=False):
        with st.form("new_budget_form", clear_on_submit=True):
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"], key="budget_category_select")
            amount = st.number_input("Monthly Budget Amount (Rs.)", min_value=1.0, step=10.0, format="%.2f", key="budget_amount_input")
            
            submitted = st.form_submit_button("Set Budget", key="set_budget_button")
            if submitted:
                write_budget_to_file(category, int(amount*100))
                st.success(f"Budget for {category} set!")

    transactions = load_transactions()
    budgets = load_budgets()

    if not budgets:
        st.info("No budgets have been set. Use the form above to set your monthly budgets.")
        return

    st.header("Current Month's Budget Tracking")

    if not transactions:
        st.info("No transactions recorded to track against budgets for the current month.")
        return
    
    df = pd.DataFrame(transactions)
    df['amount'] = df['amount'] / 100
    df['date'] = pd.to_datetime(df['date'])
    current_month_df = df[df['date'].dt.month == datetime.now().month]

    if current_month_df.empty:
        st.info("No transactions for the current month to track against budgets.")
        return

    num_budgets = len(budgets)
    cols_per_row = 3
    
    budget_items = list(budgets.items())

    # Split budgets into rows for display
    for i in range(0, num_budgets, cols_per_row):
        current_row_budgets = budget_items[i : i + cols_per_row]
        cols = st.columns(len(current_row_budgets)) # Create columns for only this row's budgets
        
        for col_idx, (category, budget_amount_paisa) in enumerate(current_row_budgets):
            with cols[col_idx]:
                budget_amount = budget_amount_paisa / 100
                spent = current_month_df[(current_month_df['category'] == category) & (current_month_df['type'] == 'expense')]['amount'].sum()
                utilization = (spent / budget_amount * 100) if budget_amount > 0 else 0
                
                st.subheader(category)
                st.write(f"Budget: Rs. {budget_amount:,.2f}")
                st.write(f"Spent: Rs. {spent:,.2f}")

                # Determine color for the progress bar
                if utilization < 70:
                    progress_color_style = "#4CAF50" # Green
                elif 70 <= utilization < 100:
                    progress_color_style = "#FFC107" # Amber
                else:
                    progress_color_style = "#F44336" # Red
                
                st.markdown(f"""
                    <style>
                        .stProgress > div > div > div > div {{
                            background-color: {progress_color_style};
                        }}
                    </style>""", unsafe_allow_html=True)
                st.progress(min(utilization / 100, 1.0))
                st.write(f"Utilization: {utilization:.1f}%")

                if utilization > 100:
                    st.error(f"Over budget by Rs. {spent - budget_amount:,.2f}!")

def analytics_page():
    st.title("Financial Analytics")
    st.markdown("Dive deeper into your spending, income, and savings patterns.")

    transactions = load_transactions()
    budgets = load_budgets()

    if not transactions:
        st.warning("No transaction data available for analytics.")
        return

    df = pd.DataFrame(transactions)
    df['amount'] = df['amount'] / 100
    df['date'] = pd.to_datetime(df['date'])
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_df = df[df['date'].dt.month == current_month]

    # --- Spending Analysis ---
    st.header("Spending Analysis")
    if not current_month_df.empty:
        expense_df = current_month_df[current_month_df['type'] == 'expense']
        if not expense_df.empty:
            spending_by_category = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False)
            
            st.subheader("Spending Breakdown by Category")
            st.dataframe(spending_by_category.to_frame().style.format({"amount": "Rs. {:,.2f}"}))
            
            st.subheader("Top 3 Spending Categories")
            for i, (category, amount) in enumerate(spending_by_category.head(3).items()):
                st.write(f"{i+1}. {category}: Rs. {amount:,.2f}")
        else:
            st.info("No expenses recorded for the current month.")
    else:
        st.info("No transactions for the current month.")

    # --- Income Analysis ---
    st.header("Income Analysis")
    if not current_month_df.empty:
        income_df = current_month_df[current_month_df['type'] == 'income']
        if not income_df.empty:
            income_by_source = income_df.groupby('category')['amount'].sum().sort_values(ascending=False)
            st.subheader("Income by Source")
            st.dataframe(income_by_source.to_frame().style.format({"amount": "Rs. {:,.2f}"}))
        else:
            st.info("No income recorded for the current month.")
    else:
        st.info("No transactions for the current month.")

    # --- Savings Analysis ---
    st.header("Savings Analysis")
    total_income_current_month = current_month_df[current_month_df['type'] == 'income']['amount'].sum()
    total_expense_current_month = current_month_df[current_month_df['type'] == 'expense']['amount'].sum()
    net_savings_current_month = total_income_current_month - total_expense_current_month
    savings_rate_current_month = (net_savings_current_month / total_income_current_month * 100) if total_income_current_month > 0 else 0
    
    st.subheader("Current Month's Savings")
    st.metric("Net Savings", f"Rs. {net_savings_current_month:,.2f}")
    st.metric("Savings Rate", f"{savings_rate_current_month:,.1f}%")

    # --- Financial Health Score ---
    st.header("Financial Health Score")
    # This is a simplified calculation for display purposes
    score = 0
    recommendations = []
    
    # Savings Rate (40 points)
    savings_score = 0
    if savings_rate_current_month >= 20:
        savings_score = 40
    elif savings_rate_current_month >= 10:
        savings_score = 25
    elif savings_rate_current_month > 0:
        savings_score = 10
    else:
        recommendations.append("Increase your savings rate by reducing unnecessary expenses or increasing income.")
    score += savings_score

    # Budget Adherence (30 points) - simplified for web
    budget_adherence_score = 0
    if budgets and not expense_df.empty: # Check if budgets exist AND expense_df is not empty
        over_budget_categories_count = 0
        for category, budget_amount_paisa in budgets.items():
            budget_amount = budget_amount_paisa / 100
            # Use .get() with default 0 to safely handle categories not in expense_df
            spent = expense_df[expense_df['category'] == category]['amount'].sum() if category in expense_df['category'].unique() else 0
            if spent > budget_amount:
                over_budget_categories_count += 1
        
        if over_budget_categories_count == 0:
            budget_adherence_score = 30
        elif over_budget_categories_count <= len(budgets) / 2:
            budget_adherence_score = 15
        else:
            budget_adherence_score = 5
    elif budgets and expense_df.empty:
        # If budgets exist but no expenses, perfect adherence for now.
        budget_adherence_score = 30
    else:
        recommendations.append("Set up budgets for better financial control.")
    score += budget_adherence_score

    # Income vs Expenses (30 points)
    income_vs_expense_score = 0
    if total_income_current_month > 0:
        if net_savings_current_month >= (total_income_current_month * 0.2):
            income_vs_expense_score = 30
        elif net_savings_current_month > 0:
            income_vs_expense_score = 20
        elif net_savings_current_month == 0:
            income_vs_expense_score = 10
        else:
            income_vs_expense_score = 0
            recommendations.append("Your expenses exceed your income. Focus on reducing spending or increasing income.")
    score += income_vs_expense_score

    total_score = min(score, 100) # Cap at 100

    col1, col2 = st.columns([1,2])
    with col1:
        st.metric("Overall Score", f"{total_score}/100")
    with col2:
        st.subheader("Score Breakdown")
        st.write(f"Savings Rate: {savings_score}/40")
        st.write(f"Budget Adherence: {budget_adherence_score}/30")
        st.write(f"Income vs Expenses: {income_vs_expense_score}/30")

    if recommendations:
        st.subheader("Recommendations to Improve Score")
        for rec in recommendations:
            st.info(rec)

def smart_assistant_page():
    st.title("Smart Assistant")
    st.markdown("Your personal AI assistant to help you manage your finances.")

    transactions = load_transactions()
    budgets = load_budgets()

    if not transactions:
        st.warning("No transaction data available for the smart assistant.")
        return

    # --- Daily Financial Check ---
    with st.expander("Daily Financial Check", expanded=True):
        st.header(f"Daily Check for {datetime.now().strftime('%Y-%m-%d')}")
        today = datetime.now()
        todays_spending = sum(
            t["amount"] for t in transactions 
            if t["date"].date() == today.date() and t["type"] == "expense"
        ) / 100
        
        st.metric("Today's Spending", f"Rs. {todays_spending:,.2f}")
        
        if budgets:
            total_monthly_budget = sum(budgets.values()) / 100
            days_in_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            daily_budget = total_monthly_budget / days_in_month.day if days_in_month.day > 0 else 0
            
            st.metric("Estimated Daily Budget", f"Rs. {daily_budget:,.2f}")

    # --- Spending Alerts ---
    with st.expander("Active Alerts"):
        alerts = []
        if budgets:
            current_month_expenses = defaultdict(int)
            for t in transactions:
                if t["type"] == "expense" and t["date"].month == today.month:
                    current_month_expenses[t["category"]] += t["amount"]

            for category, budget_amount in budgets.items():
                utilization = (current_month_expenses.get(category, 0) / budget_amount * 100) if budget_amount > 0 else 0
                if utilization >= 80:
                    alerts.append(f"High budget use for '{category}': {utilization:.1f}% used.")
        
        if not alerts:
            st.success("No active alerts. Great job!")
        else:
            for alert in alerts:
                st.warning(alert)

    # --- Smart Recommendations ---
    with st.expander("Recommendations"):
        recommendations = []
        # Add more rules here based on the logic in the smart_assistant.py
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income' and t['date'].month == today.month)
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense' and t['date'].month == today.month)
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else -100

        if savings_rate < 10:
            recommendations.append("Your savings rate is low. Try the 50/30/20 rule (50% needs, 30% wants, 20% savings).")
        if not budgets:
            recommendations.append("Set budgets for top spending categories to gain better control.")
        
        if not recommendations:
            st.info("You're on the right track. Keep up the good work!")
        else:
            for rec in recommendations:
                st.info(rec)

def financial_goals_page():
    st.title("Financial Goals")

    # Goal setting form
    with st.expander("Set a New Goal"):
        with st.form("new_goal_form", clear_on_submit=True):
            goal_name = st.text_input("Goal Name (e.g., Emergency Fund)")
            target_amount = st.number_input("Target Amount (Rs.)", min_value=1.0)
            
            submitted = st.form_submit_button("Set Goal")
            if submitted:
                with open("database/goals.txt", "a") as f:
                    f.write(f"{goal_name},{int(target_amount * 100)},0\n")
                st.success(f"Goal '{goal_name}' set!")

    # Display goals
    st.header("Your Progress")
    try:
        with open("database/goals.txt", "r") as f:
            goals = f.readlines()
        
        if not goals:
            st.info("No financial goals set yet.")
        else:
            transactions = load_transactions()
            total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
            total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
            current_savings = (total_income - total_expense) / 100

            st.metric("Total Savings Available for Goals", f"Rs. {current_savings:,.2f}")
            
            for goal in goals:
                name, target_paisa_str, _ = goal.strip().split(',')
                target_amount = int(target_paisa_str) / 100
                
                progress_percent = (current_savings / target_amount * 100) if target_amount > 0 else 0
                
                st.subheader(name)
                st.progress(min(progress_percent / 100, 1.0))
                st.write(f"Rs. {min(current_savings, target_amount):,.2f} / Rs. {target_amount:,.2f} ({progress_percent:.1f}%)")

    except FileNotFoundError:
        st.info("No goals file found. Set your first goal above!")

def data_management_page():
    st.title("Data Management")
    
    st.subheader("Export Data")
    if st.button("Export Transactions to CSV"):
        transactions = load_transactions()
        df = pd.DataFrame(transactions)
        df['amount'] /= 100
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")

    st.subheader("Import Data")
    uploaded_file = st.file_uploader("Choose a CSV file to import transactions", type="csv")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Basic validation
            if list(df.columns) == ["date", "type", "category", "description", "amount"]:
                if st.button("Import Data"):
                    with open("database/transactions.txt", "a") as f:
                        for _, row in df.iterrows():
                            f.write(f"{row['date']},{row['type']},{row['category']},{row['description']},{int(float(row['amount'])*100)}\n")
                    st.success("Data imported successfully!")
                    st.cache_data.clear()
            else:
                st.error("Invalid CSV format.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- Main App ---
def main():
    st.sidebar.title("Finance Tracker")
    
    pages = {
        "Dashboard": dashboard_page,
        "Transactions": transactions_page,
        "Budgets": budgets_page,
        "Financial Goals": financial_goals_page,
        "Analytics": analytics_page,
        "Smart Assistant": smart_assistant_page,
        "Data Management": data_management_page,
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()), key="sidebar_radio")
    
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()
