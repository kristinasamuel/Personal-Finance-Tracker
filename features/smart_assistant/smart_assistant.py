import questionary
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta
from collections import defaultdict
import os

from features.analytics.analytics import read_transactions, read_budgets

console = Console()


def daily_financial_check():
    """Provides a daily financial check-up."""
    console.print("\n[bold cyan]----- Daily Financial Check ----- [/bold cyan]")
    today = datetime.now()
    console.print(f"Date: {today.strftime('%Y-%m-%d')}\n")

    transactions = read_transactions()
    budgets = read_budgets()

    # Calculate today's spending
    todays_spending = sum(
        t["amount"] for t in transactions 
        if t["date"].date() == today.date() and t["type"] == "expense"
    )
    console.print(f"Today's Spending: [bold red]{todays_spending / 100:.2f}[/bold red]")

    # Calculate daily budget
    if budgets:
        total_monthly_budget = sum(budgets.values())
        days_in_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        daily_budget = total_monthly_budget / days_in_month.day if days_in_month.day > 0 else 0
        remaining_daily_budget = daily_budget - todays_spending
        
        daily_budget_style = "green" if remaining_daily_budget >= 0 else "red"
        console.print(f"Estimated Daily Budget: [green]{daily_budget / 100:.2f}[/green]")
        console.print(f"Remaining Daily Budget: [{daily_budget_style}]{remaining_daily_budget / 100:.2f}[/{daily_budget_style}]")
    else:
        console.print("No budgets set. Set budgets to get daily estimates.")

    # Alerts
    spending_alerts()

    # Tip of the day
    console.print("\n[bold]💡 Tip of the Day:[/bold]")
    _get_daily_tip(transactions, budgets)


def _get_daily_tip(transactions, budgets):
    """Helper to provide a simple daily financial tip."""
    if not budgets:
        console.print("  - Set budgets for your main spending categories to better control your finances.")
        return
    
    savings_this_month = sum(t["amount"] for t in transactions if t["type"] == "income") - sum(t["amount"] for t in transactions if t["type"] == "expense")
    if savings_this_month > 0:
        console.print("  - You are on track to save this month. Consider allocating a portion of your savings to an investment.")
    else:
        console.print("  - Review your recent expenses. Can you identify one non-essential purchase to skip next week?")


def smart_recommendations():
    """Generates and displays smart financial recommendations."""
    console.print("\n[bold cyan]----- Smart Recommendations ----- [/bold cyan]")
    transactions = read_transactions()
    budgets = read_budgets()
    recommendations = []

    # Recommendation Engine Rules
    # 1. Overspending Categories
    if budgets:
        current_month_expenses = defaultdict(int)
        today = datetime.now()
        for t in transactions:
            if t["type"] == "expense" and t["date"].month == today.month and t["date"].year == today.year:
                current_month_expenses[t["category"]] += t["amount"]

        over_budget_categories = [cat for cat, budget in budgets.items() if current_month_expenses.get(cat, 0) > budget]
        if over_budget_categories:
            recommendations.append(f"You are over budget in {', '.join(over_budget_categories)}. Consider reducing spending in these areas.")

    # 2. Low Savings Rate
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income" and t["date"].month == datetime.now().month)
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense" and t["date"].month == datetime.now().month)
    savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else -100
    if savings_rate < 10:
        recommendations.append("Your savings rate is low. Try the 50/30/20 rule: 50% on needs, 30% on wants, and 20% on savings.")

    # 3. No Budgets Set
    if not budgets:
        recommendations.append("You don't have any budgets set. Setting budgets for categories like Food, Shopping, and Transport can help you control your spending.")

    # 4. Good Performance
    if savings_rate > 20 and not over_budget_categories:
        recommendations.append("You are doing a great job with your finances! Consider increasing your savings goal or investing more.")

    # Display Recommendations
    if recommendations:
        console.print("\n[bold]Here are some recommendations for you:[/bold]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"{i}. {rec}")
    else:
        console.print("\n[green]You are on the right track. Keep up the good work![/green]")
    
    # Also show current alerts
    spending_alerts()


def spending_alerts():
    """Checks for and displays any spending alerts."""
    console.print("\n[bold]⚠️ Active Alerts:[/bold]")
    transactions = read_transactions()
    budgets = read_budgets()
    alerts = []
    
    # Budget alerts
    if budgets:
        current_month_expenses = defaultdict(int)
        today = datetime.now()
        for t in transactions:
            if t["type"] == "expense" and t["date"].month == today.month and t["date"].year == today.year:
                current_month_expenses[t["category"]] += t["amount"]

        for category, budget_amount in budgets.items():
            spent_amount = current_month_expenses.get(category, 0)
            utilization = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0
            if utilization >= 80:
                alerts.append(f"  - [yellow]High budget utilization for '{category}': {utilization:.1f}% used.[/yellow]")

    # Large transaction alerts
    if transactions:
        total_income_current_month = sum(t["amount"] for t in transactions if t["type"] == "income" and t["date"].month == datetime.now().month)
        if total_income_current_month > 0:
            for t in transactions:
                if t["type"] == "expense" and t["date"].date() == datetime.now().date():
                    if t["amount"] > (total_income_current_month * 0.2): # Over 20% of monthly income
                        alerts.append(f"  - [orange3]Large transaction detected: {t['amount']/100:.2f} for '{t['description']}'.[/orange3]")
    
    if not alerts:
        console.print("  - No active alerts. Well done!")
    else:
        for alert in alerts:
            console.print(alert)

def savings_opportunities():
    """Analyzes spending to find savings opportunities."""
    console.print("\n[bold cyan]----- Savings Opportunities ----- [/bold cyan]")
    transactions = read_transactions()
    
    current_month_expenses = defaultdict(int)
    today = datetime.now()
    for t in transactions:
        if t["type"] == "expense" and t["date"].month == today.month and t["date"].year == today.year:
            current_month_expenses[t["category"]] += t["amount"]

    if not current_month_expenses:
        console.print("[yellow]Not enough spending data to identify savings opportunities.[/yellow]")
        return
        
    # Find top spending category that is not a "bill"
    top_category = None
    top_amount = 0
    for category, amount in sorted(current_month_expenses.items(), key=lambda item: item[1], reverse=True):
        if category.lower() not in ["bills", "health", "transport"]: # Exclude essentials
            top_category = category
            top_amount = amount
            break
            
    if not top_category:
        console.print("[green]Your spending on non-essential categories is well-managed this month![/green]")
        return

    console.print("\n[bold]Spending Reduction Suggestion:[/bold]")
    console.print(f"Your top discretionary spending category this month is [bold]'{top_category}'[/bold] with a total of {top_amount / 100:.2f}.")

    # Suggest a 20% reduction
    reduction_percentage = 20
    potential_savings = top_amount * (reduction_percentage / 100)
    console.print(f"By reducing your '{top_category}' spending by {reduction_percentage}%, you could save an estimated [bold green]{potential_savings / 100:.2f}[/bold green] per month.")

    console.print("\n[bold]'What If' Scenario:[/bold]")
    annual_savings = potential_savings * 12
    console.print(f"Saving {potential_savings / 100:.2f} per month could lead to an extra [bold green]{annual_savings / 100:.2f}[/bold green] in one year!")
    console.print(f"In five years, that could become [bold green]{(annual_savings * 5) / 100:.2f}[/bold green] (not including any investment returns).")

def set_financial_goal():
    """Allows users to set financial goals."""
    console.print("\n[bold cyan]----- Set a New Financial Goal ----- [/bold cyan]")
    try:
        goal_name = questionary.text("What is the name of your goal? (e.g., Emergency Fund)").ask()
        if not goal_name: return

        target_amount_str = questionary.text(
            f"What is the target amount for '{goal_name}'?",
            validate=lambda text: text.replace('.', '', 1).isdigit() and float(text) > 0 or "Please enter a valid positive amount."
        ).ask()
        if not target_amount_str: return
        
        target_amount_paisa = int(float(target_amount_str) * 100)

        # For simplicity, we'll store a "current amount" of 0.
        # A more complex system might allocate savings.
        with open("database/goals.txt", "a") as f:
            f.write(f"{goal_name},{target_amount_paisa},0\n")
        
        console.print(f"[green]Goal '{goal_name}' set successfully![/green]")

    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")


def view_financial_goals():
    """Displays progress towards financial goals."""
    console.print("\n[bold cyan]----- Your Financial Goals ----- [/bold cyan]")
    try:
        with open("database/goals.txt", "r") as f:
            goals = f.readlines()
        
        if not goals:
            console.print("[yellow]You have not set any financial goals yet.[/yellow]")
            return

        transactions = read_transactions()
        total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
        total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
        # Simplified: total net savings is considered the "current amount" for all goals.
        current_savings = total_income - total_expense
        
        console.print(f"Your current total savings available is [bold green]{current_savings / 100:.2f}[/bold green].\n")

        for goal in goals:
            parts = goal.strip().split(',')
            if len(parts) == 3:
                name, target_paisa_str, _ = parts
                target_paisa = int(target_paisa_str)

                progress_percent = (current_savings / target_paisa * 100) if target_paisa > 0 else 0
                progress_percent = min(progress_percent, 100) # Cap at 100%

                console.print(f"[bold]{name}[/bold] (Target: {target_paisa/100:.2f})")
                
                progress_bar_length = 40
                filled_length = int(progress_bar_length * (progress_percent / 100))
                empty_length = progress_bar_length - filled_length
                progress_bar = f"[green]{'█' * filled_length}[/green][white]{'░' * empty_length}[/white]"

                console.print(f"{progress_bar} {progress_percent:.1f}%")
                console.print(f"  Saved: {min(current_savings, target_paisa) / 100:.2f} / {target_paisa / 100:.2f}\n")
    
    except FileNotFoundError:
        console.print("[yellow]You have not set any financial goals yet.[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred while viewing goals: {e}[/red]")
