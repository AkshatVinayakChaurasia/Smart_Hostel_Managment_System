"""
dashboard.py - Dashboard & Statistics module

Pulls live counts from all data files and displays a
text-based dashboard with key hostel metrics.
"""

from database.db_handler import DataHandler
from utils.display import (
    print_banner, print_header, print_line,
    print_dashboard_stats, print_info, pause, clear_screen
)


def show_dashboard(user: dict):
    """
    Render the main dashboard with key hostel statistics.
    Works for both admin and student views.
    """
    clear_screen()
    print_banner()
    print_header("Dashboard Overview")

    # -- Fetch live statistics -----------------------------------------
    total_students   = DataHandler.count("students")
    active_students  = DataHandler.count_where("students", "is_active", True)
    total_rooms      = DataHandler.count("rooms")

    rooms_data       = DataHandler.get_all("rooms")
    occupied_rooms   = sum(1 for r in rooms_data if r.get("occupied", 0) > 0)
    vacant_rooms     = sum(1 for r in rooms_data if r.get("occupied", 0) == 0)
    total_beds       = sum(r.get("capacity", 0) for r in rooms_data)
    occupied_beds    = sum(r.get("occupied", 0) for r in rooms_data)

    open_complaints  = DataHandler.count_where("complaints", "status", "Open")
    total_complaints = DataHandler.count("complaints")

    pending_fees     = DataHandler.count_where("fees", "status", "Pending")
    partial_fees     = DataHandler.count_where("fees", "status", "Partial")
    paid_fees        = DataHandler.count_where("fees", "status", "Paid")

    total_notices    = DataHandler.count("notices")

    # -- Display student stats -----------------------------------------
    print("\n  -- Student Summary " + "-" * 46)
    print_dashboard_stats({
        "Total Students": total_students,
        "Active":         active_students,
        "Total Rooms":    total_rooms,
        "Total Beds":     total_beds,
    })

    # -- Occupancy stats -----------------------------------------------
    print("  -- Occupancy " + "-" * 51)
    occupancy_pct = f"{(occupied_beds / total_beds * 100):.1f}%" if total_beds else "0%"
    print_dashboard_stats({
        "Occupied Rooms": occupied_rooms,
        "Vacant Rooms":   vacant_rooms,
        "Beds Occupied":  occupied_beds,
        "Occupancy %":    occupancy_pct,
    })

    # -- Fee & Complaints ----------------------------------------------
    print("  -- Financials & Complaints " + "-" * 37)
    print_dashboard_stats({
        "Fees Paid":     paid_fees,
        "Partial Fees":  partial_fees,
        "Pending Fees":  pending_fees,
        "Open Complaints": open_complaints,
    })

    # -- Notice Board --------------------------------------------------
    print("  -- Notice Board " + "-" * 48)
    notices = DataHandler.get_all("notices")
    important = [n for n in notices if n.get("is_important")]

    if not notices:
        print_info("No notices posted yet.")
    else:
        print(f"\n  Total Notices: {total_notices}  |  Important: {len(important)}\n")
        for n in notices[:3]:          # show latest 3
            tag = " [!] IMPORTANT" if n.get("is_important") else ""
            print(f"  [{n.get('category','General')}] {n.get('title','')}{tag}")
            print(f"      Posted: {n.get('posted_date','')}  |  "
                  f"Expires: {n.get('expiry_date', 'N/A')}")
        if len(notices) > 3:
            print(f"\n  ... and {len(notices) - 3} more notice(s).")

    print()
    print_line()
    pause()
