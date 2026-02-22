import requests, time
from random import randint
from app.client.engsel import get_family, get_package_details, get_package
from app.menus.util import pause
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.service.auth import AuthInstance
from app.service.decoy import DecoyInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance

# Purchase
def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        # Balance with Decoy
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
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print_warning(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")
        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
        if balance_answer.lower() != "y":
            print_warning("Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_error(f"Failed to get family data for code: {family_code}.")
        pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    
    print_rule()
    successful_purchases = []
    packages_count = 0
    for variant in variants:
        packages_count += len(variant["package_options"])
    
    purchase_count = 0
    start_buying = False
    if start_from_option <= 1:
        start_buying = True

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                print(f"Skipping option {option_order}. {option['name']}")
                continue
            
            option_name = option["name"]
            option_price = option["price"]
            
            purchase_count += 1
            print_info(f"Purchase {purchase_count}/{packages_count} → {variant_name} - {option_order}. {option_name} — Rp {option['price']}")
            
            payment_items = []
            
            try:
                if use_decoy:                
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
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                print_error(f"Exception fetching package details: {e} — Skipping.")
                continue
            
            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )
            
            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
            
            res = None
            
            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_package_detail["package_option"]["price"]
                
            error_msg = ""

            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "🤑",
                    False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        
                        print_info(f"Adjusted total amount to: {valid_amount}")
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "SHARE_PACKAGE",
                            False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=-1
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            error_msg = ""
                            successful_purchases.append(
                                f"{variant_name}|{option_order}. {option_name} - {option_price}"
                            )
                            
                            if pause_on_success:
                                print_success("Purchase successful!")
                                pause()
                            else:
                                print_success("Purchase successful!")
                        else:
                            error_msg = res.get("message", "")
                else:
                    successful_purchases.append(
                        f"{variant_name}|{option_order}. {option_name} - {option_price}"
                    )
                    if pause_on_success:
                        print_success("Purchase successful!")
                        pause()
                    else:
                        print_success("Purchase successful!")

            except Exception as e:
                print_error(f"Exception occurred while creating order: {e}")
                res = None
            print_rule()
            should_delay = error_msg == "" or "Failed call ipaas purchase" in error_msg
            if delay_seconds > 0 and should_delay:
                print_info(f"Waiting {delay_seconds}s before next purchase...")
                time.sleep(delay_seconds)
                
    print_rule()
    console.print(f"[bold white]Family:[/bold white] {family_name}  [bold green]Berhasil: {len(successful_purchases)}[/bold green]")
    if len(successful_purchases) > 0:
        t = make_table(("#", "bold cyan", "right"), ("Pembelian", "white", "left"))
        for i, p in enumerate(successful_purchases, 1):
            t.add_row(str(i), p)
        console.print(t)
    print_rule()
    pause()

def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        # Balance with Decoy
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
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print_warning(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")
        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
        if balance_answer.lower() != "y":
            print_warning("Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_error(f"Failed to get family data for code: {family_code}.")
        pause()
        return None
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = None
    for variant in variants:
        if variant["package_variant_code"] == variant_code:
            target_variant = variant
            break
    if not target_variant:
        print_error(f"Variant code {variant_code} not found in family {family_name}.")
        pause()
        return None
    target_option = None
    for option in target_variant["package_options"]:
        if option["order"] == option_order:
            target_option = option
            break
    if not target_option:
        print_error(f"Option order {option_order} not found in variant {target_variant['name']}.")
        pause()
        return None
    option_name = target_option["name"]
    option_price = target_option["price"]
    print_rule()
    successful_purchases = []
    
    for i in range(n):
        print_info(f"Purchase {i + 1}/{n} → {target_variant['name']} - {option_order}. {option_name} — Rp {option_price}")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        
        payment_items = []
        
        try:
            if use_decoy:
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
            
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            print_error(f"Exception fetching package: {e} — Skipping.")
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        res = None
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
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
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(
                            f"{target_variant['name']}|{option_order}. {option_name} - {option_price}"
                        )
                        
                        if pause_on_success:
                            print_success("Purchase successful!")
                            pause()
                        else:
                            print_success("Purchase successful!")
            else:
                successful_purchases.append(
                    f"{target_variant['name']}|{option_order}. {option_name} - {option_price}"
                )
                if pause_on_success:
                    print_success("Purchase successful!")
                    pause()
                else:
                    print_success("Purchase successful!")
        except Exception as e:
            print_error(f"Exception occurred while creating order: {e}")
            res = None
        print_rule()

        if delay_seconds > 0 and i < n - 1:
            print_info(f"Waiting {delay_seconds}s before next purchase...")
            time.sleep(delay_seconds)

    print_rule()
    console.print(f"[bold white]Family: {family_name}  Variant: {target_variant['name']}  Option: {option_order}. {option_name}[/bold white]")
    console.print(f"[bold green]Total berhasil: {len(successful_purchases)}/{n}[/bold green]")
    if len(successful_purchases) > 0:
        t = make_table(("#", "bold cyan", "right"), ("Pembelian", "white", "left"))
        for i, p in enumerate(successful_purchases, 1):
            t.add_row(str(i), p)
        console.print(t)
    print_rule()
    pause()
    return True

def purchase_n_times_by_option_code(
    n: int,
    option_code: str,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
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
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        print_warning(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")
        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
        if balance_answer.lower() != "y":
            print_warning("Pembelian dibatalkan oleh user.")
            pause()
            return None
    
    print_rule()
    successful_purchases = []
    
    for i in range(n):
        print_info(f"Purchase {i + 1}/{n}...")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        
        payment_items = []
        
        try:
            if use_decoy:
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
            
            target_package_detail = get_package(
                api_key,
                tokens,
                option_code,
            )
        except Exception as e:
            print_error(f"Exception fetching package: {e} — Skipping.")
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        res = None
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
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
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(
                            f"Purchase {i + 1}"
                        )
                        
                        if pause_on_success:
                            print_success("Purchase successful!")
                            pause()
                        else:
                            print_success("Purchase successful!")
            else:
                successful_purchases.append(
                    f"Purchase {i + 1}"
                )
                if pause_on_success:
                    print_success("Purchase successful!")
                    pause()
                else:
                    print_success("Purchase successful!")
        except Exception as e:
            print_error(f"Exception occurred while creating order: {e}")
            res = None
        print_rule()

        if delay_seconds > 0 and i < n - 1:
            print_info(f"Waiting {delay_seconds}s before next purchase...")
            time.sleep(delay_seconds)

    print_rule()
    console.print(f"[bold green]Total berhasil: {len(successful_purchases)}/{n}[/bold green]")
    if len(successful_purchases) > 0:
        t = make_table(("#", "bold cyan", "right"), ("Pembelian", "white", "left"))
        for i, p in enumerate(successful_purchases, 1):
            t.add_row(str(i), p)
        console.print(t)
    print_rule()
    pause()
    return True
