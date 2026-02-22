import requests
import json


from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.client.ewallet import show_multipayment
from app.client.qris import show_qris_payment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        console.print("\n[bold red]🔥 Paket Hot[/bold red]")
        print_rule()
        
        url = "https://me.mashu.lol/pg-hot.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print_error("Gagal mengambil data hot package.")
            pause()
            return None

        hot_packages = response.json()

        table = make_table(
            ("No",      "bold cyan", "right"),
            ("Family",  "",          "left"),
            ("Variant", "dim",       "left"),
            ("Option",  "yellow",    "left"),
        )
        for idx, p in enumerate(hot_packages):
            table.add_row(
                str(idx + 1),
                p['family_name'],
                p['variant_name'],
                p['option_name'],
            )
        from rich.panel import Panel
        console.print(Panel(table, title="[bold cyan]🔥 Daftar Paket Hot[/bold cyan]", border_style="cyan", expand=False))
        
        console.print("[bold cyan]00.[/bold cyan] Kembali ke menu utama")
        print_rule()
        choice = console.input("[bold cyan]Pilih paket (nomor): [/bold cyan]")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_error("Gagal mengambil data family.")
                pause()
                continue
            
            package_variants = family_data["package_variants"]
            option_code = None
            for variant in package_variants:
                if variant["name"] == selected_bm["variant_name"]:
                    selected_variant = variant
                    
                    package_options = selected_variant["package_options"]
                    for option in package_options:
                        if option["order"] == selected_bm["order"]:
                            selected_option = option
                            option_code = selected_option["package_option_code"]
                            break
            
            if option_code:
                print(f"{option_code}")
                show_package_details(api_key, tokens, option_code, is_enterprise)            
            
        else:
            print_error("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        console.print("\n[bold red]🔥 Paket Hot 2[/bold red]")
        print_rule()
        
        url = "https://me.mashu.lol/pg-hot2.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print_error("Gagal mengambil data hot package.")
            pause()
            return None

        hot_packages = response.json()

        table = make_table(
            ("No",    "bold cyan",  "right"),
            ("Nama",  "",           "left"),
            ("Harga", "bold green", "right"),
        )
        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p['name'], str(p['price']))
        from rich.panel import Panel
        console.print(Panel(table, title="[bold cyan]🔥 Daftar Paket Hot 2[/bold cyan]", border_style="cyan", expand=False))
        
        console.print("[bold cyan]00.[/bold cyan] Kembali ke menu utama")
        print_rule()
        choice = console.input("[bold cyan]Pilih paket (nomor): [/bold cyan]")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print_warning("Paket tidak tersedia.")
                pause()
                continue
            
            payment_items = []
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )
                
                # Force failed when one of the package detail is None
                if not package_detail:
                    print_error(f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            clear_screen()
            console.print("\n[bold cyan]📦 Detail Paket Hot[/bold cyan]")
            print_rule()
            console.print(f"[bold white]Nama  :[/bold white] {selected_package['name']}")
            console.print(f"[bold green]Harga :[/bold green] {selected_package['price']}")
            console.print(f"[dim]Detail:[/dim] {selected_package['detail']}")
            print_rule()
            
            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                console.print("\n[bold cyan]Pilih Metode Pembelian:[/bold cyan]")
                console.print("[bold cyan]1.[/bold cyan] Balance")
                console.print("[bold cyan]2.[/bold cyan] E-Wallet")
                console.print("[bold cyan]3.[/bold cyan] QRIS")
                console.print("[bold cyan]00.[/bold cyan] Kembali ke menu sebelumnya")
                
                input_method = console.input("[bold cyan]Pilih metode (nomor): [/bold cyan]")
                if input_method == "1":
                    if overwrite_amount == -1:
                        print_warning(f"Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']}!!!")
                        balance_answer = console.input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
                        if balance_answer.lower() != "y":
                            print_warning("Pembelian dibatalkan oleh user.")
                            pause()
                            in_payment_menu = False
                            continue

                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    console.input("[dim]Tekan [bold cyan]Enter[/bold cyan] untuk kembali...[/dim]")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "2":
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    console.input("[dim]Tekan [bold cyan]Enter[/bold cyan] untuk kembali...[/dim]")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "3":
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )

                    console.input("[dim]Tekan [bold cyan]Enter[/bold cyan] untuk kembali...[/dim]")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "00":
                    in_payment_menu = False
                    continue
                else:
                    print_error("Metode tidak valid. Silahkan coba lagi.")
                    pause()
                    continue
        else:
            print_error("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
