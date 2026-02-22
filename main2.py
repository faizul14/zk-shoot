import os
import requests
import sys, json
from datetime import datetime

from app.service.git import check_for_updates

from app.menus.util import clear_screen, pause
from app.menus.ui import console, print_info, print_error, print_success, print_warning, make_table, print_rule
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.table import Table
from rich import box
from app.client.engsel import (
    get_balance,
    get_package,
)
from app.client.engsel2 import get_tiering_info, validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil

WIDTH = 55

def show_main_menu(profile):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")

    # ── Profile Panel ─────────────────────────────────────────────
    grid = Table.grid(padding=(0, 1), expand=True)
    grid.add_column(justify="center", width=3) # Icon
    grid.add_column(justify="left")            # Value 1
    grid.add_column(justify="center", width=2) # │
    grid.add_column(justify="left")            # Value 2

    grid.add_row(
        "📱", 
        f"[bold cyan]{profile['number']}[/]", 
        "[dim]│[/]", 
        f"[bold yellow]{profile['subscription_type']}[/]"
    )
    grid.add_row(
        "💰", 
        f"[dim]Pulsa:[/] [bold green]Rp {profile['balance']}[/]", 
        "[dim]│[/]", 
        f"[dim]Aktif:[/] [bold]{expired_at_dt}[/]"
    )
    
    p_info = profile['point_info'].split('|')
    p_left = p_info[0].strip() if len(p_info) > 0 else profile['point_info']
    p_right = p_info[1].strip() if len(p_info) > 1 else ""
    
    grid.add_row(
        "⭐", 
        f"[bold magenta]{p_left}[/]", 
        "[dim]│[/]" if p_right else "", 
        f"[bold magenta]{p_right}[/]"
    )

    console.print(Panel(grid, title="[bold cyan]Dor MyXL[/bold cyan]", border_style="cyan", expand=False, width=62))

    # ── Menu Table ────────────────────────────────────────────────
    all_items = [
        ("1",  "Login / Ganti Akun"),
        ("2",  "Lihat Paket Saya"),
        ("3",  "🔥 Beli Paket HOT"),
        ("4",  "🔥 Beli Paket HOT-2"),
        ("5",  "Beli via Option Code"),
        ("6",  "Beli via Family Code"),
        ("00", "Bookmark Paket"),
        ("R",  "Register"),
        ("N",  "Notifikasi"),
        ("V",  "Validate MSISDN"),
        ("99", "🚪 Tutup Aplikasi"),
    ]

    menu_table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
        expand=True,
    )
    menu_table.add_column("k", style="bold cyan", justify="right", no_wrap=True, width=4)
    menu_table.add_column("v", justify="left")  # NO style → inherits terminal fg

    for k, v in all_items:
        menu_table.add_row(f"{k}.", v)

    console.print(Panel(
        menu_table,
        title="[bold cyan]Menu[/bold cyan]",
        border_style="cyan",
        expand=False,
        width=45,
    ))

show_menu = True

# Saya mengganti nama fungsi main() Anda menjadi run_xl_app()
def run_xl_app():
    
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            balance_remaining = balance.get("remaining")
            balance_expired_at = balance.get("expired_at")
            
            point_info = "Points: N/A | Tier: N/A"
            
            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = console.input("\n[bold cyan]Pilih menu: [/bold cyan]")
            # If T
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print_error("Tidak ada akun yang dipilih atau gagal memuat akun.")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                if verify_api_token():
                    show_hot_menu2()
                else:
                    show_token_menu()
            elif choice == "5":
                option_code = input("Enter option code (or '99' to cancel): ")
                if option_code == "99":
                    continue
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice == "6":
                family_code = input("Enter family code (or '99' to cancel): ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            # elif choice == "7":
            #     family_code = input("Enter family code (or '99' to cancel): ")
            #     if family_code == "99":
            #         continue

            #     start_from_option = input("Start purchasing from option number (default 1): ")
            #     try:
            #         start_from_option = int(start_from_option)
            #     except ValueError:
            #         start_from_option = 1

            #     use_decoy = input("Use decoy package? (y/n): ").lower() == 'y'
            #     pause_on_success = input("Pause on each successful purchase? (y/n): ").lower() == 'y'
            #     delay_seconds = input("Delay seconds between purchases (0 for no delay): ")
            #     try:
            #         delay_seconds = int(delay_seconds)
            #     except ValueError:
            #         delay_seconds = 0
            #     purchase_by_family(
            #         family_code,
            #         use_decoy,
            #         pause_on_success,
            #         delay_seconds,
            #         start_from_option
            #     )
            # elif choice == "8":
            #     show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            # elif choice == "9":
            #     show_family_info(AuthInstance.api_key, active_user["tokens"])
            # elif choice == "10":
            #     show_circle_info(AuthInstance.api_key, active_user["tokens"])
            # elif choice == "11":
            #     input_11 = input("Is enterprise store? (y/n): ").lower()
            #     is_enterprise = input_11 == 'y'
            #     show_store_segments_menu(is_enterprise)
            # elif choice == "12":
            #     input_12_1 = input("Is enterprise? (y/n): ").lower()
            #     is_enterprise = input_12_1 == 'y'
            #     show_family_list_menu(profile['subscription_type'], is_enterprise)
            # elif choice == "13":
            #     input_13_1 = input("Is enterprise? (y/n): ").lower()
            #     is_enterprise = input_13_1 == 'y'
                
            #     show_store_packages_menu(profile['subscription_type'], is_enterprise)
            # elif choice == "14":
            #     input_14_1 = input("Is enterprise? (y/n): ").lower()
            #     is_enterprise = input_14_1 == 'y'
                
            #     show_redeemables_menu(is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                print_info("Sampai jumpa! 👋")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("Enter msisdn (628xxxx): ")
                nik = input("Enter NIK: ")
                kk = input("Enter KK: ")
                
                res = dukcapil(
                    AuthInstance.api_key,
                    msisdn,
                    kk,
                    nik,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "v":
                msisdn = input("Enter the msisdn to validate (628xxxx): ")
                res = validate_msisdn(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    msisdn,
                )
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                print_error("Pilihan tidak valid. Coba lagi.")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print_error("Tidak ada akun yang dipilih atau gagal memuat akun.")
# --- Akhir dari kode asli Anda ---


# --- Awal dari Logika Token Baru ---

# URL API Token, bisa diambil dari environment variable sistem atau default
TOKEN_API_URL = os.getenv("TOKEN_API_URL", "https://be-personalstorage-production.up.railway.app/api/public/xltoken/checktoken")
TOKEN_FILE_NAME = "token.key" # Nama file untuk menyimpan token

def verify_api_token():
    """
    Memverifikasi token API yang tersimpan di token.key ke endpoint /checktoken.
    Mengembalikan True jika valid dan aktif, False jika tidak.
    """
    token = None
    try:
        with open(TOKEN_FILE_NAME, 'r') as f:
            token = f.read().strip()
    except FileNotFoundError:
        print_error(f"File {TOKEN_FILE_NAME} tidak ditemukan. Harap tambahkan token.")
        return False
    except Exception as e:
        print_error(f"Gagal membaca file {TOKEN_FILE_NAME}: {e}")
        return False
    
    if not token:
        print_error(f"Token dalam {TOKEN_FILE_NAME} kosong. Harap tambahkan token.")
        return False

    print_info("Memverifikasi token...")
    try:
        response = requests.post(TOKEN_API_URL, json={"token": token})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("isactive"):
                print_success("Verifikasi token berhasil. Token aktif.")
                return True
            else:
                print_warning("Token valid tetapi tidak aktif.")
                return False

        elif response.status_code == 401:
            print_error("Token ditemukan tapi tidak aktif (deactivated).")
            return False
        elif response.status_code == 404:
            print_error("Token tidak ditemukan atau telah dicabut (revoked).")
            return False
        elif response.status_code == 400:
            print_error("Permintaan buruk (Bad Request). Token mungkin kosong atau format salah.")
            return False
        else:
            print_error(f"Error tidak diketahui saat verifikasi token. Status: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("Koneksi ke server token gagal. Pastikan server token berjalan.")
        return False
    except Exception as e:
        print_error(f"Terjadi error saat memverifikasi token: {e}")
        return False

def add_new_token():
    """
    Meminta pengguna untuk token baru dan menyimpannya ke file token.key.
    """
    new_token = input("Masukkan token API baru Anda: ").strip()
    if not new_token:
        print_error("Token tidak boleh kosong.")
        return

    try:
        with open(TOKEN_FILE_NAME, 'w') as f:
            f.write(new_token)
        print_success(f"Token baru telah disimpan di {TOKEN_FILE_NAME}")
    except Exception as e:
        print_error(f"Gagal menyimpan token ke file {TOKEN_FILE_NAME}: {e}")

def show_token_menu():
    """
    Menampilkan menu untuk manajemen token jika verifikasi gagal.
    """
    while True:
        clear_screen()
        console.print(Panel(
            "[bold red]Token API Anda tidak valid, tidak aktif, atau sudah mencapai limit transaksi.[/bold red]",
            title="[bold red]⚠ Manajemen Token API[/bold red]",
            border_style="red",
            expand=False,
            width=62,
        ))
        console.print("[bold cyan]1.[/bold cyan] Tambah / Ganti Token")
        console.print("[bold cyan]2.[/bold cyan] Coba Lanjutkan (setelah menambah token)")
        console.print("[bold red]3.[/bold red] Keluar")
        print_rule()
        
        choice = console.input("[bold cyan]Pilih menu: [/bold cyan]")
        
        if choice == "1":
            add_new_token()
            pause()
        elif choice == "2":
            if verify_api_token():
                print_success("Token berhasil diverifikasi. Melanjutkan ke aplikasi...")
                pause()
                run_xl_app()
                break
            else:
                print_error("Token masih tidak valid.")
                pause()
        elif choice == "3":
            print_info("Keluar dari aplikasi.")
            sys.exit(0)
        else:
            print_error("Pilihan tidak valid.")
            pause()

def main():
    """
    Fungsi main() baru yang menjadi entry point.
    Mengecek update, lalu memverifikasi token sebelum menjalankan aplikasi utama.
    """
    try:
        print_info("Memeriksa pembaruan...")
        need_update = check_for_updates()
        if need_update:
            pause()
        
        if verify_api_token():
            run_xl_app()
        else:
            show_token_menu()

    except KeyboardInterrupt:
        console.print("\n[bold red]Aplikasi ditutup.[/bold red]")
    except Exception as e:
        print_error(f"Terjadi error yang tidak terduga: {e}")

# --- Akhir dari Logika Token Baru ---


if __name__ == "__main__":
    # Sekarang kita memanggil fungsi main() yang baru,
    # yang berisi logika pengecekan update DAN pengecekan token.
    main()