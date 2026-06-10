"""
Student Management GUI for HostelHub.
Entity: 'students', ID field: 'student_id'
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui import (COLORS, FONTS, center_window, create_header,
                 create_treeview, populate_treeview, make_toolbar)
from database.db_handler import DataHandler


# ---------------------------------------------------------------------------
# Helper: auto-generate next student ID like STU001, STU002, ...
# ---------------------------------------------------------------------------
def _next_student_id():
    """Return the next available student ID string."""
    students = DataHandler.get_all("students")
    max_num = 0
    for s in students:
        sid = s.get("student_id", "")
        if sid.startswith("STU"):
            try:
                num = int(sid[3:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"STU{max_num + 1:03d}"


# ---------------------------------------------------------------------------
# Refresh treeview
# ---------------------------------------------------------------------------
def _refresh(tree):
    """Reload all students into the treeview."""
    students = DataHandler.get_all("students")
    rows = []
    for s in students:
        rows.append((
            s.get("student_id", ""),
            s.get("name", ""),
            s.get("course", ""),
            s.get("year", ""),
            s.get("mobile", ""),
            s.get("room_number", ""),
            "Yes" if s.get("is_active", True) else "No",
            s.get("joined_date", ""),
        ))
    populate_treeview(tree, rows)


# ---------------------------------------------------------------------------
# Register (Add) dialog
# ---------------------------------------------------------------------------
def _register_student(parent, tree):
    """Open a dialog to register a new student."""
    dlg = tk.Toplevel(parent)
    dlg.title("Register New Student")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 420, 380)
    dlg.transient(parent)
    dlg.grab_set()

    new_id = _next_student_id()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    # --- fields ---
    labels = ["Student ID:", "Name:", "Course:", "Year (1-4):",
              "Mobile (10 digits):", "Address:"]

    for idx, lbl_text in enumerate(labels):
        tk.Label(frame, text=lbl_text, font=FONTS['body'],
                 bg=COLORS['bg'], fg=COLORS['text']).grid(
            row=idx, column=0, sticky='w', pady=4)

    # Student ID (read-only)
    id_var = tk.StringVar(value=new_id)
    ttk.Entry(frame, textvariable=id_var, state='readonly', width=28).grid(
        row=0, column=1, pady=4, padx=6)

    name_var = tk.StringVar()
    ttk.Entry(frame, textvariable=name_var, width=28).grid(
        row=1, column=1, pady=4, padx=6)

    course_var = tk.StringVar()
    ttk.Entry(frame, textvariable=course_var, width=28).grid(
        row=2, column=1, pady=4, padx=6)

    year_var = tk.StringVar()
    ttk.Combobox(frame, textvariable=year_var, width=26,
                 values=["1", "2", "3", "4"], state='readonly').grid(
        row=3, column=1, pady=4, padx=6)

    mobile_var = tk.StringVar()
    ttk.Entry(frame, textvariable=mobile_var, width=28).grid(
        row=4, column=1, pady=4, padx=6)

    addr_var = tk.StringVar()
    ttk.Entry(frame, textvariable=addr_var, width=28).grid(
        row=5, column=1, pady=4, padx=6)

    def _save():
        name = name_var.get().strip()
        course = course_var.get().strip()
        year = year_var.get().strip()
        mobile = mobile_var.get().strip()
        address = addr_var.get().strip()

        # Validation
        if not name or not course or not year:
            messagebox.showwarning("Missing Info",
                                   "Name, Course and Year are required.",
                                   parent=dlg)
            return
        if not mobile.isdigit() or len(mobile) != 10:
            messagebox.showwarning("Invalid Mobile",
                                   "Mobile must be exactly 10 digits.",
                                   parent=dlg)
            return

        student_record = {
            "student_id": new_id,
            "name": name,
            "course": course,
            "year": int(year),
            "mobile": mobile,
            "address": address,
            "room_number": "Not Allocated",
            "joined_date": str(date.today()),
            "is_active": True,
        }
        DataHandler.insert("students", student_record)

        # Also create a user account for the student
        user_record = {
            "username": new_id,
            "password": new_id.lower(),
            "role": "student",
            "name": name,
        }
        DataHandler.insert("users", user_record)

        messagebox.showinfo("Success",
                            f"Student {new_id} registered successfully!",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.grid(row=6, column=0, columnspan=2, pady=14)
    ttk.Button(btn_frame, text="Save", style="Accent.TButton",
               command=_save).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ---------------------------------------------------------------------------
# View Details dialog
# ---------------------------------------------------------------------------
def _view_details(parent, tree):
    """Show full details of the selected student."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection",
                               "Please select a student first.", parent=parent)
        return
    sid = tree.item(selected[0])['values'][0]
    record = DataHandler.find_by_id("students", "student_id", str(sid))
    if not record:
        messagebox.showerror("Not Found", "Student record not found.",
                             parent=parent)
        return

    dlg = tk.Toplevel(parent)
    dlg.title(f"Student Details - {sid}")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 400, 340)
    dlg.transient(parent)
    dlg.grab_set()

    frame = tk.Frame(dlg, bg=COLORS['card'], bd=0,
                     highlightbackground=COLORS['border'],
                     highlightthickness=1)
    frame.pack(fill='both', expand=True, padx=16, pady=16)

    fields = [
        ("Student ID", record.get("student_id", "")),
        ("Name", record.get("name", "")),
        ("Course", record.get("course", "")),
        ("Year", record.get("year", "")),
        ("Mobile", record.get("mobile", "")),
        ("Address", record.get("address", "")),
        ("Room", record.get("room_number", "")),
        ("Joined", record.get("joined_date", "")),
        ("Active", "Yes" if record.get("is_active", True) else "No"),
    ]
    for i, (label, value) in enumerate(fields):
        tk.Label(frame, text=f"{label}:", font=FONTS['body'],
                 bg=COLORS['card'], fg=COLORS['text'],
                 anchor='w').grid(row=i, column=0, sticky='w', padx=10, pady=3)
        tk.Label(frame, text=str(value), font=FONTS['body'],
                 bg=COLORS['card'], fg='#555555',
                 anchor='w').grid(row=i, column=1, sticky='w', padx=10, pady=3)

    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=8)
    dlg.wait_window()


# ---------------------------------------------------------------------------
# Update dialog
# ---------------------------------------------------------------------------
def _update_student(parent, tree):
    """Open dialog to edit the selected student."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection",
                               "Please select a student first.", parent=parent)
        return
    sid = tree.item(selected[0])['values'][0]
    record = DataHandler.find_by_id("students", "student_id", str(sid))
    if not record:
        messagebox.showerror("Not Found", "Student record not found.",
                             parent=parent)
        return

    dlg = tk.Toplevel(parent)
    dlg.title(f"Update Student - {sid}")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 420, 340)
    dlg.transient(parent)
    dlg.grab_set()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    tk.Label(frame, text=f"Student ID: {sid}", font=FONTS['subhead'],
             bg=COLORS['bg'], fg=COLORS['primary']).grid(
        row=0, column=0, columnspan=2, sticky='w', pady=6)

    labels = ["Name:", "Course:", "Year (1-4):", "Mobile:", "Address:"]
    for idx, lbl in enumerate(labels, start=1):
        tk.Label(frame, text=lbl, font=FONTS['body'],
                 bg=COLORS['bg'], fg=COLORS['text']).grid(
            row=idx, column=0, sticky='w', pady=4)

    name_var = tk.StringVar(value=record.get("name", ""))
    ttk.Entry(frame, textvariable=name_var, width=28).grid(
        row=1, column=1, pady=4, padx=6)

    course_var = tk.StringVar(value=record.get("course", ""))
    ttk.Entry(frame, textvariable=course_var, width=28).grid(
        row=2, column=1, pady=4, padx=6)

    year_var = tk.StringVar(value=str(record.get("year", "")))
    ttk.Combobox(frame, textvariable=year_var, width=26,
                 values=["1", "2", "3", "4"], state='readonly').grid(
        row=3, column=1, pady=4, padx=6)

    mobile_var = tk.StringVar(value=record.get("mobile", ""))
    ttk.Entry(frame, textvariable=mobile_var, width=28).grid(
        row=4, column=1, pady=4, padx=6)

    addr_var = tk.StringVar(value=record.get("address", ""))
    ttk.Entry(frame, textvariable=addr_var, width=28).grid(
        row=5, column=1, pady=4, padx=6)

    def _save():
        name = name_var.get().strip()
        course = course_var.get().strip()
        year = year_var.get().strip()
        mobile = mobile_var.get().strip()
        address = addr_var.get().strip()
        if not name or not course or not year:
            messagebox.showwarning("Missing Info",
                                   "Name, Course and Year are required.",
                                   parent=dlg)
            return
        if not mobile.isdigit() or len(mobile) != 10:
            messagebox.showwarning("Invalid Mobile",
                                   "Mobile must be exactly 10 digits.",
                                   parent=dlg)
            return

        record["name"] = name
        record["course"] = course
        record["year"] = int(year)
        record["mobile"] = mobile
        record["address"] = address

        DataHandler.update("students", "student_id", str(sid), record)
        messagebox.showinfo("Updated",
                            f"Student {sid} updated successfully!",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.grid(row=6, column=0, columnspan=2, pady=14)
    ttk.Button(btn_frame, text="Save", style="Accent.TButton",
               command=_save).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
def _delete_student(parent, tree):
    """Delete the selected student after confirmation."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection",
                               "Please select a student first.", parent=parent)
        return
    sid = tree.item(selected[0])['values'][0]
    if not messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete {sid}?",
                               parent=parent):
        return
    DataHandler.delete("students", "student_id", str(sid))
    messagebox.showinfo("Deleted", f"Student {sid} has been deleted.",
                        parent=parent)
    _refresh(tree)


# ===================================================================
# PUBLIC: Admin view
# ===================================================================
def open_student_window(parent, user):
    """Open Student Management window (Admin view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - Student Management")
    win.configure(bg=COLORS['bg'])
    center_window(win, 980, 560)
    win.transient(parent)
    win.grab_set()

    # Header
    create_header(win, "Student Management")

    # Toolbar
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Register New", style="Accent.TButton",
               command=lambda: _register_student(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="View Details",
               command=lambda: _view_details(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Update",
               command=lambda: _update_student(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Delete",
               command=lambda: _delete_student(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _refresh(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # Treeview
    columns = ('sid', 'name', 'course', 'year', 'mobile',
               'room', 'active', 'joined')
    headings = ('Student ID', 'Name', 'Course', 'Year', 'Mobile',
                'Room', 'Active', 'Joined')
    widths = (90, 140, 110, 50, 100, 110, 60, 100)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh(tree)
    win.wait_window()


# ===================================================================
# PUBLIC: Student profile (read-only)
# ===================================================================
def open_student_profile(parent, user):
    """Show the logged-in student's own profile."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - My Profile")
    win.configure(bg=COLORS['bg'])
    center_window(win, 440, 400)
    win.transient(parent)
    win.grab_set()

    create_header(win, "My Profile")

    student = DataHandler.find_by_id("students", "student_id",
                                     user.get("username", ""))

    frame = tk.Frame(win, bg=COLORS['card'], bd=0,
                     highlightbackground=COLORS['border'],
                     highlightthickness=1)
    frame.pack(fill='both', expand=True, padx=20, pady=14)

    if not student:
        tk.Label(frame, text="Profile not found.",
                 font=FONTS['body'], bg=COLORS['card'],
                 fg=COLORS['danger']).pack(pady=30)
    else:
        fields = [
            ("Student ID", student.get("student_id", "")),
            ("Name", student.get("name", "")),
            ("Course", student.get("course", "")),
            ("Year", student.get("year", "")),
            ("Mobile", student.get("mobile", "")),
            ("Address", student.get("address", "")),
            ("Room", student.get("room_number", "")),
            ("Joined", student.get("joined_date", "")),
            ("Active", "Yes" if student.get("is_active") else "No"),
        ]
        for i, (label, value) in enumerate(fields):
            tk.Label(frame, text=f"{label}:", font=FONTS['body'],
                     bg=COLORS['card'], fg=COLORS['text'],
                     anchor='w').grid(row=i, column=0, sticky='w',
                                      padx=12, pady=4)
            tk.Label(frame, text=str(value), font=FONTS['body'],
                     bg=COLORS['card'], fg='#555555',
                     anchor='w').grid(row=i, column=1, sticky='w',
                                      padx=12, pady=4)

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)
    win.wait_window()
