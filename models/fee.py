"""
fee.py - Fee record data model
"""

from datetime import datetime

FEE_STATUS = ["Paid", "Pending", "Partial"]

# Late fine per day (in Rupees) applied after due_date passes
LATE_FINE_PER_DAY = 10.0
FINE_GRACE_DAYS   = 5     # fine applies only after this many grace days past due


class FeeRecord:
    """
    Represents a fee payment record for a student.

    Attributes:
        fee_id        : Unique ID (e.g. FEE001)
        student_id    : Linked student's ID
        student_name  : Student's full name (denormalized for display)
        amount_due    : Total fee amount to be paid
        amount_paid   : Amount already paid
        fine_amount   : Late fine accumulated (computed / stored)
        month         : Fee month descriptor (e.g. "June 2025")
        due_date      : ISO date string "YYYY-MM-DD"
        payment_date  : ISO date string when fully paid (blank if unpaid)
        status        : One of FEE_STATUS
        remarks       : Free-text admin note
    """

    def __init__(
        self,
        fee_id:       str,
        student_id:   str,
        student_name: str,
        amount_due:   float,
        amount_paid:  float = 0.0,
        fine_amount:  float = 0.0,
        month:        str   = "",
        due_date:     str   = "",
        payment_date: str   = "",
        status:       str   = "Pending",
        remarks:      str   = "",
    ):
        self.fee_id       = fee_id
        self.student_id   = student_id
        self.student_name = student_name
        self.amount_due   = float(amount_due)
        self.amount_paid  = float(amount_paid)
        self.fine_amount  = float(fine_amount)
        self.month        = month
        self.due_date     = due_date
        self.payment_date = payment_date
        self.status       = status
        self.remarks      = remarks

    # -- Computed Properties -------------------------------------------

    @property
    def balance(self) -> float:
        """Outstanding balance = amount_due + fine_amount - amount_paid."""
        return max(0.0, self.amount_due + self.fine_amount - self.amount_paid)

    @property
    def is_overdue(self) -> bool:
        """True if due_date has passed and fee is not fully paid."""
        if self.status == "Paid" or not self.due_date:
            return False
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            return datetime.today().date() > due
        except ValueError:
            return False

    @property
    def days_overdue(self) -> int:
        """Number of calendar days past due_date (0 if not overdue)."""
        if not self.is_overdue or not self.due_date:
            return 0
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
            delta = (datetime.today().date() - due).days
            return max(0, delta)
        except ValueError:
            return 0

    def calculate_fine(self) -> float:
        """
        Calculate fine based on days overdue minus grace period.
        fine = max(0, days_overdue - FINE_GRACE_DAYS) * LATE_FINE_PER_DAY
        Only applies if fee is not fully Paid.
        """
        if self.status == "Paid":
            return 0.0
        billable_days = max(0, self.days_overdue - FINE_GRACE_DAYS)
        return round(billable_days * LATE_FINE_PER_DAY, 2)

    def refresh_fine(self):
        """Update fine_amount in-place based on current date."""
        self.fine_amount = self.calculate_fine()

    def apply_payment(self, payment: float) -> str:
        """
        Apply a payment amount and update status.
        Returns a result string: 'paid', 'partial', or error message.

        Validations:
          - payment must be positive
          - payment cannot exceed outstanding balance
        """
        if payment <= 0:
            return "error: payment must be a positive amount"
        total_due = self.amount_due + self.fine_amount
        if self.amount_paid + payment > total_due:
            return f"error: payment Rs.{payment:.2f} exceeds balance Rs.{self.balance:.2f}"

        self.amount_paid += payment

        # Recalculate status
        if self.amount_paid >= total_due:
            self.status       = "Paid"
            self.payment_date = datetime.now().strftime("%Y-%m-%d")
            return "paid"
        else:
            self.status = "Partial"
            return "partial"

    # -- Serialization -------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "fee_id":        self.fee_id,
            "student_id":    self.student_id,
            "student_name":  self.student_name,
            "amount_due":    self.amount_due,
            "amount_paid":   self.amount_paid,
            "fine_amount":   self.fine_amount,
            "month":         self.month,
            "due_date":      self.due_date,
            "payment_date":  self.payment_date,
            "status":        self.status,
            "remarks":       self.remarks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeeRecord":
        return cls(
            fee_id       = data.get("fee_id", ""),
            student_id   = data.get("student_id", ""),
            student_name = data.get("student_name", ""),
            amount_due   = data.get("amount_due", 0.0),
            amount_paid  = data.get("amount_paid", 0.0),
            fine_amount  = data.get("fine_amount", 0.0),
            month        = data.get("month", ""),
            due_date     = data.get("due_date", ""),
            payment_date = data.get("payment_date", ""),
            status       = data.get("status", "Pending"),
            remarks      = data.get("remarks", ""),
        )

    def __str__(self) -> str:
        return (
            f"Fee({self.fee_id}) | {self.student_name} | "
            f"Due: Rs.{self.amount_due:.2f} | Paid: Rs.{self.amount_paid:.2f} | "
            f"Fine: Rs.{self.fine_amount:.2f} | {self.status}"
        )
