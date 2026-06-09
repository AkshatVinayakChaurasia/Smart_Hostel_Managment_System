"""
validators.py - Input validation helpers for HostelHub
"""

import re


def is_non_empty(value: str, field_name: str = "Field") -> tuple[bool, str]:
    """Check that a string is not empty."""
    if not value or not value.strip():
        return False, f"{field_name} cannot be empty."
    return True, ""


def is_valid_mobile(mobile: str) -> tuple[bool, str]:
    """Validate a 10-digit Indian mobile number."""
    pattern = r"^[6-9]\d{9}$"
    if not re.match(pattern, mobile.strip()):
        return False, "Mobile number must be 10 digits starting with 6-9."
    return True, ""


def is_valid_year(year: str) -> tuple[bool, str]:
    """Validate academic year (1-4)."""
    if not year.strip().isdigit() or int(year.strip()) not in range(1, 5):
        return False, "Year must be between 1 and 4."
    return True, ""


def is_positive_number(value: str, field_name: str = "Value") -> tuple[bool, str]:
    """Check that a value is a positive number."""
    try:
        num = float(value.strip())
        if num <= 0:
            return False, f"{field_name} must be a positive number."
        return True, ""
    except ValueError:
        return False, f"{field_name} must be a valid number."


def is_valid_room_capacity(value: str) -> tuple[bool, str]:
    """Validate room capacity (1-10)."""
    try:
        cap = int(value.strip())
        if cap < 1 or cap > 10:
            return False, "Room capacity must be between 1 and 10."
        return True, ""
    except ValueError:
        return False, "Capacity must be an integer."


def is_valid_name(name: str) -> tuple[bool, str]:
    """
    Validate a person's name:
    - Must be at least 2 characters
    - Must not be purely numeric
    """
    stripped = name.strip()
    if len(stripped) < 2:
        return False, "Name must be at least 2 characters long."
    if stripped.isdigit():
        return False, "Name cannot be purely numeric."
    return True, ""


def validate_input(value: str, validators: list) -> tuple[bool, str]:
    """
    Run multiple validators on a value in order.
    Stops at the first failure.

    Args:
        value:      The input string to validate
        validators: List of validator callables returning (bool, str)
    Returns:
        (True, "") on success, (False, error_message) on failure
    """
    for validator in validators:
        ok, msg = validator(value)
        if not ok:
            return False, msg
    return True, ""
