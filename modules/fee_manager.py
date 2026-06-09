"""
fee_manager.py - Fee Management Module (Phase 4)

Features:
  1. Generate Fee Record       (admin: create new fee for a student)
  2. View Fee Records          (admin: all records, sortable)
  3. Pay Hostel Fee            (admin: record a payment)
  4. View Pending Fees         (admin + student: show dues)
  5. Calculate / Apply Fine    (admin: compute and store late fines)
  6. Generate Fee Receipt      (print formatted receipt to terminal)
  7. Export Fee Report CSV     (admin: export to exports/)
  8. [Student] My Fee Status   (student: view own fee records)

Validation Rules:
  - Payment amount must be > 0
  - Payment cannot exceed outstanding balance (amount_due + fine - amount_paid)
  - Student must exist before generating a fee
  - Duplicate fee for same student+month prompts a warning (not blocked)
  - Fine is auto-calculated from due_date using LATE_FINE_PER_DAY constant

Uses: FeeRecord model, Student model, DataHandler, display utilities, helpers.
"""

import os
from datetime import datetime

from models.fee      import FeeRecord, FEE_STATUS, LATE_FINE_PER_DAY, FINE_GRACE_DAYS
from models.student  import Student
from database.db_handler import DataHandler
from utils.display   import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)
from utils.helpers   import (
    generate_id, export_to_csv, current_date, format_date, truncate
)

# -- Constants ---------------------------------------------------------
FEE_ENTITY     = "fees"
STU_ENTITY     = "students"
FEE_ID_FIELD   = "fee_id"
STU_ID_FIELD   = "student_id"
EXPORT_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "exports")

FEE_TABLE_HEADERS = ["Fee ID", "Student", "Month", "Due", "Paid", "Fine", "Balance", "Status"]


# =======================================================================
#  INTERNAL HELPERS
# =======================================================================

def _load_fees() -> list[FeeRecord]:
    """Load all fee records as FeeRecord objects."""
    return [FeeRecord.from_dict(r) for r in DataHandler.get_all(FEE_ENTITY)]


def _save_fee(fee: FeeRecord) -> bool:
    """Persist a single updated FeeRecord."""
    return DataHandler.update(FEE_ENTITY, FEE_ID_FIELD, fee.fee_id, fee.to_dict())


def _find_fee(fee_id: str) -> FeeRecord | None:
    """Find a FeeRecord by fee_id, or None."""
    rec = DataHandler.find_by_id(FEE_ENTITY, FEE_ID_FIELD, fee_id.strip().upper())
    return FeeRecord.from_dict(rec) if rec else None


def _find_student(student_id: str) -> Student | None:
    """Find a Student by student_id, or None."""
    rec = DataHandler.find_by_id(STU_ENTITY, STU_ID_FIELD, student_id.strip().upper())
    return Student.from_dict(rec) if rec else None


def _fees_as_rows(fees: list[FeeRecord]) -> list[list]:
    """
    Convert FeeRecord objects to display rows.
    Uses a list comprehension for clean transformation.
    """
    return [
        [
            f.fee_id,
            truncate(f.student_name, 14),
            f.month,
            f"Rs.{f.amount_due:.0f}",
            f"Rs.{f.amount_paid:.0f}",
            f"Rs.{f.fine_amount:.0f}",
            f"Rs.{f.balance:.0f}",
            f.status,
        ]
        for f in fees
    ]


def _next_fee_id() -> str:
    """Generate the next sequential fee ID (e.g. FEE004)."""
    existing = [r.get(FEE_ID_FIELD, "") for r in DataHandler.get_all(FEE_ENTITY)]
    return generate_id("FEE", existing)


def _print_fee_detail(fee: FeeRecord):
    """Print a full detail card for a single fee record."""
    print()
    print_line("-")
    print(f"  Fee ID       : {fee.fee_id}")
    print(f"  Student      : {fee.student_id} - {fee.student_name}")
    print(f"  Month        : {fee.month}")
    print(f"  Due Date     : {format_date(fee.due_date) if fee.due_date else 'N/A'}")
    print(f"  Amount Due   : Rs.{fee.amount_due:,.2f}")
    print(f"  Amount Paid  : Rs.{fee.amount_paid:,.2f}")
    print(f"  Fine Amount  : Rs.{fee.fine_amount:,.2f}")
    print(f"  Balance      : Rs.{fee.balance:,.2f}")
    print(f"  Status       : {fee.status}")
    if fee.is_overdue:
        print(f"  Overdue      : {fee.days_overdue} day(s) past due date")
    if fee.payment_date:
        print(f"  Paid On      : {format_date(fee.payment_date)}")
    if fee.remarks:
        print(f"  Remarks      : {fee.remarks}")
    print_line("-")
    print()


# =======================================================================
#  FEATURE 1 - GENERATE FEE RECORD
# =======================================================================

def generate_fee_record():
    """
    Admin: create a new fee record for a student.
    - Validates student existence
    - Warns if a fee for same student+month already exists
    - Prompts for amount and due date
    """
    clear_screen()
    print_banner()
    print_header("Generate Fee Record")

    student_id = input("  >  Enter Student ID: ").strip().upper()
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
        print_error(f"Student {student_id} is Inactive. Cannot generate fee.")
        pause()
        return

    print(f"\n  Student: {student_id} - {student.name} | {student.course} Year-{student.year}")

    # Month input
    current_month = datetime.now().strftime("%B %Y")
    month = input(f"  >  Month (default: {current_month}): ").strip()
    if not month:
        month = current_month

    # Warn on duplicate month+student
    all_fees = _load_fees()
    existing = [
        f for f in all_fees
        if f.student_id == student_id and f.month.lower() == month.lower()
    ]
    if existing:
        print_warning(
            f"A fee record for {student_id} for '{month}' already exists "
            f"({existing[0].fee_id}, Status: {existing[0].status})."
        )
        if not confirm("Generate a new record anyway? (y/n)"):
            pause()
            return

    # Amount
    while True:
        amt_str = input("  >  Fee Amount (Rs.): ").strip()
        try:
            amount = float(amt_str)
            if amount <= 0:
                print_error("Amount must be greater than zero.")
                continue
            break
        except ValueError:
            print_error("Invalid amount. Enter a number like 5000 or 4500.50")

    # Due date
    due_date_input = input("  >  Due Date (YYYY-MM-DD, Enter for today): ").strip()
    if not due_date_input:
        due_date_input = current_date()
    else:
        try:
            datetime.strptime(due_date_input, "%Y-%m-%d")
        except ValueError:
            print_error("Invalid date format. Using today's date.")
            due_date_input = current_date()

    remarks = input("  >  Remarks (optional): ").strip()

    fee_id = _next_fee_id()

    print()
    print_line("-")
    print(f"  Fee ID     : {fee_id}")
    print(f"  Student    : {student_id} - {student.name}")
    print(f"  Month      : {month}")
    print(f"  Amount Due : Rs.{amount:,.2f}")
    print(f"  Due Date   : {due_date_input}")
    print_line("-")

    if not confirm("Confirm and save fee record? (y/n)"):
        print_warning("Fee record creation cancelled.")
        pause()
        return

    new_fee = FeeRecord(
        fee_id       = fee_id,
        student_id   = student_id,
        student_name = student.name,
        amount_due   = amount,
        amount_paid  = 0.0,
        fine_amount  = 0.0,
        month        = month,
        due_date     = due_date_input,
        payment_date = "",
        status       = "Pending",
        remarks      = remarks,
    )

    if DataHandler.insert(FEE_ENTITY, new_fee.to_dict()):
        print_success(f"Fee record {fee_id} created for {student.name} ({month}).")
    else:
        print_error("Failed to save fee record.")

    pause()


# =======================================================================
#  FEATURE 2 - VIEW FEE RECORDS
# =======================================================================

def view_fee_records():
    """Admin: display all fee records with sort options."""
    clear_screen()
    print_banner()
    print_header("All Fee Records")

    fees = _load_fees()
    if not fees:
        print_info("No fee records found.")
        pause()
        return

    print("\n  Sort by:")
    print("    [1]  Fee ID (default)")
    print("    [2]  Student Name (A-Z)")
    print("    [3]  Amount Due (high first)")
    print("    [4]  Status (Pending first)")
    print("    [5]  Month")
    sort_choice = input("\n  >  Choice (Enter for default): ").strip()

    # Lambda sort map
    sort_map = {
        "2": lambda f: f.student_name.lower(),
        "3": lambda f: -f.amount_due,
        "4": lambda f: ["Pending", "Partial", "Paid"].index(f.status)
                       if f.status in ["Pending", "Partial", "Paid"] else 99,
        "5": lambda f: f.month.lower(),
    }
    key_fn  = sort_map.get(sort_choice, lambda f: f.fee_id)
    fees    = sorted(fees, key=key_fn)

    print_table(FEE_TABLE_HEADERS, _fees_as_rows(fees))

    # Summary footer
    total_due   = sum(f.amount_due for f in fees)
    total_paid  = sum(f.amount_paid for f in fees)
    total_fine  = sum(f.fine_amount for f in fees)
    total_bal   = sum(f.balance for f in fees)
    paid_count  = sum(1 for f in fees if f.status == "Paid")
    pend_count  = sum(1 for f in fees if f.status == "Pending")
    part_count  = sum(1 for f in fees if f.status == "Partial")

    print_line()
    print(f"  Records: {len(fees)}  |  Paid: {paid_count}  |  Partial: {part_count}  |  Pending: {pend_count}")
    print(f"  Total Due: Rs.{total_due:,.2f}  |  Collected: Rs.{total_paid:,.2f}  |  "
          f"Fines: Rs.{total_fine:,.2f}  |  Outstanding: Rs.{total_bal:,.2f}")
    print_line()

    # Offer detail view
    fee_id_input = input("\n  >  Enter Fee ID for full details (Enter to skip): ").strip().upper()
    if fee_id_input:
        fee = _find_fee(fee_id_input)
        if fee:
            _print_fee_detail(fee)
        else:
            print_error(f"Fee ID '{fee_id_input}' not found.")

    pause()


# =======================================================================
#  FEATURE 3 - PAY HOSTEL FEE
# =======================================================================

def pay_fee():
    """
    Admin: record a payment against a fee record.

    Validations:
      1. Fee record must exist
      2. Fee must not already be fully Paid
      3. Payment amount must be > 0
      4. Payment cannot exceed outstanding balance
    """
    clear_screen()
    print_banner()
    print_header("Record Fee Payment")

    # Search by student ID or fee ID
    print("  Find fee by:")
    print("    [1]  Fee ID  (e.g. FEE002)")
    print("    [2]  Student ID  (shows their pending fees)")
    search_choice = input("\n  >  Choice: ").strip()

    fee = None

    if search_choice == "1":
        fee_id_input = input("  >  Fee ID: ").strip().upper()
        fee = _find_fee(fee_id_input)
        if not fee:
            print_error(f"Fee ID '{fee_id_input}' not found.")
            pause()
            return

    elif search_choice == "2":
        stu_id = input("  >  Student ID: ").strip().upper()
        all_fees = _load_fees()
        # List comprehension: unpaid fees for this student
        stu_fees = [f for f in all_fees
                    if f.student_id == stu_id and f.status != "Paid"]
        if not stu_fees:
            print_warning(f"No pending fees found for student {stu_id}.")
            pause()
            return

        print(f"\n  Unpaid fees for {stu_id}:")
        print_table(FEE_TABLE_HEADERS, _fees_as_rows(stu_fees))

        fee_id_sel = input("  >  Enter Fee ID to pay: ").strip().upper()
        fee = _find_fee(fee_id_sel)
        if not fee:
            print_error(f"Fee ID '{fee_id_sel}' not found.")
            pause()
            return

    else:
        print_error("Invalid choice.")
        pause()
        return

    # Validation: already paid
    if fee.status == "Paid":
        print_warning(f"Fee {fee.fee_id} is already marked as Paid.")
        pause()
        return

    # Refresh fine before showing balance
    fee.refresh_fine()

    _print_fee_detail(fee)

    print(f"  Outstanding Balance: Rs.{fee.balance:,.2f}  (includes fine: Rs.{fee.fine_amount:.2f})")

    # Get payment amount
    while True:
        amt_str = input("\n  >  Payment Amount (Rs.): ").strip()
        try:
            payment = float(amt_str)
        except ValueError:
            print_error("Invalid amount. Enter a number like 2500 or 5000")
            continue

        result = fee.apply_payment(payment)

        if result.startswith("error"):
            print_error(result.replace("error: ", "").capitalize())
            continue
        break

    # Confirm
    print()
    print_line("-")
    print(f"  Fee ID    : {fee.fee_id}  ({fee.month})")
    print(f"  Student   : {fee.student_name}")
    print(f"  Payment   : Rs.{payment:,.2f}")
    print(f"  New Status: {fee.status}")
    print(f"  Remaining : Rs.{fee.balance:,.2f}")
    print_line("-")

    if not confirm("Confirm this payment? (y/n)"):
        print_warning("Payment cancelled.")
        pause()
        return

    if _save_fee(fee):
        print_success(f"Payment of Rs.{payment:,.2f} recorded for {fee.fee_id}. Status: {fee.status}")
    else:
        print_error("Failed to save payment. Check data files.")

    pause()


# =======================================================================
#  FEATURE 4 - VIEW PENDING FEES
# =======================================================================

def view_pending_fees():
    """Show all fees that are Pending or Partial (not fully paid)."""
    clear_screen()
    print_banner()
    print_header("Pending / Unpaid Fees")

    fees = _load_fees()

    # List comprehension: only unpaid fees
    pending = [f for f in fees if f.status != "Paid"]

    if not pending:
        print_success("All fee records are fully paid. No dues outstanding.")
        pause()
        return

    # Sort by due_date ascending (most overdue first), using lambda
    pending = sorted(pending, key=lambda f: f.due_date or "9999-99-99")

    print_table(FEE_TABLE_HEADERS, _fees_as_rows(pending))

    # Flag overdue records
    overdue = [f for f in pending if f.is_overdue]
    if overdue:
        print(f"  ** OVERDUE ({len(overdue)} record(s)):")
        for f in overdue:
            print(f"     {f.fee_id}  {f.student_name:<20}  "
                  f"{f.days_overdue} days overdue  "
                  f"Balance: Rs.{f.balance:,.2f}")
        print()

    total_outstanding = sum(f.balance for f in pending)
    print_line()
    print(f"  Pending Records : {len(pending)}  |  "
          f"Overdue: {len(overdue)}  |  "
          f"Total Outstanding: Rs.{total_outstanding:,.2f}")
    print_line()

    pause()


# =======================================================================
#  FEATURE 5 - CALCULATE & APPLY FINE
# =======================================================================

def calculate_fines():
    """
    Admin: compute and update fine_amount for all overdue unpaid fees.
    Fine = max(0, days_overdue - FINE_GRACE_DAYS) * LATE_FINE_PER_DAY
    """
    clear_screen()
    print_banner()
    print_header("Calculate Late Fines")

    fees = _load_fees()

    # List comprehension: only overdue and unpaid
    overdue_fees = [f for f in fees if f.is_overdue and f.status != "Paid"]

    if not overdue_fees:
        print_info(
            f"No overdue unpaid fees found.\n"
            f"  Fine policy: Rs.{LATE_FINE_PER_DAY:.0f}/day after {FINE_GRACE_DAYS} grace days."
        )
        pause()
        return

    print(f"\n  Fine rate  : Rs.{LATE_FINE_PER_DAY:.0f} per day  (after {FINE_GRACE_DAYS} grace days)")
    print(f"  Overdue fees found: {len(overdue_fees)}")
    print()

    # Preview fines before applying
    print(f"  {'Fee ID':<8} {'Student':<20} {'Days Overdue':<14} {'Existing Fine':<15} {'New Fine'}")
    print("  " + "-" * 65)
    for f in overdue_fees:
        new_fine = f.calculate_fine()
        print(f"  {f.fee_id:<8} {truncate(f.student_name, 18):<20} "
              f"{f.days_overdue:<14} Rs.{f.fine_amount:<12.2f} Rs.{new_fine:.2f}")

    print()
    if not confirm("Apply these fines to all overdue records? (y/n)"):
        print_warning("Fine calculation cancelled. No changes made.")
        pause()
        return

    updated = 0
    for f in overdue_fees:
        f.refresh_fine()   # calls calculate_fine() and stores result
        if _save_fee(f):
            updated += 1

    print_success(f"Fines applied to {updated}/{len(overdue_fees)} fee record(s).")
    pause()


# =======================================================================
#  FEATURE 6 - GENERATE FEE RECEIPT
# =======================================================================

def generate_receipt():
    """Print a formatted fee receipt to the terminal."""
    clear_screen()
    print_banner()
    print_header("Fee Receipt")

    fee_id_input = input("  >  Enter Fee ID: ").strip().upper()
    if not fee_id_input:
        print_error("Fee ID cannot be empty.")
        pause()
        return

    fee = _find_fee(fee_id_input)
    if not fee:
        print_error(f"Fee ID '{fee_id_input}' not found.")
        pause()
        return

    # Formatted receipt
    width = 60
    border = "=" * width
    print()
    print(f"  {border}")
    print(f"  {'HOSTELHUB - FEE RECEIPT':^{width}}")
    print(f"  {'Smart Hostel Management System':^{width}}")
    print(f"  {border}")
    print(f"  Receipt No   : {fee.fee_id}")
    print(f"  Generated On : {datetime.now().strftime('%d %b %Y  %H:%M')}")
    print(f"  {'-' * width}")
    print(f"  Student ID   : {fee.student_id}")
    print(f"  Student Name : {fee.student_name}")
    print(f"  Month        : {fee.month}")
    print(f"  Due Date     : {format_date(fee.due_date) if fee.due_date else 'N/A'}")
    print(f"  {'-' * width}")
    print(f"  Fee Amount   : Rs.{fee.amount_due:>10,.2f}")
    print(f"  Fine Amount  : Rs.{fee.fine_amount:>10,.2f}")
    print(f"                 {'-' * 14}")
    print(f"  Total Due    : Rs.{fee.amount_due + fee.fine_amount:>10,.2f}")
    print(f"  Amount Paid  : Rs.{fee.amount_paid:>10,.2f}")
    print(f"  Balance Due  : Rs.{fee.balance:>10,.2f}")
    print(f"  {'-' * width}")
    print(f"  Status       : {fee.status}")
    if fee.payment_date:
        print(f"  Payment Date : {format_date(fee.payment_date)}")
    if fee.remarks:
        print(f"  Remarks      : {fee.remarks}")
    print(f"  {border}")
    print(f"  {'*** OFFICIAL RECEIPT - HostelHub ***':^{width}}")
    print(f"  {border}")
    print()

    pause()


# =======================================================================
#  FEATURE 7 - EXPORT FEE REPORT CSV
# =======================================================================

def export_fee_report():
    """Export all fee records to a CSV file in the exports/ directory."""
    clear_screen()
    print_banner()
    print_header("Export Fee Report")

    fees = _load_fees()
    if not fees:
        print_info("No fee records to export.")
        pause()
        return

    print("  Export options:")
    print("    [1]  All records")
    print("    [2]  Pending / Partial only")
    print("    [3]  Paid only")
    choice = input("\n  >  Choice (default: all): ").strip()

    filter_map = {
        "2": [f for f in fees if f.status != "Paid"],
        "3": [f for f in fees if f.status == "Paid"],
    }
    # Use generator expression to pick data set
    export_fees = filter_map.get(choice, fees)

    if not export_fees:
        print_warning("No records match the selected filter.")
        pause()
        return

    headers = [
        "Fee ID", "Student ID", "Student Name", "Month",
        "Amount Due", "Amount Paid", "Fine Amount", "Balance",
        "Due Date", "Payment Date", "Status", "Remarks"
    ]

    # Generator-style: build rows lazily via generator expression
    rows = list(
        (
            f.fee_id, f.student_id, f.student_name, f.month,
            f"{f.amount_due:.2f}", f"{f.amount_paid:.2f}",
            f"{f.fine_amount:.2f}", f"{f.balance:.2f}",
            f.due_date, f.payment_date, f.status, f.remarks
        )
        for f in export_fees
    )

    date_str  = datetime.now().strftime("%Y-%m-%d")
    filename  = f"fee_report_{date_str}.csv"
    filepath  = os.path.join(EXPORT_DIR, filename)

    if export_to_csv(filepath, headers, rows):
        print_success(f"Fee report exported: exports/{filename}  ({len(rows)} record(s))")
    else:
        print_error("Export failed. Check write permissions.")

    pause()


# =======================================================================
#  STUDENT VIEW - MY FEE STATUS
# =======================================================================

def _view_my_fees(user: dict):
    """Student: view their own fee records."""
    clear_screen()
    print_banner()
    print_header("My Fee Status")

    student_id = user.get("username", "")
    fees       = _load_fees()

    # List comprehension: only this student's fees, sorted by month
    my_fees = sorted(
        [f for f in fees if f.student_id == student_id],
        key=lambda f: f.month
    )

    if not my_fees:
        print_info("No fee records found for your account.")
        pause()
        return

    print_table(FEE_TABLE_HEADERS, _fees_as_rows(my_fees))

    total_paid = sum(f.amount_paid for f in my_fees)
    total_bal  = sum(f.balance for f in my_fees)

    print_line()
    print(f"  Total Paid: Rs.{total_paid:,.2f}  |  Outstanding: Rs.{total_bal:,.2f}")
    print_line()

    # Overdue warning
    overdue = [f for f in my_fees if f.is_overdue]
    if overdue:
        print_warning(f"You have {len(overdue)} overdue fee(s). Please pay immediately.")

    # Offer receipt view
    fee_id_input = input("\n  >  Enter Fee ID to view receipt (Enter to skip): ").strip().upper()
    if fee_id_input:
        fee = _find_fee(fee_id_input)
        if fee and fee.student_id == student_id:
            # Show simplified receipt (reuse function)
            generate_receipt_for(fee)
        elif fee:
            print_error("You can only view receipts for your own fees.")
        else:
            print_error(f"Fee ID '{fee_id_input}' not found.")

    pause()


def generate_receipt_for(fee: FeeRecord):
    """Helper: print receipt for a given FeeRecord object (reuse from student view)."""
    width = 60
    border = "=" * width
    print()
    print(f"  {border}")
    print(f"  {'HOSTELHUB - FEE RECEIPT':^{width}}")
    print(f"  {border}")
    print(f"  Receipt No   : {fee.fee_id}")
    print(f"  Student      : {fee.student_id} - {fee.student_name}")
    print(f"  Month        : {fee.month}")
    print(f"  Amount Due   : Rs.{fee.amount_due:>10,.2f}")
    print(f"  Amount Paid  : Rs.{fee.amount_paid:>10,.2f}")
    print(f"  Balance      : Rs.{fee.balance:>10,.2f}")
    print(f"  Status       : {fee.status}")
    print(f"  {border}")
    print()


# =======================================================================
#  FEE MENU ENTRY POINT
# =======================================================================

_ADMIN_OPTIONS = [
    "[1] Generate Fee Record",
    "[2] View All Fee Records",
    "[3] Record Payment",
    "[4] View Pending / Unpaid Fees",
    "[5] Calculate Late Fines",
    "[6] Generate Fee Receipt",
    "[7] Export Fee Report (CSV)",
    "[8] Back to Main Menu",
]

_STUDENT_OPTIONS = [
    "[1] My Fee Status",
    "[2] View Fee Receipt",
    "[3] Back to Main Menu",
]


def fee_menu(user: dict):
    """Entry point called from main.py. Role-based routing."""
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Fee Management", _ADMIN_OPTIONS)

            if choice == "1":
                generate_fee_record()
            elif choice == "2":
                view_fee_records()
            elif choice == "3":
                pay_fee()
            elif choice == "4":
                view_pending_fees()
            elif choice == "5":
                calculate_fines()
            elif choice == "6":
                generate_receipt()
            elif choice == "7":
                export_fee_report()
            elif choice == "8":
                break
            else:
                print_error("Invalid choice. Enter a number between 1 and 8.")
                pause()

        else:
            # Student: read-only access to own fees
            choice = print_menu("My Fees", _STUDENT_OPTIONS)

            if choice == "1":
                _view_my_fees(user)
            elif choice == "2":
                # Direct receipt lookup
                fee_id_input = input("\n  >  Enter Fee ID: ").strip().upper()
                fee = _find_fee(fee_id_input)
                if fee and fee.student_id == user.get("username", ""):
                    generate_receipt_for(fee)
                    pause()
                elif fee:
                    print_error("You can only view receipts for your own fees.")
                    pause()
                else:
                    print_error(f"Fee ID '{fee_id_input}' not found.")
                    pause()
            elif choice == "3":
                break
            else:
                print_error("Invalid choice.")
                pause()
