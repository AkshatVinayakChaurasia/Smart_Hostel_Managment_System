"""
reports.py - System Reports Module (Phase 5)

Provides lightweight summary reports for admin:
  1. Hostel Occupancy Report
  2. Fee Pending Summary
  3. Complaint Status Summary
  4. Attendance Summary
  5. Export All Reports (combined CSV)

All data is read live from JSON files via DataHandler.
No external dependencies required.
"""

import os
from datetime import datetime

from database.db_handler import DataHandler
from models.fee          import FeeRecord
from models.complaint    import Complaint
from models.attendance   import AttendanceRecord
from models.room         import Room
from utils.display       import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_success, print_error, print_info,
    print_warning, pause
)
from utils.helpers       import export_to_csv

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "exports")


# =======================================================================
#  REPORT 1 - HOSTEL OCCUPANCY REPORT
# =======================================================================

def report_occupancy():
    """Print a quick hostel occupancy summary with per-floor breakdown."""
    clear_screen()
    print_banner()
    print_header("Hostel Occupancy Report")

    rooms = [Room.from_dict(r) for r in DataHandler.get_all("rooms")]
    if not rooms:
        print_info("No room data available.")
        pause()
        return

    total_rooms  = len(rooms)
    total_beds   = sum(r.capacity for r in rooms)
    occ_beds     = sum(r.occupied for r in rooms)
    free_beds    = total_beds - occ_beds
    full_rooms   = sum(1 for r in rooms if r.status == "Full")
    partial_rooms= sum(1 for r in rooms if r.status == "Partial")
    vacant_rooms = sum(1 for r in rooms if r.status == "Vacant")
    occ_pct      = (occ_beds / total_beds * 100) if total_beds else 0

    print()
    print("  +------------------------------------------------+")
    print(f"  |  OVERALL OCCUPANCY : {occ_pct:>5.1f}%                  |")
    print(f"  |  Rooms: {total_rooms:<3}  Full:{full_rooms:<3}  Partial:{partial_rooms:<3}  Vacant:{vacant_rooms:<3}  |")
    print(f"  |  Beds : {total_beds:<3}  Occupied:{occ_beds:<3}  Free:{free_beds:<3}            |")
    print("  +------------------------------------------------+")

    # Per-floor summary using list comprehension
    floors = sorted(set(r.floor for r in rooms))
    print("\n  -- By Floor " + "-" * 36)
    for fl in floors:
        fl_rooms = [r for r in rooms if r.floor == fl]
        fl_beds  = sum(r.capacity for r in fl_rooms)
        fl_occ   = sum(r.occupied for r in fl_rooms)
        fl_pct   = (fl_occ / fl_beds * 100) if fl_beds else 0
        bar      = _bar(fl_occ, fl_beds, 12)
        print(f"  Floor {fl}:  {bar}  {fl_pct:.1f}%  ({len(fl_rooms)} rooms, {fl_beds} beds)")

    # Student count cross-check
    students = DataHandler.get_all("students")
    allocated = sum(
        1 for s in students
        if s.get("room_number") and s.get("room_number") != "Not Allocated"
    )
    print(f"\n  Students with rooms: {allocated} / {len(students)}")
    print()
    pause()


# =======================================================================
#  REPORT 2 - FEE PENDING SUMMARY
# =======================================================================

def report_fees():
    """Fee collection summary: paid vs pending vs partial."""
    clear_screen()
    print_banner()
    print_header("Fee Collection Summary")

    fees = [FeeRecord.from_dict(r) for r in DataHandler.get_all("fees")]
    if not fees:
        print_info("No fee records found.")
        pause()
        return

    total_due   = sum(f.amount_due for f in fees)
    total_paid  = sum(f.amount_paid for f in fees)
    total_fine  = sum(f.fine_amount for f in fees)
    total_bal   = sum(f.balance for f in fees)
    paid_cnt    = sum(1 for f in fees if f.status == "Paid")
    partial_cnt = sum(1 for f in fees if f.status == "Partial")
    pending_cnt = sum(1 for f in fees if f.status == "Pending")
    overdue     = [f for f in fees if f.is_overdue]

    collection_pct = (total_paid / (total_due + total_fine) * 100) if (total_due + total_fine) else 0

    print()
    print("  +------------------------------------------------+")
    print(f"  |  COLLECTION RATE : {collection_pct:>5.1f}%                   |")
    print(f"  |  Records: {len(fees):<4}  Paid:{paid_cnt:<3}  Partial:{partial_cnt:<3}  Pending:{pending_cnt:<3}  |")
    print(f"  |  Total Due   : Rs.{total_due:>10,.2f}                 |")
    print(f"  |  Collected   : Rs.{total_paid:>10,.2f}                 |")
    print(f"  |  Fines       : Rs.{total_fine:>10,.2f}                 |")
    print(f"  |  Outstanding : Rs.{total_bal:>10,.2f}                 |")
    print("  +------------------------------------------------+")

    if overdue:
        print_warning(f"\n  {len(overdue)} OVERDUE fee record(s):")
        for f in overdue:
            print(f"    {f.fee_id}  {f.student_name:<20}  "
                  f"{f.days_overdue} days  Balance: Rs.{f.balance:,.2f}")

    # Pending list
    pending = sorted(
        [f for f in fees if f.status != "Paid"],
        key=lambda f: f.student_name.lower()
    )
    if pending:
        print(f"\n  -- Unpaid / Partial ({len(pending)} records) " + "-" * 20)
        for f in pending:
            print(f"  {f.fee_id:<8} {f.student_id:<8} {f.student_name:<20} "
                  f"{f.status:<8} Balance: Rs.{f.balance:,.2f}")

    print()
    pause()


# =======================================================================
#  REPORT 3 - COMPLAINT STATUS SUMMARY
# =======================================================================

def report_complaints():
    """Complaint status breakdown by type and priority."""
    clear_screen()
    print_banner()
    print_header("Complaint Status Summary")

    complaints = [Complaint.from_dict(r) for r in DataHandler.get_all("complaints")]
    if not complaints:
        print_info("No complaints found.")
        pause()
        return

    open_c    = [c for c in complaints if c.status == "Open"]
    in_prog   = [c for c in complaints if c.status == "In Progress"]
    resolved  = [c for c in complaints if c.status == "Resolved"]
    closed    = [c for c in complaints if c.status == "Closed"]

    print()
    print("  +-------------------------------------------+")
    print(f"  |  TOTAL COMPLAINTS : {len(complaints):<3}                   |")
    print(f"  |  Open: {len(open_c):<3}  In Progress: {len(in_prog):<3}              |")
    print(f"  |  Resolved: {len(resolved):<3}  Closed: {len(closed):<3}            |")
    print("  +-------------------------------------------+")

    # By priority - list comprehension
    high   = [c for c in complaints if c.priority == "High"]
    medium = [c for c in complaints if c.priority == "Medium"]
    low    = [c for c in complaints if c.priority == "Low"]

    print(f"\n  -- By Priority " + "-" * 28)
    print(f"  High   : {len(high):<3}  |  Medium: {len(medium):<3}  |  Low: {len(low):<3}")

    # By type
    from models.complaint import COMPLAINT_TYPES
    print(f"\n  -- By Type " + "-" * 32)
    for ctype in COMPLAINT_TYPES:
        count = sum(1 for c in complaints if c.complaint_type == ctype)
        if count:
            open_of_type = sum(1 for c in complaints
                               if c.complaint_type == ctype and c.is_open)
            print(f"  {ctype:<14} : {count:<3}  (Active: {open_of_type})")

    # Active complaints sorted by priority
    active = sorted(
        [c for c in complaints if c.is_open],
        key=lambda c: {"High": 0, "Medium": 1, "Low": 2}.get(c.priority, 99)
    )
    if active:
        print(f"\n  -- Active Complaints ({len(active)}) -- Priority Order " + "-" * 10)
        for c in active:
            print(f"  {c.complaint_id}  {c.priority:<7}  {c.complaint_type:<14}  "
                  f"{c.student_name:<20}  {c.status}")

    print()
    pause()


# =======================================================================
#  REPORT 4 - ATTENDANCE SUMMARY
# =======================================================================

def report_attendance():
    """Attendance summary: per-student stats and overall percentage."""
    clear_screen()
    print_banner()
    print_header("Attendance Summary")

    records = [AttendanceRecord.from_dict(r) for r in DataHandler.get_all("attendance")]
    if not records:
        print_info("No attendance records found.")
        pause()
        return

    total_records = len(records)
    total_present = sum(1 for r in records if r.status == "Present")
    total_absent  = sum(1 for r in records if r.status == "Absent")
    total_leave   = sum(1 for r in records if r.status == "Leave")
    dates         = sorted(set(r.date for r in records))
    overall_pct   = (total_present / total_records * 100) if total_records else 0

    print()
    print("  +-------------------------------------------+")
    print(f"  |  ATTENDANCE RECORDS : {total_records:<3}                  |")
    print(f"  |  Dates Covered  : {len(dates):<3}                      |")
    print(f"  |  Present: {total_present:<3}  Absent: {total_absent:<3}  Leave: {total_leave:<3}    |")
    print(f"  |  Overall Attendance% : {overall_pct:>5.1f}%              |")
    print("  +-------------------------------------------+")

    # Per-student summary
    stu_map: dict[str, list] = {}
    for r in records:
        stu_map.setdefault(r.student_id, []).append(r)

    print(f"\n  -- Per-Student Breakdown " + "-" * 18)
    low_stu = []
    for sid, recs in sorted(stu_map.items()):
        present = sum(1 for r in recs if r.status == "Present")
        pct     = (present / len(recs) * 100) if recs else 0
        bar     = _bar(present, len(recs), 10)
        name    = recs[0].student_name
        print(f"  {sid}  {name:<20}  {bar}  {pct:.1f}%  ({len(recs)} days)")
        if pct < 75:
            low_stu.append((sid, name, f"{pct:.1f}%"))

    if low_stu:
        print_warning(f"\n  {len(low_stu)} student(s) below 75%:")
        for sid, name, pct in low_stu:
            print(f"     {sid}  {name}  {pct}")

    print()
    pause()


# =======================================================================
#  REPORT 5 - EXPORT ALL REPORTS
# =======================================================================

def export_all_reports():
    """Export 4 summary CSVs in one go."""
    clear_screen()
    print_banner()
    print_header("Export All System Reports")

    date_str = datetime.now().strftime("%Y-%m-%d")
    results  = []

    # -- Occupancy CSV
    rooms    = [Room.from_dict(r) for r in DataHandler.get_all("rooms")]
    occ_rows = list((
        r.room_number, r.room_type, str(r.floor),
        str(r.capacity), str(r.occupied),
        str(r.capacity - r.occupied), r.status
    ) for r in rooms)
    occ_path = os.path.join(EXPORT_DIR, f"report_occupancy_{date_str}.csv")
    ok = export_to_csv(occ_path,
                       ["Room", "Type", "Floor", "Capacity", "Occupied", "Free", "Status"],
                       occ_rows)
    results.append(("Occupancy", ok, f"report_occupancy_{date_str}.csv", len(occ_rows)))

    # -- Fee CSV
    fees     = [FeeRecord.from_dict(r) for r in DataHandler.get_all("fees")]
    fee_rows = list((
        f.fee_id, f.student_id, f.student_name, f.month,
        f"{f.amount_due:.2f}", f"{f.amount_paid:.2f}",
        f"{f.fine_amount:.2f}", f"{f.balance:.2f}", f.status
    ) for f in fees)
    fee_path = os.path.join(EXPORT_DIR, f"report_fees_{date_str}.csv")
    ok = export_to_csv(fee_path,
                       ["Fee ID","Stu ID","Name","Month","Due","Paid","Fine","Balance","Status"],
                       fee_rows)
    results.append(("Fees", ok, f"report_fees_{date_str}.csv", len(fee_rows)))

    # -- Complaints CSV
    comps    = [Complaint.from_dict(r) for r in DataHandler.get_all("complaints")]
    cmp_rows = list((
        c.complaint_id, c.student_id, c.student_name,
        c.complaint_type, c.priority, c.status,
        c.filed_date, c.resolved_date, c.description[:60]
    ) for c in comps)
    cmp_path = os.path.join(EXPORT_DIR, f"report_complaints_{date_str}.csv")
    ok = export_to_csv(cmp_path,
                       ["CMP ID","Stu ID","Name","Type","Priority","Status",
                        "Filed","Resolved","Description"],
                       cmp_rows)
    results.append(("Complaints", ok, f"report_complaints_{date_str}.csv", len(cmp_rows)))

    # -- Attendance CSV (per-student summary)
    att_recs = [AttendanceRecord.from_dict(r) for r in DataHandler.get_all("attendance")]
    stu_map: dict[str, list] = {}
    for r in att_recs:
        stu_map.setdefault(r.student_id, []).append(r)
    att_rows = list((
        sid,
        recs[0].student_name,
        str(len(recs)),
        str(sum(1 for r in recs if r.status == "Present")),
        str(sum(1 for r in recs if r.status == "Absent")),
        str(sum(1 for r in recs if r.status == "Leave")),
        f"{(sum(1 for r in recs if r.status=='Present') / len(recs) * 100):.1f}%"
    ) for sid, recs in sorted(stu_map.items()))
    att_path = os.path.join(EXPORT_DIR, f"report_attendance_{date_str}.csv")
    ok = export_to_csv(att_path,
                       ["Stu ID","Name","Total","Present","Absent","Leave","Pct%"],
                       att_rows)
    results.append(("Attendance", ok, f"report_attendance_{date_str}.csv", len(att_rows)))

    # Print results
    print()
    all_ok = True
    for name, success, fname, count in results:
        if success:
            print(f"  [OK]   {name:<12} -> exports/{fname}  ({count} rows)")
        else:
            print(f"  [FAIL] {name:<12} -> Export failed")
            all_ok = False

    print()
    if all_ok:
        print_success(f"All 4 reports exported to exports/  (date: {date_str})")
    else:
        print_warning("Some reports failed to export. Check write permissions.")

    pause()


# =======================================================================
#  UTILITY
# =======================================================================

def _bar(filled: int, total: int, width: int = 10) -> str:
    """ASCII progress bar."""
    if total == 0:
        return "[" + "." * width + "]"
    n = round(filled / total * width)
    return "[" + "#" * n + "." * (width - n) + "]"


# =======================================================================
#  REPORTS MENU ENTRY POINT
# =======================================================================

_ADMIN_OPTIONS = [
    "[1] Hostel Occupancy Report",
    "[2] Fee Collection Summary",
    "[3] Complaint Status Summary",
    "[4] Attendance Summary",
    "[5] Export All Reports (CSV)",
    "[6] Back to Main Menu",
]


def reports_menu(user: dict):
    """Entry point for system reports - admin only."""
    while True:
        clear_screen()
        print_banner()
        choice = print_menu("System Reports", _ADMIN_OPTIONS)

        if choice == "1":
            report_occupancy()
        elif choice == "2":
            report_fees()
        elif choice == "3":
            report_complaints()
        elif choice == "4":
            report_attendance()
        elif choice == "5":
            export_all_reports()
        elif choice == "6":
            break
        else:
            from utils.display import print_error
            print_error("Invalid choice. Enter 1 to 6.")
            pause()
