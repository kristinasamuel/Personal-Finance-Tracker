import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from datetime import datetime, timedelta
from collections import defaultdict
import os

console = Console()

# Helper function to read transactions
def read_transactions():
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
        console.print("[yellow]No transactions found.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading transactions: {e}[/red]")
    return transactions

# Helper function to read budgets
def read_budgets():
    budgets = {}
    try:
        with open("database/budgets.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    category, amount = parts
                    budgets[category] = int(amount)
    except FileNotFoundError:
        console.print("[yellow]No budgets set yet.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading budgets: {e}[/red]")
    return budgets

def spending_analysis():
    """Performs and displays spending analysis."""
    console.print("\n[bold magenta]----- Spending Analysis ----- [/bold magenta]")
    transactions = read_transactions()
    if not transactions:
        console.print("[yellow]No transactions available for analysis.[/yellow]")
        return

    current_month_expenses = defaultdict(int)
    last_month_expenses = defaultdict(int)
    current_month_total_expense = 0
    last_month_total_expense = 0

    today = datetime.now()
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate last month's start and end
    first_day_of_current_month = today.replace(day=1)
    last_month_end = first_day_of_current_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


    for t in transactions:
        if t["type"] == "expense":
            if t["date"].month == today.month and t["date"].year == today.year:
                current_month_expenses[t["category"]] += t["amount"]
                current_month_total_expense += t["amount"]
            elif t["date"].month == last_month_start.month and t["date"].year == last_month_start.year:
                last_month_expenses[t["category"]] += t["amount"]
                last_month_total_expense += t["amount"]

    if current_month_total_expense == 0:
        console.print("[yellow]No expenses recorded for the current month.[/yellow]")
        return

    # 1. Breakdown by category (ASCII pie chart)
    console.print("\n[bold]Spending by Category (Current Month):[/bold]")
    for category, amount in sorted(current_month_expenses.items(), key=lambda item: item[1], reverse=True):
        percentage = (amount / current_month_total_expense) * 100
        bar = '█' * int(percentage // 2) # Each block represents 2%
        console.print(f"{category:<15} {bar:<25} {percentage:.1f}% ({amount / 100:.2f})")

    # 2. Top 3 spending categories
    console.print("\n[bold]Top 3 Spending Categories (Current Month):[/bold]")
    sorted_expenses = sorted(current_month_expenses.items(), key=lambda item: item[1], reverse=True)
    for i, (category, amount) in enumerate(sorted_expenses[:3]):
        console.print(f"{i+1}. {category}: {amount / 100:.2f}")

    # 3. Average daily expense
    days_in_month_so_far = (today - current_month_start).days + 1
    average_daily_expense = current_month_total_expense / days_in_month_so_far if days_in_month_so_far > 0 else 0
    console.print(f"\n[bold]Average Daily Expense (Current Month):[/bold] {average_daily_expense / 100:.2f}")

    # 4. Comparison with last month and spending trends
    console.print("\n[bold]Month-over-Month Spending Comparison:[/bold]")
    console.print(f"  Current Month Total Expense: {current_month_total_expense / 100:.2f}")
    console.print(f"  Last Month Total Expense: {last_month_total_expense / 100:.2f}")

    if last_month_total_expense > 0:
        change = ((current_month_total_expense - last_month_total_expense) / last_month_total_expense) * 100
        if change > 0:
            console.print(f"  Spending is [red]up {change:.1f}%[/red] compared to last month.")
        elif change < 0:
            console.print(f"  Spending is [green]down {abs(change):.1f}%[/green] compared to last month.")
        else:
            console.print("  Spending is about the same as last month.")
    else:
        if current_month_total_expense > 0:
            console.print("  No expenses recorded last month to compare.")

def income_analysis():
    """Performs and displays income analysis."""
    console.print("\n[bold magenta]----- Income Analysis ----- [/bold magenta]")
    transactions = read_transactions()
    if not transactions:
        console.print("[yellow]No transactions available for analysis.[/yellow]")
        return

    current_month_income = defaultdict(int)
    last_month_income = defaultdict(int)
    current_month_total_income = 0
    last_month_total_income = 0

    today = datetime.now()
    first_day_of_current_month = today.replace(day=1)
    last_month_end = first_day_of_current_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for t in transactions:
        if t["type"] == "income":
            if t["date"].month == today.month and t["date"].year == today.year:
                current_month_income[t["category"]] += t["amount"]
                current_month_total_income += t["amount"]
            elif t["date"].month == last_month_start.month and t["date"].year == last_month_start.year:
                last_month_income[t["category"]] += t["amount"]
                last_month_total_income += t["amount"]

    if current_month_total_income == 0:
        console.print("[yellow]No income recorded for the current month.[/yellow]")
        return

    # 1. Income by source
    console.print("\n[bold]Income by Source (Current Month):[/bold]")
    for source, amount in sorted(current_month_income.items(), key=lambda item: item[1], reverse=True):
        console.print(f"- {source}: {amount / 100:.2f}")

    # 2. Total income this month
    console.print(f"\n[bold]Total Income (Current Month):[/bold] {current_month_total_income / 100:.2f}")

    # 3. Comparison with last month
    console.print("\n[bold]Month-over-Month Income Comparison:[/bold]")
    console.print(f"  Current Month Total Income: {current_month_total_income / 100:.2f}")
    console.print(f"  Last Month Total Income: {last_month_total_income / 100:.2f}")

    if last_month_total_income > 0:
        change = ((current_month_total_income - last_month_total_income) / last_month_total_income) * 100
        if change > 0:
            console.print(f"  Income is [green]up {change:.1f}%[/green] compared to last month.")
        elif change < 0:
            console.print(f"  Income is [red]down {abs(change):.1f}%[/red] compared to last month.")
        else:
            console.print("  Income is about the same as last month.")
    else:
        if current_month_total_income > 0:
            console.print("  No income recorded last month to compare.")
    
    # 4. Income stability (simple assessment)
    console.print("\n[bold]Income Stability Assessment:[/bold]")
    if last_month_total_income > 0 and abs(current_month_total_income - last_month_total_income) < (last_month_total_income * 0.1):
        console.print("[green]  Your income appears to be stable.[/green]")
    elif current_month_total_income > 0 and last_month_total_income == 0:
        console.print("[yellow]  First month with income recorded, or income is new.[/yellow]")
    else:
        console.print("[yellow]  Your income shows some fluctuations month-over-month. Consider analyzing sources for consistency.[/yellow]")

def savings_analysis():
    """Performs and displays savings analysis."""
    console.print("\n[bold magenta]----- Savings Analysis ----- [/bold magenta]")
    transactions = read_transactions()
    if not transactions:
        console.print("[yellow]No transactions available for analysis.[/yellow]")
        return

    monthly_data = defaultdict(lambda: {"income": 0, "expense": 0})
    today = datetime.now()

    for t in transactions:
        month_year = (t["date"].year, t["date"].month)
        if t["type"] == "income":
            monthly_data[month_year]["income"] += t["amount"]
        elif t["type"] == "expense":
            monthly_data[month_year]["expense"] += t["amount"]

    # Get data for the last 3 months
    savings_trend = []
    for i in range(3):
        target_month = today.replace(day=1) - timedelta(days=30 * i) # Approximate
        target_month_year = (target_month.year, target_month.month)
        
        income = monthly_data[target_month_year]["income"]
        expense = monthly_data[target_month_year]["expense"]
        savings = income - expense
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        savings_trend.append({
            "month": target_month.strftime('%Y-%m'),
            "income": income,
            "expense": expense,
            "savings": savings,
            "savings_rate": savings_rate
        })
    savings_trend.reverse() # Oldest to newest

    current_month_savings = savings_trend[-1]["savings"]
    current_month_savings_rate = savings_trend[-1]["savings_rate"]

    # 1. Monthly savings amount
    console.print(f"\n[bold]Current Month ({savings_trend[-1]['month']}) Savings:[/bold] {current_month_savings / 100:.2f}")

    # 2. Savings rate %
    console.print(f"[bold]Current Month Savings Rate:[/bold] {current_month_savings_rate:.1f}%")

    # 3. Savings trend (last 3 months)
    console.print("\n[bold]Savings Trend (Last 3 Months):[/bold]")
    table = Table()
    table.add_column("Month", style="cyan")
    table.add_column("Income", justify="right", style="green")
    table.add_column("Expense", justify="right", style="red")
    table.add_column("Savings", justify="right")
    table.add_column("Savings Rate", justify="right")

    for data in savings_trend:
        savings_style = "green" if data["savings"] >= 0 else "red"
        table.add_row(
            data["month"],
            f"{data['income'] / 100:.2f}",
            f"{data['expense'] / 100:.2f}",
            f"[{savings_style}]{data['savings'] / 100:.2f}[/{savings_style}]",
            f"{data['savings_rate']:.1f}%"
        )
    console.print(table)

    # 4. Savings goal progress (simple feedback)
    console.print("\n[bold]Savings Feedback:[/bold]")
    if current_month_savings_rate >= 20:
        console.print("[green]  Excellent savings rate! Keep up the great work.[/green]")
    elif current_month_savings_rate >= 10:
        console.print("[yellow]  Good progress on savings. Consider ways to increase it further.[/yellow]")
    else:
        console.print("[red]  Your savings rate is low. Review your expenses to find areas for improvement.[/red]")

def financial_health_score():
    """Calculates and displays financial health score."""
    console.print("\n[bold magenta]----- Financial Health Score ----- [/bold magenta]")
    transactions = read_transactions()
    budgets_data = read_budgets()

    if not transactions:
        console.print("[yellow]No transactions available to calculate financial health score.[/yellow]")
        return
    
    current_month = datetime.now().month
    current_year = datetime.now().year

    total_income_current_month = 0
    total_expense_current_month = 0
    expenses_by_category_current_month = defaultdict(int)

    for t in transactions:
        if t["date"].month == current_month and t["date"].year == current_year:
            if t["type"] == "income":
                total_income_current_month += t["amount"]
            elif t["type"] == "expense":
                total_expense_current_month += t["amount"]
                expenses_by_category_current_month[t["category"]] += t["amount"]
    
    score = 0
    recommendations = []
    
    # 1. Savings Rate (40 points)
    savings = total_income_current_month - total_expense_current_month
    savings_rate = (savings / total_income_current_month * 100) if total_income_current_month > 0 else 0
    
    savings_score = 0
    if savings_rate >= 20:
        savings_score = 40
    elif savings_rate >= 10:
        savings_score = 25
    elif savings_rate > 0:
        savings_score = 10
    else:
        recommendations.append("Increase your savings rate by reducing unnecessary expenses or increasing income.")
    score += savings_score
    console.print(f"  - Savings Rate Score: [bold]{savings_score}[/bold]/40 ({savings_rate:.1f}%)")

    # 2. Budget Adherence (30 points)
    budget_adherence_score = 0
    if budgets_data:
        over_budget_categories = 0
        total_budget_amount = 0
        total_spent_against_budget = 0
        
        for category, budget_amount in budgets_data.items():
            spent = expenses_by_category_current_month.get(category, 0)
            total_budget_amount += budget_amount
            total_spent_against_budget += min(spent, budget_amount) # Only count spent up to budget for adherence
            if spent > budget_amount:
                over_budget_categories += 1
        
        if total_budget_amount > 0:
            if over_budget_categories == 0 and total_spent_against_budget <= total_budget_amount:
                budget_adherence_score = 30
            elif over_budget_categories == 0 and total_spent_against_budget > total_budget_amount: # Spent more than total budget but not over individual categories
                budget_adherence_score = 20
                recommendations.append("Review your overall budget, as total spending exceeded total allocated budget.")
            elif over_budget_categories > 0:
                budget_adherence_score = 10
                recommendations.append(f"Address overspending in categories: {[c for c, b in budgets_data.items() if expenses_by_category_current_month.get(c, 0) > b]}.")
        else:
            recommendations.append("Set up budgets for better financial control.")
    else:
        recommendations.append("Set up budgets to track your spending effectively.")

    score += budget_adherence_score
    console.print(f"  - Budget Adherence Score: [bold]{budget_adherence_score}[/bold]/30")

    # 3. Income vs Expenses (30 points)
    income_vs_expense_score = 0
    if total_income_current_month > 0:
        if savings >= (total_income_current_month * 0.2): # Saving 20% or more
            income_vs_expense_score = 30
        elif savings > 0: # Positive savings
            income_vs_expense_score = 20
        elif savings == 0: # Break even
            income_vs_expense_score = 10
            recommendations.append("Aim to have positive savings (income > expenses).")
        else: # Negative savings
            income_vs_expense_score = 0
            recommendations.append("Your expenses exceed your income. Focus on reducing spending or increasing income.")
    else:
        if total_expense_current_month > 0:
            recommendations.append("No income recorded for the current month, but expenses exist. Please record your income.")
    score += income_vs_expense_score
    console.print(f"  - Income vs Expenses Score: [bold]{income_vs_expense_score}[/bold]/30")

    console.print(f"\n[bold green]Overall Financial Health Score: {score}/100[/bold green]")

    if score >= 80:
        console.print("[green]  Interpretation: Excellent! Your finances are in great shape. Keep up the good habits.[/green]")
    elif score >= 60:
        console.print("[yellow]  Interpretation: Good. You're on the right track, but there's room for improvement.[/yellow]")
    elif score >= 40:
        console.print("[orange3]  Interpretation: Fair. Some areas need attention to improve your financial health.[/orange3]")
    else:
        console.print("[red]  Interpretation: Needs Work. It's time to take serious action to improve your financial situation.[/red]")
    
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"  - {rec}")
    else:
        console.print("\n[bold]Recommendations:[/bold]\n  - Continue monitoring your finances and adjust as needed.")

def generate_comprehensive_report():
    """Generates and displays a comprehensive financial report."""
    console.print("\n[bold magenta]----- Comprehensive Monthly Financial Report ----- [/bold magenta]")
    console.print(f"[bold]Report for:[/bold] {datetime.now().strftime('%B %Y')}\n")

    transactions = read_transactions()
    budgets_data = read_budgets()

    if not transactions:
        console.print("[yellow]No transactions available to generate a comprehensive report.[/yellow]")
        return
    
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Filter current month's transactions
    current_month_transactions = [
        t for t in transactions 
        if t["date"].month == current_month and t["date"].year == current_year
    ]

    total_income = sum(t["amount"] for t in current_month_transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in current_month_transactions if t["type"] == "expense")
    net_savings = total_income - total_expense

    # Month Overview
    console.print("[bold underline]1. Month Overview[/underline][/bold]")
    console.print(f"  Total Income: [green]{total_income / 100:.2f}[/green]")
    console.print(f"  Total Expenses: [red]{total_expense / 100:.2f}[/red]")
    net_savings_style = "green" if net_savings >= 0 else "red"
    console.print(f"  Net Savings: [{net_savings_style}]{net_savings / 100:.2f}[/{net_savings_style}]\n")

    # Income Summary
    console.print("[bold underline]2. Income Summary[/underline][/bold]")
    income_by_source = defaultdict(int)
    for t in current_month_transactions:
        if t["type"] == "income":
            income_by_source[t["category"]] += t["amount"]
    
    if income_by_source:
        for source, amount in sorted(income_by_source.items(), key=lambda item: item[1], reverse=True):
            console.print(f"  - {source}: {amount / 100:.2f}")
    else:
        console.print("  No income recorded for this month.")
    console.print("")

    # Expense Summary
    console.print("[bold underline]3. Expense Summary[/underline][/bold]")
    expenses_by_category = defaultdict(int)
    for t in current_month_transactions:
        if t["type"] == "expense":
            expenses_by_category[t["category"]] += t["amount"]
    
    if expenses_by_category:
        for category, amount in sorted(expenses_by_category.items(), key=lambda item: item[1], reverse=True):
            console.print(f"  - {category}: {amount / 100:.2f}")
        
        console.print("\n  [bold]Top 3 Spending Categories:[/bold]")
        for i, (category, amount) in enumerate(sorted(expenses_by_category.items(), key=lambda item: item[1], reverse=True)[:3]):
            console.print(f"  {i+1}. {category}: {amount / 100:.2f}")
    else:
        console.print("  No expenses recorded for this month.")
    console.print("")

    # Budget Performance
    console.print("[bold underline]4. Budget Performance[/underline][/bold]")
    if budgets_data:
        budget_table = Table()
        budget_table.add_column("Category", style="cyan")
        budget_table.add_column("Budget", justify="right")
        budget_table.add_column("Spent", justify="right")
        budget_table.add_column("Remaining", justify="right")
        budget_table.add_column("Status", justify="left")

        for category, budget_amount in budgets_data.items():
            spent_amount = expenses_by_category.get(category, 0)
            remaining_amount = budget_amount - spent_amount
            status_style = "green"
            status_text = "OK"
            if spent_amount > budget_amount * 0.9:
                status_style = "yellow"
                status_text = "Nearing Limit"
            if spent_amount > budget_amount:
                status_style = "red"
                status_text = "OVER BUDGET"
            
            budget_table.add_row(
                category,
                f"{budget_amount / 100:.2f}",
                f"{spent_amount / 100:.2f}",
                f"[{status_style}]{remaining_amount / 100:.2f}[/{status_style}]",
                f"[{status_style}]{status_text}[/{status_style}]"
            )
        console.print(budget_table)
    else:
        console.print("  No budgets set for this month.")
    console.print("")

    # Savings Achieved (re-using logic from savings_analysis)
    console.print("[bold underline]5. Savings Overview[/underline][/bold]")
    if total_income > 0:
        savings_rate = (net_savings / total_income * 100)
        console.print(f"  Net Savings: [{net_savings_style}]{net_savings / 100:.2f}[/{net_savings_style}]")
        console.print(f"  Savings Rate: {savings_rate:.1f}%")
        if savings_rate >= 20:
            console.print("[green]  Excellent savings rate![/green]")
        elif savings_rate >= 10:
            console.print("[yellow]  Good progress on savings.[/yellow]")
        else:
            console.print("[red]  Savings rate needs improvement.[/red]")
    else:
        console.print("  No income recorded, so savings cannot be calculated.")
    console.print("")

    # Simple Next Month Projections
    console.print("[bold underline]6. Next Month Projections (Simplified)[/underline][/bold]")
    if total_income > 0 and total_expense > 0:
        projected_savings = total_income - total_expense # Assume similar spending/income
        proj_style = "green" if projected_savings >= 0 else "red"
        console.print(f"  If current trends continue, projected net savings: [{proj_style}]{projected_savings / 100:.2f}[/{proj_style}]")
    else:
        console.print("  Not enough data to make projections.")
    console.print("")

    # Recommendations from Financial Health Score (simplified)
    console.print("[bold underline]7. Recommendations[/underline][/bold]")
    # This would ideally call financial_health_score and extract recommendations
    # For simplicity, we'll give some general ones based on current month's data
    if net_savings < 0:
        console.print("  - Your expenses exceeded your income this month. Review spending to identify areas for reduction.")
    elif total_income > 0 and (net_savings / total_income) < 0.1:
        console.print("  - Aim to increase your savings rate to at least 10-20% of your income.")
    if budgets_data:
        over_budget_categories = [cat for cat, budget_amount in budgets_data.items() if expenses_by_category.get(cat, 0) > budget_amount]
        if over_budget_categories:
            console.print(f"  - Pay attention to spending in categories like: [red]{', '.join(over_budget_categories)}[/red]")
    console.print("")
