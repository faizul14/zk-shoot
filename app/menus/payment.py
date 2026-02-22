from datetime import datetime, timedelta

from app.client.engsel2 import get_pending_transaction, get_transaction_history
from app.menus.util import clear_screen
from app.menus.ui import console, print_error, print_warning, print_rule, make_table

def show_transaction_history(api_key, tokens):
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        console.print("\n[bold cyan]💳 Riwayat Transaksi[/bold cyan]")
        print_rule()

        data = None
        history = []
        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            print_error(f"Gagal mengambil riwayat transaksi: {e}")
            history = []
        
        if len(history) == 0:
            print_warning("Tidak ada riwayat transaksi.")
        else:
            table = make_table(
                ("No",      "bold cyan",   "right"),
                ("Nama",    "white",       "left"),
                ("Harga",   "bold green",  "right"),
                ("Tanggal", "dim white",   "left"),
                ("Metode",  "yellow",      "left"),
                ("Status",  "bold white",  "center"),
                ("Bayar",   "bold white",  "center"),
            )
            for idx, transaction in enumerate(history, start=1):
                transaction_timestamp = transaction.get("timestamp", 0)
                dt = datetime.fromtimestamp(transaction_timestamp)
                dt_jakarta = dt - timedelta(hours=7)
                formatted_time = dt_jakarta.strftime("%d %b %Y %H:%M")

                status = transaction.get('status', '-')
                pay_status = transaction.get('payment_status', '-')
                status_style = "bold green" if status == "SUCCESS" else "bold red" if "FAIL" in status else "yellow"
                pay_style    = "bold green" if pay_status == "PAID" else "bold red" if "FAIL" in pay_status else "yellow"

                table.add_row(
                    str(idx),
                    transaction['title'],
                    transaction['price'],
                    formatted_time,
                    transaction['payment_method_label'],
                    f"[{status_style}]{status}[/]",
                    f"[{pay_style}]{pay_status}[/]",
                )
            from rich.panel import Panel
            console.print(Panel(table, title="[bold cyan]💳 Riwayat Transaksi[/bold cyan]", border_style="cyan", expand=False))

        print_rule()
        console.print("[bold cyan]0.[/bold cyan] Refresh  |  [bold cyan]00.[/bold cyan] Kembali ke Menu Utama")
        choice = console.input("\n[bold cyan]Pilih opsi: [/bold cyan]")
        if choice == "0":
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            print_error("Opsi tidak valid. Silakan coba lagi.")