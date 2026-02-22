from app.menus.util import clear_screen
from app.menus.ui import console, print_success, print_error, print_warning, print_info, print_rule, make_table
from app.client.engsel import get_notifications, get_notification_detail
from app.service.auth import AuthInstance

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        print_info("Fetching notifications...")
        clear_screen()
        
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        notifications_res = get_notifications(api_key, tokens)
        if not notifications_res:
            print_warning("No notifications found.")
            return
        
        notifications = notifications_res.get("data", {}).get("inbox", [])
        
        if not notifications:
            print_warning("No notifications available.")
            return
        
        console.print("\n[bold cyan]🔔 Notifikasi[/bold cyan]")
        print_rule()

        unread_count = 0
        table = make_table(
            ("No",    "bold cyan",    "right"),
            ("Status","bold yellow",  "center"),
            ("Pesan", "white",        "left"),
            ("Waktu", "dim white",    "left"),
        )
        for idx, notification in enumerate(notifications):
            is_read = notification.get("is_read", False)
            brief_message = notification.get("brief_message", "")
            time_str = notification.get("timestamp", "")
            
            if is_read:
                status_text = "[dim]READ[/dim]"
                label_style = "dim"
            else:
                status_text = "[bold yellow]UNREAD[/bold yellow]"
                label_style = "bold white"
                unread_count += 1

            table.add_row(
                str(idx + 1),
                status_text,
                f"[{label_style}]{brief_message}[/]",
                f"[dim]{time_str}[/dim]",
            )

        console.print(table)
        console.print(f"[dim]Total: {len(notifications)} | [bold yellow]Unread: {unread_count}[/bold yellow][/dim]")
        print_rule()

        console.print("[bold cyan]1.[/bold cyan] Tandai Semua Dibaca  |  [bold cyan]00.[/bold cyan] Kembali ke Menu Utama")
        choice = console.input("\n[bold cyan]Pilihan: [/bold cyan]")

        if choice == "1":
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print_success(f"Marked as READ: {notification_id}")
            console.input("[dim]Tekan [bold cyan]Enter[/bold cyan] untuk kembali...[/dim]")
        elif choice == "00":
            in_notification_menu = False
        else:
            print_error("Pilihan tidak valid. Coba lagi.")
