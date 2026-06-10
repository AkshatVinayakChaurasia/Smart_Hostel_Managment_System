"""
main.py - HostelHub Entry Point

Smart Hostel Management System with Tkinter GUI.
Run this file to start the application:

    python main.py           (launches GUI - default)
    python main.py --console (launches console mode)

Architecture:
  - Auth validates login via users.json
  - Role-based dashboards route to feature module GUIs
  - All data stored in /data/*.json
  - DataHandler provides a unified read/write API
  - GUI built with standard Tkinter + ttk
"""

import sys
import os

# Make all sub-packages importable from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =====================================================================
#  GUI MODE (default)
# =====================================================================

def run_gui():
    """Launch the HostelHub Tkinter GUI application."""
    import tkinter as tk
    from gui import apply_theme, center_window, COLORS
    from gui.login_window import LoginWindow
    from gui.admin_dashboard import AdminDashboard
    from gui.student_dashboard import StudentDashboard

    root = tk.Tk()
    root.title("HostelHub - Smart Hostel Management System")
    root.configure(bg=COLORS["bg"])
    center_window(root, 1050, 650)
    root.minsize(900, 550)

    # Apply ttk theme
    apply_theme(root)

    current_frame = [None]  # mutable container for frame reference

    def show_login():
        """Show the login screen."""
        if current_frame[0]:
            current_frame[0].destroy()
        root.title("HostelHub - Login")
        frame = LoginWindow(root, on_login_success=on_login)
        current_frame[0] = frame

    def on_login(user):
        """Handle successful login - route to appropriate dashboard."""
        if current_frame[0]:
            current_frame[0].destroy()

        role = user.get("role", "").lower()
        if role == "admin":
            root.title("HostelHub - Admin Dashboard")
            frame = AdminDashboard(root, user, on_logout=show_login)
        elif role == "student":
            root.title("HostelHub - Student Dashboard")
            frame = StudentDashboard(root, user, on_logout=show_login)
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "Unknown user role.")
            show_login()
            return
        current_frame[0] = frame

    # Start with login screen
    show_login()
    root.mainloop()


# =====================================================================
#  CONSOLE MODE (legacy - use --console flag)
# =====================================================================

def run_console():
    """Launch the original console-based HostelHub application."""
    from modules.auth              import AuthManager
    from modules.dashboard         import show_dashboard
    from modules.student_manager   import student_menu
    from modules.room_manager      import room_menu
    from modules.fee_manager       import fee_menu
    from modules.complaint_manager import complaint_menu
    from modules.attendance_manager import attendance_menu
    from modules.notice_manager    import notice_menu
    from modules.reports           import reports_menu
    from utils.display import (
        print_banner, print_menu, print_line,
        print_error, print_warning, clear_screen, pause
    )

    ADMIN_MENU_OPTIONS = [
        "[1]  Dashboard Overview",
        "[2]  Student Management",
        "[3]  Room Management",
        "[4]  Fee Management",
        "[5]  Complaint Management",
        "[6]  Attendance Management",
        "[7]  Notice Board",
        "[8]  System Reports",
        "[9]  Logout",
    ]

    STUDENT_MENU_OPTIONS = [
        "[1]  Dashboard",
        "[2]  My Room Details",
        "[3]  My Fee Status",
        "[4]  My Complaints",
        "[5]  My Attendance",
        "[6]  Notice Board",
        "[7]  Logout",
    ]

    def run_admin_menu(user, auth):
        while True:
            clear_screen()
            print_banner()
            print(f"  Logged in as: {user['name']}  [ ADMIN ]\n")
            choice = print_menu("Admin Menu", ADMIN_MENU_OPTIONS)
            if   choice == "1": show_dashboard(user)
            elif choice == "2": student_menu(user)
            elif choice == "3": room_menu(user)
            elif choice == "4": fee_menu(user)
            elif choice == "5": complaint_menu(user)
            elif choice == "6": attendance_menu(user)
            elif choice == "7": notice_menu(user)
            elif choice == "8": reports_menu(user)
            elif choice == "9":
                auth.logout()
                print_warning("You have been logged out.")
                pause()
                break
            else:
                print_error("Invalid choice. Please enter 1-9.")
                pause()

    def run_student_menu(user, auth):
        while True:
            clear_screen()
            print_banner()
            print(f"  Logged in as: {user['name']}  [ STUDENT | ID: {user['username']} ]\n")
            choice = print_menu("Student Menu", STUDENT_MENU_OPTIONS)
            if   choice == "1": show_dashboard(user)
            elif choice == "2": room_menu(user)
            elif choice == "3": fee_menu(user)
            elif choice == "4": complaint_menu(user)
            elif choice == "5": attendance_menu(user)
            elif choice == "6": notice_menu(user)
            elif choice == "7":
                auth.logout()
                print_warning("You have been logged out.")
                pause()
                break
            else:
                print_error("Invalid choice. Please enter 1-7.")
                pause()

    auth = AuthManager()
    while True:
        user = auth.login_loop()
        if auth.is_admin:
            run_admin_menu(user, auth)
        elif auth.is_student:
            run_student_menu(user, auth)
        else:
            print_error("Unknown role. Contact administrator.")
            pause()
            auth.logout()

        clear_screen()
        print_banner()
        again = input("  >  Login again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            clear_screen()
            print_banner()
            print("  Thank you for using HostelHub. Goodbye!\n")
            print_line()
            break


# =====================================================================
#  ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        run_gui()
