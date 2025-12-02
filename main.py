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
        pass
    return transactions

@st.cache_data
def load_budgets():
    """Reads budgets from the database file."""
    budgets = {}
    try:
        with open("database/budgets.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    category, amount = parts
                    budgets[category] = int(amount)
    except FileNotFoundError:
        pass
    return budgets

# --- UI Pages ---

def dashboard_page():
    st.title("Dashboard")
    st.markdown("A quick overview of your financial health for the current month.")

    transactions = load_transactions()
    budgets = load_budgets()

    if not transactions:
        st.warning("No transaction data. Please add transactions or import data.")
        return

    df = pd.DataFrame(transactions)
    df['amount'] = df['amount'] / 100
    df['date'] = pd.to_datetime(df['date'])
    
    current_month_df = df[df['date'].dt.month == datetime.now().month]

    # --- Balance Section ---
    st.header("Current Month's Financial Overview")
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
        cols = st.columns(num_budgets if num_budgets > 0 else 1)
        
        for i, (category, budget_amount_paisa) in enumerate(budgets.items()):
            with cols[i % len(cols)]:
                budget_amount = budget_amount_paisa / 100
                spent = current_month_df[(current_month_df['category'] == category) & (current_month_df['type'] == 'expense')]['amount'].sum()
                utilization = (spent / budget_amount * 100) if budget_amount > 0 else 0
                
                st.subheader(category)
                
                if utilization < 70:
                    st.success(f"Spent: Rs. {spent:,.2f} of Rs. {budget_amount:,.2f}")
                elif 70 <= utilization < 100:
                    st.warning(f"Spent: Rs. {spent:,.2f} of Rs. {budget_amount:,.2f}")
                else:
                    st.error(f"Spent: Rs. {spent:,.2f} of Rs. {budget_amount:,.2f}")
                
                st.progress(min(utilization / 100, 1.0))
                
                if utilization > 100:
                    st.error(f"Over budget by Rs. {spent - budget_amount:,.2f}")
    
    st.markdown("---")
    
    # --- Recent Transactions Table ---
    st.header("Recent Transactions")
    def style_type(series):
        return ['color: green' if val == 'income' else 'color: red' for val in series]
    st.dataframe(
        df.sort_values(by="date", ascending=False).head(10)
        .style.apply(style_type, subset=['type'])
        .format({"amount": "Rs. {:,.2f}"}),
        use_container_width=True
    )

def transactions_page():
    st.title("Manage Transactions")
    
    with st.expander("Add New Transaction", expanded=False):
        with st.form("new_transaction_form", clear_on_submit=True):
            trans_type = st.selectbox("Type", ["expense", "income"])
            if trans_type == "expense":
                category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"])
            else:
                category = st.selectbox("Category", ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"])
            
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
            description = st.text_input("Description")
            date = st.date_input("Date", datetime.now())
            
            submitted = st.form_submit_button("Add Transaction")
            if submitted:
                with open("database/transactions.txt", "a") as f:
                    f.write(f"{date.strftime('%Y-%m-%d')},{trans_type},{category},{description},{int(amount*100)}\n")
                st.success("Transaction added!")
                st.cache_data.clear()

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
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"])
            amount = st.number_input("Monthly Budget Amount", min_value=1.0, step=10.0)
            
            submitted = st.form_submit_button("Set Budget")
            if submitted:
                # This is a simple implementation. A real app should handle updates.
                with open("database/budgets.txt", "a") as f:
                    f.write(f"{category},{int(amount*100)}\n")
                st.success(f"Budget for {category} set!")
                st.cache_data.clear()

    dashboard_page() # Display the dashboard view of budgets

def analytics_page():
    st.title("Financial Analytics")
    # For simplicity, we are calling the dashboard page, which has the main analytics.
    # A more advanced version would have more detailed charts here.
    dashboard_page()

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
