"""
room.py - Room data model
"""

ROOM_TYPES = ["Single", "Double", "Triple", "Dormitory"]


class Room:
    """
    Represents a hostel room record.

    Attributes:
        room_number : Unique identifier (e.g. "101")
        room_type   : One of ROOM_TYPES
        capacity    : Maximum number of students
        occupied    : Current number of students in the room
        floor       : Floor number
        amenities   : List of amenity strings
        occupants   : List of student_id strings currently in this room
    """

    def __init__(
        self,
        room_number: str,
        room_type: str,
        capacity: int,
        occupied: int = 0,
        floor: int = 1,
        amenities: list = None,
        occupants: list = None,
    ):
        self.room_number = room_number
        self.room_type   = room_type
        self.capacity    = int(capacity)
        self.occupied    = int(occupied)
        self.floor       = int(floor)
        self.amenities   = amenities or []
        self.occupants   = occupants or []

    # -- Computed Properties -------------------------------------------

    @property
    def vacant_beds(self) -> int:
        """Number of beds still available."""
        return max(0, self.capacity - self.occupied)

    @property
    def is_available(self) -> bool:
        """True if at least one bed is free."""
        return self.vacant_beds > 0

    @property
    def status(self) -> str:
        """Human-readable occupancy status."""
        if self.occupied == 0:
            return "Vacant"
        elif self.occupied >= self.capacity:
            return "Full"
        else:
            return "Partial"

    @property
    def occupancy_pct(self) -> float:
        """Occupancy as a percentage (0.0 - 100.0)."""
        if self.capacity == 0:
            return 0.0
        return (self.occupied / self.capacity) * 100.0

    # -- Occupant helpers ----------------------------------------------

    def add_occupant(self, student_id: str) -> bool:
        """
        Add a student to this room.
        Returns False if the room is already full or student already here.
        """
        if student_id in self.occupants:
            return False
        if self.occupied >= self.capacity:
            return False
        self.occupants.append(student_id)
        self.occupied += 1
        return True

    def remove_occupant(self, student_id: str) -> bool:
        """
        Remove a student from this room.
        Returns False if the student is not in this room.
        """
        if student_id not in self.occupants:
            return False
        self.occupants.remove(student_id)
        self.occupied = max(0, self.occupied - 1)
        return True

    def has_occupant(self, student_id: str) -> bool:
        """Check whether a specific student is assigned to this room."""
        return student_id in self.occupants

    # -- Serialization -------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "room_number": self.room_number,
            "room_type":   self.room_type,
            "capacity":    self.capacity,
            "occupied":    self.occupied,
            "floor":       self.floor,
            "amenities":   self.amenities,
            "occupants":   self.occupants,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        return cls(
            room_number = data.get("room_number", ""),
            room_type   = data.get("room_type", "Single"),
            capacity    = data.get("capacity", 1),
            occupied    = data.get("occupied", 0),
            floor       = data.get("floor", 1),
            amenities   = data.get("amenities", []),
            occupants   = data.get("occupants", []),
        )

    def __str__(self) -> str:
        return (
            f"Room {self.room_number} | {self.room_type} | "
            f"Floor {self.floor} | {self.occupied}/{self.capacity} beds | {self.status}"
        )
