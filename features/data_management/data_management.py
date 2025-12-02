import questionary
from rich.console import Console
import os
import json
import csv
import shutil
from datetime import datetime

from features.analytics.analytics import read_transactions, read_budgets

console = Console()

def export_transactions_csv():
    """Exports all transactions to a CSV file."""
    console.print("\n[bold cyan]----- Export Transactions to CSV ----- [/bold cyan]")
    transactions = read_transactions()
    if not transactions:
        console.print("[yellow]No transactions to export.[/yellow]")
        return

    try:
        filename = "transactions_export.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "description", "amount"])
            
            for t in transactions:
                writer.writerow([
                    t["date"].strftime('%Y-%m-%d'),
                    t["type"],
                    t["category"],
                    t["description"],
                    f"{t['amount'] / 100:.2f}"
                ])
        
        console.print(f"[green]Successfully exported {len(transactions)} transactions to '{filename}'[/green]")
    except Exception as e:
        console.print(f"[red]An error occurred during CSV export: {e}[/red]")

def export_transactions_json():
    """Exports all transactions to a JSON file."""
    console.print("\n[bold cyan]----- Export Transactions to JSON ----- [/bold cyan]")
    transactions = read_transactions()
    if not transactions:
        console.print("[yellow]No transactions to export.[/yellow]")
        return

    try:
        filename = "transactions_export.json"
        
        # Create a serializable version of the transactions
        serializable_transactions = []
        for t in transactions:
            serializable_transactions.append({
                "date": t["date"].isoformat(),
                "type": t["type"],
                "category": t["category"],
                "description": t["description"],
                "amount": t['amount'] / 100
            })

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serializable_transactions, f, indent=4)
        
        console.print(f"[green]Successfully exported {len(transactions)} transactions to '{filename}'[/green]")
    except Exception as e:
        console.print(f"[red]An error occurred during JSON export: {e}[/red]")

def export_monthly_report():
    """Exports a comprehensive monthly report to a JSON file."""
    console.print("\n[bold cyan]----- Export Comprehensive Monthly Report ----- [/bold cyan]")
    
    transactions = read_transactions()
    budgets = read_budgets()
    
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Filter transactions for the current month
    monthly_transactions = [t for t in transactions if t['date'].month == current_month and t['date'].year == current_year]
    
    if not monthly_transactions:
        console.print("[yellow]No transactions found for the current month. Report cannot be generated.[/yellow]")
        return
        
    # --- Start building the report object ---
    report = {
        "report_month": today.strftime("%Y-%m"),
        "generated_at": today.isoformat(),
        "summary": {},
        "income_analysis": {},
        "expense_analysis": {},
        "budget_performance": [],
        "financial_health": {},
        "recommendations": [],
        "transactions": []
    }
    
    # 1. Summary & Core Analytics
    total_income = sum(t['amount'] for t in monthly_transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in monthly_transactions if t['type'] == 'expense')
    net_savings = total_income - total_expense
    
    report["summary"] = {
        "total_income": total_income / 100,
        "total_expense": total_expense / 100,
        "net_savings": net_savings / 100,
        "savings_rate": (net_savings / total_income * 100) if total_income > 0 else 0
    }
    
    # 2. Income & Expense Analysis
    report["income_analysis"]["sources"] = {
        cat: sum(t['amount'] for t in monthly_transactions if t['type'] == 'income' and t['category'] == cat) / 100
        for cat in set(t['category'] for t in monthly_transactions if t['type'] == 'income')
    }
    
    expense_by_cat = {
        cat: sum(t['amount'] for t in monthly_transactions if t['type'] == 'expense' and t['category'] == cat)
        for cat in set(t['category'] for t in monthly_transactions if t['type'] == 'expense')
    }
    report["expense_analysis"]["categories"] = {k: v / 100 for k, v in expense_by_cat.items()}
    
    # 3. Budget Performance
    if budgets:
        for category, budget_amount in budgets.items():
            spent = expense_by_cat.get(category, 0)
            report["budget_performance"].append({
                "category": category,
                "budget": budget_amount / 100,
                "spent": spent / 100,
                "remaining": (budget_amount - spent) / 100,
                "utilization": (spent / budget_amount * 100) if budget_amount > 0 else 0
            })

    # 4. Financial Health Score (Simplified version from smart_assistant)
    savings_score = 40 if report["summary"]["savings_rate"] >= 20 else 10 if report["summary"]["savings_rate"] > 0 else 0
    income_vs_expense_score = 30 if report["summary"]["savings_rate"] >= 20 else 20 if report["summary"]["savings_rate"] > 0 else 0
    report["financial_health"] = {
        "score": savings_score + income_vs_expense_score, # Max 70 without budget score
        "comment": "Score is based on savings and income vs. expense ratio."
    }

    # 5. Recommendations
    if report["summary"]["savings_rate"] < 10:
        report["recommendations"].append("Savings rate is low. Aim to save at least 10-20% of your income.")
    
    # 6. Transactions
    report["transactions"] = [{
        "date": t["date"].isoformat(),
        "type": t["type"],
        "category": t["category"],
        "description": t["description"],
        "amount": t['amount'] / 100
    } for t in monthly_transactions]
    
    # --- Write report to file ---
    try:
        filename = f"monthly_report_{current_year}_{current_month:02d}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        console.print(f"[green]Successfully exported monthly report to '{filename}'[/green]")
    except Exception as e:
        console.print(f"[red]An error occurred during JSON report export: {e}[/red]")

def import_transactions_csv():
    """Imports transactions from a CSV file."""
    console.print("\n[bold cyan]----- Import Transactions from CSV ----- [/bold cyan]")
    
    try:
        filepath = questionary.path("Enter the path to the CSV file:").ask()
        if not filepath or not os.path.exists(filepath):
            console.print("[red]File not found.[/red]")
            return

        with open(filepath, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Validate header
            expected_header = ["date", "type", "category", "description", "amount"]
            if header != expected_header:
                console.print(f"[red]Invalid CSV header. Expected: {expected_header}[/red]")
                return
            
            new_transactions = []
            invalid_rows = 0
            for row in reader:
                try:
                    # Basic validation
                    date_str, type, category, description, amount_str = row
                    datetime.strptime(date_str, '%Y-%m-%d') # Validate date format
                    amount_paisa = int(float(amount_str) * 100)
                    
                    new_transactions.append(f"{date_str},{type.lower()},{category},{description},{amount_paisa}")
                except (ValueError, IndexError):
                    invalid_rows += 1
            
            if not new_transactions and invalid_rows > 0:
                console.print(f"[red]Could not read any valid transactions from the file. Found {invalid_rows} invalid rows.[/red]")
                return

            # Check for duplicates
            try:
                with open("database/transactions.txt", "r") as f:
                    existing_transactions = set(line.strip() for line in f)
            except FileNotFoundError:
                existing_transactions = set()

            unique_transactions_to_add = [t for t in new_transactions if t not in existing_transactions]
            duplicate_count = len(new_transactions) - len(unique_transactions_to_add)

            console.print(f"\n[bold]Import Summary:[/bold]")
            console.print(f"  - Found {len(new_transactions)} transactions in the file.")
            console.print(f"  - [green]{len(unique_transactions_to_add)} new transactions to import.[/green]")
            console.print(f"  - [yellow]{duplicate_count} duplicate transactions will be skipped.[/yellow]")
            console.print(f"  - [red]{invalid_rows} invalid rows were skipped.[/red]")

            if not unique_transactions_to_add:
                console.print("\nNo new transactions to import.")
                return

            confirm = questionary.confirm("Do you want to proceed with the import?").ask()
            if confirm:
                with open("database/transactions.txt", "a") as f:
                    for t_str in unique_transactions_to_add:
                        f.write(t_str + "\n")
                console.print(f"\n[green]Successfully imported {len(unique_transactions_to_add)} new transactions![/green]")
            else:
                console.print("Import cancelled.")

    except FileNotFoundError:
        console.print("[red]The specified file was not found.[/red]")
    except Exception as e:
        console.print(f"[red]An error occurred during import: {e}[/red]")

def backup_data():
    """Creates a timestamped backup of the data files."""
    console.print("\n[bold cyan]----- Create Data Backup ----- [/bold cyan]")
    
    backup_dir = "backups"
    data_dir = "database"
    
    if not os.path.exists(data_dir):
        console.print("[red]Data directory 'database' not found. Nothing to back up.[/red]")
        return
        
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename_base = f"backup-{timestamp}"
        backup_path_base = os.path.join(backup_dir, backup_filename_base)
        
        # Create a zip archive of the database directory
        shutil.make_archive(backup_path_base, 'zip', data_dir)
        
        console.print(f"[green]Successfully created backup: '{backup_path_base}.zip'[/green]")
        
        # Auto-cleanup old backups (keep last 10)
        backups = sorted(os.listdir(backup_dir), key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
        if len(backups) > 10:
            files_to_delete = backups[:-10]
            console.print(f"Cleaning up {len(files_to_delete)} old backup(s)...")
            for f in files_to_delete:
                os.remove(os.path.join(backup_dir, f))
                
    except Exception as e:
        console.print(f"[red]An error occurred during backup: {e}[/red]")


def restore_data():
    """Restores data from a selected backup."""
    console.print("\n[bold cyan]----- Restore Data from Backup ----- [/bold cyan]")
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir) or not os.listdir(backup_dir):
        console.print("[yellow]No backups found.[/yellow]")
        return
        
    try:
        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith('.zip')],
            key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
            reverse=True
        )
        
        if not backups:
            console.print("[yellow]No backup files (.zip) found in the backups directory.[/yellow]")
            return
            
        backup_to_restore = questionary.select(
            "Select a backup to restore:",
            choices=backups
        ).ask()
        
        if not backup_to_restore:
            return

        confirm = questionary.confirm(
            "This will overwrite all current data. Are you sure you want to restore?",
            default=False
        ).ask()
        
        if confirm:
            backup_path = os.path.join(backup_dir, backup_to_restore)
            data_dir = "database"
            
            # Remove current data and restore from backup
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                
            shutil.unpack_archive(backup_path, data_dir, 'zip')
            
            console.print(f"[green]Successfully restored data from '{backup_to_restore}'[/green]")
        else:
            console.print("Restore operation cancelled.")
            
    except Exception as e:
        console.print(f"[red]An error occurred during restore: {e}[/red]")

def validate_data():
    """Checks the integrity of the data files."""
    console.print("\n[bold cyan]----- Data Validation Check ----- [/bold cyan]")
    issues_found = 0
    
    # Validate transactions.txt
    console.print("\n[bold]Checking 'database/transactions.txt'...[/bold]")
    try:
        with open("database/transactions.txt", "r") as f:
            for i, line in enumerate(f, 1):
                parts = line.strip().split(',')
                if len(parts) != 5:
                    console.print(f"  - [red]Issue on line {i}: Incorrect number of columns ({len(parts)}). Expected 5.[/red]")
                    issues_found += 1
                    continue
                
                date_str, _, _, _, amount_str = parts
                
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    console.print(f"  - [red]Issue on line {i}: Invalid date format '{date_str}'. Expected YYYY-MM-DD.[/red]")
                    issues_found += 1

                if not amount_str.isdigit() and not (amount_str.startswith('-') and amount_str[1:].isdigit()):
                    console.print(f"  - [red]Issue on line {i}: Amount '{amount_str}' is not a valid integer.[/red]")
                    issues_found += 1
    except FileNotFoundError:
        console.print("  - [yellow]'database/transactions.txt' not found.[/yellow]")
    except Exception as e:
        console.print(f"  - [red]An unexpected error occurred: {e}[/red]")
        issues_found += 1

    # Validate budgets.txt
    console.print("\n[bold]Checking 'database/budgets.txt'...[/bold]")
    try:
        with open("database/budgets.txt", "r") as f:
            for i, line in enumerate(f, 1):
                parts = line.strip().split(',')
                if len(parts) != 2:
                    console.print(f"  - [red]Issue on line {i}: Incorrect number of columns ({len(parts)}). Expected 2.[/red]")
                    issues_found += 1
                    continue
                
                _, amount_str = parts
                if not amount_str.isdigit():
                    console.print(f"  - [red]Issue on line {i}: Amount '{amount_str}' is not a valid integer.[/red]")
                    issues_found += 1
    except FileNotFoundError:
        console.print("  - [yellow]'database/budgets.txt' not found.[/yellow]")
    except Exception as e:
        console.print(f"  - [red]An unexpected error occurred: {e}[/red]")
        issues_found += 1
        
    console.print("\n[bold]Validation Summary:[/bold]")
    if issues_found == 0:
        console.print("[green]All data files seem to be in good shape![/green]")
    else:
        console.print(f"[yellow]Found {issues_found} potential issue(s). Please review the details above.[/yellow]")
