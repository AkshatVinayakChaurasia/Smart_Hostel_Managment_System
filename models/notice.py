"""
notice.py - Notice Board data model
"""

NOTICE_CATEGORIES = ["General", "Fee", "Maintenance", "Event", "Emergency", "Holiday"]


class Notice:
    """Represents a hostel notice board entry."""

    def __init__(
        self,
        notice_id: str,
        title: str,
        content: str,
        category: str = "General",
        posted_by: str = "Admin",
        posted_date: str = "",
        expiry_date: str = "",
        is_important: bool = False,
    ):
        self.notice_id = notice_id
        self.title = title
        self.content = content
        self.category = category
        self.posted_by = posted_by
        self.posted_date = posted_date
        self.expiry_date = expiry_date
        self.is_important = is_important

    def to_dict(self) -> dict:
        return {
            "notice_id": self.notice_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "posted_by": self.posted_by,
            "posted_date": self.posted_date,
            "expiry_date": self.expiry_date,
            "is_important": self.is_important,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notice":
        return cls(
            notice_id=data.get("notice_id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            category=data.get("category", "General"),
            posted_by=data.get("posted_by", "Admin"),
            posted_date=data.get("posted_date", ""),
            expiry_date=data.get("expiry_date", ""),
            is_important=data.get("is_important", False),
        )

    def __str__(self) -> str:
        tag = " [!] IMPORTANT" if self.is_important else ""
        return f"Notice({self.notice_id}) | [{self.category}] {self.title}{tag}"
