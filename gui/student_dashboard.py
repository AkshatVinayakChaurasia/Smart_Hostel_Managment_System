"""
student_dashboard.py - Student Dashboard for HostelHub GUI

Shows limited-access buttons for student self-service:
profile, room, fees, complaints, attendance, notices.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gui import COLORS, FONTS, create_header, make_status_bar, DashboardCard


STUDENT_BUTTONS = [
    ("My\nProfile",     "PROFILE",    "profile"),
    ("My\nRoom",        "ROOM",       "room"),
    ("My\nFees",        "FEES",       "fees"),
    ("My\nComplaints",  "COMPLAINTS", "complaints"),
    ("My\nAttendance",  "ATTENDANCE", "attendance"),
    ("Notice\nBoard",   "NOTICES",    "notices"),
]

_BTN_COLORS = {
    "profile":    ("#2563eb", "#ffffff", "#1d4ed8"),
    "room":       ("#10b981", "#ffffff", "#059669"),
    "fees":       ("#f59e0b", "#ffffff", "#d97706"),
    "complaints": ("#ef4444", "#ffffff", "#dc2626"),
    "attendance": ("#8b5cf6", "#ffffff", "#7c3aed"),
    "notices":    ("#06b6d4", "#ffffff", "#0891b2"),
}


def _open(module_path, func_name, parent, user):
    import importlib
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        func(parent, user)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open module:\n{e}")


_OPENERS = {
    "profile":    lambda p, u: _open("gui.student_gui",   "open_student_profile", p, u),
    "room":       lambda p, u: _open("gui.room_gui",      "open_my_room",        p, u),
    "fees":       lambda p, u: _open("gui.fee_gui",       "open_my_fees",        p, u),
    "complaints": lambda p, u: _open("gui.complaint_gui", "open_my_complaints",  p, u),
    "attendance": lambda p, u: _open("gui.attendance_gui","open_my_attendance",   p, u),
    "notices":    lambda p, u: _open("gui.notice_gui",    "open_notice_window",  p, u),
}


class StudentDashboard(ttk.Frame):
    """Student self-service dashboard with limited module access."""

    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout
        self._build_ui()

    def _build_ui(self):
        self.pack(fill="both", expand=True)

        # Header
        header = create_header(self, "HostelHub - Student Dashboard")
        tk.Label(header,
                 text=f"{self.user.get('name', '')}  |  {self.user.get('username', '')}",
                 font=FONTS["body"], bg=COLORS["primary"],
                 fg="#bdc3c7").pack(side="right", padx=20)

        # Button grid
        grid_frame = tk.Frame(self, bg=COLORS["bg"])
        grid_frame.pack(fill="both", expand=True, padx=30, pady=25)
        grid_frame.columnconfigure((0, 1, 2), weight=1)

        for idx, (label, icon, key) in enumerate(STUDENT_BUTTONS):
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

        # Logout
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=30, pady=(0, 15))
        ttk.Button(bottom, text="Logout", style="Danger.TButton",
                   command=self._logout).pack(side="right")

        # Status
        make_status_bar(self,
                        f"Student: {self.user.get('name', '')}  |  ID: {self.user.get('username', '')}")

    def _open_module(self, key):
        opener = _OPENERS.get(key)
        if opener:
            opener(self.winfo_toplevel(), self.user)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_logout()
