"""
Notice Board GUI for HostelHub.
Entity: 'notices', ID field: 'notice_id'
Combined view for admin and student roles.
Admin can add and delete notices; all users can view details.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui import (COLORS, FONTS, create_header, create_treeview,
                 populate_treeview, make_toolbar, center_window)
from database.db_handler import DataHandler

# --- Constants ---
CATEGORIES = ['General', 'Academic', 'Event', 'Maintenance', 'Emergency']


def _next_notice_id():
    """Generate next notice ID like NOT001, NOT002, etc."""
    records = DataHandler.get_all("notices")
    if not records:
        return "NOT001"
    nums = []
    for r in records:
        nid = r.get('notice_id', '')
        if nid.startswith('NOT') and nid[3:].isdigit():
            nums.append(int(nid[3:]))
    next_num = max(nums) + 1 if nums else 1
    return f"NOT{next_num:03d}"


def _refresh_notices(tree):
    """Load all notices into the treeview."""
    records = DataHandler.get_all("notices")
    rows = []
    for r in records:
        rows.append((
            r.get('notice_id', ''),
            r.get('title', ''),
            r.get('category', ''),
            r.get('posted_by', ''),
            r.get('posted_date', '')
        ))
    populate_treeview(tree, rows)


# ---------------------------------------------------------------
# Combined View (Admin + Student)
# ---------------------------------------------------------------
def open_notice_window(parent, user):
    """Open Notice Board window (combined admin/student view)."""
    role = user.get('role', 'student')

    win = tk.Toplevel(parent)
    win.title("HostelHub - Notice Board")
    win.configure(bg=COLORS['bg'])
    center_window(win, 900, 540)
    win.transient(parent)
    win.grab_set()

    create_header(win, "Notice Board")

    # --- Toolbar ---
    toolbar = make_toolbar(win)

    # Admin-only buttons
    if role == 'admin':
        ttk.Button(toolbar, text="Add Notice", style="Accent.TButton",
                   command=lambda: _add_notice(win, tree, user)).pack(
                       side='left', padx=3)
        ttk.Button(toolbar, text="Delete Notice",
                   command=lambda: _delete_notice(win, tree)).pack(
                       side='left', padx=3)

    ttk.Button(toolbar, text="View Details",
               command=lambda: _view_notice_details(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _refresh_notices(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # --- Treeview ---
    columns = ('nid', 'title', 'category', 'posted_by', 'date')
    headings = ('Notice ID', 'Title', 'Category', 'Posted By', 'Date')
    widths = (90, 250, 110, 130, 100)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh_notices(tree)
    win.wait_window()


def _add_notice(parent, tree, user):
    """Dialog to add a new notice (Admin only)."""
    dlg = tk.Toplevel(parent)
    dlg.title("Add New Notice")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 450, 380)
    dlg.transient(parent)
    dlg.grab_set()

    frame = ttk.Frame(dlg)
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    ttk.Label(frame, text="Add New Notice",
              font=FONTS['subhead']).grid(row=0, column=0, columnspan=2, pady=8)

    ttk.Label(frame, text="Title:").grid(row=1, column=0, sticky='w', pady=5)
    title_var = tk.StringVar()
    ttk.Entry(frame, textvariable=title_var, width=30).grid(row=1, column=1, sticky='w')

    ttk.Label(frame, text="Category:").grid(row=2, column=0, sticky='w', pady=5)
    cat_var = tk.StringVar()
    ttk.Combobox(frame, textvariable=cat_var, values=CATEGORIES,
                 state='readonly', width=27).grid(row=2, column=1, sticky='w')

    ttk.Label(frame, text="Content:").grid(row=3, column=0, sticky='nw', pady=5)
    content_text = tk.Text(frame, width=30, height=6, font=FONTS['entry'])
    content_text.grid(row=3, column=1, sticky='w', pady=5)

    def save():
        title = title_var.get().strip()
        category = cat_var.get().strip()
        content = content_text.get('1.0', 'end').strip()

        if not title:
            messagebox.showwarning("Missing Field", "Please enter a title.")
            return
        if not category:
            messagebox.showwarning("Missing Field", "Please select a category.")
            return
        if not content:
            messagebox.showwarning("Missing Field", "Please enter content.")
            return

        new_notice = {
            'notice_id': _next_notice_id(),
            'title': title,
            'content': content,
            'category': category,
            'posted_by': user.get('name', user.get('username', 'Admin')),
            'posted_date': str(date.today()),
            'is_active': True
        }
        DataHandler.insert("notices", new_notice)
        messagebox.showinfo("Posted",
                            f"Notice {new_notice['notice_id']} posted successfully.")
        dlg.destroy()
        _refresh_notices(tree)

    ttk.Button(frame, text="Post Notice", style="Accent.TButton",
               command=save).grid(row=4, column=0, columnspan=2, pady=12)

    dlg.wait_window()


def _delete_notice(parent, tree):
    """Delete the selected notice (Admin only)."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a notice first.")
        return

    values = tree.item(selected[0], 'values')
    notice_id = values[0]

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete notice '{notice_id}'?")
    if not confirm:
        return

    DataHandler.delete("notices", "notice_id", notice_id)
    messagebox.showinfo("Deleted", f"Notice {notice_id} deleted.")
    _refresh_notices(tree)


def _view_notice_details(tree):
    """Show full details of the selected notice."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a notice first.")
        return

    values = tree.item(selected[0], 'values')
    notice_id = values[0]
    record = DataHandler.find_by_id("notices", "notice_id", notice_id)
    if not record:
        messagebox.showerror("Error", "Notice record not found.")
        return

    details = (
        f"Notice ID: {record.get('notice_id', '')}\n"
        f"Title: {record.get('title', '')}\n"
        f"Category: {record.get('category', '')}\n"
        f"Posted By: {record.get('posted_by', '')}\n"
        f"Date: {record.get('posted_date', '')}\n"
        f"{'=' * 40}\n"
        f"{record.get('content', '')}"
    )
    messagebox.showinfo("Notice Details", details)
