"""
Room Management GUI for HostelHub.
Entity: 'rooms', ID field: 'room_number'
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui import (COLORS, FONTS, center_window, create_header,
                 create_treeview, populate_treeview, make_toolbar)
from database.db_handler import DataHandler


# ---------------------------------------------------------------------------
# Refresh treeview
# ---------------------------------------------------------------------------
def _refresh(tree):
    """Reload all rooms into the treeview."""
    rooms = DataHandler.get_all("rooms")
    rows = []
    for r in rooms:
        capacity = r.get("capacity", 0)
        occupied = r.get("occupied", 0)
        vacant = capacity - occupied
        rows.append((
            r.get("room_number", ""),
            r.get("room_type", ""),
            r.get("floor", ""),
            capacity,
            occupied,
            vacant,
            r.get("status", ""),
        ))
    populate_treeview(tree, rows)


# ---------------------------------------------------------------------------
# Allocate Room dialog
# ---------------------------------------------------------------------------
def _allocate_room(parent, tree):
    """Open dialog to allocate a student to a room."""
    dlg = tk.Toplevel(parent)
    dlg.title("Allocate Room")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 380, 220)
    dlg.transient(parent)
    dlg.grab_set()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    tk.Label(frame, text="Room Number:", font=FONTS['body'],
             bg=COLORS['bg'], fg=COLORS['text']).grid(
        row=0, column=0, sticky='w', pady=6)
    room_var = tk.StringVar()
    ttk.Entry(frame, textvariable=room_var, width=22).grid(
        row=0, column=1, pady=6, padx=6)

    tk.Label(frame, text="Student ID:", font=FONTS['body'],
             bg=COLORS['bg'], fg=COLORS['text']).grid(
        row=1, column=0, sticky='w', pady=6)
    stu_var = tk.StringVar()
    ttk.Entry(frame, textvariable=stu_var, width=22).grid(
        row=1, column=1, pady=6, padx=6)

    def _save():
        room_no = room_var.get().strip()
        stu_id = stu_var.get().strip()
        if not room_no or not stu_id:
            messagebox.showwarning("Missing Info",
                                   "Both Room Number and Student ID are required.",
                                   parent=dlg)
            return

        # 1. Find room and validate capacity
        room = DataHandler.find_by_id("rooms", "room_number", room_no)
        if not room:
            messagebox.showerror("Not Found",
                                 f"Room {room_no} does not exist.",
                                 parent=dlg)
            return
        if room.get("occupied", 0) >= room.get("capacity", 0):
            messagebox.showerror("Room Full",
                                 f"Room {room_no} is already at full capacity.",
                                 parent=dlg)
            return

        # 2. Find student and validate no existing allocation
        student = DataHandler.find_by_id("students", "student_id", stu_id)
        if not student:
            messagebox.showerror("Not Found",
                                 f"Student {stu_id} does not exist.",
                                 parent=dlg)
            return
        if student.get("room_number", "Not Allocated") != "Not Allocated":
            messagebox.showerror("Already Allocated",
                                 f"Student {stu_id} already has room "
                                 f"{student['room_number']}.",
                                 parent=dlg)
            return

        # 3. Update room: add occupant, increment occupied count
        occupants = room.get("occupants", [])
        occupants.append(stu_id)
        room["occupants"] = occupants
        room["occupied"] = room.get("occupied", 0) + 1
        DataHandler.update("rooms", "room_number", room_no, room)

        # 4. Update student's room_number
        student["room_number"] = room_no
        DataHandler.update("students", "student_id", stu_id, student)

        messagebox.showinfo("Success",
                            f"Student {stu_id} allocated to Room {room_no}.",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.grid(row=2, column=0, columnspan=2, pady=16)
    ttk.Button(btn_frame, text="Allocate", style="Accent.TButton",
               command=_save).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ---------------------------------------------------------------------------
# Vacate Room dialog
# ---------------------------------------------------------------------------
def _vacate_room(parent, tree):
    """Remove an occupant from the selected room."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection",
                               "Please select a room first.", parent=parent)
        return

    room_no = str(tree.item(selected[0])['values'][0])
    room = DataHandler.find_by_id("rooms", "room_number", room_no)
    if not room:
        messagebox.showerror("Not Found", "Room record not found.",
                             parent=parent)
        return

    occupants = room.get("occupants", [])
    if not occupants:
        messagebox.showinfo("Empty", f"Room {room_no} has no occupants.",
                            parent=parent)
        return

    # Dialog to pick which occupant to remove
    dlg = tk.Toplevel(parent)
    dlg.title(f"Vacate Room {room_no}")
    dlg.configure(bg=COLORS['bg'])
    center_window(dlg, 360, 200)
    dlg.transient(parent)
    dlg.grab_set()

    frame = tk.Frame(dlg, bg=COLORS['bg'])
    frame.pack(fill='both', expand=True, padx=20, pady=15)

    tk.Label(frame, text="Select occupant to remove:", font=FONTS['body'],
             bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w', pady=6)

    occ_var = tk.StringVar()
    occ_cb = ttk.Combobox(frame, textvariable=occ_var, width=24,
                          values=occupants, state='readonly')
    occ_cb.pack(pady=6)
    if occupants:
        occ_cb.current(0)

    def _do_vacate():
        stu_id = occ_var.get().strip()
        if not stu_id:
            messagebox.showwarning("No Selection",
                                   "Please select an occupant.", parent=dlg)
            return
        if not messagebox.askyesno("Confirm Vacate",
                                   f"Remove {stu_id} from Room {room_no}?",
                                   parent=dlg):
            return

        # Update room: remove occupant, decrement count
        occupants.remove(stu_id)
        room["occupants"] = occupants
        room["occupied"] = max(room.get("occupied", 1) - 1, 0)
        DataHandler.update("rooms", "room_number", room_no, room)

        # Update student: reset room to Not Allocated
        student = DataHandler.find_by_id("students", "student_id", stu_id)
        if student:
            student["room_number"] = "Not Allocated"
            DataHandler.update("students", "student_id", stu_id, student)

        messagebox.showinfo("Vacated",
                            f"Student {stu_id} removed from Room {room_no}.",
                            parent=dlg)
        dlg.destroy()
        _refresh(tree)

    btn_frame = tk.Frame(frame, bg=COLORS['bg'])
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="Vacate", style="Accent.TButton",
               command=_do_vacate).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Cancel",
               command=dlg.destroy).pack(side='left', padx=6)

    dlg.wait_window()


# ===================================================================
# PUBLIC: Admin view
# ===================================================================
def open_room_window(parent, user):
    """Open Room Management window (Admin view)."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - Room Management")
    win.configure(bg=COLORS['bg'])
    center_window(win, 950, 520)
    win.transient(parent)
    win.grab_set()

    # Header
    create_header(win, "Room Management")

    # Toolbar
    toolbar = make_toolbar(win)
    ttk.Button(toolbar, text="Allocate Room", style="Accent.TButton",
               command=lambda: _allocate_room(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Vacate",
               command=lambda: _vacate_room(win, tree)).pack(
        side='left', padx=3)
    ttk.Button(toolbar, text="Refresh",
               command=lambda: _refresh(tree)).pack(side='left', padx=3)
    ttk.Button(toolbar, text="Close",
               command=win.destroy).pack(side='right', padx=3)

    # Treeview
    columns = ('room_no', 'type', 'floor', 'capacity',
               'occupied', 'vacant', 'status')
    headings = ('Room No', 'Type', 'Floor', 'Capacity',
                'Occupied', 'Vacant', 'Status')
    widths = (90, 110, 60, 80, 80, 80, 100)
    tree, tree_frame = create_treeview(win, columns, headings, widths)
    tree_frame.pack(fill='both', expand=True, padx=12, pady=8)

    _refresh(tree)
    win.wait_window()


# ===================================================================
# PUBLIC: Student view -- my room
# ===================================================================
def open_my_room(parent, user):
    """Show the student's current room details."""
    win = tk.Toplevel(parent)
    win.title("HostelHub - My Room")
    win.configure(bg=COLORS['bg'])
    center_window(win, 420, 360)
    win.transient(parent)
    win.grab_set()

    create_header(win, "My Room")

    # Look up student record to find their room
    stu_id = user.get("username", "")
    student = DataHandler.find_by_id("students", "student_id", stu_id)

    frame = tk.Frame(win, bg=COLORS['card'], bd=0,
                     highlightbackground=COLORS['border'],
                     highlightthickness=1)
    frame.pack(fill='both', expand=True, padx=20, pady=14)

    if not student or student.get("room_number", "Not Allocated") == "Not Allocated":
        tk.Label(frame, text="You have not been allocated a room yet.",
                 font=FONTS['body'], bg=COLORS['card'],
                 fg=COLORS['warning']).pack(pady=40)
    else:
        room_no = student["room_number"]
        room = DataHandler.find_by_id("rooms", "room_number", room_no)
        if not room:
            tk.Label(frame, text=f"Room {room_no} info not available.",
                     font=FONTS['body'], bg=COLORS['card'],
                     fg=COLORS['danger']).pack(pady=40)
        else:
            capacity = room.get("capacity", 0)
            occupied = room.get("occupied", 0)
            fields = [
                ("Room Number", room.get("room_number", "")),
                ("Room Type", room.get("room_type", "")),
                ("Floor", room.get("floor", "")),
                ("Capacity", capacity),
                ("Occupied", occupied),
                ("Vacant", capacity - occupied),
                ("Status", room.get("status", "")),
                ("Roommates", ", ".join(
                    o for o in room.get("occupants", []) if o != stu_id
                ) or "None"),
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
