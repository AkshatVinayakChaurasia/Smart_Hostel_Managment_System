"""
helpers.py - Common utility helpers for HostelHub
"""

import os
import json
import csv
from datetime import datetime


# ---------------------------------------------
#  Date / Time helpers
# ---------------------------------------------

def current_date() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def current_datetime() -> str:
    """Return current datetime as YYYY-MM-DD HH:MM:SS."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_date(date_str: str, from_fmt: str = "%Y-%m-%d", to_fmt: str = "%d %b %Y") -> str:
    """Reformat a date string."""
    try:
        dt = datetime.strptime(date_str, from_fmt)
        return dt.strftime(to_fmt)
    except ValueError:
        return date_str


# ---------------------------------------------
#  JSON helpers
# ---------------------------------------------

def load_json(filepath: str) -> list | dict:
    """
    Load JSON data from a file.
    Returns an empty list if the file does not exist or is empty.
    """
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_json(filepath: str, data: list | dict) -> bool:
    """
    Save data to a JSON file (pretty-printed).
    Creates parent directories if needed.
    Returns True on success, False on failure.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False


# ---------------------------------------------
#  CSV helpers
# ---------------------------------------------

def export_to_csv(filepath: str, headers: list[str], rows: list[list]) -> bool:
    """
    Export data to a CSV file.
    Creates the file (and parent dirs) if they don't exist.
    Returns True on success.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return True
    except IOError:
        return False


# ---------------------------------------------
#  ID generation
# ---------------------------------------------

def generate_id(prefix: str, existing_ids: list[str]) -> str:
    """
    Generate a unique sequential ID like STU001, RM003, etc.

    Args:
        prefix:       Short prefix string (e.g., "STU", "RM", "FEE")
        existing_ids: List of already-used IDs with the same prefix
    Returns:
        New unique ID string
    """
    numbers = []
    for eid in existing_ids:
        if eid.startswith(prefix):
            try:
                numbers.append(int(eid[len(prefix):]))
            except ValueError:
                pass
    next_num = max(numbers, default=0) + 1
    return f"{prefix}{next_num:03d}"


# ---------------------------------------------
#  String helpers
# ---------------------------------------------

def title_case(s: str) -> str:
    """Convert a string to Title Case."""
    return s.strip().title()


def truncate(s: str, max_len: int = 25) -> str:
    """Truncate a string to max_len characters."""
    s = str(s)
    return s if len(s) <= max_len else s[:max_len - 3] + "..."
