"""
notice_manager.py - Notice Board Module (Phase 5)

Features (Admin):
  1. Add Notice     - create a new notice with category and importance flag
  2. View Notices   - newest first, with [!] IMPORTANT tag
  3. Delete Notice  - by notice ID with confirmation

Features (Student):
  - View all active notices (read-only)

Rules:
  - Newest notices displayed first (sorted by posted_date desc)
  - Admin-only: add and delete notices
  - Students: view only
"""

import os
from datetime import datetime

from models.notice      import Notice, NOTICE_CATEGORIES
from database.db_handler import DataHandler
from utils.display      import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)
from utils.helpers      import generate_id, current_date, truncate

# -- Constants ---------------------------------------------------------
NOT_ENTITY   = "notices"
NOT_ID_FIELD = "notice_id"

NOT_TABLE_HEADERS = ["Notice ID", "Category", "Title", "Posted By", "Posted On", "Important"]


# =======================================================================
#  INTERNAL HELPERS
# =======================================================================

def _load_notices() -> list[Notice]:
    """Load all notices as Notice objects, newest first."""
    all_n = [Notice.from_dict(r) for r in DataHandler.get_all(NOT_ENTITY)]
    # Lambda sort: newest posted_date first
    return sorted(all_n, key=lambda n: n.posted_date, reverse=True)


def _next_notice_id() -> str:
    """Generate the next sequential notice ID (e.g. NOT004)."""
    existing = [r.get(NOT_ID_FIELD, "") for r in DataHandler.get_all(NOT_ENTITY)]
    return generate_id("NOT", existing)


def _notices_as_rows(notices: list[Notice]) -> list[list]:
    """List comprehension: Notice objects to display table rows."""
    return [
        [
            n.notice_id,
            n.category,
            truncate(n.title, 30),
            n.posted_by,
            n.posted_date,
            "[!]" if n.is_important else "  -",
        ]
        for n in notices
    ]


def _print_notice_full(n: Notice):
    """Print the full content of a notice card."""
    print()
    print_line("-")
    tag = "  [!] IMPORTANT" if n.is_important else ""
    print(f"  [{n.notice_id}]  {n.title.upper()}{tag}")
    print(f"  Category : {n.category}")
    print(f"  Posted By: {n.posted_by}  |  Date: {n.posted_date}")
    if n.expiry_date:
        print(f"  Expires  : {n.expiry_date}")
    print()
    # Word-wrap content at 60 chars
    words   = n.content.split()
    line_buf = "  "
    for word in words:
        if len(line_buf) + len(word) + 1 > 62:
            print(line_buf)
            line_buf = "  " + word + " "
        else:
            line_buf += word + " "
    if line_buf.strip():
        print(line_buf)
    print_line("-")
    print()


# =======================================================================
#  FEATURE 1 - ADD NOTICE
# =======================================================================

def add_notice(user: dict):
    """Admin: create and post a new notice."""
    clear_screen()
    print_banner()
    print_header("Add New Notice")

    # Title
    title = input("  >  Notice Title: ").strip()
    if len(title) < 5:
        print_error("Title too short. Minimum 5 characters.")
        pause()
        return

    # Category
    print("\n  Category:")
    for i, cat in enumerate(NOTICE_CATEGORIES, 1):
        print(f"    [{i}]  {cat}")
    cat_choice = input("\n  >  Category (Enter for General): ").strip()
    try:
        cat_idx  = int(cat_choice) - 1
        category = NOTICE_CATEGORIES[cat_idx] if 0 <= cat_idx < len(NOTICE_CATEGORIES) else "General"
    except (ValueError, IndexError):
        category = "General"

    # Content / message
    print("\n  Notice Content (type your message, Enter twice to finish):")
    lines = []
    while True:
        line = input("  ")
        if not line and lines:
            break
        lines.append(line)
    content = " ".join(lines).strip()
    if len(content) < 10:
        print_error("Content too short. Please provide at least 10 characters.")
        pause()
        return

    # Expiry date
    expiry = input("\n  >  Expiry Date (YYYY-MM-DD, Enter to skip): ").strip()
    if expiry:
        try:
            datetime.strptime(expiry, "%Y-%m-%d")
        except ValueError:
            print_warning("Invalid expiry date format. Skipping.")
            expiry = ""

    # Important flag
    is_important_input = input("\n  >  Mark as Important? (y/n): ").strip().lower()
    is_important = is_important_input in ("y", "yes")

    notice_id = _next_notice_id()
    posted_by = user.get("username", "Admin")

    print()
    print_line("-")
    print(f"  Notice ID : {notice_id}")
    print(f"  Title     : {title}")
    print(f"  Category  : {category}")
    print(f"  Important : {'Yes' if is_important else 'No'}")
    print(f"  Posted By : {posted_by}")
    print(f"  Content   : {truncate(content, 55)}")
    print_line("-")

    if not confirm("Post this notice? (y/n)"):
        print_warning("Notice cancelled.")
        pause()
        return

    new_notice = Notice(
        notice_id    = notice_id,
        title        = title,
        content      = content,
        category     = category,
        posted_by    = posted_by,
        posted_date  = current_date(),
        expiry_date  = expiry,
        is_important = is_important,
    )

    if DataHandler.insert(NOT_ENTITY, new_notice.to_dict()):
        print_success(f"Notice {notice_id} posted: '{title}'")
    else:
        print_error("Failed to save notice.")

    pause()


# =======================================================================
#  FEATURE 2 - VIEW NOTICES
# =======================================================================

def view_notices():
    """View all notices - newest first. Shared by admin and students."""
    clear_screen()
    print_banner()
    print_header("Notice Board")

    notices = _load_notices()   # already sorted newest first

    if not notices:
        print_info("No notices have been posted yet.")
        pause()
        return

    # Pin important notices at top, then rest newest first
    important = [n for n in notices if n.is_important]
    regular   = [n for n in notices if not n.is_important]
    ordered   = important + regular

    print_table(NOT_TABLE_HEADERS, _notices_as_rows(ordered))
    print_line()
    print(f"  Total: {len(ordered)}  |  Important: {len(important)}  |  Regular: {len(regular)}")
    print_line()

    # Offer full read
    nid_input = input("\n  >  Enter Notice ID to read full content (Enter to skip): ").strip().upper()
    if nid_input:
        rec = DataHandler.find_by_id(NOT_ENTITY, NOT_ID_FIELD, nid_input)
        if rec:
            _print_notice_full(Notice.from_dict(rec))
        else:
            print_error(f"Notice ID '{nid_input}' not found.")

    pause()


# =======================================================================
#  FEATURE 3 - DELETE NOTICE
# =======================================================================

def delete_notice():
    """Admin: delete a notice by ID with confirmation."""
    clear_screen()
    print_banner()
    print_header("Delete Notice")

    notices = _load_notices()
    if not notices:
        print_info("No notices to delete.")
        pause()
        return

    print_table(NOT_TABLE_HEADERS, _notices_as_rows(notices))

    nid_input = input("  >  Enter Notice ID to delete: ").strip().upper()
    if not nid_input:
        print_error("Notice ID cannot be empty.")
        pause()
        return

    rec = DataHandler.find_by_id(NOT_ENTITY, NOT_ID_FIELD, nid_input)
    if not rec:
        print_error(f"Notice ID '{nid_input}' not found.")
        pause()
        return

    notice = Notice.from_dict(rec)
    print()
    print_line("-")
    print(f"  Notice ID : {notice.notice_id}")
    print(f"  Title     : {notice.title}")
    print(f"  Category  : {notice.category}")
    print(f"  Posted On : {notice.posted_date}")
    print_line("-")

    if not confirm(f"Delete notice '{notice.title}'? This cannot be undone. (y/n)"):
        print_warning("Delete cancelled.")
        pause()
        return

    if DataHandler.delete(NOT_ENTITY, NOT_ID_FIELD, nid_input):
        print_success(f"Notice {nid_input} deleted.")
    else:
        print_error("Failed to delete notice.")

    pause()


# =======================================================================
#  NOTICE MENU ENTRY POINT
# =======================================================================

_ADMIN_OPTIONS = [
    "[1] View All Notices",
    "[2] Post New Notice",
    "[3] Delete Notice",
    "[4] Back to Main Menu",
]

_STUDENT_OPTIONS = [
    "[1] View Notice Board",
    "[2] Back to Main Menu",
]


def notice_menu(user: dict):
    """Entry point called from main.py. Role-based routing."""
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Notice Board", _ADMIN_OPTIONS)

            if choice == "1":
                view_notices()
            elif choice == "2":
                add_notice(user)
            elif choice == "3":
                delete_notice()
            elif choice == "4":
                break
            else:
                print_error("Invalid choice. Enter 1 to 4.")
                pause()

        else:
            # Students: view only
            choice = print_menu("Notice Board", _STUDENT_OPTIONS)

            if choice == "1":
                view_notices()
            elif choice == "2":
                break
            else:
                print_error("Invalid choice.")
                pause()
