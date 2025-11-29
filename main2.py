import os
import requests # Diperlukan untuk memanggil API token
import sys, json
from datetime import datetime

# --- Awal dari kode asli Anda ---
from app.service.git import check_for_updates

from app.menus.util import clear_screen, pause
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
    print("=" * WIDTH)
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    print(f"Nomor: {profile['number']} | Type: {profile['subscription_type']}".center(WIDTH))
    print(f"Pulsa: Rp {profile['balance']} | Aktif sampai: {expired_at_dt}".center(WIDTH))
    print(f"{profile['point_info']}".center(WIDTH))
    print("=" * WIDTH)
    print("Menu:")
    print("1. Login/Ganti akun")
    print("2. Lihat Paket Saya")
    print("3. Beli Paket 🔥 HOT 🔥")
    print("4. Beli Paket 🔥 HOT-2 🔥")
    print("5. Beli Paket Berdasarkan Option Code")
    print("6. Beli Paket Berdasarkan Family Code")
    # print("7. Beli Semua Paket di Family Code (loop)")
    # print("8. Riwayat Transaksi")
    # print("9. Family Plan/Akrab Organizer")
    # print("10. [WIP] Circle")
    # print("11. Store Segments")
    # print("12. Store Family List")
    # print("13. Store Packages")
    # print("14. Redemables")
    print("R. Register")
    print("N. Notifikasi")
    print("V. Validate msisdn")
    print("00. Bookmark Paket")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")

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

            choice = input("Pilih menu: ")
            # If T
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("No user selected or failed to load user.")
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
                print("Exiting the application.")
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
                print("Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")
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
        print(f"File {TOKEN_FILE_NAME} tidak ditemukan. Harap tambahkan token.")
        return False
    except Exception as e:
        print(f"Gagal membaca file {TOKEN_FILE_NAME}: {e}")
        return False
    
    if not token:
        print(f"Token dalam {TOKEN_FILE_NAME} kosong. Harap tambahkan token.")
        return False

    print("Memverifikasi token...")
    try:
        response = requests.post(TOKEN_API_URL, json={"token": token})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("isactive"):
                print("Verifikasi token berhasil. Token aktif.")
                return True
            else:
                # Ini adalah kasus 200 OK tapi isactive: false, yang seharusnya tidak terjadi
                # berdasarkan API doc (seharusnya 401), tapi kita tangani untuk keamanan.
                print("Token valid tetapi tidak aktif.")
                return False

        elif response.status_code == 401:
            print("Token ditemukan tapi tidak aktif (deactivated).")
            return False
        elif response.status_code == 404:
            print("Token tidak ditemukan atau telah dicabut (revoked).")
            return False
        elif response.status_code == 400:
            print("Permintaan buruk (Bad Request). Token mungkin kosong atau format salah.")
            return False
        else:
            print(f"Error tidak diketahui saat verifikasi token. Status: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("Koneksi ke server token gagal. Pastikan server token berjalan.")
        return False
    except Exception as e:
        print(f"Terjadi error saat memverifikasi token: {e}")
        return False

def add_new_token():
    """
    Meminta pengguna untuk token baru dan menyimpannya ke file token.key.
    """
    new_token = input("Masukkan token API baru Anda: ").strip()
    if not new_token:
        print("Token tidak boleh kosong.")
        return

    try:
        with open(TOKEN_FILE_NAME, 'w') as f:
            f.write(new_token)
        
        print(f"Token baru telah disimpan di {TOKEN_FILE_NAME}")
        
    except Exception as e:
        print(f"Gagal menyimpan token ke file {TOKEN_FILE_NAME}: {e}")

def show_token_menu():
    """
    Menampilkan menu untuk manajemen token jika verifikasi gagal.
    """
    while True:
        clear_screen()
        print("=" * WIDTH)
        print("Manajemen Token API".center(WIDTH))
        print("=" * WIDTH)
        print("Token API Anda tidak valid atau tidak aktif atau sudah mencapai limit transaksi")
        print("\nMenu:")
        print("1. Tambah / Ganti Token")
        print("2. Coba Lanjutkan (setelah menambah token)")
        print("3. Keluar")
        print("-" * WIDTH)
        
        choice = input("Pilih menu: ")
        
        if choice == "1":
            add_new_token()
            pause()
        elif choice == "2":
            if verify_api_token():
                print("Token berhasil diverifikasi. Melanjutkan ke aplikasi...")
                pause()
                run_xl_app() # Panggil aplikasi utama
                break # Keluar dari loop token menu
            else:
                print("Token masih tidak valid.")
                pause()
        elif choice == "3":
            print("Keluar dari aplikasi.")
            sys.exit(0)
        else:
            print("Pilihan tidak valid.")
            pause()

def main():
    """
    Fungsi main() baru yang menjadi entry point.
    Mengecek update, lalu memverifikasi token sebelum menjalankan aplikasi utama.
    """
    try:
        print("Checking for updates...")
        need_update = check_for_updates()
        if need_update:
            pause()
        
        # Verifikasi token di sini
        if verify_api_token():
            run_xl_app() # Token valid, jalankan aplikasi XL
        else:
            show_token_menu() # Token tidak valid, tampilkan menu token

    except KeyboardInterrupt:
        print("\nExiting the application.")
    except Exception as e:
       print(f"An unexpected error occurred: {e}")
       # Anda bisa menambahkan logging error yang lebih detail di sini

# --- Akhir dari Logika Token Baru ---


if __name__ == "__main__":
    # Sekarang kita memanggil fungsi main() yang baru,
    # yang berisi logika pengecekan update DAN pengecekan token.
    main()