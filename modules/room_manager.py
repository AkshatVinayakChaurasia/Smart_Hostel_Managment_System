"""
room_manager.py - Room Management Module (Phase 3)

Features:
  1. View All Rooms              (sortable, filtered by type/floor)
  2. View Vacant Rooms           (list comprehension filter)
  3. Allocate Room to Student    (with full validation rules)
  4. Transfer Student Room       (move between rooms atomically)
  5. Vacate Room / Remove Student
  6. Room Occupancy Summary      (stats table + per-room breakdown)
  7. Repair Occupancy Data       (admin consistency check & fix)

Allocation Rules Enforced:
  - Room must exist
  - Room must not be full
  - Student must exist and be active
  - Student must not already have a room allocated
  - Duplicate occupant prevented at both room and student levels

Uses: Room model, Student model, DataHandler, display utilities.
"""

from models.room import Room, ROOM_TYPES
from models.student import Student
from database.db_handler import DataHandler
from utils.display import (
    clear_screen, print_banner, print_header, print_line,
    print_menu, print_table, print_success, print_error,
    print_warning, print_info, pause, confirm
)
from utils.helpers import truncate

# -- Constants ---------------------------------------------------------
ROOM_ENTITY    = "rooms"
STUDENT_ENTITY = "students"
ROOM_ID_FIELD  = "room_number"
STU_ID_FIELD   = "student_id"

# Column headers for the room list table
ROOM_TABLE_HEADERS = ["Room No", "Type", "Floor", "Capacity", "Occupied", "Vacant", "Status"]
ROOM_TABLE_WIDTHS  = [9, 12, 7, 9, 9, 7, 10]


# =======================================================================
#  INTERNAL HELPER FUNCTIONS
# =======================================================================

def _load_rooms() -> list[Room]:
    """
    Load all rooms from JSON and return a list of Room objects.
    Uses a list comprehension for clean, readable transformation.
    """
    return [Room.from_dict(r) for r in DataHandler.get_all(ROOM_ENTITY)]


def _save_room(room: Room) -> bool:
    """Persist a single updated Room back to JSON."""
    return DataHandler.update(ROOM_ENTITY, ROOM_ID_FIELD, room.room_number, room.to_dict())


def _find_room(room_number: str) -> Room | None:
    """Retrieve a single Room object by room number, or None."""
    record = DataHandler.find_by_id(ROOM_ENTITY, ROOM_ID_FIELD, room_number.strip())
    return Room.from_dict(record) if record else None


def _find_student(student_id: str) -> Student | None:
    """Retrieve a single Student object by ID, or None."""
    record = DataHandler.find_by_id(STUDENT_ENTITY, STU_ID_FIELD, student_id.strip().upper())
    return Student.from_dict(record) if record else None


def _rooms_as_rows(rooms: list[Room]) -> list[list]:
    """
    Convert Room objects into display rows for print_table.
    List comprehension: clean one-liner transformation.
    """
    return [
        [
            r.room_number,
            r.room_type,
            f"Floor {r.floor}",
            r.capacity,
            r.occupied,
            r.vacant_beds,
            r.status,
        ]
        for r in rooms
    ]


def _print_room_detail(room: Room):
    """Print full detail card for a single room."""
    print()
    print_line("-")
    print(f"  Room Number  : {room.room_number}")
    print(f"  Type         : {room.room_type}")
    print(f"  Floor        : {room.floor}")
    print(f"  Capacity     : {room.capacity} bed(s)")
    print(f"  Occupied     : {room.occupied} bed(s)")
    print(f"  Vacant Beds  : {room.vacant_beds}")
    print(f"  Status       : {room.status}")
    print(f"  Occupancy    : {room.occupancy_pct:.1f}%")
    print(f"  Amenities    : {', '.join(room.amenities) if room.amenities else 'None'}")

    # Show occupant names alongside IDs
    if room.occupants:
        print(f"  Occupants    :")
        for sid in room.occupants:
            stu = _find_student(sid)
            name = stu.name if stu else "Unknown"
            print(f"               {sid} - {name}")
    else:
        print(f"  Occupants    : (none)")
    print_line("-")
    print()


def _occupancy_bar(occupied: int, capacity: int, bar_len: int = 15) -> str:
    """
    Render a simple ASCII occupancy progress bar.
    e.g.  [###########....]  3/5
    Uses safe ASCII characters for Windows cp1252 console compatibility.
    """
    if capacity == 0:
        return "[" + "." * bar_len + "]  0/0"
    filled = round((occupied / capacity) * bar_len)
    bar    = "#" * filled + "." * (bar_len - filled)
    return f"[{bar}]  {occupied}/{capacity}"


def _sync_occupied_count(room: Room) -> Room:
    """
    Ensure room.occupied always matches len(room.occupants).
    Fixes any drift between the two fields before a save.
    """
    room.occupied = len(room.occupants)
    return room


# =======================================================================
#  FEATURE 1 - VIEW ALL ROOMS
# =======================================================================

def view_all_rooms():
    """Display all rooms in a formatted table with sort/filter options."""
    clear_screen()
    print_banner()
    print_header("All Rooms")

    rooms = _load_rooms()
    if not rooms:
        print_info("No rooms found in the system.")
        pause()
        return

    # -- Sort options using lambdas ------------------------------------
    print("\n  Sort / Filter:")
    print("    [1]  Room Number (default)")
    print("    [2]  Floor")
    print("    [3]  Occupancy % (high -> low)")
    print("    [4]  Room Type")
    print("    [5]  Show only available rooms")
    sort_choice = input("\n  >  Choice (Enter for default): ").strip()

    sort_map = {
        "2": lambda r: r.floor,
        "3": lambda r: -r.occupancy_pct,           # negative = descending
        "4": lambda r: r.room_type.lower(),
    }

    if sort_choice == "5":
        # List comprehension filter: only rooms with vacant beds
        display_rooms = [r for r in rooms if r.is_available]
        if not display_rooms:
            print_warning("All rooms are currently full.")
            pause()
            return
        print_info(f"Showing {len(display_rooms)} available room(s).")
    else:
        key = sort_map.get(sort_choice, lambda r: r.room_number)
        display_rooms = sorted(rooms, key=key)

    # -- Table ---------------------------------------------------------
    rows = _rooms_as_rows(display_rooms)
    print_table(ROOM_TABLE_HEADERS, rows)

    # -- Occupancy bars -------------------------------------------------
    # BUG5 FIX: label bars according to what's actually displayed
    if sort_choice == "5":
        print("  Occupancy Overview (available rooms only):")
    else:
        print("  Occupancy Overview (all rooms):")
    print()
    for r in sorted(display_rooms, key=lambda r: r.room_number):
        bar = _occupancy_bar(r.occupied, r.capacity)
        print(f"  Room {r.room_number:<5}  {bar}  [{r.room_type}]")
    print()

    # -- Summary stats: always show full-hostel totals ------------------
    total      = len(rooms)
    full_rooms = sum(1 for r in rooms if r.status == "Full")
    vacant     = sum(1 for r in rooms if r.status == "Vacant")
    partial    = sum(1 for r in rooms if r.status == "Partial")
    total_beds = sum(r.capacity for r in rooms)
    occ_beds   = sum(r.occupied for r in rooms)
    pct        = (occ_beds / total_beds * 100) if total_beds else 0

    print_line()
    print("  HOSTEL TOTALS:")
    print(f"  Rooms: {total}  |  Full: {full_rooms}  |  Partial: {partial}  |  Vacant: {vacant}")
    print(f"  Beds : {total_beds} total  |  {occ_beds} occupied  |  {total_beds - occ_beds} free  |  {pct:.1f}% occupancy")
    print_line()

    # Offer detailed view of one room
    detail_no = input("\n  >  Enter Room Number for full details (Enter to skip): ").strip()
    if detail_no:
        room = _find_room(detail_no)
        if room:
            _print_room_detail(room)
        else:
            print_error(f"Room '{detail_no}' not found.")

    pause()


# =======================================================================
#  FEATURE 2 - VIEW VACANT ROOMS
# =======================================================================

def view_vacant_rooms():
    """Show only rooms that have at least one free bed."""
    clear_screen()
    print_banner()
    print_header("Vacant / Available Rooms")

    rooms = _load_rooms()

    # List comprehension: filter rooms with vacant beds
    vacant_rooms = [r for r in rooms if r.is_available]

    if not vacant_rooms:
        print_warning("No rooms are currently available. All beds are occupied.")
        pause()
        return

    # Sort by vacant beds descending (most available first) using lambda
    vacant_rooms = sorted(vacant_rooms, key=lambda r: -r.vacant_beds)

    print_success(f"{len(vacant_rooms)} room(s) available for allocation.")

    rows = _rooms_as_rows(vacant_rooms)
    print_table(ROOM_TABLE_HEADERS, rows)

    # Group by type - uses dict comprehension + list comprehension
    print("  Available Rooms by Type:")
    print()
    grouped = {
        rtype: [r for r in vacant_rooms if r.room_type == rtype]
        for rtype in ROOM_TYPES
        if any(r.room_type == rtype for r in vacant_rooms)
    }
    for rtype, grp in grouped.items():
        room_nos = ", ".join(r.room_number for r in grp)
        free_beds = sum(r.vacant_beds for r in grp)
        print(f"  {rtype:<12} -> Rooms: {room_nos}  ({free_beds} free bed(s))")

    print()
    pause()


# =======================================================================
#  FEATURE 3 - ALLOCATE ROOM TO STUDENT
# =======================================================================

def allocate_room():
    """
    Allocate a room bed to a student.

    Validation rules (all enforced):
      1. Room must exist
      2. Room must have a free bed
      3. Student must exist
      4. Student must be active (is_active = True)
      5. Student must not already have a room assigned
      6. Student must not already be in this room's occupants list
    """
    clear_screen()
    print_banner()
    print_header("Allocate Room to Student")

    # -- Step 1: Pick a room -------------------------------------------
    # Show available rooms first for reference
    all_rooms    = _load_rooms()
    avail_rooms  = [r for r in all_rooms if r.is_available]

    if not avail_rooms:
        print_warning("No rooms are currently available. Cannot allocate.")
        pause()
        return

    print("\n  Available Rooms:")
    avail_rows = _rooms_as_rows(sorted(avail_rooms, key=lambda r: r.room_number))
    print_table(ROOM_TABLE_HEADERS, avail_rows)

    room_number = input("  >  Enter Room Number to allocate: ").strip()
    if not room_number:
        print_error("Room number cannot be empty.")
        pause()
        return

    room = _find_room(room_number)

    # Validation 1: Room must exist
    if not room:
        print_error(f"Room '{room_number}' does not exist.")
        pause()
        return

    # Validation 2: Room must have space
    if not room.is_available:
        print_error(f"Room {room_number} is full ({room.occupied}/{room.capacity} beds occupied).")
        pause()
        return

    # -- Step 2: Pick a student ----------------------------------------
    student_id = input("  >  Enter Student ID to allocate: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    student = _find_student(student_id)

    # Validation 3: Student must exist
    if not student:
        print_error(f"Student ID '{student_id}' not found.")
        pause()
        return

    # Validation 4: Student must be active
    if not student.is_active:
        print_error(f"Student {student_id} ({student.name}) is marked Inactive. Cannot allocate.")
        pause()
        return

    # Validation 5: Student must not already have a room
    if student.room_number and student.room_number != "Not Allocated":
        print_error(
            f"Student {student_id} ({student.name}) is already in Room {student.room_number}.\n"
            "  Use 'Transfer Room' to move them."
        )
        pause()
        return

    # Validation 6: Student not already in this room's occupants (safety net)
    if room.has_occupant(student_id):
        print_error(f"Student {student_id} is already listed as an occupant of Room {room_number}.")
        pause()
        return

    # -- Step 3: Confirm and save --------------------------------------
    print()
    print_line("-")
    print(f"  Student  : {student_id} - {student.name}")
    print(f"  Room     : {room_number} ({room.room_type}, Floor {room.floor})")
    print(f"  Beds     : {room.occupied}/{room.capacity} -> {room.occupied + 1}/{room.capacity}")
    print(f"  Amenities: {', '.join(room.amenities) if room.amenities else 'None'}")
    print_line("-")

    if not confirm("Confirm room allocation? (y/n)"):
        print_warning("Allocation cancelled.")
        pause()
        return

    # -- BUG6 FIX: re-read room fresh from disk right before saving ----
    # Ensures count is accurate even if user browsed a stale snapshot.
    room = _find_room(room_number)
    if not room:
        print_error(f"Room {room_number} could not be re-read. Allocation aborted.")
        pause()
        return
    if not room.is_available:
        print_error(
            f"Room {room_number} just became full before saving. Allocation aborted."
        )
        pause()
        return
    if room.has_occupant(student_id):
        print_error(f"Student {student_id} was already added to Room {room_number}. Aborted.")
        pause()
        return

    # -- Atomic update: room + student --------------------------------
    room.add_occupant(student_id)       # updates occupied count and occupants list
    _sync_occupied_count(room)          # keep occupied == len(occupants)
    student.room_number = room_number

    room_saved    = _save_room(room)
    student_saved = DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, student_id, student.to_dict())

    if room_saved and student_saved:
        print_success(
            f"Room {room_number} allocated to {student_id} ({student.name}) successfully!"
        )
    else:
        print_error("Allocation failed during save. Check data files.")

    pause()


# =======================================================================
#  FEATURE 4 - TRANSFER STUDENT ROOM
# =======================================================================

def transfer_room():
    """
    Move a student from their current room to a new room.
    Atomically:
      - Removes from old room's occupants list & decrements occupied
      - Adds to new room's occupants list & increments occupied
      - Updates student's room_number field
    """
    clear_screen()
    print_banner()
    print_header("Transfer Student Room")

    student_id = input("  >  Enter Student ID to transfer: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    student = _find_student(student_id)
    if not student:
        print_error(f"Student ID '{student_id}' not found.")
        pause()
        return

    if not student.is_active:
        print_error(f"Student {student_id} is Inactive. Cannot transfer.")
        pause()
        return

    current_room_no = student.room_number
    if not current_room_no or current_room_no == "Not Allocated":
        print_error(
            f"Student {student_id} ({student.name}) has no room currently. "
            "Use 'Allocate Room' instead."
        )
        pause()
        return

    old_room = _find_room(current_room_no)
    if not old_room:
        print_warning(
            f"Current room '{current_room_no}' not found in records. "
            "Proceeding with allocation to new room anyway."
        )

    # -- Show available rooms for new selection -------------------------
    all_rooms   = _load_rooms()
    avail_rooms = [
        r for r in all_rooms
        if r.is_available and r.room_number != current_room_no
    ]

    if not avail_rooms:
        print_warning("No other available rooms to transfer to.")
        pause()
        return

    print(f"\n  Student   : {student_id} - {student.name}")
    print(f"  Current   : Room {current_room_no}")
    print("\n  Available rooms for transfer:")
    print_table(ROOM_TABLE_HEADERS, _rooms_as_rows(
        sorted(avail_rooms, key=lambda r: r.room_number)
    ))

    new_room_no = input("  >  Enter New Room Number: ").strip()  # BUG3: strip whitespace
    if not new_room_no:
        print_error("New room number cannot be empty.")
        pause()
        return

    # Compare after stripping to avoid false mismatch on trailing spaces
    if new_room_no.strip() == current_room_no.strip():
        print_error("New room is the same as the current room. Transfer cancelled.")
        pause()
        return

    new_room = _find_room(new_room_no)
    if not new_room:
        print_error(f"Room '{new_room_no}' does not exist.")
        pause()
        return

    if not new_room.is_available:
        print_error(f"Room {new_room_no} is full ({new_room.occupied}/{new_room.capacity} beds). Choose another.")
        pause()
        return

    if new_room.has_occupant(student_id):
        print_error(f"Student {student_id} is already listed in Room {new_room_no}.")
        pause()
        return

    # -- Confirm -------------------------------------------------------
    print()
    print_line("-")
    print(f"  Student   : {student_id} - {student.name}")
    print(f"  From Room : {current_room_no}  ->  To Room : {new_room_no}")
    print(f"  New Room  : {new_room.room_type}, Floor {new_room.floor}, "
          f"{new_room.occupied}/{new_room.capacity} beds")
    print_line("-")

    if not confirm("Confirm room transfer? (y/n)"):
        print_warning("Transfer cancelled.")
        pause()
        return

    # -- Atomic transfer -----------------------------------------------
    # Remove from old room
    if old_room:
        old_room.remove_occupant(student_id)
        _sync_occupied_count(old_room)
        _save_room(old_room)

    # Re-read new room from disk right before adding (BUG6 pattern)
    new_room = _find_room(new_room_no)
    if not new_room:
        print_error(f"Room {new_room_no} could not be re-read. Transfer aborted.")
        pause()
        return
    if not new_room.is_available:
        print_error(f"Room {new_room_no} just became full. Transfer aborted.")
        pause()
        return

    new_room.add_occupant(student_id)
    _sync_occupied_count(new_room)
    _save_room(new_room)

    # Update student
    student.room_number = new_room_no
    DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, student_id, student.to_dict())

    print_success(
        f"Student {student_id} ({student.name}) transferred "
        f"from Room {current_room_no} to Room {new_room_no}."
    )
    pause()


# =======================================================================
#  FEATURE 5 - VACATE ROOM (REMOVE STUDENT FROM ROOM)
# =======================================================================

def vacate_room():
    """
    Remove a student from their current room.
    - Decrements room's occupied count
    - Removes student from occupants list
    - Sets student's room_number to 'Not Allocated'
    """
    clear_screen()
    print_banner()
    print_header("Vacate Room")

    print("  Vacate by:")
    print("    [1]  Student ID")
    print("    [2]  Room Number (vacate all or specific occupant)")
    choice = input("\n  >  Choice: ").strip()

    if choice == "1":
        _vacate_by_student()
    elif choice == "2":
        _vacate_by_room()
    else:
        print_error("Invalid choice.")
        pause()


def _vacate_by_student():
    """Remove a specific student from whichever room they occupy."""
    student_id = input("  >  Enter Student ID: ").strip().upper()
    if not student_id:
        print_error("Student ID cannot be empty.")
        pause()
        return

    student = _find_student(student_id)
    if not student:
        print_error(f"Student ID '{student_id}' not found.")
        pause()
        return

    if not student.room_number or student.room_number == "Not Allocated":
        print_warning(f"Student {student_id} ({student.name}) has no room to vacate.")
        pause()
        return

    room = _find_room(student.room_number)

    # BUG2 FIX: capture room_no string NOW before we clear student.room_number
    vacated_room_no = student.room_number

    print()
    print_line("-")
    print(f"  Student : {student_id} - {student.name}")
    print(f"  Room    : {vacated_room_no}")
    print_line("-")

    if not confirm("Remove student from this room? (y/n)"):
        print_warning("Cancelled.")
        pause()
        return

    # Update room (room object may be None if room was deleted from data)
    if room:
        room.remove_occupant(student_id)
        _sync_occupied_count(room)
        _save_room(room)
    else:
        print_warning(
            f"Room {vacated_room_no} not found in room records. "
            "Student record will still be updated."
        )

    # Update student - clear room assignment
    student.room_number = "Not Allocated"
    DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, student_id, student.to_dict())

    # BUG2 FIX: use captured string, not room object attribute
    print_success(f"Student {student_id} ({student.name}) has vacated Room {vacated_room_no}.")
    pause()


def _vacate_by_room():
    """Vacate a room - either a specific student or all occupants."""
    room_number = input("  >  Enter Room Number: ").strip()
    if not room_number:
        print_error("Room number cannot be empty.")
        pause()
        return

    room = _find_room(room_number)
    if not room:
        print_error(f"Room '{room_number}' not found.")
        pause()
        return

    if not room.occupants:
        print_warning(f"Room {room_number} is already vacant.")
        pause()
        return

    _print_room_detail(room)

    print("  Vacate options:")
    print("    [1]  Remove a specific occupant")
    print("    [2]  Vacate entire room (remove all occupants)")
    opt = input("\n  >  Choice: ").strip()

    if opt == "1":
        # Show occupant IDs, let admin pick one
        print("\n  Current occupants:")
        for i, sid in enumerate(room.occupants, 1):
            stu = _find_student(sid)
            name = stu.name if stu else "Unknown"
            print(f"    [{i}]  {sid} - {name}")

        sid_input = input("\n  >  Enter Student ID to remove: ").strip().upper()
        if sid_input not in room.occupants:
            print_error(f"Student {sid_input} is not in Room {room_number}.")
            pause()
            return

        if not confirm(f"Remove {sid_input} from Room {room_number}? (y/n)"):
            print_warning("Cancelled.")
            pause()
            return

        room.remove_occupant(sid_input)
        _save_room(room)

        # Update that student's record
        stu = _find_student(sid_input)
        if stu:
            stu.room_number = "Not Allocated"
            DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, sid_input, stu.to_dict())

        print_success(f"Student {sid_input} removed from Room {room_number}.")

    elif opt == "2":
        # BUG4 FIX: wrap in try/except and report partial failures
        if not confirm(
            f"Vacate entire Room {room_number} ({len(room.occupants)} student(s))? (y/n)"
        ):
            print_warning("Cancelled.")
            pause()
            return

        # Snapshot the list before mutating the room object
        occupant_ids = list(room.occupants)
        failed       = []

        for sid in occupant_ids:
            try:
                stu = _find_student(sid)
                if stu:
                    stu.room_number = "Not Allocated"
                    DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, sid, stu.to_dict())
                else:
                    print_warning(f"Student {sid} not found in student records (skipped).")
            except Exception as e:
                failed.append(sid)
                print_error(f"Failed to update student {sid}: {e}")

        # Clear room only after all student updates attempted
        room.occupants = [sid for sid in room.occupants if sid in failed]
        _sync_occupied_count(room)
        _save_room(room)

        released = len(occupant_ids) - len(failed)
        if not failed:
            print_success(
                f"Room {room_number} fully vacated. {released} student(s) unassigned."
            )
        else:
            print_warning(
                f"Partial vacate: {released} student(s) released, "
                f"{len(failed)} failed ({', '.join(failed)})."
            )
    else:
        print_error("Invalid option. Enter [1] or [2].")

    pause()


# =======================================================================
#  FEATURE 6 - ROOM OCCUPANCY SUMMARY
# =======================================================================

def room_occupancy_summary():
    """
    Display a comprehensive occupancy report:
    - Overall hostel stats
    - Per-floor breakdown
    - Per-room-type breakdown
    - Full occupancy table with bars
    """
    clear_screen()
    print_banner()
    print_header("Room Occupancy Summary")

    rooms = _load_rooms()
    if not rooms:
        print_info("No rooms found.")
        pause()
        return

    # -- Overall stats -------------------------------------------------
    total_rooms  = len(rooms)
    total_beds   = sum(r.capacity for r in rooms)
    occ_beds     = sum(r.occupied for r in rooms)
    free_beds    = total_beds - occ_beds
    full_rooms   = sum(1 for r in rooms if r.status == "Full")
    partial_rooms= sum(1 for r in rooms if r.status == "Partial")
    vacant_rooms = sum(1 for r in rooms if r.status == "Vacant")
    overall_pct  = (occ_beds / total_beds * 100) if total_beds else 0

    # BUG8 FIX: replaced box-drawing chars (++++|) with safe ASCII
    print()
    print("  +----------------------------------------------------------+")
    print(f"  |  OVERALL OCCUPANCY : {overall_pct:>5.1f}%                           |")
    print(f"  |  Total Rooms: {total_rooms:<4}  |  Full: {full_rooms:<3}  |  Partial: {partial_rooms:<3}  |  Vacant: {vacant_rooms:<3}  |")
    print(f"  |  Total Beds : {total_beds:<4}  |  Occupied: {occ_beds:<3}  |  Free: {free_beds:<3}            |")
    print("  +----------------------------------------------------------+")

    # -- Per-floor breakdown -------------------------------------------
    print("\n  -- By Floor " + "-" * 52)
    floors = sorted(set(r.floor for r in rooms))
    for fl in floors:
        floor_rooms = [r for r in rooms if r.floor == fl]
        fl_beds     = sum(r.capacity for r in floor_rooms)
        fl_occ      = sum(r.occupied for r in floor_rooms)
        fl_pct      = (fl_occ / fl_beds * 100) if fl_beds else 0
        bar         = _occupancy_bar(fl_occ, fl_beds, 20)
        print(f"  Floor {fl}:  {bar}   {fl_pct:.1f}%  ({len(floor_rooms)} rooms)")

    # -- Per-room-type breakdown ---------------------------------------
    print("\n  -- By Room Type " + "-" * 48)
    for rtype in ROOM_TYPES:
        # List comprehension: filter rooms by type
        type_rooms = [r for r in rooms if r.room_type == rtype]
        if not type_rooms:
            continue
        t_beds = sum(r.capacity for r in type_rooms)
        t_occ  = sum(r.occupied for r in type_rooms)
        t_pct  = (t_occ / t_beds * 100) if t_beds else 0
        bar    = _occupancy_bar(t_occ, t_beds, 20)
        print(f"  {rtype:<12} {bar}   {t_pct:.1f}%  ({len(type_rooms)} rooms)")

    # -- Full room-by-room table sorted by occupancy % desc -----------
    print("\n  -- Room-by-Room Detail " + "-" * 41)
    sorted_rooms = sorted(rooms, key=lambda r: -r.occupancy_pct)  # lambda sort
    print()
    print(f"  {'Room':<7} {'Type':<12} {'Floor':<7} {'Bar':<22} {'Occ%':<7} {'Status'}")
    print("  " + "-" * 65)
    for r in sorted_rooms:
        bar = _occupancy_bar(r.occupied, r.capacity, 12)
        print(
            f"  {r.room_number:<7} {r.room_type:<12} {r.floor:<7} "
            f"{bar:<22} {r.occupancy_pct:<7.1f} {r.status}"
        )

    print()
    print_line()
    pause()


# =======================================================================
#  ROOM MODULE MENU ENTRY POINT
# =======================================================================

# Admin menu options
_ADMIN_OPTIONS = [
    "[1] View All Rooms",
    "[2] View Vacant / Available Rooms",
    "[3] Allocate Room to Student",
    "[4] Transfer Student Room",
    "[5] Vacate Room",
    "[6] Room Occupancy Summary",
    "[7] Repair Occupancy Data (Admin)",
    "[8] Back to Main Menu",
]

# Student view options (read-only)
_STUDENT_OPTIONS = [
    "[1] View My Room Details",
    "[2] View Available Rooms",
    "[3] Back to Main Menu",
]


def room_menu(user: dict):
    """
    Entry point called from main.py.
    Admin sees full CRUD; student sees read-only view.
    """
    while True:
        clear_screen()
        print_banner()

        if user.get("role") == "admin":
            choice = print_menu("Room Management", _ADMIN_OPTIONS)

            if choice == "1":
                view_all_rooms()
            elif choice == "2":
                view_vacant_rooms()
            elif choice == "3":
                allocate_room()
            elif choice == "4":
                transfer_room()
            elif choice == "5":
                vacate_room()
            elif choice == "6":
                room_occupancy_summary()
            elif choice == "7":
                repair_occupancy_consistency()
            elif choice == "8":
                break
            else:
                print_error("Invalid choice. Enter a number between 1 and 8.")
                pause()

        else:
            # Student: read-only
            choice = print_menu("Room Info", _STUDENT_OPTIONS)

            if choice == "1":
                _view_my_room(user)
            elif choice == "2":
                view_vacant_rooms()
            elif choice == "3":
                break
            else:
                print_error("Invalid choice.")
                pause()


def _view_my_room(user: dict):
    """Allow a logged-in student to view their own room details."""
    clear_screen()
    print_banner()
    print_header("My Room Details")

    student_id = user.get("username", "")
    student    = _find_student(student_id)

    if not student:
        print_warning("Your student profile was not found. Contact the admin.")
        pause()
        return

    if not student.room_number or student.room_number == "Not Allocated":
        print_warning("You have not been allocated a room yet. Contact the admin.")
        pause()
        return

    room = _find_room(student.room_number)
    if not room:
        print_error(f"Room {student.room_number} details not found.")
        pause()
        return

    # Show room details (without listing other occupant IDs for privacy)
    print()
    print_line("-")
    print(f"  Room Number  : {room.room_number}")
    print(f"  Type         : {room.room_type}")
    print(f"  Floor        : {room.floor}")
    print(f"  Capacity     : {room.capacity} bed(s)")
    print(f"  Occupied     : {room.occupied} bed(s)")
    print(f"  Your Bed     : Assigned [OK]")  # BUG7 FIX: replaced emoji with ASCII
    print(f"  Amenities    : {', '.join(room.amenities) if room.amenities else 'None'}")
    print_line("-")
    print()

    pause()


# =======================================================================
#  FEATURE 7 - REPAIR OCCUPANCY CONSISTENCY  (BUG9 FIX)
# =======================================================================

def repair_occupancy_consistency():
    """
    Admin utility: scan all rooms and students for data drift.

    Checks:
      1. Room.occupied count vs len(Room.occupants)
      2. Every occupant ID in a room exists in students.json
      3. Every student whose room_number != 'Not Allocated' is
         actually listed as an occupant in that room

    Offers to auto-fix any drift found.
    """
    clear_screen()
    print_banner()
    print_header("[ADMIN] Repair Occupancy Data")

    rooms    = _load_rooms()
    students = DataHandler.get_all(STUDENT_ENTITY)

    # Build lookup maps
    room_map = {r.room_number: r for r in rooms}
    stu_map  = {s.get(STU_ID_FIELD, ""): s for s in students}

    issues = []   # list of (description, fix_callable)

    # -- Check 1: occupied count drift ---------------------------------
    for room in rooms:
        expected_count = len(room.occupants)
        if room.occupied != expected_count:
            desc = (
                f"Room {room.room_number}: occupied={room.occupied} "
                f"but occupants list has {expected_count} entries."
            )
            issues.append((desc, "count_drift", room.room_number))

    # -- Check 2: ghost occupants (IDs in room but not in students) -----
    for room in rooms:
        for sid in room.occupants:
            if sid not in stu_map:
                desc = (
                    f"Room {room.room_number}: occupant '{sid}' "
                    f"not found in students.json (ghost ID)."
                )
                issues.append((desc, "ghost_occupant", room.room_number, sid))

    # -- Check 3: student's room_number not reflected in room occupants -
    for s in students:
        sid      = s.get(STU_ID_FIELD, "")
        s_room   = s.get("room_number", "Not Allocated")
        if s_room and s_room != "Not Allocated":
            room = room_map.get(s_room)
            if room is None:
                desc = (
                    f"Student {sid} ({s.get('name','?')}) has room_number='{s_room}' "
                    f"but that room does not exist."
                )
                issues.append((desc, "missing_room", sid, s_room))
            elif sid not in room.occupants:
                desc = (
                    f"Student {sid} ({s.get('name','?')}) claims Room {s_room} "
                    f"but is NOT in that room's occupants list."
                )
                issues.append((desc, "not_in_room", sid, s_room))

    # -- Report ---------------------------------------------------------
    if not issues:
        print_success("No data inconsistencies found. All records are clean!")
        pause()
        return

    print_warning(f"{len(issues)} issue(s) found:")
    print()
    for i, issue in enumerate(issues, 1):
        print(f"  [{i}] {issue[0]}")

    print()
    if not confirm("Auto-fix all issues? (y/n)"):
        print_warning("No changes made.")
        pause()
        return

    # -- Auto-fix -------------------------------------------------------
    fixed = 0
    # Re-load fresh copies for mutation
    rooms    = _load_rooms()
    room_map = {r.room_number: r for r in rooms}

    for issue in issues:
        kind = issue[1]

        if kind == "count_drift":
            room_no = issue[2]
            room    = room_map.get(room_no)
            if room:
                _sync_occupied_count(room)
                _save_room(room)
                print_info(f"Fixed count drift in Room {room_no}.")
                fixed += 1

        elif kind == "ghost_occupant":
            room_no, ghost_sid = issue[2], issue[3]
            room = room_map.get(room_no)
            if room and ghost_sid in room.occupants:
                room.occupants.remove(ghost_sid)
                _sync_occupied_count(room)
                _save_room(room)
                print_info(f"Removed ghost occupant '{ghost_sid}' from Room {room_no}.")
                fixed += 1

        elif kind == "missing_room":
            sid, bad_room = issue[2], issue[3]
            stu_dict = stu_map.get(sid)
            if stu_dict:
                stu_dict["room_number"] = "Not Allocated"
                DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, sid, stu_dict)
                print_info(f"Cleared invalid room '{bad_room}' from student {sid}.")
                fixed += 1

        elif kind == "not_in_room":
            sid, room_no = issue[2], issue[3]
            room = room_map.get(room_no)
            if room and not room.has_occupant(sid) and room.is_available:
                room.add_occupant(sid)
                _sync_occupied_count(room)
                _save_room(room)
                print_info(f"Added student {sid} back to Room {room_no} occupants.")
                fixed += 1
            elif room and not room.is_available:
                # Room is full - clear the student's stale room_number instead
                stu_dict = stu_map.get(sid)
                if stu_dict:
                    stu_dict["room_number"] = "Not Allocated"
                    DataHandler.update(STUDENT_ENTITY, STU_ID_FIELD, sid, stu_dict)
                    print_info(
                        f"Room {room_no} full - cleared stale room_number from student {sid}."
                    )
                    fixed += 1

    print()
    print_success(f"Repair complete: {fixed}/{len(issues)} issue(s) fixed.")
    pause()
