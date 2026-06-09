"""
student.py - Student data model
"""


class Student:
    """Represents a hostel student record."""

    def __init__(
        self,
        student_id: str,
        name: str,
        course: str,
        year: int,
        mobile: str,
        address: str,
        room_number: str = "Not Allocated",
        joined_date: str = "",
        is_active: bool = True,
    ):
        self.student_id = student_id
        self.name = name
        self.course = course
        self.year = int(year)
        self.mobile = mobile
        self.address = address
        self.room_number = room_number
        self.joined_date = joined_date
        self.is_active = is_active

    # -- Serialization ------------------------------------------------

    def to_dict(self) -> dict:
        """Convert Student to a JSON-serializable dictionary."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "course": self.course,
            "year": self.year,
            "mobile": self.mobile,
            "address": self.address,
            "room_number": self.room_number,
            "joined_date": self.joined_date,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Create a Student instance from a dictionary."""
        return cls(
            student_id=data.get("student_id", ""),
            name=data.get("name", ""),
            course=data.get("course", ""),
            year=data.get("year", 1),
            mobile=data.get("mobile", ""),
            address=data.get("address", ""),
            room_number=data.get("room_number", "Not Allocated"),
            joined_date=data.get("joined_date", ""),
            is_active=data.get("is_active", True),
        )

    def __str__(self) -> str:
        return (
            f"Student({self.student_id}) | {self.name} | "
            f"{self.course} Year-{self.year} | Room: {self.room_number}"
        )
