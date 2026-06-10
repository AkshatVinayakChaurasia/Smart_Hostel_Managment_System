"""
Fee Management GUI for HostelHub.
Entity: 'fees', ID field: 'fee_id'
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui import (COLORS, FONTS, center_window, create_header,
                 create_treeview, populate_treeview, make_toolbar)
from database.db_handler import DataHandler


# ---------------------------------------------------------------------------
# Helper: auto-generate next fee ID like FEE001, FEE002, ...
# ---------------------------------------------------------------------------
def _next_fee_id():
    """Return the next available fee ID string."""
    fees = DataHandler.get_all("fees")
    max_num = 0
    for f in fees:
        fid = f.get("fee_id", "")
        if fid.startswith("FEE"):
            try:
                num = int(fid[3:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"FEE{max_num + 1:03d}"


# ---------------------------------------------------------------------------
# Build rows for the treeview from a list of fee records
# ---------------------------------------------------------------------------
def _build_rows(fees):
    """Convert fee records into treeview rows."""
    rows = []
    for f in fees:
        rows.append((
            f.get("fee_id", ""),
            f.get("student_id", ""),
            f.get("student_name", ""),
            f.get("amount", 0),
            f.get("paid_amount", 0),
            f.get("fine_amount", 0),
            f.get("month", ""),
            f.get("payment_status", "Pending"),
        ))
    return rows


# ---------------------------------------------------------------------------
# Refresh treeview (all fees)
# ---------------------------------------------------------------------------
def _refresh(tree):
    """Reload all fee records into the treeview."""
    fees = DataHandler.get_all("fees")
    populate_treeview(tree, _build_rows(fees))


# ---------------------------------------------------------------------------
# Generate Fee dialog
# ---------------------------------------------------------------------------
def _generate_fee(parent, tree):
    """Open dialog to generate a new fee entry."""
    dlg = tk.Toplevel(parent)
    dlg.title("Generate Fee")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 420, 340)
    dlg.transient(parent)
    dlg.grab_set()

    new_id = _next_fee_id()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    labels = ["Fee ID:", "Student ID:", "Amount:", "Month:", "Due Date:"]
    for idx, lbl in enumerate(labels):
        tk.Label(frame, text=lbl, font=FONTS['body'],
                 bg=COLORS['bg'], fg=COLORS['text']).grid(
            row=idx, column=0, sticky='w', pady=5)

    # Fee ID (read-only)
    id_var = tk.StringVar(value=new_id)
    ttk.Entry(frame, textvariable=id_var, state='readonly', width=26).grid(
        row=0, column=1, pady=5, padx=6)

    stu_var = tk.StringVar()
    ttk.Entry(frame, textvariable=stu_var, width=26).grid(
        row=1, column=1, pady=5, padx=6)

    amt_var = tk.StringVar()
    ttk.Entry(frame, textvariable=amt_var, width=26).grid(
        row=2, column=1, pady=5, padx=6)

    month_var = tk.StringVar()
    ttk.Entry(frame, textvariable=month_var, width=26).grid(
        row=3, column=1, pady=5, padx=6)

    due_var = tk.StringVar()
    ttk.Entry(frame, textvariable=due_var, width=26).grid(
        row=4, column=1, pady=5, padx=6)

    # Hint labels
    tk.Label(frame, text="(e.g. June 2026)", font=FONTS['small'],
             bg=COLORS['bg'], fg='#95a5a6').grid(
        row=3, column=2, sticky='w')
    tk.Label(frame, text="(YYYY-MM-DD)", font=FONTS['small'],
             bg=COLORS['bg'], fg='#95a5a6').grid(
        row=4, column=2, sticky='w')

    def _save():
        stu_id = stu_var.get().strip()
        amount_str = amt_var.get().strip()
        month = month_var.get().strip()
        due_date = due_var.get().strip()

        if not stu_id or not amount_str or not month or not due_date:
            messagebox.showwarning("Missing Info",
                                   "All fields are required.", parent=dlg)
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Amount",
                                   "Amount must be a positive number.",
                                   parent=dlg)
            return

        # Look up student name
        student = DataHandler.find_by_id("students", "student_id", stu_id)
        if not student:
            messagebox.showerror("Not Found",
                                 f"Student {stu_id} does not exist.",
                                 parent=dlg)
            return

        fee_record = {
            "fee_id": new_id,
            "student_id": stu_id,
            "student_name": student.get("name", ""),
            "amount": amount,
            "paid_amount": 0,
            "fine_amount": 0,
            "month": month,
            "due_date": due_date,
            "payment_date": "",
            "payment_status": "Pending",
            "receipt_number": "",
        }
        DataHandler.insert("fees", fee_record)
        messagebox.showinfo("Success",
                            f"Fee {new_id} generated for {stu_id}.",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.grid(row=5, column=0, columnspan=2, pady=14)
    ttk.Button(btn_frame, text="Generate", style="Accent.TButton",
               command=_save).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ---------------------------------------------------------------------------
# Record Payment dialog
# ---------------------------------------------------------------------------
def _record_payment(parent, tree):
    """Open dialog to record a payment against a selected fee."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection",
                               "Please select a fee record first.",
                               parent=parent)
        return

    fee_id = str(tree.item(selected[0])['values'][0])
    fee = DataHandler.find_by_id("fees", "fee_id", fee_id)
    if not fee:
        messagebox.showerror("Not Found", "Fee record not found.",
                             parent=parent)
        return

    amount = fee.get("amount", 0)
    paid = fee.get("paid_amount", 0)
    remaining = amount - paid

    if remaining <= 0:
        messagebox.showinfo("Fully Paid",
                            f"Fee {fee_id} is already fully paid.",
                            parent=parent)
        return

    dlg = tk.Toplevel(parent)
    dlg.title(f"Record Payment - {fee_id}")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 380, 300)
    dlg.transient(parent)
    dlg.grab_set()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    # Show fee summary info
    info_lines = [
        f"Fee ID: {fee_id}",
        f"Student: {fee.get('student_id', '')} - {fee.get('student_name', '')}",
        f"Total Amount: {amount}",
        f"Already Paid: {paid}",
        f"Remaining: {remaining}",
    ]
    for line in info_lines:
        tk.Label(frame, text=line, font=FONTS['body'],
                 bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w', pady=2)

    # Payment amount entry
    tk.Label(frame, text="Payment Amount:", font=FONTS['body'],
             bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w', pady=(10, 2))
    pay_var = tk.StringVar()
    ttk.Entry(frame, textvariable=pay_var, width=20).pack(anchor='w')

    # Optional receipt number
    tk.Label(frame, text="Receipt Number (optional):", font=FONTS['body'],
             bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w', pady=(6, 2))
    receipt_var = tk.StringVar()
    ttk.Entry(frame, textvariable=receipt_var, width=20).pack(anchor='w')

    def _save():
        pay_str = pay_var.get().strip()
        try:
            payment = float(pay_str)
            if payment <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid",
                                   "Enter a valid positive payment amount.",
                                   parent=dlg)
            return

        # Check overpayment
        if paid + payment > amount:
            messagebox.showwarning("Overpayment",
                                   f"Payment cannot exceed remaining "
                                   f"balance of {remaining}.",
                                   parent=dlg)
            return

        new_paid = paid + payment
        fee["paid_amount"] = new_paid
        fee["payment_status"] = "Paid" if new_paid >= amount else "Partial"

        receipt = receipt_var.get().strip()
        if receipt:
            fee["receipt_number"] = receipt

        # Record today as payment date
        from datetime import date as dt_date
        fee["payment_date"] = str(dt_date.today())

        DataHandler.update("fees", "fee_id", fee_id, fee)
        messagebox.showinfo("Payment Recorded",
                            f"Payment of {payment} recorded for {fee_id}.\n"
                            f"Status: {fee['payment_status']}",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Record Payment", style="Accent.TButton",
               command=_save).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ---------------------------------------------------------------------------
# View Pending fees only
# ---------------------------------------------------------------------------
def _view_pending(tree):
    """Filter the treeview to show only unpaid / partial fees."""
    fees = DataHandler.get_all("fees")
    pending = [f for f in fees if f.get("payment_status", "") != "Paid"]
    populate_treeview(tree, _build_rows(pending))


# ===================================================================
# PUBLIC: Admin view
# ===================================================================
def open_fee_window(parent, user):
    """Open Fee Management window (Admin view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - Fee Management")
    win.configure(bg=COLORS['bg'])
    center_window(win, 1020, 540)
    win.transient(parent)
    win.grab_set()

    # Header
    create_header(win, "Fee Management")

    # Toolbar
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Generate Fee", style="Accent.TButton",
               command=lambda: _generate_fee(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Record Payment",
               command=lambda: _record_payment(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="View Pending",
               command=lambda: _view_pending(tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _refresh(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # Treeview
    columns = ('fee_id', 'stu_id', 'name', 'amount',
               'paid', 'fine', 'month', 'status')
    headings = ('Fee ID', 'Student ID', 'Name', 'Amount',
                'Paid', 'Fine', 'Month', 'Status')
    widths = (80, 90, 130, 80, 80, 60, 100, 80)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh(tree)
    win.wait_window()


# ===================================================================
# PUBLIC: Student view -- my fees
# ===================================================================
def open_my_fees(parent, user):
    """Show fees for the logged-in student only."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - My Fees")
    win.configure(bg=COLORS['bg'])
    center_window(win, 900, 460)
    win.transient(parent)
    win.grab_set()

    create_header(win, "My Fees")

    stu_id = user.get("username", "")

    # Toolbar (minimal)
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _load_my_fees()).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # Treeview
    columns = ('fee_id', 'amount', 'paid', 'fine',
               'month', 'due', 'pay_date', 'status')
    headings = ('Fee ID', 'Amount', 'Paid', 'Fine',
                'Month', 'Due Date', 'Payment Date', 'Status')
    widths = (80, 80, 80, 60, 100, 100, 100, 80)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    def _load_my_fees():
        fees = DataHandler.get_all("fees")
        my_fees = [f for f in fees if f.get("student_id") == stu_id]
        rows = []
        for f in my_fees:
            rows.append((
                f.get("fee_id", ""),
                f.get("amount", 0),
                f.get("paid_amount", 0),
                f.get("fine_amount", 0),
                f.get("month", ""),
                f.get("due_date", ""),
                f.get("payment_date", ""),
                f.get("payment_status", "Pending"),
            ))
        populate_treeview(tree, rows)

        # Update summary
        total = sum(f.get("amount", 0) for f in my_fees)
        paid_total = sum(f.get("paid_amount", 0) for f in my_fees)
        pending = total - paid_total
        summary_lbl.config(
            text=f"  Total: {total}  |  Paid: {paid_total}  |  Pending: {pending}")

    # Summary bar at the bottom
    summary_frame = tk.Frame(win, bg=COLORS['card'], bd=0,
                             highlightbackground=COLORS['border'],
                             highlightthickness=1)
    summary_frame.pack(fill='x', padx=12, pady=(0, 10))
    summary_lbl = tk.Label(summary_frame, text="  Total: 0  |  Paid: 0  |  Pending: 0",
                           font=FONTS['subhead'], bg=COLORS['card'],
                           fg=COLORS['primary'])
    summary_lbl.pack(anchor='w', padx=8, pady=6)

    _load_my_fees()
    win.wait_window()
