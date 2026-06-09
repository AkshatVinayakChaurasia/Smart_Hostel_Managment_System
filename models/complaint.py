"""
complaint.py - Complaint data model
"""

COMPLAINT_TYPES = ["Electricity", "Water", "Internet", "Cleanliness", "Maintenance", "Other"]
COMPLAINT_STATUS = ["Open", "In Progress", "Resolved", "Closed"]
PRIORITY_LEVELS = ["Low", "Medium", "High"]


class Complaint:
    """Represents a hostel complaint submitted by a student."""

    def __init__(
        self,
        complaint_id: str,
        student_id: str,
        student_name: str,
        complaint_type: str,
        description: str,
        priority: str = "Medium",
        status: str = "Open",
        filed_date: str = "",
        resolved_date: str = "",
        remarks: str = "",
    ):
        self.complaint_id = complaint_id
        self.student_id = student_id
        self.student_name = student_name
        self.complaint_type = complaint_type
        self.description = description
        self.priority = priority
        self.status = status
        self.filed_date = filed_date
        self.resolved_date = resolved_date
        self.remarks = remarks

    @property
    def is_open(self) -> bool:
        return self.status in ("Open", "In Progress")

    def to_dict(self) -> dict:
        return {
            "complaint_id": self.complaint_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "complaint_type": self.complaint_type,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "filed_date": self.filed_date,
            "resolved_date": self.resolved_date,
            "remarks": self.remarks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Complaint":
        return cls(
            complaint_id=data.get("complaint_id", ""),
            student_id=data.get("student_id", ""),
            student_name=data.get("student_name", ""),
            complaint_type=data.get("complaint_type", "Other"),
            description=data.get("description", ""),
            priority=data.get("priority", "Medium"),
            status=data.get("status", "Open"),
            filed_date=data.get("filed_date", ""),
            resolved_date=data.get("resolved_date", ""),
            remarks=data.get("remarks", ""),
        )

    def __str__(self) -> str:
        return (
            f"Complaint({self.complaint_id}) | {self.complaint_type} | "
            f"{self.student_name} | {self.priority} | {self.status}"
        )
