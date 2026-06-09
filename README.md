# Smart_Hostel_Managment_System
# HostelHub – Smart Hostel Management System

A console-based, menu-driven Smart Hostel Management System built in Python.

## Tech Stack
- Python (OOP)
- SQLite3 / JSON file handling
- Standard Python libraries only

# ID: admin
# Password: admin123

## Project Structure

```
hostelhub/
│
├── main.py                  # Entry point
├── requirements.txt         # Dependencies (standard library only)
├── README.md
│
├── data/                    # JSON data files
│   ├── students.json
│   ├── rooms.json
│   ├── fees.json
│   ├── complaints.json
│   ├── attendance.json
│   └── notices.json
│
├── models/                  # OOP Data Models
│   ├── __init__.py
│   ├── student.py
│   ├── room.py
│   ├── fee.py
│   ├── complaint.py
│   ├── attendance.py
│   └── notice.py
│
├── modules/                 # Feature Modules
│   ├── __init__.py
│   ├── auth.py
│   ├── student_manager.py
│   ├── room_manager.py
│   ├── fee_manager.py
│   ├── complaint_manager.py
│   ├── attendance_manager.py
│   └── notice_manager.py
│
├── database/                # Database layer
│   ├── __init__.py
│   └── db_handler.py
│
├── utils/                   # Utility helpers
│   ├── __init__.py
│   ├── display.py           # Table/menu display helpers
│   ├── validators.py        # Input validation
│   └── helpers.py           # Common helpers
│
└── exports/                 # CSV exports (generated at runtime)
```

## How to Run
```
python main.py
```

## Modules
1. Authentication (Admin / Student login)
2. Student Management
3. Room Management
4. Fee Management
5. Complaint Management
6. Attendance Management
7. Notice Board
8. Dashboard / Statistics
