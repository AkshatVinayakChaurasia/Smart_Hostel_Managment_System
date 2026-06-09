"""
display.py - Console display helpers for HostelHub
Provides formatted tables, menus, banners, and separator lines.
"""

import os


# ---------------------------------------------
#  Terminal helpers
# ---------------------------------------------

def clear_screen():
    """Clear the terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def print_line(char="-", width=65):
    """Print a horizontal separator line."""
    print(char * width)


def print_header(title: str, width: int = 65):
    """Print a styled section header."""
    print()
    print_line("=", width)
    print(f"  {title.upper()}")
    print_line("=", width)


def print_banner():
    """Print the HostelHub application banner."""
    clear_screen()
    print()
    print("  +==========================================================+")
    print("  |      HOSTELHUB - Smart Hostel Management System          |")
    print("  |              Console-Based ERP Dashboard                 |")
    print("  +==========================================================+")
    print()


def print_menu(title: str, options: list[str], prompt: str = "Enter choice"):
    """
    Print a numbered menu with a title.

    Args:
        title:   Menu heading
        options: List of option strings (without numbering)
        prompt:  Input prompt text
    Returns:
        User's raw input string
    """
    print_header(title)
    for idx, option in enumerate(options, start=1):
        print(f"    [{idx}]  {option}")
    print_line()
    return input(f"\n  >  {prompt}: ").strip()


def print_table(headers: list[str], rows: list[list], col_width: int = 18):
    """
    Print a simple ASCII table.

    Args:
        headers:   Column header strings
        rows:      List of row data (each row is a list)
        col_width: Fixed column width (characters)
    """
    if not rows:
        print("\n  (No records found)\n")
        return

    # Build format string
    fmt = "  " + "".join(f"{{:<{col_width}}}" for _ in headers)
    sep = "  " + ("-" * col_width + " ") * len(headers)

    print()
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        # Truncate long values to fit column width
        display_row = [str(v)[:col_width - 1] for v in row]
        print(fmt.format(*display_row))
    print()


def print_success(msg: str):
    """Print a success message."""
    print(f"\n  [OK]  {msg}\n")


def print_error(msg: str):
    """Print an error message."""
    print(f"\n  [X]  {msg}\n")


def print_warning(msg: str):
    """Print a warning message."""
    print(f"\n  [!] {msg}\n")


def print_info(msg: str):
    """Print an informational message."""
    print(f"\n  [i] {msg}\n")


def pause(msg: str = "Press Enter to continue..."):
    """Pause and wait for user to press Enter."""
    input(f"\n  {msg}")


def confirm(prompt: str = "Are you sure? (y/n)") -> bool:
    """Ask the user for a yes/no confirmation."""
    answer = input(f"\n  >  {prompt}: ").strip().lower()
    return answer in ("y", "yes")


def print_stat_card(label: str, value, width: int = 20):
    """Print a single stat card inline."""
    border = "-" * width
    label_str = label[:width - 2].center(width)
    value_str = str(value).center(width)
    print(f"  +{border}+")
    print(f"  |{label_str}|")
    print(f"  |{value_str}|")
    print(f"  +{border}+")


def print_dashboard_stats(stats: dict):
    """
    Print a row of dashboard stat cards.

    Args:
        stats: dict of {label: value}
    """
    print()
    keys = list(stats.keys())
    vals = list(stats.values())
    width = 18

    # Top border row
    border = ("-" * width)
    print("  " + "  ".join(f"+{border}+" for _ in keys))

    # Label row
    labels = [k[:width].center(width) for k in keys]
    print("  " + "  ".join(f"|{l}|" for l in labels))

    # Value row
    values = [str(v)[:width].center(width) for v in vals]
    print("  " + "  ".join(f"|{v}|" for v in values))

    # Bottom border row
    print("  " + "  ".join(f"+{border}+" for _ in keys))
    print()
