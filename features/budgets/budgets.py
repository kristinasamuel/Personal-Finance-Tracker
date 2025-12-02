import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from datetime import datetime
import os

console = Console()

def set_budget():
    """Allows the user to set a monthly budget for a category."""
    try:
        category = questionary.select(
            "Select a category for the budget:",
            choices=["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]
        ).ask()
        if category is None: return

        amount_str = questionary.text(
            f"Enter the monthly budget amount for {category}:",
            validate=lambda text: text.replace('.', '', 1).isdigit() and float(text) > 0 or "Please enter a valid positive amount."
        ).ask()
        if amount_str is None: return

        amount_paisa = int(float(amount_str) * 100)

        with open("database/budgets.txt", "a") as f:
            f.write(f"{category},{amount_paisa}\n")
        
        console.print(f"[green]Budget for {category} set to {amount_paisa / 100:.2f} successfully![/green]")

    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def view_budgets():
    """Displays all set budgets and tracks spending against them."""
    current_month = datetime.now().month
    current_year = datetime.now().year

    budgets = {}
    expenses = {}

    try:
        with open("database/budgets.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    category, amount = parts
                    budgets[category] = int(amount)
    except FileNotFoundError:
        console.print("[yellow]No budgets set yet.[/yellow]")
        return
    except Exception as e:
        console.print(f"[red]Error reading budgets: {e}[/red]")
        return

    if not budgets:
        console.print("[yellow]No budgets set yet.[/yellow]")
        return

    try:
        with open("database/transactions.txt", "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 5:
                    date_str, type, category, _, amount_str = parts
                    transaction_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if transaction_date.month == current_month and transaction_date.year == current_year and type == 'expense':
                        expenses[category] = expenses.get(category, 0) + int(amount_str)
    except FileNotFoundError:
        console.print("[yellow]No transactions recorded for the current month.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading transactions: {e}[/red]")

    table = Table(title=f"Monthly Budgets ({datetime.now().strftime('%B %Y')})")
    table.add_column("Category", style="cyan", min_width=12)
    table.add_column("Budget", justify="right", style="green")
    table.add_column("Spent", justify="right", style="red")
    table.add_column("Remaining", justify="right")
    table.add_column("Utilization", justify="left")
    table.add_column("Status", justify="left")

    total_budget = 0
    total_spent = 0

    for category, budget_amount in budgets.items():
        spent_amount = expenses.get(category, 0)
        remaining_amount = budget_amount - spent_amount
        
        total_budget += budget_amount
        total_spent += spent_amount

        utilization_percent = (spent_amount / budget_amount * 100) if budget_amount > 0 else 0

        status_style = ""
        status_text = ""
        if utilization_percent < 70:
            status_style = "green"
            status_text = "OK"
        elif utilization_percent >= 70 and utilization_percent <= 100:
            status_style = "yellow"
            status_text = "Warning"
        else:
            status_style = "red"
            status_text = "OVER"
        
        # Progress bar
        progress_bar_length = 20
        filled_length = int(progress_bar_length * (spent_amount / budget_amount)) if budget_amount > 0 else 0
        filled_length = min(filled_length, progress_bar_length) # Cap at max length
        empty_length = progress_bar_length - filled_length
        progress_bar = f"[{status_style}]{'█' * filled_length}{'░' * empty_length}[/]"


        table.add_row(
            category,
            f"{budget_amount / 100:.2f}",
            f"{spent_amount / 100:.2f}",
            f"[bold {status_style}]{remaining_amount / 100:.2f}[/bold {status_style}]",
            f"{progress_bar} {utilization_percent:.1f}%",
            f"[{status_style}]{status_text}[/{status_style}]"
        )
    
    console.print(table)

    # Overall Summary
    overall_remaining = total_budget - total_spent
    overall_utilization_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    overall_status_style = ""
    if overall_utilization_percent < 70:
        overall_status_style = "green"
    elif overall_utilization_percent >= 70 and overall_utilization_percent <= 100:
        overall_status_style = "yellow"
    else:
        overall_status_style = "red"

    console.print("\n[bold]Overall Monthly Summary:[/bold]")
    console.print(f"  Total Budget: [green]{total_budget / 100:.2f}[/green]")
    console.print(f"  Total Spent: [red]{total_spent / 100:.2f}[/red]")
    console.print(f"  Total Remaining: [{overall_status_style}]{overall_remaining / 100:.2f}[/{overall_status_style}]")
    console.print(f"  Overall Utilization: [{overall_status_style}]{overall_utilization_percent:.1f}%[/{overall_status_style}]")

    if overall_remaining < 0:
        console.print("[bold red]  Warning: You are over your total budget for the month![/bold red]")
    
    console.print("\n[bold]Recommendations:[/bold]")
    over_budget_categories = [cat for cat, budget_amount in budgets.items() if expenses.get(cat, 0) > budget_amount]
    if over_budget_categories:
        console.print(f"  - Consider reviewing spending in: [red]{', '.join(over_budget_categories)}[/red]")
    
    if overall_utilization_percent > 90 and overall_remaining > 0:
        console.print("  - You are close to hitting your total budget. Track carefully for the rest of the month.")
    elif overall_utilization_percent < 50:
        console.print("  - Great job managing your budget! Keep up the good work.")
