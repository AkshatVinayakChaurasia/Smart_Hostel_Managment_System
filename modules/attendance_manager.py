"""
attendance_manager.py - Attendance Management Module (Phase 5)

Features:
  1. Mark Attendance       (admin: single student OR bulk for all active students)
  2. View Attendance       (admin: by date, sortable)
  3. Attendance Percentage (admin: per-student stats over all records)
  4. Student History       (admin + student: full attendance history)
  5. Export Attendance CSV (admin)

  Student view:
  - My Attendance History
  - My Attendance Percentage

Rules:
  - Duplicate record (same student_id + date) is blocked
  - Student must exist and be active before marking
  - Status options: Present, Absent, Leave
"""

import os
from datetime import datetime

from models.attendance  import AttendanceRecord
from models.student     import Student
from database.db_handler import DataHandler
from utils.display      import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)
from utils.helpers      import generate_id, export_to_csv, current_date, truncate

# -- Constants ---------------------------------------------------------
ATT_ENTITY    = "attendance"
STU_ENTITY    = "students"
ATT_ID_FIELD  = "record_id"
STU_ID_FIELD  = "student_id"
STATUS_OPTIONS = ["Present", "Absent", "Leave"]
EXPORT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "exports")

ATT_TABLE_HEADERS = ["Record ID", "Student ID", "Name", "Date", "Status", "In Time", "Out Time"]


# =======================================================================
#  INTERNAL HELPERS
# =======================================================================

def _load_attendance() -> list[AttendanceRecord]:
    """Load all attendance records as AttendanceRecord objects."""
    return [AttendanceRecord.from_dict(r) for r in DataHandler.get_all(ATT_ENTITY)]


def _find_student(student_id: str) -> Student | None:
    """Find a Student by ID, or None."""
    rec = DataHandler.find_by_id(STU_ENTITY, STU_ID_FIELD, student_id.strip().upper())
    return Student.from_dict(rec) if rec else None


def _next_att_id() -> str:
    """Generate the next sequential attendance record ID (e.g. ATT007)."""
    existing = [r.get(ATT_ID_FIELD, "") for r in DataHandler.get_all(ATT_ENTITY)]
    return generate_id("ATT", existing)


def _is_duplicate(student_id: str, date: str) -> bool:
    """Return True if an attendance record already exists for student+date."""
    records = DataHandler.get_all(ATT_ENTITY)
    return any(
        r.get("student_id") == student_id and r.get("date") == date
        for r in records
    )


def _attendance_as_rows(records: list[AttendanceRecord]) -> list[list]:
    """List comprehension: convert AttendanceRecord objects to display rows."""
    return [
        [
            r.record_id,
            r.student_id,
            truncate(r.student_name, 14),
            r.date,
            r.status,
            r.in_time  if r.in_time  else "-",
            r.out_time if r.out_time else "-",
        ]
        for r in records
    ]


def _calculate_percentage(records: list[AttendanceRecord]) -> dict:
    """
    Calculate attendance statistics from a list of records.
    Returns dict with counts and percentage.
    """
    total   = len(records)
    present = sum(1 for r in records if r.status == "Present")
    absent  = sum(1 for r in records if r.status == "Absent")
    leave   = sum(1 for r in records if r.status == "Leave")
    pct     = round((present / total * 100), 2) if total else 0.0
    return {
        "total": total, "present": present,
        "absent": absent, "leave": leave, "percentage": pct
    }


def _prompt_status() -> str:
    """Prompt admin to select attendance status. Returns chosen status or ''."""
    print("\n  Status:")
    for i, s in enumerate(STATUS_OPTIONS, 1):
        print(f"    [{i}]  {s}")
    choice = input("\n  >  Select status: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(STATUS_OPTIONS):
            return STATUS_OPTIONS[idx]
    except ValueError:
        pass
    return ""


# =======================================================================
#  FEATURE 1 - MARK ATTENDANCE
# =======================================================================

def mark_attendance():
    """
    Admin: mark attendance for one or all active students.
    Duplicate check: same student_id + date is blocked.
    """
    clear_screen()
    print_banner()
    print_header("Mark Attendance")

    today = current_date()
    date_input = input(f"  >  Date (YYYY-MM-DD, Enter for today [{today}]): ").strip()
    if not date_input:
        date_input = today
    else:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print_error("Invalid date format. Using today's date.")
            date_input = today

    print(f"\n  Marking attendance for: {date_input}")
    print("  Mode:")
    print("    [1]  Single student")
    print("    [2]  All active students (bulk)")
    mode = input("\n  >  Choice: ").strip()

    if mode == "1":
        _mark_single(date_input)
    elif mode == "2":
        _mark_bulk(date_input)
    else:
        print_error("Invalid choice.")
        pause()


def _mark_single(date: str):
    """Mark attendance for one student."""
    student_id = input("  >  Student ID: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    student = _find_student(student_id)
    if not student:
        print_error(f"Student '{student_id}' not found.")
        pause()
        return

    if not student.is_active:
        print_error(f"Student {student_id} is Inactive.")
        pause()
        return

    if _is_duplicate(student_id, date):
        print_warning(f"Attendance for {student_id} on {date} already exists.")
        pause()
        return

    status = _prompt_status()
    if not status:
        print_error("Invalid status selection.")
        pause()
        return

    in_time = out_time = ""
    if status == "Present":
        in_time  = input("  >  In Time (HH:MM, Enter to skip): ").strip()
        out_time = input("  >  Out Time (HH:MM, Enter to skip): ").strip()

    record = AttendanceRecord(
        record_id    = _next_att_id(),
        student_id   = student_id,
        student_name = student.name,
        date         = date,
        status       = status,
        in_time      = in_time,
        out_time     = out_time,
    )

    if DataHandler.insert(ATT_ENTITY, record.to_dict()):
        print_success(f"Attendance marked: {student.name} | {date} | {status}")
    else:
        print_error("Failed to save attendance record.")
    pause()


def _mark_bulk(date: str):
    """Bulk-mark attendance for all active students."""
    all_students = DataHandler.get_all(STU_ENTITY)
    # List comprehension: only active students
    active = [Student.from_dict(s) for s in all_students if s.get("is_active")]

    if not active:
        print_warning("No active students found.")
        pause()
        return

    # Find already-marked students for this date
    already_marked = {
        r.get("student_id")
        for r in DataHandler.get_all(ATT_ENTITY)
        if r.get("date") == date
    }

    to_mark = [s for s in active if s.student_id not in already_marked]

    if not to_mark:
        print_warning(f"All active students already have attendance for {date}.")
        pause()
        return

    print(f"\n  {len(to_mark)} student(s) to mark ({len(already_marked)} already done).")
    print("  Default status for bulk marking:")
    default_status = _prompt_status()
    if not default_status:
        print_error("Invalid status.")
        pause()
        return

    if not confirm(f"Mark all {len(to_mark)} students as '{default_status}' for {date}? (y/n)"):
        print_warning("Bulk attendance cancelled.")
        pause()
        return

    saved = 0
    for student in to_mark:
        record = AttendanceRecord(
            record_id    = _next_att_id(),
            student_id   = student.student_id,
            student_name = student.name,
            date         = date,
            status       = default_status,
            in_time      = "",
            out_time      = "",
        )
        if DataHandler.insert(ATT_ENTITY, record.to_dict()):
            saved += 1

    print_success(f"Bulk attendance complete: {saved}/{len(to_mark)} records saved for {date}.")
    pause()


# =======================================================================
#  FEATURE 2 - VIEW ATTENDANCE
# =======================================================================

def view_attendance():
    """Admin: view attendance filtered by date or student."""
    clear_screen()
    print_banner()
    print_header("View Attendance")

    records = _load_attendance()
    if not records:
        print_info("No attendance records found.")
        pause()
        return

    print("  View by:")
    print("    [1]  Specific Date")
    print("    [2]  Specific Student")
    print("    [3]  All Records")
    view_choice = input("\n  >  Choice: ").strip()

    if view_choice == "1":
        today = current_date()
        date_input = input(f"  >  Date (YYYY-MM-DD, Enter for today [{today}]): ").strip()
        if not date_input:
            date_input = today
        # List comprehension: filter by date
        filtered = [r for r in records if r.date == date_input]
        label = f"Date: {date_input}"

    elif view_choice == "2":
        stu_id = input("  >  Student ID: ").strip().upper()
        # List comprehension: filter by student, newest first
        filtered = sorted(
            [r for r in records if r.student_id == stu_id],
            key=lambda r: r.date, reverse=True
        )
        label = f"Student: {stu_id}"

    elif view_choice == "3":
        # Lambda sort: by date descending, then student_id
        filtered = sorted(records, key=lambda r: (r.date, r.student_id), reverse=True)
        label = "All Records"

    else:
        print_error("Invalid choice.")
        pause()
        return

    if not filtered:
        print_warning(f"No records found for {label}.")
        pause()
        return

    print_info(f"{len(filtered)} record(s)  [{label}]")
    print_table(ATT_TABLE_HEADERS, _attendance_as_rows(filtered))

    # Quick summary
    stats = _calculate_percentage(filtered)
    print_line()
    print(f"  Present: {stats['present']}  |  Absent: {stats['absent']}  |  "
          f"Leave: {stats['leave']}  |  Total: {stats['total']}  |  "
          f"Attendance%: {stats['percentage']:.1f}%")
    print_line()

    pause()


# =======================================================================
#  FEATURE 3 - ATTENDANCE PERCENTAGE REPORT
# =======================================================================

def attendance_percentage():
    """Admin: show per-student attendance percentage across all records."""
    clear_screen()
    print_banner()
    print_header("Attendance Percentage - All Students")

    records = _load_attendance()
    if not records:
        print_info("No attendance records found.")
        pause()
        return

    # Group records by student_id using a dictionary
    student_records: dict[str, list[AttendanceRecord]] = {}
    for r in records:
        student_records.setdefault(r.student_id, []).append(r)

    # Build stats rows using list comprehension
    rows = []
    for sid, recs in sorted(student_records.items()):
        stats  = _calculate_percentage(recs)
        name   = recs[0].student_name
        bar    = _pct_bar(stats["percentage"])
        rows.append([
            sid, truncate(name, 16),
            str(stats["total"]), str(stats["present"]),
            str(stats["absent"]), str(stats["leave"]),
            f"{stats['percentage']:.1f}%", bar,
        ])

    headers = ["Stu ID", "Name", "Total", "Present", "Absent", "Leave", "Pct%", "Bar"]
    print_table(headers, rows)

    # Flag low attendance (below 75%)
    low = [(r[0], r[1], r[6]) for r in rows if float(r[6].replace("%", "")) < 75.0]
    if low:
        print_warning(f"Low attendance (<75%): {len(low)} student(s):")
        for sid, name, pct in low:
            print(f"     {sid}  {name:<18}  {pct}")
    else:
        print_success("All students have attendance >= 75%.")

    print()
    pause()


def _pct_bar(pct: float, width: int = 12) -> str:
    """ASCII progress bar for attendance percentage (0-100)."""
    filled = round(pct / 100 * width)
    empty  = width - filled
    return f"[{'#' * filled}{'.' * empty}]"


# =======================================================================
#  FEATURE 4 - STUDENT ATTENDANCE HISTORY
# =======================================================================

def student_history(student_id: str = ""):
    """
    Admin: look up any student's full attendance history.
    If student_id is passed (from student login), shows their own.
    """
    clear_screen()
    print_banner()
    print_header("Student Attendance History")

    if not student_id:
        student_id = input("  >  Student ID: ").strip().upper()

    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    student = _find_student(student_id)
    if not student:
        print_error(f"Student '{student_id}' not found.")
        pause()
        return

    records = _load_attendance()
    # List comprehension + lambda sort: newest first
    history = sorted(
        [r for r in records if r.student_id == student_id],
        key=lambda r: r.date, reverse=True
    )

    print(f"\n  Student: {student_id} - {student.name} | {student.course} Yr-{student.year}")
    print(f"  Room   : {student.room_number}")
    print()

    if not history:
        print_info("No attendance records found for this student.")
        pause()
        return

    print_table(ATT_TABLE_HEADERS, _attendance_as_rows(history))

    stats = _calculate_percentage(history)
    bar   = _pct_bar(stats["percentage"])
    print_line()
    print(f"  Total Days : {stats['total']}  |  Present: {stats['present']}  |  "
          f"Absent: {stats['absent']}  |  Leave: {stats['leave']}")
    print(f"  Attendance : {stats['percentage']:.1f}%  {bar}")
    print_line()

    if stats["percentage"] < 75:
        print_warning(f"Attendance below 75%! Current: {stats['percentage']:.1f}%")

    pause()


# =======================================================================
#  FEATURE 5 - EXPORT ATTENDANCE CSV
# =======================================================================

def export_attendance():
    """Export attendance records to CSV file."""
    clear_screen()
    print_banner()
    print_header("Export Attendance Report")

    records = _load_attendance()
    if not records:
        print_info("No attendance records to export.")
        pause()
        return

    headers = ["Record ID", "Student ID", "Student Name", "Date",
               "Status", "In Time", "Out Time"]

    # Generator expression: row builder
    rows = list(
        (r.record_id, r.student_id, r.student_name,
         r.date, r.status, r.in_time, r.out_time)
        for r in sorted(records, key=lambda r: (r.date, r.student_id))
    )

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"attendance_report_{date_str}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    if export_to_csv(filepath, headers, rows):
        print_success(f"Exported: exports/{filename}  ({len(rows)} record(s))")
    else:
        print_error("Export failed. Check write permissions.")

    pause()


# =======================================================================
#  ATTENDANCE MENU ENTRY POINT
# =======================================================================

_ADMIN_OPTIONS = [
    "[1] Mark Attendance",
    "[2] View Attendance",
    "[3] Attendance Percentage Report",
    "[4] Student History",
    "[5] Export Attendance CSV",
    "[6] Back to Main Menu",
]

_STUDENT_OPTIONS = [
    "[1] My Attendance History",
    "[2] My Attendance Percentage",
    "[3] Back to Main Menu",
]


def attendance_menu(user: dict):
    """Entry point called from main.py. Role-based routing."""
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Attendance Management", _ADMIN_OPTIONS)

            if choice == "1":
                mark_attendance()
            elif choice == "2":
                view_attendance()
            elif choice == "3":
                attendance_percentage()
            elif choice == "4":
                student_history()
            elif choice == "5":
                export_attendance()
            elif choice == "6":
                break
            else:
                print_error("Invalid choice. Enter 1 to 6.")
                pause()

        else:
            # Student: read-only - own records only
            choice = print_menu("My Attendance", _STUDENT_OPTIONS)
            student_id = user.get("username", "")

            if choice == "1":
                student_history(student_id)
            elif choice == "2":
                # Inline percentage for student
                records = _load_attendance()
                my_recs = [r for r in records if r.student_id == student_id]
                if not my_recs:
                    print_info("No attendance records found for your account.")
                else:
                    stats = _calculate_percentage(my_recs)
                    bar   = _pct_bar(stats["percentage"])
                    clear_screen()
                    print_banner()
                    print_header("My Attendance Summary")
                    print()
                    print_line("-")
                    print(f"  Total Days : {stats['total']}")
                    print(f"  Present    : {stats['present']}")
                    print(f"  Absent     : {stats['absent']}")
                    print(f"  Leave      : {stats['leave']}")
                    print(f"  Percentage : {stats['percentage']:.1f}%  {bar}")
                    print_line("-")
                    if stats["percentage"] < 75:
                        print_warning(f"Warning: Attendance below 75%!")
                    else:
                        print_success("Attendance is above 75% minimum.")
                pause()
            elif choice == "3":
                break
            else:
                print_error("Invalid choice.")
                pause()
