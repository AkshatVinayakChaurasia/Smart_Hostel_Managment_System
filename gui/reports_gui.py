"""
System Reports GUI for HostelHub.
Admin-only dashboard showing summary statistics across all entities.
Includes CSV export functionality.
"""

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui import (COLORS, FONTS, create_header, make_toolbar, center_window)
from database.db_handler import DataHandler


def _gather_stats():
    """Collect summary statistics from all entities."""
    stats = {}

    # --- Students ---
    students = DataHandler.get_all("students")
    stats['total_students'] = len(students)
    stats['active_students'] = sum(
        1 for s in students if s.get('status', 'Active') == 'Active')

    # --- Rooms ---
    rooms = DataHandler.get_all("rooms")
    stats['total_rooms'] = len(rooms)
    stats['occupied_rooms'] = sum(
        1 for r in rooms if r.get('status', '') == 'Occupied')
    stats['vacant_rooms'] = stats['total_rooms'] - stats['occupied_rooms']

    # --- Fees ---
    fees = DataHandler.get_all("fees")
    stats['total_fees'] = len(fees)
    total_paid = 0
    total_pending = 0
    for f in fees:
        amt = float(f.get('amount', 0))
        if f.get('status', '').lower() == 'paid':
            total_paid += amt
        else:
            total_pending += amt
    stats['paid_amount'] = total_paid
    stats['pending_amount'] = total_pending

    # --- Complaints ---
    complaints = DataHandler.get_all("complaints")
    stats['total_complaints'] = len(complaints)
    stats['open_complaints'] = sum(
        1 for c in complaints if c.get('status', '') == 'Open')
    stats['resolved_complaints'] = sum(
        1 for c in complaints if c.get('status', '') == 'Resolved')

    # --- Attendance ---
    attendance = DataHandler.get_all("attendance")
    stats['total_attendance'] = len(attendance)
    present_count = sum(
        1 for a in attendance if a.get('status', '') == 'Present')
    if stats['total_attendance'] > 0:
        stats['present_pct'] = round(
            (present_count / stats['total_attendance']) * 100, 1)
    else:
        stats['present_pct'] = 0.0

    return stats


def _make_stat_label(parent, text, value, row, col):
    """Create a styled stat label inside a frame."""
    lbl = ttk.Label(parent, text=f"{text}: {value}", font=FONTS['body'])
    lbl.grid(row=row, column=col, sticky='w', padx=15, pady=4)
    return lbl


# ---------------------------------------------------------------
# Admin Reports View
# ---------------------------------------------------------------
def open_reports_window(parent, user):
    """Open System Reports window (Admin-only view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - System Reports")
    win.configure(bg=COLORS['bg'])
    center_window(win, 700, 580)
    win.transient(parent)
    win.grab_set()

    create_header(win, "System Reports")

    # --- Toolbar ---
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Refresh", style="Accent.TButton",
               command=lambda: _refresh_stats(content_frame)).pack(
                   side='left', padx=3)
    ttk.Button(toolbar, text="Export CSV",
               command=lambda: _export_csv()).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Scrollable content area ---
    content_frame = ttk.Frame(win)
    content_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh_stats(content_frame)
    win.wait_window()


def _refresh_stats(content_frame):
    """Refresh all stat cards in the content frame."""
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    stats = _gather_stats()

    # --- Student Stats ---
    student_frame = ttk.LabelFrame(content_frame, text="  Students  ",
                                    padding=10)
    student_frame.pack(fill='x', pady=5)
    _make_stat_label(student_frame, "Total Students",
                     stats['total_students'], 0, 0)
    _make_stat_label(student_frame, "Active Students",
                     stats['active_students'], 0, 1)

    # --- Room Stats ---
    room_frame = ttk.LabelFrame(content_frame, text="  Rooms  ",
                                 padding=10)
    room_frame.pack(fill='x', pady=5)
    _make_stat_label(room_frame, "Total Rooms",
                     stats['total_rooms'], 0, 0)
    _make_stat_label(room_frame, "Occupied",
                     stats['occupied_rooms'], 0, 1)
    _make_stat_label(room_frame, "Vacant",
                     stats['vacant_rooms'], 0, 2)

    # --- Fee Stats ---
    fee_frame = ttk.LabelFrame(content_frame, text="  Fees  ",
                                padding=10)
    fee_frame.pack(fill='x', pady=5)
    _make_stat_label(fee_frame, "Total Fee Records",
                     stats['total_fees'], 0, 0)
    _make_stat_label(fee_frame, "Paid Amount",
                     f"Rs. {stats['paid_amount']:,.2f}", 1, 0)
    _make_stat_label(fee_frame, "Pending Amount",
                     f"Rs. {stats['pending_amount']:,.2f}", 1, 1)

    # --- Complaint Stats ---
    comp_frame = ttk.LabelFrame(content_frame, text="  Complaints  ",
                                 padding=10)
    comp_frame.pack(fill='x', pady=5)
    _make_stat_label(comp_frame, "Total Complaints",
                     stats['total_complaints'], 0, 0)
    _make_stat_label(comp_frame, "Open",
                     stats['open_complaints'], 0, 1)
    _make_stat_label(comp_frame, "Resolved",
                     stats['resolved_complaints'], 0, 2)

    # --- Attendance Stats ---
    att_frame = ttk.LabelFrame(content_frame, text="  Attendance  ",
                                padding=10)
    att_frame.pack(fill='x', pady=5)
    _make_stat_label(att_frame, "Total Records",
                     stats['total_attendance'], 0, 0)
    _make_stat_label(att_frame, "Overall Present %",
                     f"{stats['present_pct']}%", 0, 1)

    # --- Report generated timestamp ---
    ts_label = ttk.Label(content_frame,
                         text=f"Report generated: {date.today()}",
                         font=FONTS['small'])
    ts_label.pack(anchor='e', pady=(8, 0))


def _export_csv():
    """Export summary report to exports/system_report.csv."""
    stats = _gather_stats()

    # Determine export path relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = os.path.join(project_root, "exports")
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, "system_report.csv")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Category', 'Metric', 'Value'])
            writer.writerow(['Students', 'Total Students', stats['total_students']])
            writer.writerow(['Students', 'Active Students', stats['active_students']])
            writer.writerow(['Rooms', 'Total Rooms', stats['total_rooms']])
            writer.writerow(['Rooms', 'Occupied Rooms', stats['occupied_rooms']])
            writer.writerow(['Rooms', 'Vacant Rooms', stats['vacant_rooms']])
            writer.writerow(['Fees', 'Total Fee Records', stats['total_fees']])
            writer.writerow(['Fees', 'Paid Amount', stats['paid_amount']])
            writer.writerow(['Fees', 'Pending Amount', stats['pending_amount']])
            writer.writerow(['Complaints', 'Total Complaints', stats['total_complaints']])
            writer.writerow(['Complaints', 'Open', stats['open_complaints']])
            writer.writerow(['Complaints', 'Resolved', stats['resolved_complaints']])
            writer.writerow(['Attendance', 'Total Records', stats['total_attendance']])
            writer.writerow(['Attendance', 'Overall Present %', stats['present_pct']])
            writer.writerow(['Report', 'Generated Date', str(date.today())])

        messagebox.showinfo("Export Successful",
                            f"Report exported to:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Could not export report:\n{e}")
