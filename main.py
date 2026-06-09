"""
main.py - HostelHub Entry Point

Console-based Smart Hostel Management System.
Run this file to start the application:

    python main.py

Architecture:
  - Auth module validates login
  - Role-based menus route to feature modules
  - All data stored in /data/*.json
  - DataHandler provides a unified read/write API

Modules:
  Phase 1: Auth, Dashboard
  Phase 2: Student Management
  Phase 3: Room Management
  Phase 4: Fee Management, Complaint Management
  Phase 5: Attendance Management, Notice Board, System Reports
"""

import sys
import os

# Make all sub-packages importable from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.auth               import AuthManager
from modules.dashboard          import show_dashboard
from modules.student_manager    import student_menu
from modules.room_manager       import room_menu
from modules.fee_manager        import fee_menu
from modules.complaint_manager  import complaint_menu
from modules.attendance_manager import attendance_menu
from modules.notice_manager     import notice_menu
from modules.reports            import reports_menu

from utils.display import (
    print_banner, print_menu, print_line,
    print_error, print_warning, clear_screen, pause
)


# =======================================================================
#  ADMIN MENU
# =======================================================================

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


def run_admin_menu(user: dict, auth: AuthManager):
    """Main loop for the Admin dashboard menu."""
    while True:
        clear_screen()
        print_banner()
        print(f"  Logged in as: {user['name']}  [ ADMIN ]\n")

        choice = print_menu("Admin Menu", ADMIN_MENU_OPTIONS)

        if choice == "1":
            show_dashboard(user)
        elif choice == "2":
            student_menu(user)
        elif choice == "3":
            room_menu(user)
        elif choice == "4":
            fee_menu(user)
        elif choice == "5":
            complaint_menu(user)
        elif choice == "6":
            attendance_menu(user)
        elif choice == "7":
            notice_menu(user)
        elif choice == "8":
            reports_menu(user)
        elif choice == "9":
            auth.logout()
            print_warning("You have been logged out.")
            pause()
            break
        else:
            print_error("Invalid choice. Please enter a number from 1 to 9.")
            pause()


# =======================================================================
#  STUDENT MENU
# =======================================================================

STUDENT_MENU_OPTIONS = [
    "[1]  Dashboard",
    "[2]  My Room Details",
    "[3]  My Fee Status",
    "[4]  My Complaints",
    "[5]  My Attendance",
    "[6]  Notice Board",
    "[7]  Logout",
]


def run_student_menu(user: dict, auth: AuthManager):
    """Main loop for the Student dashboard menu."""
    while True:
        clear_screen()
        print_banner()
        print(f"  Logged in as: {user['name']}  [ STUDENT | ID: {user['username']} ]\n")

        choice = print_menu("Student Menu", STUDENT_MENU_OPTIONS)

        if choice == "1":
            show_dashboard(user)
        elif choice == "2":
            room_menu(user)
        elif choice == "3":
            fee_menu(user)
        elif choice == "4":
            complaint_menu(user)
        elif choice == "5":
            attendance_menu(user)
        elif choice == "6":
            notice_menu(user)
        elif choice == "7":
            auth.logout()
            print_warning("You have been logged out.")
            pause()
            break
        else:
            print_error("Invalid choice. Please enter a number from 1 to 7.")
            pause()


# =======================================================================
#  APPLICATION ENTRY POINT
# =======================================================================

def main():
    """Start the HostelHub application."""
    auth = AuthManager()

    while True:
        # Login loop
        user = auth.login_loop()

        # Route to role-specific menu
        if auth.is_admin:
            run_admin_menu(user, auth)
        elif auth.is_student:
            run_student_menu(user, auth)
        else:
            print_error("Unknown role. Contact administrator.")
            pause()
            auth.logout()

        # After logout: ask to exit or login again
        clear_screen()
        print_banner()
        again = input("  >  Login again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            clear_screen()
            print_banner()
            print("  Thank you for using HostelHub. Goodbye!\n")
            print_line()
            break


if __name__ == "__main__":
    main()
