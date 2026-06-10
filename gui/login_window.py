"""
login_window.py - Login Screen for HostelHub GUI

Shows username/password fields and validates against users.json
via the existing DataHandler backend.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gui import COLORS, FONTS, center_window
from database.db_handler import DataHandler


class LoginWindow(ttk.Frame):
    """Login form displayed inside the main application root."""

    def __init__(self, master, on_login_success):
        """
        Args:
            master:           Root Tk window
            on_login_success: Callback function(user_dict) on valid login
        """
        super().__init__(master)
        self.on_login_success = on_login_success
        self._build_ui()

    # -----------------------------------------------------------------
    def _build_ui(self):
        self.configure(style="TFrame")
        self.pack(fill="both", expand=True)

        # Centered container
        outer = ttk.Frame(self)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # Login Card
        card = tk.Frame(outer, bg=COLORS["card"], bd=0,
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(padx=40, pady=20)

        # Top Accent Strip (5px brand color)
        accent_strip = tk.Frame(card, bg=COLORS["accent"], height=5)
        accent_strip.pack(fill="x")

        # Inner container for padding
        inner = tk.Frame(card, bg=COLORS["card"], padx=40, pady=30)
        inner.pack()

        # Title/Logo
        tk.Label(inner, text="HostelHub",
                 font=("Segoe UI", 24, "bold"), bg=COLORS["card"],
                 fg=COLORS["primary"]).pack(pady=(10, 2))
        
        # Subtitle
        tk.Label(inner, text="Smart Hostel Management System",
                 font=("Segoe UI", 11, "bold"), bg=COLORS["card"],
                 fg=COLORS["text_muted"]).pack(pady=(0, 20))

        # Form
        form = tk.Frame(inner, bg=COLORS["card"])
        form.pack(pady=10)

        tk.Label(form, text="Username", font=FONTS["body"],
                 bg=COLORS["card"], fg=COLORS["text"], anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_user = ttk.Entry(form, width=30, font=FONTS["entry"])
        self.entry_user.grid(row=1, column=0, pady=(0, 15), ipady=5)
        self.entry_user.focus_set()

        tk.Label(form, text="Password", font=FONTS["body"],
                 bg=COLORS["card"], fg=COLORS["text"], anchor="w").grid(
            row=2, column=0, sticky="w", pady=(0, 4))
        self.entry_pass = ttk.Entry(form, width=30, font=FONTS["entry"],
                                    show="*")
        self.entry_pass.grid(row=3, column=0, pady=(0, 25), ipady=5)

        # Login button
        btn_login = ttk.Button(form, text="Login",
                               style="Accent.TButton",
                               command=self._attempt_login)
        btn_login.grid(row=4, column=0, sticky="ew", ipady=4)

        # Bind Enter key
        self.entry_pass.bind("<Return>", lambda e: self._attempt_login())
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())

        # Hint at bottom of card
        tk.Label(inner, text="Admin: admin / admin123   |   Student: STU001 / stu001",
                 font=FONTS["small"], bg=COLORS["card"],
                 fg=COLORS["text_muted"]).pack(pady=(15, 0))

    # -----------------------------------------------------------------
    def _attempt_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Login", "Please enter both username and password.")
            return

        user = self._validate(username, password)
        if user:
            self.on_login_success(user)
        else:
            messagebox.showerror("Login Failed",
                                 "Invalid username or password.\nPlease try again.")
            self.entry_pass.delete(0, "end")
            self.entry_pass.focus_set()

    @staticmethod
    def _validate(username: str, password: str):
        """Check credentials against users.json via DataHandler."""
        users = DataHandler.get_all("users")
        for u in users:
            if (u.get("username", "").strip().lower() == username.lower()
                    and u.get("password", "") == password):
                return u
        return None
