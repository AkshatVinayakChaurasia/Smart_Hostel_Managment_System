"""
db_handler.py - Central JSON-based data access layer for HostelHub

All modules read/write through this handler to ensure consistent
data loading and saving.  Using JSON files avoids the need for
a running database server and keeps the project beginner-friendly.
"""

import os
from utils.helpers import load_json, save_json

# --- File paths ------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

PATHS = {
    "students":   os.path.join(DATA_DIR, "students.json"),
    "rooms":      os.path.join(DATA_DIR, "rooms.json"),
    "fees":       os.path.join(DATA_DIR, "fees.json"),
    "complaints": os.path.join(DATA_DIR, "complaints.json"),
    "attendance": os.path.join(DATA_DIR, "attendance.json"),
    "notices":    os.path.join(DATA_DIR, "notices.json"),
    "users":      os.path.join(DATA_DIR, "users.json"),
}


class DataHandler:
    """
    Central data access class.
    Each module should instantiate or import a shared DataHandler.
    Provides load / save / get-all / find-by-id operations.
    """

    # -- Load / Save --------------------------------------------------

    @staticmethod
    def load(entity: str) -> list[dict]:
        """Load all records for an entity (returns list of dicts)."""
        path = PATHS.get(entity)
        if not path:
            raise ValueError(f"Unknown entity: '{entity}'")
        data = load_json(path)
        return data if isinstance(data, list) else []

    @staticmethod
    def save(entity: str, records: list[dict]) -> bool:
        """Persist a list of records for an entity."""
        path = PATHS.get(entity)
        if not path:
            raise ValueError(f"Unknown entity: '{entity}'")
        return save_json(path, records)

    # -- CRUD helpers -------------------------------------------------

    @classmethod
    def get_all(cls, entity: str) -> list[dict]:
        """Return all records for an entity."""
        return cls.load(entity)

    @classmethod
    def find_by_id(cls, entity: str, id_field: str, id_value: str) -> dict | None:
        """Find a single record matching id_field == id_value."""
        for record in cls.load(entity):
            if str(record.get(id_field)) == str(id_value):
                return record
        return None

    @classmethod
    def insert(cls, entity: str, new_record: dict) -> bool:
        """Append a new record to the entity store."""
        records = cls.load(entity)
        records.append(new_record)
        return cls.save(entity, records)

    @classmethod
    def update(cls, entity: str, id_field: str, id_value: str, updated_record: dict) -> bool:
        """
        Replace a matching record in the entity store.
        Returns True if the record was found and updated.
        """
        records = cls.load(entity)
        for i, rec in enumerate(records):
            if str(rec.get(id_field)) == str(id_value):
                records[i] = updated_record
                cls.save(entity, records)
                return True
        return False

    @classmethod
    def delete(cls, entity: str, id_field: str, id_value: str) -> bool:
        """
        Remove a matching record from the entity store.
        Returns True if the record was found and removed.
        """
        records = cls.load(entity)
        new_records = [r for r in records if str(r.get(id_field)) != str(id_value)]
        if len(new_records) == len(records):
            return False  # Nothing deleted
        cls.save(entity, new_records)
        return True

    @classmethod
    def search(cls, entity: str, field: str, query: str) -> list[dict]:
        """Case-insensitive substring search on a specific field."""
        query = query.strip().lower()
        return [
            r for r in cls.load(entity)
            if query in str(r.get(field, "")).lower()
        ]

    # -- Statistics ---------------------------------------------------

    @classmethod
    def count(cls, entity: str) -> int:
        """Return total count of records for an entity."""
        return len(cls.load(entity))

    @classmethod
    def count_where(cls, entity: str, field: str, value) -> int:
        """Count records where field == value."""
        return sum(
            1 for r in cls.load(entity)
            if str(r.get(field, "")).lower() == str(value).lower()
        )
