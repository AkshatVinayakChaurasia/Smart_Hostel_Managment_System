"""
Attendance Management GUI for HostelHub.
Entity: 'attendance', ID field: 'attendance_id'
Admin view: mark attendance, view summary, manage all records.
Student view: view own attendance records with percentage.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui import (COLORS, FONTS, create_header, create_treeview,
                 populate_treeview, make_toolbar, center_window)
from database.db_handler import DataHandler


def _next_attendance_id():
    """Generate next attendance ID like ATT001, ATT002, etc."""
    records = DataHandler.get_all("attendance")
    if not records:
        return "ATT001"
    nums = []
    for r in records:
        aid = r.get('attendance_id', '')
        if aid.startswith('ATT') and aid[3:].isdigit():
            nums.append(int(aid[3:]))
    next_num = max(nums) + 1 if nums else 1
    return f"ATT{next_num:03d}"


def _calc_percentage(records):
    """Calculate attendance percentage from a list of records."""
    total = len(records)
    if total == 0:
        return 0.0
    present = sum(1 for r in records if r.get('status') == 'Present')
    return round((present / total) * 100, 1)


def _refresh_all(tree):
    """Load all attendance records into the treeview."""
    records = DataHandler.get_all("attendance")
    rows = [(r.get('attendance_id', ''), r.get('student_id', ''),
             r.get('date', ''), r.get('status', '')) for r in records]
    populate_treeview(tree, rows)


# ---------------------------------------------------------------
# Admin View
# ---------------------------------------------------------------
def open_attendance_window(parent, user):
    """Open Attendance Management window (Admin view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - Attendance Management")
    win.configure(bg=COLORS['bg'])
    center_window(win, 900, 560)
    win.transient(parent)
    win.grab_set()

    create_header(win, "Attendance Management")

    # --- Toolbar ---
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Mark Attendance", style="Accent.TButton",
               command=lambda: _mark_attendance(win, tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="View Summary",
               command=lambda: _view_summary(win)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _refresh_all(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Treeview ---
    columns = ('aid', 'student', 'date', 'status')
    headings = ('ID', 'Student ID', 'Date', 'Status')
    widths = (100, 160, 140, 120)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh_all(tree)
    win.wait_window()


def _mark_attendance(parent, tree):
    """Dialog to mark attendance for a student."""
    dlg = tk.Toplevel(parent)
    dlg.title("Mark Attendance")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 380, 260)
    dlg.transient(parent)
    dlg.grab_set()

    frame = ttk.Frame(dlg)
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    ttk.Label(frame, text="Mark Attendance",
              font=FONTS['subhead']).grid(row=0, column=0, columnspan=2, pady=8)

    ttk.Label(frame, text="Student ID:").grid(row=1, column=0, sticky='w', pady=5)
    sid_var = tk.StringVar()
    sid_entry = ttk.Entry(frame, textvariable=sid_var, width=22)
    sid_entry.grid(row=1, column=1, sticky='w')

    ttk.Label(frame, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky='w', pady=5)
    date_var = tk.StringVar(value=str(date.today()))
    date_entry = ttk.Entry(frame, textvariable=date_var, width=22)
    date_entry.grid(row=2, column=1, sticky='w')

    ttk.Label(frame, text="Status:").grid(row=3, column=0, sticky='w', pady=5)
    status_var = tk.StringVar(value='Present')
    status_combo = ttk.Combobox(frame, textvariable=status_var,
                                values=['Present', 'Absent', 'Leave'],
                                state='readonly', width=19)
    status_combo.grid(row=3, column=1, sticky='w')

    def save():
        student_id = sid_var.get().strip()
        att_date = date_var.get().strip()
        status = status_var.get()

        if not student_id:
            messagebox.showwarning("Missing Field", "Please enter a Student ID.")
            return
        if not att_date:
            messagebox.showwarning("Missing Field", "Please enter a date.")
            return

        # Check for duplicate: same student + same date
        all_records = DataHandler.get_all("attendance")
        for r in all_records:
            if r.get('student_id') == student_id and r.get('date') == att_date:
                messagebox.showwarning(
                    "Duplicate",
                    f"Attendance already marked for {student_id} on {att_date}.")
                return

        new_record = {
            'attendance_id': _next_attendance_id(),
            'student_id': student_id,
            'date': att_date,
            'status': status
        }
        DataHandler.insert("attendance", new_record)
        messagebox.showinfo("Marked",
                            f"Attendance marked: {student_id} - {status} on {att_date}.")
        dlg.destroy()
        _refresh_all(tree)

    ttk.Button(frame, text="Save", style="Accent.TButton",
               command=save).grid(row=4, column=0, columnspan=2, pady=12)

    dlg.wait_window()


def _view_summary(parent):
    """Show attendance percentage summary per student."""
    records = DataHandler.get_all("attendance")
    if not records:
        messagebox.showinfo("Summary", "No attendance records found.")
        return

    win = tk.Toplevel(parent)
    win.title("Attendance Summary")
    win.configure(bg=COLORS['bg'])
    center_window(win, 600, 420)
    win.transient(parent)
    win.grab_set()

    create_header(win, "Attendance Summary")

    # --- Summary Treeview ---
    columns = ('student', 'total', 'present', 'absent', 'leave', 'percent')
    headings = ('Student ID', 'Total', 'Present', 'Absent', 'Leave', 'Percentage')
    widths = (130, 60, 70, 60, 60, 90)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    # Group records by student_id
    summary = {}
    for r in records:
        sid = r.get('student_id', 'Unknown')
        if sid not in summary:
            summary[sid] = {'total': 0, 'Present': 0, 'Absent': 0, 'Leave': 0}
        summary[sid]['total'] += 1
        status = r.get('status', '')
        if status in summary[sid]:
            summary[sid][status] += 1

    rows = []
    for sid, data in sorted(summary.items()):
        pct = round((data['Present'] / data['total']) * 100, 1) if data['total'] else 0
        rows.append((sid, data['total'], data['Present'],
                      data['Absent'], data['Leave'], f"{pct}%"))
    populate_treeview(tree, rows)

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)
    win.wait_window()


# ---------------------------------------------------------------
# Student View
# ---------------------------------------------------------------
def open_my_attendance(parent, user):
    """Open My Attendance window (Student view)."""
    student_id = user.get('username', '')

    win = tk.Toplevel(parent)
    win.title("HostelHub - My Attendance")
    win.configure(bg=COLORS['bg'])
    center_window(win, 750, 520)
    win.transient(parent)
    win.grab_set()

    create_header(win, "My Attendance")

    # --- Percentage summary label at top ---
    summary_frame = ttk.Frame(win)
    summary_frame.pack(fill='x', padx=12, pady=(8, 0))
    pct_label = ttk.Label(summary_frame, text="Attendance: --",
                          font=FONTS['subhead'])
    pct_label.pack(side='left', padx=5)

    # --- Toolbar ---
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _load_student_att(tree, student_id,
                                                  pct_label)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Treeview ---
    columns = ('aid', 'student', 'date', 'status')
    headings = ('ID', 'Student ID', 'Date', 'Status')
    widths = (100, 140, 140, 120)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _load_student_att(tree, student_id, pct_label)
    win.wait_window()


def _load_student_att(tree, student_id, pct_label):
    """Load attendance records for a specific student and update percentage."""
    all_records = DataHandler.get_all("attendance")
    filtered = [r for r in all_records if r.get('student_id') == student_id]

    rows = [(r.get('attendance_id', ''), r.get('student_id', ''),
             r.get('date', ''), r.get('status', '')) for r in filtered]
    populate_treeview(tree, rows)

    pct = _calc_percentage(filtered)
    total = len(filtered)
    present = sum(1 for r in filtered if r.get('status') == 'Present')
    pct_label.config(
        text=f"Attendance: {pct}%  ({present} present out of {total} days)")
