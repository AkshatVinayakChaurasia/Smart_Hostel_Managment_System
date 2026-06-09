"""
complaint_manager.py - Complaint Management Module (Phase 4)

Features:
  1. Register Complaint        (student OR admin on behalf of student)
  2. View All Complaints       (admin: sortable table)
  3. Search Complaint          (by ID, student, type, keyword)
  4. Update Complaint Status   (admin: Open -> In Progress -> Resolved)
  5. Resolve Complaint         (admin: mark resolved with remarks)
  6. Filter Complaints         (by status / type / priority)
  7. Export Complaint Report   (CSV export to exports/)
  8. [Student] My Complaints   (student: view and file own complaints)

Complaint Status Flow:
  Open  ->  In Progress  ->  Resolved  ->  Closed

Priority Levels: High, Medium, Low
  - High  : Electricity, Internet, Water outages
  - Medium: Cleanliness, Maintenance
  - Low   : Other / misc

Uses: Complaint model, Student model, DataHandler, display utilities.
"""

import os
from datetime import datetime

from models.complaint import Complaint, COMPLAINT_TYPES, COMPLAINT_STATUS, PRIORITY_LEVELS
from models.student   import Student
from database.db_handler import DataHandler
from utils.display    import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)
from utils.helpers    import generate_id, export_to_csv, current_date, truncate

# -- Constants ---------------------------------------------------------
CMP_ENTITY   = "complaints"
STU_ENTITY   = "students"
CMP_ID_FIELD = "complaint_id"
STU_ID_FIELD = "student_id"
EXPORT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "exports")

# Default priority suggestion per complaint type
_TYPE_PRIORITY = {
    "Electricity": "High",
    "Water":       "High",
    "Internet":    "High",
    "Maintenance": "Medium",
    "Cleanliness": "Medium",
    "Other":       "Low",
}


def _type_priority_mapping(complaint_type: str) -> str:
    """Return the suggested priority for a given complaint type."""
    return _TYPE_PRIORITY.get(complaint_type, "Medium")

CMP_TABLE_HEADERS = ["CMP ID", "Student", "Type", "Priority", "Status", "Filed On"]


# =======================================================================
#  INTERNAL HELPERS
# =======================================================================

def _load_complaints() -> list[Complaint]:
    """Load all complaints from JSON as Complaint objects."""
    return [Complaint.from_dict(r) for r in DataHandler.get_all(CMP_ENTITY)]


def _save_complaint(cmp: Complaint) -> bool:
    """Persist a single updated Complaint record."""
    return DataHandler.update(CMP_ENTITY, CMP_ID_FIELD, cmp.complaint_id, cmp.to_dict())


def _find_complaint(cmp_id: str) -> Complaint | None:
    """Find a Complaint by complaint_id, or None."""
    rec = DataHandler.find_by_id(CMP_ENTITY, CMP_ID_FIELD, cmp_id.strip().upper())
    return Complaint.from_dict(rec) if rec else None


def _find_student(student_id: str) -> Student | None:
    """Find a Student by student_id, or None."""
    rec = DataHandler.find_by_id(STU_ENTITY, STU_ID_FIELD, student_id.strip().upper())
    return Student.from_dict(rec) if rec else None


def _next_cmp_id() -> str:
    """Generate next sequential complaint ID (e.g. CMP004)."""
    existing = [r.get(CMP_ID_FIELD, "") for r in DataHandler.get_all(CMP_ENTITY)]
    return generate_id("CMP", existing)


def _complaints_as_rows(complaints: list[Complaint]) -> list[list]:
    """
    Convert Complaint objects to display table rows.
    List comprehension: single clean transformation.
    """
    return [
        [
            c.complaint_id,
            truncate(c.student_name, 14),
            c.complaint_type,
            c.priority,
            c.status,
            c.filed_date,
        ]
        for c in complaints
    ]


def _print_complaint_detail(cmp: Complaint):
    """Print a full detail card for a single complaint."""
    print()
    print_line("-")
    print(f"  Complaint ID : {cmp.complaint_id}")
    print(f"  Student      : {cmp.student_id} - {cmp.student_name}")
    print(f"  Type         : {cmp.complaint_type}")
    print(f"  Priority     : {cmp.priority}")
    print(f"  Status       : {cmp.status}")
    print(f"  Filed On     : {cmp.filed_date}")
    if cmp.resolved_date:
        print(f"  Resolved On  : {cmp.resolved_date}")
    print(f"  Description  : {cmp.description}")
    if cmp.remarks:
        print(f"  Admin Remarks: {cmp.remarks}")
    print_line("-")
    print()


def _pick_from_list(prompt: str, options: list[str]) -> str:
    """
    Generic numbered picker: show a list and return the chosen item.
    Returns empty string if the user makes an invalid choice.
    """
    for i, opt in enumerate(options, 1):
        print(f"    [{i}]  {opt}")
    choice = input(f"\n  >  {prompt}: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return ""


def _status_summary(complaints: list[Complaint]):
    """Print a quick status summary line."""
    open_c      = sum(1 for c in complaints if c.status == "Open")
    in_prog     = sum(1 for c in complaints if c.status == "In Progress")
    resolved    = sum(1 for c in complaints if c.status == "Resolved")
    closed      = sum(1 for c in complaints if c.status == "Closed")
    print_line()
    print(f"  Total: {len(complaints)}  |  Open: {open_c}  |  "
          f"In Progress: {in_prog}  |  Resolved: {resolved}  |  Closed: {closed}")
    print_line()


# =======================================================================
#  FEATURE 1 - REGISTER COMPLAINT
# =======================================================================

def register_complaint(user: dict):
    """
    File a new complaint.
    - Admin can file on behalf of any student (enter student ID)
    - Student auto-fills their own ID from login session
    """
    clear_screen()
    print_banner()
    print_header("Register New Complaint")

    # Determine student
    if user.get("role") == "admin":
        student_id = input("  >  Student ID: ").strip().upper()
        if not student_id:
            print_error("Student ID cannot be empty.")
            pause()
            return
    else:
        student_id = user.get("username", "").upper()

    student = _find_student(student_id)
    if not student:
        print_error(f"Student '{student_id}' not found.")
        pause()
        return

    if not student.is_active:
        print_error(f"Student {student_id} is Inactive. Cannot file complaint.")
        pause()
        return

    print(f"\n  Filing for: {student_id} - {student.name}")

    # Select complaint type
    print("\n  Complaint Type:")
    cmp_type = _pick_from_list("Select type", COMPLAINT_TYPES)
    if not cmp_type:
        print_error("Invalid complaint type selection.")
        pause()
        return

    # Auto-suggest priority based on type
    suggested_priority = _type_priority_mapping(cmp_type)
    print(f"\n  Priority (suggested: {suggested_priority}):")
    priority = _pick_from_list("Select priority", PRIORITY_LEVELS)
    if not priority:
        priority = suggested_priority
        print_info(f"Using suggested priority: {priority}")

    # Description
    print()
    description = input("  >  Describe the complaint (min 10 chars): ").strip()
    if len(description) < 10:
        print_error("Description too short. Please provide at least 10 characters.")
        pause()
        return

    cmp_id   = _next_cmp_id()
    filed_on = current_date()

    print()
    print_line("-")
    print(f"  Complaint ID : {cmp_id}")
    print(f"  Student      : {student_id} - {student.name}")
    print(f"  Type         : {cmp_type}")
    print(f"  Priority     : {priority}")
    print(f"  Description  : {description}")
    print(f"  Filed On     : {filed_on}")
    print_line("-")

    if not confirm("Submit this complaint? (y/n)"):
        print_warning("Complaint submission cancelled.")
        pause()
        return

    new_cmp = Complaint(
        complaint_id   = cmp_id,
        student_id     = student_id,
        student_name   = student.name,
        complaint_type = cmp_type,
        description    = description,
        priority       = priority,
        status         = "Open",
        filed_date     = filed_on,
        resolved_date  = "",
        remarks        = "",
    )

    if DataHandler.insert(CMP_ENTITY, new_cmp.to_dict()):
        print_success(f"Complaint {cmp_id} filed successfully. Status: Open")
    else:
        print_error("Failed to save complaint. Check data files.")

    pause()


# =======================================================================
#  FEATURE 2 - VIEW ALL COMPLAINTS
# =======================================================================

def view_all_complaints():
    """Admin: display all complaints in a sortable table."""
    clear_screen()
    print_banner()
    print_header("All Complaints")

    complaints = _load_complaints()
    if not complaints:
        print_info("No complaints found.")
        pause()
        return

    print("\n  Sort by:")
    print("    [1]  Complaint ID (default)")
    print("    [2]  Priority (High first)")
    print("    [3]  Status (Open first)")
    print("    [4]  Student Name (A-Z)")
    print("    [5]  Filed Date (newest first)")
    sort_choice = input("\n  >  Choice (Enter for default): ").strip()

    # Priority order map for sorting
    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    # Status order for sorting
    stat_order = {"Open": 0, "In Progress": 1, "Resolved": 2, "Closed": 3}

    sort_map = {
        "2": lambda c: prio_order.get(c.priority, 99),
        "3": lambda c: stat_order.get(c.status, 99),
        "4": lambda c: c.student_name.lower(),
        "5": lambda c: c.filed_date,
    }
    key_fn     = sort_map.get(sort_choice, lambda c: c.complaint_id)
    reverse_5  = sort_choice == "5"   # newest first for dates
    complaints = sorted(complaints, key=key_fn, reverse=reverse_5)

    print_table(CMP_TABLE_HEADERS, _complaints_as_rows(complaints))
    _status_summary(complaints)

    # Offer detail view
    cmp_id_input = input("\n  >  Enter Complaint ID for full details (Enter to skip): ").strip().upper()
    if cmp_id_input:
        cmp = _find_complaint(cmp_id_input)
        if cmp:
            _print_complaint_detail(cmp)
        else:
            print_error(f"Complaint ID '{cmp_id_input}' not found.")

    pause()


# =======================================================================
#  FEATURE 3 - SEARCH COMPLAINT
# =======================================================================

def search_complaint():
    """Search complaints by ID, student ID/name, type, or keyword in description."""
    clear_screen()
    print_banner()
    print_header("Search Complaints")

    query = input("  >  Search (ID / Student ID / Name / Keyword): ").strip().lower()
    if not query:
        print_error("Search query cannot be empty.")
        pause()
        return

    all_complaints = _load_complaints()

    # List comprehension: multi-field search
    results = [
        c for c in all_complaints
        if query in c.complaint_id.lower()
        or query in c.student_id.lower()
        or query in c.student_name.lower()
        or query in c.complaint_type.lower()
        or query in c.description.lower()
        or query in c.status.lower()
    ]

    if not results:
        print_warning(f"No complaints found matching '{query}'.")
        pause()
        return

    print_success(f"{len(results)} complaint(s) found for '{query}':")
    print_table(CMP_TABLE_HEADERS, _complaints_as_rows(results))

    # Offer detail view
    if len(results) == 1:
        _print_complaint_detail(results[0])
    else:
        cmp_id_input = input("  >  Enter Complaint ID for full details (Enter to skip): ").strip().upper()
        if cmp_id_input:
            cmp = _find_complaint(cmp_id_input)
            if cmp:
                _print_complaint_detail(cmp)
            else:
                print_error(f"Complaint ID '{cmp_id_input}' not found.")

    pause()


# =======================================================================
#  FEATURE 4 - UPDATE COMPLAINT STATUS
# =======================================================================

def update_complaint_status():
    """
    Admin: move a complaint through the status flow.
    Valid transitions:
      Open  ->  In Progress  OR  Resolved  OR  Closed
      In Progress  ->  Resolved  OR  Closed
      Resolved  ->  Closed
    """
    clear_screen()
    print_banner()
    print_header("Update Complaint Status")

    cmp_id_input = input("  >  Enter Complaint ID: ").strip().upper()
    if not cmp_id_input:
        print_error("Complaint ID cannot be empty.")
        pause()
        return

    cmp = _find_complaint(cmp_id_input)
    if not cmp:
        print_error(f"Complaint ID '{cmp_id_input}' not found.")
        pause()
        return

    _print_complaint_detail(cmp)

    if cmp.status == "Closed":
        print_warning("This complaint is already Closed. No further updates allowed.")
        pause()
        return

    # Build valid next statuses based on current
    status_flow = {
        "Open":        ["In Progress", "Resolved", "Closed"],
        "In Progress": ["Resolved", "Closed"],
        "Resolved":    ["Closed"],
    }
    next_statuses = status_flow.get(cmp.status, [])

    print(f"  Current Status: {cmp.status}")
    print("\n  Change status to:")
    new_status = _pick_from_list("Select new status", next_statuses)
    if not new_status:
        print_error("Invalid status selection.")
        pause()
        return

    remarks = input("  >  Admin Remarks (optional): ").strip()

    print()
    print_line("-")
    print(f"  Complaint : {cmp.complaint_id}  ({cmp.complaint_type})")
    print(f"  Student   : {cmp.student_name}")
    print(f"  Change    : {cmp.status}  ->  {new_status}")
    print_line("-")

    if not confirm("Confirm status update? (y/n)"):
        print_warning("Update cancelled.")
        pause()
        return

    cmp.status = new_status
    if remarks:
        cmp.remarks = remarks
    if new_status in ("Resolved", "Closed") and not cmp.resolved_date:
        cmp.resolved_date = current_date()

    if _save_complaint(cmp):
        print_success(f"Complaint {cmp.complaint_id} updated to '{new_status}'.")
    else:
        print_error("Failed to save update. Check data files.")

    pause()


# =======================================================================
#  FEATURE 5 - RESOLVE COMPLAINT (QUICK ACTION)
# =======================================================================

def resolve_complaint():
    """
    Admin: quick-resolve a complaint - sets status to Resolved
    and records resolved_date and admin remarks.
    Separate from update_status for faster workflow.
    """
    clear_screen()
    print_banner()
    print_header("Resolve Complaint")

    cmp_id_input = input("  >  Enter Complaint ID to resolve: ").strip().upper()
    if not cmp_id_input:
        print_error("Complaint ID cannot be empty.")
        pause()
        return

    cmp = _find_complaint(cmp_id_input)
    if not cmp:
        print_error(f"Complaint ID '{cmp_id_input}' not found.")
        pause()
        return

    if cmp.status in ("Resolved", "Closed"):
        print_warning(f"Complaint {cmp_id_input} is already '{cmp.status}'.")
        pause()
        return

    _print_complaint_detail(cmp)

    remarks = input("  >  Resolution remarks (required): ").strip()
    if not remarks:
        print_error("Please provide resolution remarks before resolving.")
        pause()
        return

    if not confirm(f"Mark complaint {cmp_id_input} as Resolved? (y/n)"):
        print_warning("Resolve action cancelled.")
        pause()
        return

    cmp.status        = "Resolved"
    cmp.resolved_date = current_date()
    cmp.remarks       = remarks

    if _save_complaint(cmp):
        print_success(f"Complaint {cmp_id_input} marked as Resolved. Resolved on: {cmp.resolved_date}")
    else:
        print_error("Failed to save. Check data files.")

    pause()


# =======================================================================
#  FEATURE 6 - FILTER COMPLAINTS
# =======================================================================

def filter_complaints():
    """
    Filter complaints by status, type, or priority.
    Then sort filtered results by priority (High first) using lambda.
    """
    clear_screen()
    print_banner()
    print_header("Filter Complaints")

    print("  Filter by:")
    print("    [1]  Status")
    print("    [2]  Complaint Type")
    print("    [3]  Priority")
    print("    [4]  Open / Active (not resolved)")
    filter_choice = input("\n  >  Choice: ").strip()

    all_complaints = _load_complaints()
    filtered       = []

    if filter_choice == "1":
        print("\n  Status options:")
        status = _pick_from_list("Select status", COMPLAINT_STATUS)
        if not status:
            print_error("Invalid status.")
            pause()
            return
        # List comprehension filter
        filtered = [c for c in all_complaints if c.status == status]
        label    = f"Status = {status}"

    elif filter_choice == "2":
        print("\n  Complaint types:")
        cmp_type = _pick_from_list("Select type", COMPLAINT_TYPES)
        if not cmp_type:
            print_error("Invalid type.")
            pause()
            return
        filtered = [c for c in all_complaints if c.complaint_type == cmp_type]
        label    = f"Type = {cmp_type}"

    elif filter_choice == "3":
        print("\n  Priority levels:")
        priority = _pick_from_list("Select priority", PRIORITY_LEVELS)
        if not priority:
            print_error("Invalid priority.")
            pause()
            return
        filtered = [c for c in all_complaints if c.priority == priority]
        label    = f"Priority = {priority}"

    elif filter_choice == "4":
        # List comprehension: open (not resolved/closed)
        filtered = [c for c in all_complaints if c.is_open]
        label    = "Active (Open / In Progress)"

    else:
        print_error("Invalid filter choice.")
        pause()
        return

    if not filtered:
        print_warning(f"No complaints found for filter: {label}")
        pause()
        return

    # Lambda sort: High priority first, then by filed_date (newest first)
    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    filtered   = sorted(
        filtered,
        key=lambda c: (prio_order.get(c.priority, 99), c.filed_date),
        reverse=False   # ascending priority order, date secondary
    )

    print_success(f"{len(filtered)} complaint(s) found  [Filter: {label}]")
    print_table(CMP_TABLE_HEADERS, _complaints_as_rows(filtered))
    _status_summary(filtered)

    # Offer detail view
    cmp_id_input = input("  >  Enter Complaint ID for full details (Enter to skip): ").strip().upper()
    if cmp_id_input:
        cmp = _find_complaint(cmp_id_input)
        if cmp:
            _print_complaint_detail(cmp)
        else:
            print_error(f"Complaint ID '{cmp_id_input}' not found.")

    pause()


# =======================================================================
#  FEATURE 7 - EXPORT COMPLAINT REPORT CSV
# =======================================================================

def export_complaint_report():
    """Export complaints to a CSV file in the exports/ directory."""
    clear_screen()
    print_banner()
    print_header("Export Complaint Report")

    complaints = _load_complaints()
    if not complaints:
        print_info("No complaints to export.")
        pause()
        return

    print("  Export options:")
    print("    [1]  All complaints")
    print("    [2]  Open / Active only")
    print("    [3]  Resolved / Closed only")
    choice = input("\n  >  Choice (default: all): ").strip()

    filter_map = {
        "2": [c for c in complaints if c.is_open],
        "3": [c for c in complaints if c.status in ("Resolved", "Closed")],
    }
    export_data = filter_map.get(choice, complaints)

    if not export_data:
        print_warning("No records match the selected filter.")
        pause()
        return

    headers = [
        "Complaint ID", "Student ID", "Student Name",
        "Type", "Priority", "Status",
        "Filed Date", "Resolved Date", "Description", "Remarks"
    ]

    # Generator expression for rows (lazy evaluation)
    rows = list(
        (
            c.complaint_id, c.student_id, c.student_name,
            c.complaint_type, c.priority, c.status,
            c.filed_date, c.resolved_date,
            c.description, c.remarks
        )
        for c in export_data
    )

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"complaint_report_{date_str}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    if export_to_csv(filepath, headers, rows):
        print_success(f"Complaint report exported: exports/{filename}  ({len(rows)} record(s))")
    else:
        print_error("Export failed. Check write permissions.")

    pause()


# =======================================================================
#  STUDENT VIEW - MY COMPLAINTS
# =======================================================================

def _view_my_complaints(user: dict):
    """Student: view their own complaints and file new ones."""
    clear_screen()
    print_banner()
    print_header("My Complaints")

    student_id = user.get("username", "")
    all_cmp    = _load_complaints()

    # List comprehension: only this student's complaints, newest first
    my_cmp = sorted(
        [c for c in all_cmp if c.student_id == student_id],
        key=lambda c: c.filed_date,
        reverse=True
    )

    if not my_cmp:
        print_info("You have no complaints on file.")
    else:
        print_table(CMP_TABLE_HEADERS, _complaints_as_rows(my_cmp))
        open_count = sum(1 for c in my_cmp if c.is_open)
        print_line()
        print(f"  Total: {len(my_cmp)}  |  Active: {open_count}  |  "
              f"Resolved: {len(my_cmp) - open_count}")
        print_line()

        # Offer detail view
        cmp_id_input = input("\n  >  Enter Complaint ID for full details (Enter to skip): ").strip().upper()
        if cmp_id_input:
            cmp = _find_complaint(cmp_id_input)
            if cmp and cmp.student_id == student_id:
                _print_complaint_detail(cmp)
            elif cmp:
                print_error("You can only view your own complaints.")
            else:
                print_error(f"Complaint ID '{cmp_id_input}' not found.")

    pause()


# =======================================================================
#  COMPLAINT MENU ENTRY POINT
# =======================================================================

_ADMIN_OPTIONS = [
    "[1] View All Complaints",
    "[2] Register Complaint (on behalf of student)",
    "[3] Search Complaint",
    "[4] Update Complaint Status",
    "[5] Resolve Complaint (Quick)",
    "[6] Filter Complaints",
    "[7] Export Complaint Report (CSV)",
    "[8] Back to Main Menu",
]

_STUDENT_OPTIONS = [
    "[1] My Complaints",
    "[2] File New Complaint",
    "[3] Back to Main Menu",
]


def complaint_menu(user: dict):
    """Entry point called from main.py. Role-based routing."""
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Complaint Management", _ADMIN_OPTIONS)

            if choice == "1":
                view_all_complaints()
            elif choice == "2":
                register_complaint(user)
            elif choice == "3":
                search_complaint()
            elif choice == "4":
                update_complaint_status()
            elif choice == "5":
                resolve_complaint()
            elif choice == "6":
                filter_complaints()
            elif choice == "7":
                export_complaint_report()
            elif choice == "8":
                break
            else:
                print_error("Invalid choice. Enter a number between 1 and 8.")
                pause()

        else:
            # Student: file and view own complaints
            choice = print_menu("My Complaints", _STUDENT_OPTIONS)

            if choice == "1":
                _view_my_complaints(user)
            elif choice == "2":
                register_complaint(user)
            elif choice == "3":
                break
            else:
                print_error("Invalid choice.")
                pause()
