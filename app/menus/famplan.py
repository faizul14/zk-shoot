from datetime import datetime
import json
from app.menus.util import pause, clear_screen, format_quota_byte
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.client.engsel2 import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn

WIDTH = 55

def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        res = get_family_data(api_key, tokens)
        if not res.get("data"):
            print_error("Failed to get family data.")
            pause()
            return
        
        family_detail = res["data"]
        plan_type = family_detail["member_info"]["plan_type"]
        
        if plan_type == "":
            print_warning("You are not family plan organizer.")
            pause()
            return
        
        parent_msisdn = family_detail["member_info"]["parent_msisdn"]
        members = family_detail["member_info"]["members"]
        empyt_slots = [slot for slot in members if slot.get("msisdn") == ""]
        
        total_quota_byte = family_detail["member_info"].get("total_quota", 0)
        remaining_quota_byte = family_detail["member_info"].get("remaining_quota", 0)
        
        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)
        
        end_date_ts = family_detail["member_info"].get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d")
        
        clear_screen()
        console.print("\n[bold cyan]👨‍👩‍👧‍👦 Family Plan[/bold cyan]")
        print_rule()
        console.print(f"[bold white]Plan   :[/bold white] [bold cyan]{plan_type}[/bold cyan]  │  Parent: [bold]{parent_msisdn}[/bold]")
        console.print(f"[bold white]Kuota  :[/bold white] [bold green]{remaining_quota_human}[/bold green] / {total_quota_human}  │  Exp: [yellow]{end_date}[/yellow]")
        console.print(f"[bold white]Members:[/bold white] [bold]{len(members) - len(empyt_slots)}[/bold]/{len(members)}")
        print_rule()

        # Members table
        table = make_table(
            ("No",     "bold cyan",  "right"),
            ("MSISDN", "white",      "left"),
            ("Alias",  "dim white",  "left"),
            ("Tipe",   "yellow",     "center"),
            ("Pakai",  "bold green", "right"),
            ("Alokasi","dim green",  "right"),
            ("Chances","cyan",       "center"),
        )
        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "N/A")
            formatted_msisdn = msisdn if msisdn != "" else "[dim]<Empty Slot>[/dim]"
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")
            
            add_chances = member.get("add_chances", 0)
            total_add_chances = member.get("total_add_chances", 0)
            
            quota_allocated_byte = member.get("usage", {}).get("quota_allocated", 0)
            quota_used_byte = member.get("usage", {}).get("quota_used", 0)
            
            table.add_row(
                str(idx),
                formatted_msisdn,
                alias,
                member_type,
                format_quota_byte(quota_used_byte),
                format_quota_byte(quota_allocated_byte),
                f"{add_chances}/{total_add_chances}",
            )
        from rich.panel import Panel
        console.print(Panel(table, title="[bold cyan]👨‍👩‍👦 Anggota Family Plan[/bold cyan]", border_style="cyan", expand=False))
        
        print_rule()
        console.print("[bold cyan]1.[/bold cyan] Change Member")
        console.print("[dim]limit <Slot No> <Quota MB>[/dim]  — Contoh: [dim]limit 2 1024[/dim]")
        console.print("[dim]del <Slot No>[/dim]  —  Contoh: [dim]del 3[/dim]")
        console.print("[bold cyan]00.[/bold cyan] Back to Main Menu")
        print_rule()
        
        choice = console.input("[bold cyan]Enter your choice: [/bold cyan]").strip()
        if choice == "1":
            slot_idx = console.input("Enter the slot number: ").strip()
            target_msisdn = console.input("Enter the new member's phone number (start with 62): ").strip()
            parent_alias = console.input("Enter your alias: ").strip()
            child_alias = console.input("Enter the new member's alias: ").strip()
            
            try:
                slot_idx_int = int(slot_idx)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_error("Invalid slot number.")
                    pause()
                    return
                
                if members[slot_idx_int - 1].get("msisdn") != "":
                    print_error("Selected slot is not empty. Cannot change member.")
                    pause()
                    return
                
                family_member_id = members[slot_idx_int - 1]["family_member_id"]
                slot_id = members[slot_idx_int - 1]["slot_id"]
                
                # Checking MSISDN
                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                if validation_res.get("status").lower() != "success":
                    print_error(f"MSISDN validation failed: {json.dumps(validation_res, indent=2)}")
                    pause()
                    return
                print_success("MSISDN validation successful.")
                
                target_family_plan_role = validation_res["data"].get("family_plan_role", "")
                if target_family_plan_role != "NO_ROLE":
                    print_warning(f"{target_msisdn} is already part of another family plan with role {target_family_plan_role}.")
                    pause()
                    return

                is_continue = console.input(f"Are you sure you want to assign [bold]{target_msisdn}[/bold] to slot {slot_idx_int}? (y/n): ").strip().lower()
                if is_continue != "y":
                    print_warning("Operation cancelled by user.")
                    pause()
                    return
                
                change_member_res = change_member(
                    api_key,
                    tokens,
                    parent_alias,
                    child_alias,
                    slot_id,
                    family_member_id,
                    target_msisdn,
                )
                if change_member_res.get("status") == "SUCCESS":
                    print_success("Member changed successfully.")
                else:
                    print_error(f"Failed to change member: {change_member_res.get('message', 'Unknown error')}")
                
                console.print(json.dumps(change_member_res, indent=4))
            except ValueError:
                print_error("Invalid input. Please enter a valid slot number.")
            pause()
        elif choice.startswith("del "):
            _, slot_num = choice.split(" ", 1)
            try:
                slot_idx_int = int(slot_num)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_error("Invalid slot number.")
                    pause()
                    return
                
                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    print_warning("Selected slot is already empty.")
                    pause()
                    return
                
                is_continue = console.input(f"Are you sure you want to remove member [bold]{member.get('msisdn')}[/bold] from slot {slot_idx_int}? (y/n): ").strip().lower()
                if is_continue != "y":
                    print_warning("Operation cancelled by user.")
                    pause()
                    return
                
                family_member_id = member["family_member_id"]
                res = remove_member(
                    api_key,
                    tokens,
                    family_member_id,
                )
                if res.get("status") == "SUCCESS":
                    print_success("Member removed successfully.")
                else:
                    print_error(f"Failed to remove member: {res.get('message', 'Unknown error')}")
                
                console.print(json.dumps(res, indent=4))
            except ValueError:
                print_error("Invalid input. Please enter a valid slot number.")
            pause()
        elif choice.startswith("limit "):
            _, slot_num, new_quota_mb = choice.split(" ", 2)
            try:
                slot_idx_int = int(slot_num)
                new_quota_mb_int = int(new_quota_mb)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_error("Invalid slot number.")
                    pause()
                    return
                
                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    print_warning("Selected slot is empty. Cannot set quota limit.")
                    pause()
                    return
                
                family_member_id = member["family_member_id"]
                original_allocation_byte = member.get("usage", {}).get("quota_allocated", 0)
                new_allocation_byte = new_quota_mb_int * 1024 * 1024
                
                res = set_quota_limit(
                    api_key,
                    tokens,
                    original_allocation_byte,
                    new_allocation_byte,
                    family_member_id,
                )
                if res.get("status") == "SUCCESS":
                    print_success("Quota limit set successfully.")
                else:
                    print_error(f"Failed to set quota limit: {res.get('message', 'Unknown error')}")
                
                console.print(json.dumps(res, indent=4))
            except ValueError:
                print_error("Invalid input. Please enter a valid slot number.")
            pause()
        elif choice == "00":
            in_family_menu = False
            return