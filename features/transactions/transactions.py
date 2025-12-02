import questionary
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta

# TODO: Implement the functions below

def add_expense():
    """Adds an expense transaction."""
    console = Console()
    try:
        amount_str = questionary.text(
            "Enter the expense amount:",
            validate=lambda text: text.replace('.', '', 1).isdigit() or "Please enter a valid amount."
        ).ask()
        if amount_str is None: return

        amount = int(float(amount_str) * 100)
        if amount <= 0:
            console.print("[red]Amount must be positive.[/red]")
            return

        category = questionary.select(
            "Select a category:",
            choices=["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]
        ).ask()
        if category is None: return

        description = questionary.text("Enter a description:").ask()
        if description is None: return

        date_str = questionary.text(
            "Enter the date (YYYY-MM-DD) or leave empty for today:",
            default=datetime.now().strftime('%Y-%m-%d')
        ).ask()
        if date_str is None: return

        with open("database/transactions.txt", "a") as f:
            f.write(f"{date_str},expense,{category},{description},{amount}\n")
        
        console.print("[green]Expense added successfully![/green]")

    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def add_income():
    """Adds an income transaction."""
    console = Console()
    try:
        amount_str = questionary.text(
            "Enter the income amount:",
            validate=lambda text: text.replace('.', '', 1).isdigit() or "Please enter a valid amount."
        ).ask()
        if amount_str is None: return

        amount = int(float(amount_str) * 100)
        if amount <= 0:
            console.print("[red]Amount must be positive.[/red]")
            return

        category = questionary.select(
            "Select a source:",
            choices=["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
        ).ask()
        if category is None: return

        description = questionary.text("Enter a description:").ask()
        if description is None: return

        date_str = questionary.text(
            "Enter the date (YYYY-MM-DD) or leave empty for today:",
            default=datetime.now().strftime('%Y-%m-%d')
        ).ask()
        if date_str is None: return

        with open("database/transactions.txt", "a") as f:
            f.write(f"{date_str},income,{category},{description},{amount}\n")
        
        console.print("[green]Income added successfully![/green]")

    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def list_transactions():
    """Lists all transactions."""
    console = Console()
    try:
        with open("database/transactions.txt", "r") as f:
            transactions = f.readlines()

        if not transactions:
            console.print("[yellow]No transactions found.[/yellow]")
            return

        filter_choice = questionary.select(
            "Filter transactions by:",
            choices=["All", "Last 7 days", "Expenses only", "Income only"]
        ).ask()
        if filter_choice is None: return

        table = Table(title="Transactions")
        table.add_column("Date", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="blue")
        table.add_column("Amount", justify="right", style="green")

        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        
        # Parse and sort transactions
        parsed_transactions = []
        for t in transactions:
            try:
                date_str, type, category, description, amount_str = t.strip().split(',')
                amount = int(amount_str)
                date = datetime.strptime(date_str, '%Y-%m-%d')
                parsed_transactions.append((date, type, category, description, amount))
            except ValueError:
                # Skip malformed lines
                continue
        
        # Sort by date descending
        parsed_transactions.sort(key=lambda x: x[0], reverse=True)


        for date, type, category, description, amount in parsed_transactions:
            
            # Apply filters
            if filter_choice == "Last 7 days" and date < seven_days_ago:
                continue
            if filter_choice == "Expenses only" and type != 'expense':
                continue
            if filter_choice == "Income only" and type != 'income':
                continue

            amount_display = f"{amount / 100:.2f}"
            style = "red" if type == 'expense' else "green"
            table.add_row(
                date.strftime('%Y-%m-%d'),
                type.capitalize(),
                category,
                description,
                f"[{style}]{amount_display}[/]"
            )

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]No transactions found.[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def show_balance():
    """Shows the current balance for the month."""
    console = Console()
    try:
        with open("database/transactions.txt", "r") as f:
            transactions = f.readlines()

        if not transactions:
            console.print("[yellow]No transactions found.[/yellow]")
            return

        total_income = 0
        total_expenses = 0
        current_month = datetime.now().month
        current_year = datetime.now().year

        for t in transactions:
            try:
                date_str, type, _, _, amount_str = t.strip().split(',')
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if date.month == current_month and date.year == current_year:
                    amount = int(amount_str)
                    if type == 'income':
                        total_income += amount
                    else:
                        total_expenses += amount
            except ValueError:
                continue

        balance = total_income - total_expenses

        balance_style = "green" if balance >= 0 else "red"

        table = Table(title="Current Month's Balance")
        table.add_column("Category", style="bold")
        table.add_column("Amount", justify="right")

        table.add_row("Total Income", f"[green]{total_income / 100:.2f}[/green]")
        table.add_row("Total Expenses", f"[red]{total_expenses / 100:.2f}[/red]")
        table.add_row("Balance", f"[{balance_style}]{balance / 100:.2f}[/{balance_style}]")

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]No transactions found.[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")
