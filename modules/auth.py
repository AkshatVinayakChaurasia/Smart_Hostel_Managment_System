"""
auth.py - Authentication module for HostelHub

Handles login validation for Admin and Student roles.
Credentials are stored in data/users.json.
"""

import getpass
from database.db_handler import DataHandler
from utils.display import (
    print_banner, print_header, print_line,
    print_error, print_success, clear_screen, pause
)


class AuthManager:
    """Manages login sessions for Admin and Student users."""

    def __init__(self):
        self._current_user: dict | None = None

    # -- Public API ----------------------------------------------------

    @property
    def current_user(self) -> dict | None:
        """Return the currently logged-in user dict, or None."""
        return self._current_user

    @property
    def is_admin(self) -> bool:
        return bool(self._current_user and self._current_user.get("role") == "admin")

    @property
    def is_student(self) -> bool:
        return bool(self._current_user and self._current_user.get("role") == "student")

    def logout(self):
        """Clear the current session."""
        self._current_user = None

    # -- Login flow ----------------------------------------------------

    def login(self) -> dict | None:
        """
        Show the login prompt and validate credentials.
        Returns the authenticated user dict, or None on failure.
        """
        print_banner()
        print_header("LOGIN")

        username = input("  >  Username : ").strip()
        # Use getpass so password is hidden in the terminal
        try:
            password = getpass.getpass("  >  Password : ")
        except Exception:
            # Fallback for environments that don't support getpass
            password = input("  >  Password : ").strip()

        user = self._validate_credentials(username, password)
        if user:
            self._current_user = user
            print_success(f"Welcome, {user['name']}!  [ Role: {user['role'].upper()} ]")
            pause()
            return user
        else:
            print_error("Invalid username or password. Please try again.")
            pause()
            return None

    def login_loop(self) -> dict:
        """
        Repeat the login prompt until valid credentials are entered.
        Returns the authenticated user dict.
        """
        while True:
            user = self.login()
            if user:
                return user

    # -- Private helpers -----------------------------------------------

    @staticmethod
    def _validate_credentials(username: str, password: str) -> dict | None:
        """Check username/password against stored users. Returns user dict or None."""
        users = DataHandler.get_all("users")
        for user in users:
            if (
                user.get("username", "").strip().lower() == username.strip().lower()
                and user.get("password", "") == password
            ):
                return user
        return None
