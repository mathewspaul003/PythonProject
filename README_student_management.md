# Student Management System (Python + SQLite)

A command-line Student Management System built with Python 3 and SQLite for a database-management major project. It demonstrates CRUD operations, relational database design, authentication, role-based access, input validation, and exception handling.

## Features

- First-run setup for the initial Admin account.
- Staff registration, login, and logout.
- Passwords stored as salted PBKDF2-HMAC-SHA256 hashes; passwords are never stored in plain text.
- Role-specific permissions for **Admin** and **Staff**.
- Student operations: add, list, search by ID/name/email/phone, update, and (Admin only) delete.
- Course operations: add, list, search, update, and delete (Admin only).
- Course/student foreign-key relationship; courses with enrolled students cannot be deleted.
- Admin user management: list users, create Staff accounts, change roles, and delete other accounts. The active account and final Admin are protected from deletion/demotion.
- Admin reports: student/course totals, user counts by role, and enrollment per course.
- Input checks for required fields, usernames, email, phone, IDs, fees, and enrollment dates.
- Parameterized SQL statements and helpful handling of duplicate and missing records.
- Automatic SQLite database/table creation.

## Requirements

- Python 3.10 or newer.
- No third-party Python packages are required; the project uses Python's standard library, including `sqlite3`.

## Run the application

1. Extract the project ZIP.
2. Open the extracted `student_management_final` folder in VS Code (or your preferred editor).
3. Open a terminal in that folder.
4. Run:

   ```bash
   python main.py
   ```

On first run, create the initial Admin username and password. Usernames must be 3–30 characters and may contain letters, numbers, `.`, `_`, or `-`. Passwords must be at least eight characters long.

Some IDE Run consoles cannot hide password entry. In that case, the application warns that the password will be visible and falls back to ordinary input. For hidden password entry, run the program in a real terminal.

The distributed `student_management.db` is a demonstration database with sample course and student records but **no pre-created account**. Create your own Admin when the application first starts. If you prefer a clean empty database, back up any data you want and delete `student_management.db`; a new database and its tables will be created automatically at startup.

## Main menu

```text
1. Register
2. Login
3. Exit
```

Public registration always creates a Staff account. Admin accounts are created by first-run setup or can be assigned by an existing Admin through user management.

### Admin menu

- Manage Students: add, view, search, update, delete.
- Manage Courses: add, view, search, update, delete.
- Manage Users: view accounts, create Staff account, change role, delete another account.
- View Reports: summary totals and enrollment by course.
- Logout.

### Staff menu

- Add Student.
- View All Students.
- Search Student.
- Update Student.
- View Courses.
- Logout.

Staff cannot delete students or create/update/delete courses. Permissions are also checked in the operation functions, not only hidden in the menus.

## Database design

The database contains three related tables:

- `users`: user ID, unique username, password hash, role, creation timestamp.
- `courses`: course ID, unique course name, duration, fee.
- `students`: student ID, name, unique email, phone, course ID, enrollment date.

`students.course_id` references `courses.course_id`. The foreign key is enabled for every connection, and deletion of a course with enrolled students is restricted. Primary keys, uniqueness rules, checks, and indexes support data integrity.

## Run the tests

From the project folder:

```bash
python -m unittest discover -s tests -v
```

The tests use temporary databases and do not modify the distributed sample database.

## Project files

```text
student_management_final/
├── main.py                 # Menus and command-line interaction
├── database.py             # SQLite setup, connections, schema, demo-data seeding
├── auth.py                 # Registration, password hashing, login, permissions
├── students.py             # Student CRUD and search
├── courses.py              # Course CRUD and search
├── users.py                # Admin user management
├── reports.py              # Admin summary reports
├── utils.py                # Validation and terminal table formatting
├── student_management.db   # Demo SQLite database (no user accounts)
├── tests/                  # Automated tests
├── README.md
└── .gitignore
```

## Notes

- Do not commit real personal or sensitive student information to a public repository. The included records are fictional examples.
- Do not commit virtual environments or `__pycache__` folders.
- A local database can be backed up by copying `student_management.db` while the program is closed.
