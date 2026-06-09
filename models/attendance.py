"""
attendance.py - Attendance record data model
"""


class AttendanceRecord:
    """Represents a single daily attendance entry for a student."""

    def __init__(
        self,
        record_id: str,
        student_id: str,
        student_name: str,
        date: str,
        status: str = "Present",    # "Present" | "Absent" | "Leave"
        in_time: str = "",
        out_time: str = "",
    ):
        self.record_id = record_id
        self.student_id = student_id
        self.student_name = student_name
        self.date = date
        self.status = status
        self.in_time = in_time
        self.out_time = out_time

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "date": self.date,
            "status": self.status,
            "in_time": self.in_time,
            "out_time": self.out_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttendanceRecord":
        return cls(
            record_id=data.get("record_id", ""),
            student_id=data.get("student_id", ""),
            student_name=data.get("student_name", ""),
            date=data.get("date", ""),
            status=data.get("status", "Present"),
            in_time=data.get("in_time", ""),
            out_time=data.get("out_time", ""),
        )

    def __str__(self) -> str:
        return (
            f"Attendance({self.record_id}) | {self.student_name} | "
            f"{self.date} | {self.status}"
        )
