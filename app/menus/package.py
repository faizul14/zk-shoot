import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_auth_code, get_family, get_package, get_addons, get_package_details, send_api_request
from app.client.engsel2 import unsubscribe
from app.service.bookmark import BookmarkInstance
from app.client.purchase import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.client.qris import show_qris_payment
from app.client.ewallet import show_multipayment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte
from app.service.decoy import DecoyInstance

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")
    
    clear_screen()
    console.print("\n[bold cyan]📦 Detail Paket[/bold cyan]")
    print_rule()
    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print_error("Failed to load package details.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","") #Vidio
    family_name = package.get("package_family", {}).get("name","") #Unlimited Turbo
    variant_name = package.get("package_detail_variant", "").get("name","") #For Xtra Combo
    option_name = package.get("package_option", {}).get("name","") #Vidio
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    
    family_code = package.get("package_family", {}).get("package_family_code","")
    parent_code = package.get("package_addon", {}).get("parent_code","")
    if parent_code == "":
        parent_code = "N/A"
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    print_rule()
    console.print(f"[bold white]Nama        :[/bold white] [bold cyan]{title}[/bold cyan]")
    console.print(f"[bold white]Harga       :[/bold white] [bold green]Rp {price}[/bold green]")
    console.print(f"[bold white]Payment For :[/bold white] {payment_for}")
    console.print(f"[bold white]Masa Aktif  :[/bold white] {validity}")
    console.print(f"[bold white]Point       :[/bold white] {package['package_option']['point']}")
    console.print(f"[bold white]Plan Type   :[/bold white] {package['package_family']['plan_type']}")
    print_rule()
    console.print(f"[dim]Family Code : {family_code}[/dim]")
    console.print(f"[dim]Parent Code : {parent_code}[/dim]")
    print_rule()
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        ben_table = make_table(
            ("Nama",      "white",       "left"),
            ("Item ID",   "dim white",   "left"),
            ("Tipe",      "yellow",      "center"),
            ("Total",     "bold green",  "right"),
        )
        for benefit in benefits:
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                total_str = f"{benefit['total']/60:.1f} menit"
            elif data_type == "TEXT" and benefit['total'] > 0:
                total_str = f"{benefit['total']} SMS"
            elif data_type == "DATA" and benefit['total'] > 0:
                quota = int(benefit['total'])
                if quota >= 1_000_000_000:
                    total_str = f"{quota / (1024**3):.2f} GB"
                elif quota >= 1_000_000:
                    total_str = f"{quota / (1024**2):.2f} MB"
                elif quota >= 1_000:
                    total_str = f"{quota / 1024:.2f} KB"
                else:
                    total_str = str(quota)
            else:
                total_str = f"{benefit['total']} ({data_type})"
            if benefit["is_unlimited"]:
                total_str = "Unlimited ♾"
            ben_table.add_row(
                benefit['name'],
                benefit['item_id'],
                data_type,
                total_str,
            )
        console.print("[bold white]Benefits:[/bold white]")
        console.print(ben_table)
    print_rule()
    addons = get_addons(api_key, tokens, package_option_code)
    

    bonuses = addons.get("bonuses", [])
    
    # Pick 1st bonus if available, need more testing
    # if len(bonuses) > 0:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonuses[0]["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonuses[0]["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )
    
    # Pick all bonuses, need more testing
    # for bonus in bonuses:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonus["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonus["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )

    console.print(f"[dim]Addons:[/dim]\n{json.dumps(addons, indent=2)}")
    print_rule()
    console.print(f"[dim]SnK MyXL:[/dim]\n{detail}")
    print_rule()
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        console.print("\n[bold cyan]⚙ Options:[/bold cyan]")
        console.print("[bold cyan]1.[/bold cyan] Beli dengan Pulsa")
        console.print("[bold cyan]2.[/bold cyan] Beli dengan E-Wallet")
        console.print("[bold cyan]3.[/bold cyan] Bayar dengan QRIS")
        console.print("[bold cyan]4.[/bold cyan] Pulsa + Decoy")
        console.print("[bold cyan]5.[/bold cyan] Pulsa + Decoy V2")
        console.print("[bold cyan]6.[/bold cyan] QRIS + Decoy (+1K)")
        console.print("[bold cyan]7.[/bold cyan] QRIS + Decoy V2")
        console.print("[bold cyan]8.[/bold cyan] Pulsa N kali")

        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        
        if payment_for == "REDEEM_VOUCHER":
            console.print("[bold cyan]B.[/bold cyan] Ambil sebagai bonus (jika tersedia)")
            console.print("[bold cyan]BA.[/bold cyan] Kirim bonus (jika tersedia)")
            console.print("[bold cyan]L.[/bold cyan] Beli dengan Poin (jika tersedia)")
        
        if option_order != -1:
            console.print("[bold cyan]0.[/bold cyan] Tambah ke Bookmark")
        console.print("[bold cyan]00.[/bold cyan] Kembali ke daftar paket")

        choice = console.input("\n[bold cyan]Pilihan: [/bold cyan]") 
        if choice == "00":
            return False
        elif choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print_success("Paket berhasil ditambahkan ke bookmark.")
            else:
                print_warning("Paket sudah ada di bookmark.")
            pause()
            continue
        
        elif choice == '1':
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True
            )
            input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '2':
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '3':
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '4':
            # Balance with Decoy            
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print_info(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print_success("Purchase successful!")
            else:
                print_success("Purchase successful!")
            pause()
            return True
        elif choice == '5':
            # Balance with Decoy v2 (use token confirmation from decoy)
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print_error("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print_success("Purchase successful!")
            else:
                print_success("Purchase successful!")
            pause()
            return True
        elif choice == '6':
            # QRIS decoy + Rpx
            decoy = DecoyInstance.get_decoy("qris")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print_rule()
            print_info(f"Harga Paket Utama: Rp {price}")
            print_info(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print_warning("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print_rule()

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '7':
            # QRIS decoy + Rp0
            decoy = DecoyInstance.get_decoy("qris0")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print_rule()
            print_info(f"Harga Paket Utama: Rp {price}")
            print_info(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print_warning("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print_rule()

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '8':
            #Pulsa N kali
            use_decoy_for_n_times = input("Use decoy package? (y/n): ").strip().lower() == 'y'
            n_times_str = input("Enter number of times to purchase (e.g., 3): ").strip()

            delay_seconds_str = input("Enter delay between purchases in seconds (e.g., 25): ").strip()
            if not delay_seconds_str.isdigit():
                delay_seconds_str = "0"

            try:
                n_times = int(n_times_str)
                if n_times < 1:
                    raise ValueError("Number must be at least 1.")
            except ValueError:
                print("Invalid number entered. Please enter a valid integer.")
                pause()
                continue
            purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_seconds_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )
        elif choice == '9':
            pin = input("Enter PIN: ")
            if len(pin) != 6:
                print_error("PIN too short.")
                pause()
                continue
            auth_code = get_auth_code(
                tokens,
                pin,
                active_user["number"]
            )
            
            if not auth_code:
                print_error("Failed to get auth_code")
                continue
            
            target_msisdn = input("Target number start with 62:")
            
            url = "https://me.mashu.lol/pg-decoy-edu.json"
            
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print_error("Gagal mengambil data decoy package.")
                pause()
                return None
            
            decoy_data = response.json()
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )

            # payment_items.append(
            #     PaymentItem(
            #         item_code=decoy_package_detail["package_option"]["package_option_code"],
            #         product_type="",
            #         item_price=decoy_package_detail["package_option"]["price"],
            #         item_name=decoy_package_detail["package_option"]["name"],
            #         tax=0,
            #         token_confirmation=decoy_package_detail["token_confirmation"],
            #     )
            # )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                topup_number=target_msisdn,
                stage_token=auth_code,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print_info(f"Adjusted total amount to: {valid_amount}")
                    res = show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        "SHARE_PACKAGE",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=0,
                        topup_number=target_msisdn,
                        stage_token=auth_code,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            
            payment_items.pop()
            pause()            
        elif choice.lower() == 'b':
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice.lower() == 'ba':
            destination_msisdn = input("Masukkan nomor tujuan bonus (mulai dengan 62): ").strip()
            bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            pause()
            return True
        elif choice.lower() == 'l':
            settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        else:
            print_warning("Purchase cancelled.")
            return False
    pause()
    sys.exit(0)

def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print_error("No active user tokens found.")
        pause()
        return None
    
    packages = []
    
    data = get_family(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )
    
    if not data:
        print_error("Failed to load family data.")
        pause()
        return None
    price_currency = "Rp"
    rc_bonus_type = data["package_family"].get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        console.print("\n[bold cyan]📋 Family Packages[/bold cyan]")
        print_rule()
        console.print(f"[bold white]Family :[/bold white] [bold cyan]{data['package_family']['name']}[/bold cyan]  [dim]({family_code})[/dim]")
        console.print(f"[bold white]Type   :[/bold white] {data['package_family']['package_family_type']}")
        console.print(f"[bold white]Variant:[/bold white] {len(data['package_variants'])}")
        print_rule()
        
        package_variants = data["package_variants"]
        
        option_number = 1
        variant_number = 1
        
        for variant in package_variants:
            variant_name = variant["name"]
            variant_code = variant["package_variant_code"]
            variant_table = make_table(
                ("No",    "bold cyan",  "right"),
                ("Nama",  "white",      "left"),
                ("Harga", "bold green", "right"),
                ("Kode",  "dim white",  "left"),
                title=f"Variant {variant_number}: {variant_name} ({variant_code})",
            )
            for option in variant["package_options"]:
                option_name = option["name"]
                
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                variant_table.add_row(
                    str(option_number),
                    option_name,
                    f"{price_currency} {option['price']}",
                    option["package_option_code"],
                )
                option_number += 1
            console.print(variant_table)
            variant_number += 1
        print_rule()
        console.print("[bold cyan]00.[/bold cyan] Kembali ke menu utama")
        print_rule()
        pkg_choice = console.input("[bold cyan]Pilih paket (nomor): [/bold cyan]")
        if pkg_choice == "00":
            in_package_menu = False
            return None
        
        if isinstance(pkg_choice, str) == False or not pkg_choice.isdigit():
            print_error("Input tidak valid. Silakan masukan nomor paket.")
            continue
        
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        
        if not selected_pkg:
            print_error("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
            continue
        
        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )
        
    return packages

def fetch_my_packages():
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            print("No active user tokens found.")
            pause()
            return None
        
        id_token = tokens.get("id_token")
        
        path = "api/v8/packages/quota-details"
        
        payload = {
            "is_enterprise": False,
            "lang": "en",
            "family_member_id": ""
        }
        
        print_info("Fetching my packages...")
        res = send_api_request(api_key, path, payload, id_token, "POST")
        if res.get("status") != "SUCCESS":
            print_error("Failed to fetch packages")
            console.print(f"Response: {res}")
            pause()
            return None
        
        quotas = res["data"]["quotas"]
        
        clear_screen()
        console.print("\n[bold cyan]📦 Paket Saya[/bold cyan]")
        print_rule()
        my_packages =[]
        num = 1
        for quota in quotas:
            quota_code = quota["quota_code"] # Can be used as option_code
            group_code = quota["group_code"]
            group_name = quota["group_name"]
            quota_name = quota["name"]
            family_code = "N/A"
            
            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")
            
            benefit_infos = []
            benefits = quota.get("benefits", [])
            if len(benefits) > 0:
                for benefit in benefits:
                    benefit_id = benefit.get("id", "")
                    name = benefit.get("name", "")
                    data_type = benefit.get("data_type", "N/A")
                    benefit_info = "  -----------------------------------------------------\n"
                    benefit_info += f"  ID    : {benefit_id}\n"
                    benefit_info += f"  Name  : {name}\n"
                    benefit_info += f"  Type  : {data_type}\n"
                    

                    remaining = benefit.get("remaining", 0)
                    total = benefit.get("total", 0)

                    if data_type == "DATA":
                        remaining_str = format_quota_byte(remaining)
                        total_str = format_quota_byte(total)
                        
                        benefit_info += f"  Kuota : {remaining_str} / {total_str}"
                    elif data_type == "VOICE":
                        benefit_info += f"  Kuota : {remaining/60:.2f} / {total/60:.2f} menit"
                    elif data_type == "TEXT":
                        benefit_info += f"  Kuota : {remaining} / {total} SMS"
                    else:
                        benefit_info += f"  Kuota : {remaining} / {total}"

                    benefit_infos.append(benefit_info)
                
            
            print(f"fetching package no. {num} details...")
            package_details = get_package(api_key, tokens, quota_code)
            if package_details:
                family_code = package_details["package_family"]["package_family_code"]
            
            print("=======================================================")
            print(f"Package {num}")
            print(f"Name: {quota_name}")
            print("Benefits:")
            if len(benefit_infos) > 0:
                for bi in benefit_infos:
                    print(bi)
                print("  -----------------------------------------------------")
            print(f"Group Name: {group_name}")
            print(f"Quota Code: {quota_code}")
            print(f"Family Code: {family_code}")
            print(f"Group Code: {group_code}")
            print("=======================================================")
            
            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })
            
            num += 1
        
        print_rule()
        console.print("[dim]Input nomor paket untuk lihat detail. "
                      "| [bold]del <nomor>[/bold] untuk unsubscribe. "
                      "| [bold cyan]00[/bold cyan] untuk kembali.[/dim]")
        choice = console.input("[bold cyan]Pilihan: [/bold cyan]")
        if choice == "00":
            in_my_packages_menu = False

        # Handle seletcting package to view detail
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                print_error("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
                pause()
                continue
            
            _ = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
        
        elif choice.startswith("del "):
            del_parts = choice.split(" ")
            if len(del_parts) != 2 or not del_parts[1].isdigit():
                print("Invalid input for delete command.")
                pause()
            
            del_number = int(del_parts[1])
            del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_number), None)
            if not del_pkg:
                print_error("Package not found for deletion.")
                pause()
            
            confirm = input(f"Are you sure you want to unsubscribe from package  {del_number}. {del_pkg['name']}? (y/n): ")
            if confirm.lower() == 'y':
                print_info(f"Unsubscribing from package {del_pkg['name']}...")
                success = unsubscribe(
                    api_key,
                    tokens,
                    del_pkg["quota_code"],
                    del_pkg["product_subscription_type"],
                    del_pkg["product_domain"]
                )
                if success:
                    print_success("Successfully unsubscribed from the package.")
                else:
                    print_error("Failed to unsubscribe from the package.")
            else:
                print_warning("Unsubscribe cancelled.")
            pause()
