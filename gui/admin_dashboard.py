"""
admin_dashboard.py - Admin Dashboard for HostelHub GUI

Displays a grid of large buttons for each management module.
Each button opens the corresponding module GUI in a Toplevel window.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gui import COLORS, FONTS, create_header, make_status_bar, DashboardCard


# Button configuration:  (label, icon_text, module_opener_key)
ADMIN_BUTTONS = [
    ("Student\nManagement",    "STUDENT", "students"),
    ("Room\nManagement",       "ROOMS",   "rooms"),
    ("Fee\nManagement",        "FEES",    "fees"),
    ("Complaint\nManagement",  "COMPLAINT", "complaints"),
    ("Attendance\nManagement", "ATTENDANCE", "attendance"),
    ("Notice\nBoard",          "NOTICES",  "notices"),
    ("System\nReports",        "REPORTS",  "reports"),
]

# Map keys to lazy-import module openers
_OPENERS = {
    "students":   lambda p, u: _open("gui.student_gui",   "open_student_window",   p, u),
    "rooms":      lambda p, u: _open("gui.room_gui",      "open_room_window",      p, u),
    "fees":       lambda p, u: _open("gui.fee_gui",       "open_fee_window",       p, u),
    "complaints": lambda p, u: _open("gui.complaint_gui", "open_complaint_window", p, u),
    "attendance": lambda p, u: _open("gui.attendance_gui","open_attendance_window", p, u),
    "notices":    lambda p, u: _open("gui.notice_gui",    "open_notice_window",    p, u),
    "reports":    lambda p, u: _open("gui.reports_gui",   "open_reports_window",   p, u),
}


def _open(module_path, func_name, parent, user):
    """Lazy-import a module GUI and call its opener function."""
    import importlib
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        func(parent, user)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open module:\n{e}")


# =====================================================================
#  BUTTON COLORS (tag -> bg/fg/active) - used for card badges
# =====================================================================

_BTN_COLORS = {
    "students":   ("#2563eb", "#ffffff", "#1d4ed8"), # Slate/Blue theme
    "rooms":      ("#10b981", "#ffffff", "#059669"),
    "fees":       ("#f59e0b", "#ffffff", "#d97706"),
    "complaints": ("#ef4444", "#ffffff", "#dc2626"),
    "attendance": ("#8b5cf6", "#ffffff", "#7c3aed"),
    "notices":    ("#06b6d4", "#ffffff", "#0891b2"),
    "reports":    ("#64748b", "#ffffff", "#475569"),
}


class AdminDashboard(ttk.Frame):
    """Admin dashboard with module buttons in a grid layout."""

    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.master = master
        self.user = user
        self.on_logout = on_logout
        self._build_ui()

    def _build_ui(self):
        self.pack(fill="both", expand=True)

        # -- Header --
        header = create_header(self, "HostelHub - Admin Dashboard")
        tk.Label(header, text=f"Welcome, {self.user.get('name', 'Admin')}",
                 font=FONTS["body"], bg=COLORS["primary"],
                 fg="#bdc3c7").pack(side="right", padx=20)

        # -- Button Grid --
        grid_frame = tk.Frame(self, bg=COLORS["bg"])
        grid_frame.pack(fill="both", expand=True, padx=30, pady=25)

        # Center the grid (3 columns for balanced display)
        grid_frame.columnconfigure((0, 1, 2), weight=1)

        for idx, (label, icon, key) in enumerate(ADMIN_BUTTONS):
            row, col = divmod(idx, 3)
            bg, _, _ = _BTN_COLORS[key]

            card = DashboardCard(
                grid_frame,
                title=label,
                icon_text=icon,
                accent_color=bg,
                command=lambda k=key: self._open_module(k)
            )
            card.grid(row=row, column=col, padx=16, pady=16, sticky="nsew")
            grid_frame.rowconfigure(row, weight=1)

        # -- Logout Button --
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=30, pady=(0, 15))
        ttk.Button(bottom, text="Logout", style="Danger.TButton",
                   command=self._logout).pack(side="right")

        # -- Status bar --
        make_status_bar(self, f"Logged in as: {self.user.get('name', '')}  [ADMIN]")

    def _open_module(self, key):
        opener = _OPENERS.get(key)
        if opener:
            opener(self.winfo_toplevel(), self.user)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_logout()
