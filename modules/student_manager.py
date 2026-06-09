"""
student_manager.py - Student Management Module (Phase 2)

Features:
  1. Register Student
  2. View All Students  (sortable by name / course)
  3. Search Student     (by ID, name, or mobile - recursive helper)
  4. Update Student Details
  5. Delete Student Record
  6. Export Students to CSV

Uses: DataHandler, Student model, display utilities, validators.
"""

import os
from models.student import Student
from database.db_handler import DataHandler
from utils.helpers import generate_id, current_date, export_to_csv, title_case, truncate
from utils.validators import is_non_empty, is_valid_mobile, is_valid_year, validate_input
from utils.display import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)

# -- Constants ---------------------------------------------------------
ENTITY       = "students"
ID_FIELD     = "student_id"
ID_PREFIX    = "STU"

# Table columns and matching field widths for print_table
TABLE_HEADERS  = ["ID", "Name", "Course", "Year", "Mobile", "Room", "Status"]
TABLE_WIDTHS   = [8, 18, 16, 5, 12, 14, 8]

# Courses offered (for display reference)
COURSES = [
    "B.Tech CSE", "B.Tech ECE", "B.Tech ME", "B.Tech CE",
    "B.Sc Physics", "B.Sc Chemistry", "B.Sc Maths",
    "BCA", "MCA", "MBA", "M.Tech", "B.Com", "B.A.", "Other",
]

# Exports directory path (relative to project root)
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "exports")


# =======================================================================
#  HELPER FUNCTIONS
# =======================================================================

def _students_as_rows(students: list[dict]) -> list[list]:
    """
    Convert a list of student dicts to display rows for print_table.
    Uses a list comprehension for clean, concise transformation.
    """
    return [
        [
            s.get("student_id", ""),
            truncate(s.get("name", ""), 17),
            truncate(s.get("course", ""), 15),
            s.get("year", ""),
            s.get("mobile", ""),
            truncate(s.get("room_number", "Not Allocated"), 13),
            "Active" if s.get("is_active") else "Inactive",
        ]
        for s in students
    ]


def _print_student_detail(student: dict):
    """Print a full-detail view of a single student record."""
    s = Student.from_dict(student)
    print()
    print_line("-")
    print(f"  Student ID   : {s.student_id}")
    print(f"  Name         : {s.name}")
    print(f"  Course       : {s.course}")
    print(f"  Year         : {s.year}")
    print(f"  Mobile       : {s.mobile}")
    print(f"  Address      : {s.address}")
    print(f"  Room         : {s.room_number}")
    print(f"  Joined Date  : {s.joined_date}")
    print(f"  Status       : {'Active' if s.is_active else 'Inactive'}")
    print_line("-")
    print()


def _search_recursive(students: list[dict], query: str, index: int = 0) -> list[dict]:
    """
    Recursively search through the students list for records matching
    the query string against ID, name, or mobile fields.

    Args:
        students: Full list of student dicts
        query:    Case-insensitive search term
        index:    Current position in the list (used by recursion)
    Returns:
        List of matching student dicts
    """
    # Base case: reached end of list
    if index >= len(students):
        return []

    current = students[index]
    q = query.strip().lower()

    # Check if current record matches any searchable field
    is_match = any(
        q in str(current.get(field, "")).lower()
        for field in ("student_id", "name", "mobile", "course")
    )

    # Recurse on the rest of the list
    rest = _search_recursive(students, query, index + 1)

    return ([current] + rest) if is_match else rest


def _get_prompted_input(prompt: str, validators: list, allow_skip: bool = False) -> str | None:
    """
    Prompt the user for input and run validators.
    Retries up to 3 times on invalid input.
    Returns the valid value, or None if allow_skip and user enters blank.

    Args:
        prompt:      Display label
        validators:  List of validator functions
        allow_skip:  If True, blank input means "keep current value"
    Returns:
        Validated string, or None if skipped
    """
    for attempt in range(1, 4):
        raw = input(f"  >  {prompt}: ").strip()

        if allow_skip and raw == "":
            return None   # caller interprets None as "keep unchanged"

        ok, msg = validate_input(raw, validators)
        if ok:
            return raw

        print_error(f"{msg}  (Attempt {attempt}/3)")

    print_error("Too many invalid attempts. Returning to menu.")
    return "__ABORT__"   # sentinel - caller returns early


# =======================================================================
#  FEATURE 1 - REGISTER STUDENT
# =======================================================================

def register_student():
    """Collect details and register a new student."""
    clear_screen()
    print_banner()
    print_header("Register New Student")

    # -- Auto-generate next student ID ---------------------------------
    existing_ids = [s.get(ID_FIELD, "") for s in DataHandler.get_all(ENTITY)]
    new_id       = generate_id(ID_PREFIX, existing_ids)
    print(f"\n  Auto-assigned Student ID : {new_id}")
    print_line("-")

    # -- Collect fields with validation --------------------------------
    name = _get_prompted_input("Full Name", [
        lambda v: is_non_empty(v, "Name"),
        lambda v: (True, "") if len(v.strip()) >= 2 else (False, "Name must be at least 2 characters."),
    ])
    if name in (None, "__ABORT__"):
        print_warning("Registration cancelled.")
        pause()
        return

    # Course: show options, accept free text
    print("\n  Available Courses:")
    for i, c in enumerate(COURSES, 1):
        print(f"    [{i:>2}] {c}")
    course_input = input("\n  >  Course (number or type manually): ").strip()
    if course_input.isdigit() and 1 <= int(course_input) <= len(COURSES):
        course = COURSES[int(course_input) - 1]
    elif course_input:
        course = course_input.title()
    else:
        print_warning("Course cannot be empty. Registration cancelled.")
        pause()
        return

    year = _get_prompted_input("Academic Year (1-4)", [
        lambda v: is_non_empty(v, "Year"),
        is_valid_year,
    ])
    if year in (None, "__ABORT__"):
        print_warning("Registration cancelled.")
        pause()
        return

    mobile = _get_prompted_input("Mobile Number (10 digits)", [
        lambda v: is_non_empty(v, "Mobile"),
        is_valid_mobile,
    ])
    if mobile in (None, "__ABORT__"):
        print_warning("Registration cancelled.")
        pause()
        return

    address = _get_prompted_input("Address", [
        lambda v: is_non_empty(v, "Address"),
    ])
    if address in (None, "__ABORT__"):
        print_warning("Registration cancelled.")
        pause()
        return

    # -- Check for duplicate mobile number -----------------------------
    duplicate = [
        s for s in DataHandler.get_all(ENTITY)
        if s.get("mobile") == mobile
    ]
    if duplicate:
        print_error(f"Mobile {mobile} is already registered to {duplicate[0].get('name')}.")
        pause()
        return

    # -- Build Student object and persist ------------------------------
    student = Student(
        student_id  = new_id,
        name        = title_case(name),
        course      = course,
        year        = int(year),
        mobile      = mobile,
        address     = address.strip(),
        joined_date = current_date(),
        is_active   = True,
    )

    # Preview before saving
    print()
    print_header("Confirm New Student Record")
    _print_student_detail(student.to_dict())

    if not confirm("Save this student? (y/n)"):
        print_warning("Registration cancelled.")
        pause()
        return

    if DataHandler.insert(ENTITY, student.to_dict()):
        # Also add a user login entry so student can log in
        _register_student_user(new_id, student.name)
        print_success(f"Student {new_id} - {student.name} registered successfully!")
    else:
        print_error("Failed to save student. Please try again.")

    pause()


def _register_student_user(student_id: str, name: str):
    """
    Add a login entry in users.json for the new student.
    Default password = student_id (lowercased) - e.g., 'stu004'.
    """
    from database.db_handler import DataHandler as DH
    users = DH.get_all("users")
    # Avoid duplicate user entries
    if any(u.get("username") == student_id for u in users):
        return
    default_password = student_id.lower()
    DH.insert("users", {
        "username": student_id,
        "password": default_password,
        "role":     "student",
        "name":     name,
    })


# =======================================================================
#  FEATURE 2 - VIEW ALL STUDENTS
# =======================================================================

def view_all_students():
    """Display all students in a table with sort options."""
    clear_screen()
    print_banner()
    print_header("All Students")

    students = DataHandler.get_all(ENTITY)
    if not students:
        print_info("No students registered yet.")
        pause()
        return

    # -- Sort options using lambdas ------------------------------------
    print("\n  Sort by:")
    print("    [1]  Student ID (default)")
    print("    [2]  Name (A -> Z)")
    print("    [3]  Course")
    print("    [4]  Year")
    sort_choice = input("\n  >  Choice (press Enter for default): ").strip()

    sort_key_map = {
        "2": lambda s: s.get("name", "").lower(),
        "3": lambda s: s.get("course", "").lower(),
        "4": lambda s: int(s.get("year", 0)),
    }
    sort_key = sort_key_map.get(sort_choice, lambda s: s.get("student_id", ""))
    sorted_students = sorted(students, key=sort_key)

    # -- Print table ---------------------------------------------------
    print_line()
    rows = _students_as_rows(sorted_students)
    print_table(TABLE_HEADERS, rows)

    # -- Summary footer ------------------------------------------------
    total    = len(students)
    active   = sum(1 for s in students if s.get("is_active"))
    inactive = total - active
    print(f"  Total: {total}  |  Active: {active}  |  Inactive: {inactive}")
    print_line()
    pause()


# =======================================================================
#  FEATURE 3 - SEARCH STUDENT
# =======================================================================

def search_student():
    """Search for students using a recursive search helper."""
    clear_screen()
    print_banner()
    print_header("Search Student")

    print("\n  Search by: Student ID, Name, Mobile, or Course")
    query = input("  >  Enter search term: ").strip()

    if not query:
        print_error("Search term cannot be empty.")
        pause()
        return

    all_students = DataHandler.get_all(ENTITY)

    # Use the recursive search function
    results = _search_recursive(all_students, query)

    if not results:
        print_warning(f"No students found matching '{query}'.")
        pause()
        return

    print_success(f"Found {len(results)} result(s) for '{query}':")
    rows = _students_as_rows(results)
    print_table(TABLE_HEADERS, rows)

    # Offer to view full detail of a specific result
    if len(results) == 1:
        if confirm("View full details of this student? (y/n)"):
            _print_student_detail(results[0])
    else:
        view_id = input("  >  Enter Student ID for full details (or press Enter to skip): ").strip()
        if view_id:
            matched = next((s for s in results if s.get("student_id", "").upper() == view_id.upper()), None)
            if matched:
                _print_student_detail(matched)
            else:
                print_error(f"Student ID '{view_id}' not found in results.")

    pause()


# =======================================================================
#  FEATURE 4 - UPDATE STUDENT DETAILS
# =======================================================================

def update_student():
    """Update editable fields of an existing student record."""
    clear_screen()
    print_banner()
    print_header("Update Student Details")

    student_id = input("  >  Enter Student ID to update: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    record = DataHandler.find_by_id(ENTITY, ID_FIELD, student_id)
    if not record:
        print_error(f"Student ID '{student_id}' not found.")
        pause()
        return

    # Show current details
    print_info("Current details (press Enter on any field to keep unchanged):")
    _print_student_detail(record)

    s = Student.from_dict(record)

    # -- Collect updated values (all fields optional / skippable) ------
    print("  Leave field blank to keep current value.\n")

    new_name = _get_prompted_input(f"Name [{s.name}]", [
        lambda v: (True, "") if not v else is_non_empty(v, "Name"),
    ], allow_skip=True)
    if new_name == "__ABORT__":
        pause()
        return

    new_year = _get_prompted_input(f"Year [{s.year}]", [
        lambda v: (True, "") if not v else is_valid_year(v),
    ], allow_skip=True)
    if new_year == "__ABORT__":
        pause()
        return

    new_mobile = _get_prompted_input(f"Mobile [{s.mobile}]", [
        lambda v: (True, "") if not v else is_valid_mobile(v),
    ], allow_skip=True)
    if new_mobile == "__ABORT__":
        pause()
        return

    # Check new mobile doesn't clash with another student
    if new_mobile:
        clash = [
            st for st in DataHandler.get_all(ENTITY)
            if st.get("mobile") == new_mobile and st.get("student_id") != student_id
        ]
        if clash:
            print_error(f"Mobile {new_mobile} is already used by {clash[0].get('name')}.")
            pause()
            return

    new_address = _get_prompted_input(f"Address [{s.address}]", [
        lambda v: (True, "") if not v else is_non_empty(v, "Address"),
    ], allow_skip=True)
    if new_address == "__ABORT__":
        pause()
        return

    # -- Apply changes only where new value was provided ---------------
    updated = Student(
        student_id  = s.student_id,
        name        = title_case(new_name) if new_name else s.name,
        course      = s.course,           # course change requires re-allocation; keep for now
        year        = int(new_year) if new_year else s.year,
        mobile      = new_mobile   if new_mobile   else s.mobile,
        address     = new_address  if new_address  else s.address,
        room_number = s.room_number,
        joined_date = s.joined_date,
        is_active   = s.is_active,
    )

    # Preview
    print_header("Confirm Updated Record")
    _print_student_detail(updated.to_dict())

    if not confirm("Save these changes? (y/n)"):
        print_warning("Update cancelled.")
        pause()
        return

    if DataHandler.update(ENTITY, ID_FIELD, student_id, updated.to_dict()):
        # Sync display name in users.json as well
        _sync_user_name(student_id, updated.name)
        print_success(f"Student {student_id} updated successfully!")
    else:
        print_error("Update failed. Please try again.")

    pause()


def _sync_user_name(student_id: str, new_name: str):
    """Keep the name in users.json in sync when a student name changes."""
    users = DataHandler.get_all("users")
    for u in users:
        if u.get("username") == student_id:
            u["name"] = new_name
    DataHandler.save("users", users)


# =======================================================================
#  FEATURE 5 - DELETE STUDENT RECORD
# =======================================================================

def delete_student():
    """Soft-delete a student (set is_active = False) or hard-delete on confirmation."""
    clear_screen()
    print_banner()
    print_header("Delete Student Record")

    student_id = input("  >  Enter Student ID to delete: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    record = DataHandler.find_by_id(ENTITY, ID_FIELD, student_id)
    if not record:
        print_error(f"Student ID '{student_id}' not found.")
        pause()
        return

    _print_student_detail(record)

    print("  Delete options:")
    print("    [1]  Soft Delete  (mark as Inactive - keeps record)")
    print("    [2]  Hard Delete  (permanently remove record)")
    print("    [3]  Cancel")
    choice = input("\n  >  Choice: ").strip()

    if choice == "1":
        if not confirm(f"Mark {student_id} as Inactive? (y/n)"):
            print_warning("Cancelled.")
            pause()
            return
        record["is_active"] = False
        if DataHandler.update(ENTITY, ID_FIELD, student_id, record):
            print_success(f"Student {student_id} marked as Inactive.")
        else:
            print_error("Operation failed.")

    elif choice == "2":
        if not confirm(f"PERMANENTLY delete {student_id} - {record.get('name')}? (y/n)"):
            print_warning("Cancelled.")
            pause()
            return
        if DataHandler.delete(ENTITY, ID_FIELD, student_id):
            # Also remove from users.json
            _remove_student_user(student_id)
            print_success(f"Student {student_id} permanently deleted.")
        else:
            print_error("Delete failed. Please try again.")

    else:
        print_warning("Delete cancelled.")

    pause()


def _remove_student_user(student_id: str):
    """Remove the student's login entry from users.json."""
    users = DataHandler.get_all("users")
    updated_users = [u for u in users if u.get("username") != student_id]
    DataHandler.save("users", updated_users)


# =======================================================================
#  FEATURE 6 - EXPORT STUDENTS TO CSV
# =======================================================================

def export_students():
    """Export all student records to a CSV file in the exports/ directory."""
    clear_screen()
    print_banner()
    print_header("Export Students to CSV")

    students = DataHandler.get_all(ENTITY)
    if not students:
        print_info("No students to export.")
        pause()
        return

    headers = ["Student ID", "Name", "Course", "Year", "Mobile", "Address",
               "Room Number", "Joined Date", "Status"]
    rows = [
        [
            s.get("student_id", ""),
            s.get("name", ""),
            s.get("course", ""),
            s.get("year", ""),
            s.get("mobile", ""),
            s.get("address", ""),
            s.get("room_number", ""),
            s.get("joined_date", ""),
            "Active" if s.get("is_active") else "Inactive",
        ]
        for s in students
    ]

    from utils.helpers import current_date
    filename  = f"students_export_{current_date()}.csv"
    filepath  = os.path.join(EXPORTS_DIR, filename)

    if export_to_csv(filepath, headers, rows):
        print_success(f"Exported {len(students)} student(s) to:")
        print(f"  {os.path.abspath(filepath)}\n")
    else:
        print_error("Export failed. Check file permissions.")

    pause()


# =======================================================================
#  STUDENT MODULE MENU ENTRY POINT
# =======================================================================

# Admin menu options
_ADMIN_OPTIONS = [
    "[1] Register New Student",
    "[2] View All Students",
    "[3] Search Student",
    "[4] Update Student Details",
    "[5] Delete Student",
    "[6] Export Students to CSV",
    "[7] Back to Main Menu",
]

# Student self-view options (read-only)
_STUDENT_OPTIONS = [
    "[1] View My Profile",
    "[2] Back to Main Menu",
]


def student_menu(user: dict):
    """
    Entry point called from main.py.
    Shows admin menu or student self-view based on the logged-in role.
    """
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Student Management", _ADMIN_OPTIONS)

            if choice == "1":
                register_student()
            elif choice == "2":
                view_all_students()
            elif choice == "3":
                search_student()
            elif choice == "4":
                update_student()
            elif choice == "5":
                delete_student()
            elif choice == "6":
                export_students()
            elif choice == "7":
                break
            else:
                print_error("Invalid choice. Enter a number between 1 and 7.")
                pause()

        else:
            # Student: can only view their own profile
            choice = print_menu("My Profile", _STUDENT_OPTIONS)

            if choice == "1":
                _view_own_profile(user)
            elif choice == "2":
                break
            else:
                print_error("Invalid choice.")
                pause()


def _view_own_profile(user: dict):
    """Allow a logged-in student to view their own profile."""
    clear_screen()
    print_banner()
    print_header("My Profile")

    student_id = user.get("username", "")
    record = DataHandler.find_by_id(ENTITY, ID_FIELD, student_id)

    if not record:
        print_warning("Your student profile was not found. Contact the admin.")
    else:
        _print_student_detail(record)

    pause()
