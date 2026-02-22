from app.client.engsel import get_otp, submit_otp
from app.menus.util import clear_screen, pause
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.service.auth import AuthInstance

def show_login_menu():
    clear_screen()
    console.print("\n[bold cyan]🔑 Login ke MyXL[/bold cyan]")
    print_rule()
    console.print("[bold cyan]1.[/bold cyan] Request OTP")
    console.print("[bold cyan]2.[/bold cyan] Submit OTP")
    console.print("[bold red]99.[/bold red] Tutup aplikasi")
    print_rule()

def login_prompt(api_key: str):
    clear_screen()
    console.print("\n[bold cyan]🔑 Login ke MyXL[/bold cyan]")
    print_rule()
    console.print("Masukan nomor XL [dim](Contoh: 6281234567890)[/dim]")
    phone_number = console.input("[bold cyan]Nomor: [/bold cyan]")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print_error("Nomor tidak valid. Pastikan diawali dengan '628' dan panjang benar.")
        return None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None
        print_success("OTP berhasil dikirim ke nomor Anda.")
        
        try_count = 5
        while try_count > 0:
            console.print(f"[dim]Sisa percobaan: [bold]{try_count}[/bold][/dim]")
            otp = console.input("[bold cyan]Masukkan OTP (6 digit): [/bold cyan]")
            if not otp.isdigit() or len(otp) != 6:
                print_error("OTP tidak valid. Pastikan 6 digit angka.")
                continue
            
            tokens = submit_otp(api_key, phone_number, otp)
            if not tokens:
                print_error("OTP salah. Silahkan coba lagi.")
                try_count -= 1
                continue
            
            print_success("Berhasil login!")
            return phone_number, tokens["refresh_token"]

        print_error("Gagal login setelah beberapa percobaan. Silahkan coba lagi nanti.")
        return None, None
    except Exception as e:
        return None, None

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
        
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        print_rule()
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print_error("Gagal menambah akun. Silahkan coba lagi.")
                pause()
                continue
            
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            
            if add_user:
                add_user = False
            continue
        
        console.print("\n[bold cyan]👥 Akun Tersimpan[/bold cyan]")
        print_rule()

        if not users or len(users) == 0:
            print_warning("Tidak ada akun tersimpan.")
        else:
            table = make_table(
                ("No",     "bold cyan",  "right"),
                ("Nomor",  "white",      "left"),
                ("Tipe",   "yellow",     "center"),
                ("Status", "green",      "center"),
            )
            for idx, user in enumerate(users):
                is_active = active_user and user["number"] == active_user["number"]
                status = "[bold green]✅ AKTIF[/bold green]" if is_active else "[dim]–[/dim]"
                sub_type = user.get("subscription_type", "-")
                table.add_row(str(idx + 1), str(user.get("number", "")), sub_type, status)
            console.print(table)

        print_rule()
        console.print("[bold cyan]0[/bold cyan]: Tambah Akun  "
                      "[dim]| Nomor urut: ganti akun | [/dim]"
                      "[dim]del <no>: hapus | [/dim]"
                      "[bold cyan]00[/bold cyan]: Kembali")
        print_rule()
        input_str = console.input("[bold cyan]Pilihan: [/bold cyan]")

        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        elif input_str.startswith("del "):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])
                
                # Prevent deleting the active user here
                if active_user and users[del_index - 1]["number"] == active_user["number"]:
                    print_error("Tidak dapat menghapus akun aktif. Ganti akun terlebih dahulu.")
                    pause()
                    continue
                
                if 1 <= del_index <= len(users):
                    user_to_delete = users[del_index - 1]
                    confirm = console.input(f"Yakin ingin menghapus akun [bold]{user_to_delete['number']}[/bold]? (y/n): ")
                    if confirm.lower() == 'y':
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_success("Akun berhasil dihapus.")
                        pause()
                    else:
                        print_warning("Penghapusan akun dibatalkan.")
                        pause()
                else:
                    print_error("Nomor urut tidak valid.")
                    pause()
            else:
                print_error("Perintah tidak valid. Gunakan format: del <nomor urut>")
                pause()
            continue
        else:
            print_error("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue