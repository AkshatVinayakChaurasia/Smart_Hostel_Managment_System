"""
Complaint Management GUI for HostelHub.
Entity: 'complaints', ID field: 'complaint_id'
Admin view: manage all complaints, update status, view details.
Student view: file new complaints, view own complaints.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui import (COLORS, FONTS, create_header, create_treeview,
                 populate_treeview, make_toolbar, center_window)
from database.db_handler import DataHandler

# --- Constants ---
COMPLAINT_TYPES = ['Electricity', 'Plumbing', 'Furniture', 'Cleanliness',
                   'Food', 'Security', 'Noise', 'Other']
STATUSES = ['Open', 'In Progress', 'Resolved']

# Priority auto-mapping based on complaint type
PRIORITY_MAP = {
    'Electricity': 'High', 'Plumbing': 'High', 'Security': 'High',
    'Furniture': 'Medium', 'Food': 'Medium',
    'Cleanliness': 'Low', 'Noise': 'Low', 'Other': 'Low'
}


def _next_complaint_id():
    """Generate next complaint ID like CMP001, CMP002, etc."""
    records = DataHandler.get_all("complaints")
    if not records:
        return "CMP001"
    nums = []
    for r in records:
        cid = r.get('complaint_id', '')
        if cid.startswith('CMP') and cid[3:].isdigit():
            nums.append(int(cid[3:]))
    next_num = max(nums) + 1 if nums else 1
    return f"CMP{next_num:03d}"


def _refresh_tree(tree, records):
    """Populate treeview with complaint records."""
    rows = []
    for r in records:
        rows.append((
            r.get('complaint_id', ''),
            r.get('student_name', r.get('student_id', '')),
            r.get('complaint_type', ''),
            r.get('priority', ''),
            r.get('status', ''),
            r.get('filed_date', '')
        ))
    populate_treeview(tree, rows)


# ---------------------------------------------------------------
# Admin View
# ---------------------------------------------------------------
def open_complaint_window(parent, user):
    """Open Complaint Management window (Admin view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - Complaint Management")
    win.configure(bg=COLORS['bg'])
    center_window(win, 960, 580)
    win.transient(parent)
    win.grab_set()

    create_header(win, "Complaint Management")

    # --- Toolbar ---
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Update Status", style="Accent.TButton",
               command=lambda: _update_status(win, tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="View Details",
               command=lambda: _view_details(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _load_all(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Treeview ---
    columns = ('cid', 'student', 'type', 'priority', 'status', 'date')
    headings = ('ID', 'Student', 'Type', 'Priority', 'Status', 'Date')
    widths = (80, 150, 110, 80, 100, 100)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _load_all(tree)
    win.wait_window()


def _load_all(tree):
    """Load all complaints into the treeview."""
    records = DataHandler.get_all("complaints")
    _refresh_tree(tree, records)


def _update_status(parent, tree):
    """Dialog to update complaint status and add admin remarks."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a complaint first.")
        return

    values = tree.item(selected[0], 'values')
    complaint_id = values[0]
    record = DataHandler.find_by_id("complaints", "complaint_id", complaint_id)
    if not record:
        messagebox.showerror("Error", "Complaint record not found.")
        return

    dlg = tk.Toplevel(parent)
    dlg.title("Update Complaint Status")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 400, 300)
    dlg.transient(parent)
    dlg.grab_set()

    frame = ttk.Frame(dlg)
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    ttk.Label(frame, text=f"Complaint: {complaint_id}",
              font=FONTS['subhead']).grid(row=0, column=0, columnspan=2, pady=5)

    ttk.Label(frame, text="Current Status:").grid(row=1, column=0, sticky='w', pady=4)
    ttk.Label(frame, text=record.get('status', '')).grid(row=1, column=1, sticky='w')

    ttk.Label(frame, text="New Status:").grid(row=2, column=0, sticky='w', pady=4)
    status_var = tk.StringVar(value=record.get('status', 'Open'))
    status_combo = ttk.Combobox(frame, textvariable=status_var,
                                values=STATUSES, state='readonly', width=18)
    status_combo.grid(row=2, column=1, sticky='w')

    ttk.Label(frame, text="Admin Remarks:").grid(row=3, column=0, sticky='nw', pady=4)
    remarks_text = tk.Text(frame, width=25, height=4, font=FONTS['entry'])
    remarks_text.grid(row=3, column=1, sticky='w', pady=4)
    remarks_text.insert('1.0', record.get('admin_remarks', ''))

    def save():
        new_status = status_var.get()
        remarks = remarks_text.get('1.0', 'end').strip()
        record['status'] = new_status
        record['admin_remarks'] = remarks
        if new_status == 'Resolved' and not record.get('resolved_date'):
            record['resolved_date'] = str(date.today())
        DataHandler.update("complaints", "complaint_id", complaint_id, record)
        messagebox.showinfo("Updated", f"Complaint {complaint_id} status set to '{new_status}'.")
        dlg.destroy()
        _load_all(tree)

    ttk.Button(frame, text="Save", style="Accent.TButton",
               command=save).grid(row=4, column=0, columnspan=2, pady=12)

    dlg.wait_window()


def _view_details(tree):
    """Show full details of the selected complaint."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a complaint first.")
        return

    values = tree.item(selected[0], 'values')
    complaint_id = values[0]
    record = DataHandler.find_by_id("complaints", "complaint_id", complaint_id)
    if not record:
        messagebox.showerror("Error", "Complaint record not found.")
        return

    details = (
        f"Complaint ID: {record.get('complaint_id', '')}\n"
        f"Student ID: {record.get('student_id', '')}\n"
        f"Student Name: {record.get('student_name', '')}\n"
        f"Type: {record.get('complaint_type', '')}\n"
        f"Priority: {record.get('priority', '')}\n"
        f"Status: {record.get('status', '')}\n"
        f"Filed Date: {record.get('filed_date', '')}\n"
        f"Resolved Date: {record.get('resolved_date', 'N/A')}\n"
        f"Description: {record.get('description', '')}\n"
        f"Admin Remarks: {record.get('admin_remarks', 'N/A')}"
    )
    messagebox.showinfo("Complaint Details", details)


# ---------------------------------------------------------------
# Student View
# ---------------------------------------------------------------
def open_my_complaints(parent, user):
    """Open My Complaints window (Student view)."""
    student_id = user.get('username', '')
    student_name = user.get('name', student_id)

    win = tk.Toplevel(parent)
    win.title("HostelHub - My Complaints")
    win.configure(bg=COLORS['bg'])
    center_window(win, 920, 550)
    win.transient(parent)
    win.grab_set()

    create_header(win, "My Complaints")

    # --- Toolbar ---
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="File New Complaint", style="Accent.TButton",
               command=lambda: _file_complaint(win, tree, student_id,
                                                student_name)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="View Details",
               command=lambda: _view_details(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _load_student(tree, student_id)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Treeview ---
    columns = ('cid', 'student', 'type', 'priority', 'status', 'date')
    headings = ('ID', 'Student', 'Type', 'Priority', 'Status', 'Date')
    widths = (80, 140, 110, 80, 100, 100)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _load_student(tree, student_id)
    win.wait_window()


def _load_student(tree, student_id):
    """Load complaints for a specific student."""
    all_records = DataHandler.get_all("complaints")
    filtered = [r for r in all_records if r.get('student_id') == student_id]
    _refresh_tree(tree, filtered)


def _file_complaint(parent, tree, student_id, student_name):
    """Dialog to file a new complaint."""
    dlg = tk.Toplevel(parent)
    dlg.title("File New Complaint")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 420, 320)
    dlg.transient(parent)
    dlg.grab_set()

    frame = ttk.Frame(dlg)
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    ttk.Label(frame, text="File New Complaint",
              font=FONTS['subhead']).grid(row=0, column=0, columnspan=2, pady=8)

    ttk.Label(frame, text="Complaint Type:").grid(row=1, column=0, sticky='w', pady=5)
    type_var = tk.StringVar()
    type_combo = ttk.Combobox(frame, textvariable=type_var,
                              values=COMPLAINT_TYPES, state='readonly', width=20)
    type_combo.grid(row=1, column=1, sticky='w')

    ttk.Label(frame, text="Description:").grid(row=2, column=0, sticky='nw', pady=5)
    desc_text = tk.Text(frame, width=28, height=5, font=FONTS['entry'])
    desc_text.grid(row=2, column=1, sticky='w', pady=5)

    def submit():
        comp_type = type_var.get().strip()
        description = desc_text.get('1.0', 'end').strip()
        if not comp_type:
            messagebox.showwarning("Missing Field", "Please select a complaint type.")
            return
        if not description:
            messagebox.showwarning("Missing Field", "Please enter a description.")
            return

        new_record = {
            'complaint_id': _next_complaint_id(),
            'student_id': student_id,
            'student_name': student_name,
            'complaint_type': comp_type,
            'description': description,
            'priority': PRIORITY_MAP.get(comp_type, 'Low'),
            'status': 'Open',
            'filed_date': str(date.today()),
            'resolved_date': '',
            'admin_remarks': ''
        }
        DataHandler.insert("complaints", new_record)
        messagebox.showinfo("Filed",
                            f"Complaint {new_record['complaint_id']} filed successfully.")
        dlg.destroy()
        _load_student(tree, student_id)

    ttk.Button(frame, text="Submit", style="Accent.TButton",
               command=submit).grid(row=3, column=0, columnspan=2, pady=12)

    dlg.wait_window()
