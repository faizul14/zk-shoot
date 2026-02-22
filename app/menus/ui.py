"""
Centralized Rich UI helper module for XL Token terminal app.
Import `console` and helper functions from here in all menu files.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text
from rich import box

# Singleton console used across all menu files
console = Console()

# ─── Color Palette ───────────────────────────────────────────────────────────
PRIMARY   = "bold cyan"
SECONDARY = "bold blue"
SUCCESS   = "bold green"
ERROR     = "bold red"
WARNING   = "bold yellow"
MUTED     = "dim white"
ACCENT    = "bold magenta"
HEADER_BG = "blue"

# ─── Layout Helpers ───────────────────────────────────────────────────────────
def print_header(title: str, subtitle: str = ""):
    """Render a styled panel as a section header."""
    content = Text(title, style=f"bold white", justify="center")
    if subtitle:
        content.append(f"\n{subtitle}", style="dim white")
    console.print(Panel(content, style=SECONDARY, border_style="cyan", expand=False, width=60))

def print_rule(title: str = ""):
    """Render a horizontal rule, optionally with a label."""
    console.print(Rule(title, style="cyan"))

def print_banner(ascii_art: str):
    """Print ASCII art banner in cyan."""
    console.print(ascii_art, style="cyan")

# ─── Message Helpers ──────────────────────────────────────────────────────────
def print_success(msg: str):
    console.print(f"[{SUCCESS}]✔ {msg}[/]")

def print_error(msg: str):
    console.print(f"[{ERROR}]✘ {msg}[/]")

def print_warning(msg: str):
    console.print(f"[{WARNING}]⚠ {msg}[/]")

def print_info(msg: str):
    console.print(f"[{PRIMARY}]ℹ {msg}[/]")

def pause():
    """Styled pause prompt."""
    console.input("\n[dim]Tekan [bold cyan]Enter[/] untuk lanjut...[/dim]")

# ─── Table Builders ───────────────────────────────────────────────────────────
def make_table(*columns, title: str = "", box_style=box.SIMPLE_HEAVY) -> Table:
    """
    Create a Rich Table with standard styling.
    Pass column names as positional args; each can be a str or (name, style, justify) tuple.
    """
    table = Table(
        box=box_style,
        border_style="cyan",
        header_style="bold cyan",
        title=title if title else None,
        title_style="bold white",
        show_lines=False,
        expand=False,
    )
    for col in columns:
        if isinstance(col, tuple):
            name, style, justify = col if len(col) == 3 else (*col, "left")
            table.add_column(name, style=style, justify=justify)
        else:
            table.add_column(col, style="white")
    return table

def make_menu_table(items: list[tuple], title: str = "") -> Table:
    """
    Render a numbered option menu as a Rich Table.
    items: list of (key, label) or (key, label, style) tuples.
    """
    table = Table(
        box=box.SIMPLE,
        border_style="cyan",
        header_style="bold cyan",
        show_header=False,
        title=title if title else None,
        title_style="bold white",
        expand=False,
        padding=(0, 1),
    )
    table.add_column("Key",   style="bold cyan",  justify="right",  no_wrap=True)
    table.add_column("Label", style="white",       justify="left")
    for item in items:
        key   = str(item[0])
        label = str(item[1])
        style = item[2] if len(item) > 2 else "white"
        table.add_row(f"[bold cyan]{key}[/]", f"[{style}]{label}[/]")
    return table
