"""Command-line entry point for the Student Management System."""
from __future__ import annotations
from getpass import getpass
import sqlite3
import sys
from typing import Any

from auth import (AuthError, AuthorizationError, authenticate_user, create_initial_admin,
                  get_user_count, register_user, require_role, validate_username)
from courses import CourseError, add_course, delete_course, get_course, list_courses, search_courses, update_course
from database import initialize_database
from reports import ReportError, generate_summary
from students import StudentError, add_student, delete_student, get_student, list_students, search_students, update_student
from users import UserManagementError, change_user_role, create_staff_account, delete_user, list_users
from utils import print_table


def prompt_for_password(prompt: str = "Password: ") -> str:
    """Get a password; fall back to visible input if the IDE console lacks TTY support."""
    try:
        is_tty = bool(sys.stdin.isatty())
    except (AttributeError, OSError):
        is_tty = False
    if not is_tty:
        print("(Password input is visible in this console.)")
        return input(prompt)
    try:
        password = getpass(prompt)
        # Some IDE Run consoles report TTY support but still return an empty value.
        if password:
            return password
        print("(Password hiding returned no input; password will be visible in this console.)")
        return input(prompt)
    except (KeyboardInterrupt, EOFError):
        raise
    except Exception:
        print("(Password hiding is unavailable; password will be visible in this console.)")
        return input(prompt)


def setup_initial_admin(db_path: str | None = None) -> None:
    """Ensure the first Admin exists, displaying validation errors without hidden loops."""
    while get_user_count(db_path) == 0:
        print("\nFirst-time setup: create the initial administrator.")
        print("This one-time setup is available only while no accounts exist.")
        print("Username: 3–30 characters; letters, numbers, dots, hyphens, underscores.")
        print("Password: at least 8 characters.")
        try:
            username = validate_username(input("Admin username: ").strip())
        except AuthError as error:
            print(f"Could not create administrator: {error}")
            continue
        password = prompt_for_password("Admin password (minimum 8 characters): ")
        confirmation = prompt_for_password("Confirm admin password: ")
        if not password:
            print("Could not create administrator: Password cannot be empty.")
            continue
        if password != confirmation:
            print("Could not create administrator: Passwords do not match.")
            continue
        try:
            create_initial_admin(username, password, db_path)
        except AuthError as error:
            print(f"Could not create administrator: {error}")
            continue
        print("Initial administrator created successfully.")
        break


def handle_registration(db_path: str | None = None) -> None:
    print("\n--- Staff Registration ---")
    print("New registrations receive the Staff role.")
    try:
        username = validate_username(input("Username: ").strip())
    except AuthError as error:
        print(f"Registration failed: {error}")
        return
    password = prompt_for_password("Password (minimum 8 characters): ")
    confirmation = prompt_for_password("Confirm password: ")
    if not password:
        print("Registration failed: Password cannot be empty.")
        return
    if password != confirmation:
        print("Registration failed: Passwords do not match.")
        return
    try:
        register_user(username, password, db_path)
    except AuthError as error:
        print(f"Registration failed: {error}")
    else:
        print("Registration successful. You can now log in as Staff.")


def _show_courses(user: dict[str, Any], db_path: str | None) -> list[dict[str, Any]]:
    courses = list_courses(user, db_path)
    print_table(["ID", "Course", "Duration", "Fee"],
                [[r["course_id"], r["course_name"], r["duration"], f'{r["fee"]:,.2f}'] for r in courses])
    return courses


def _show_students(user: dict[str, Any], db_path: str | None, records: list[dict[str, Any]] | None = None) -> None:
    students = list_students(user, db_path) if records is None else records
    print_table(["ID", "Name", "Email", "Phone", "Course", "Enrolled"],
                [[r["student_id"], r["name"], r["email"], r["phone"], r["course_name"], r["enrollment_date"]] for r in students])


def _add_student(user: dict[str, Any], db_path: str | None) -> None:
    print("\n--- Add Student ---")
    try:
        courses = list_courses(user, db_path)
        if not courses:
            print("No courses exist yet. Ask an Admin to add a course before adding students.")
            return
        print_table(["ID", "Course", "Duration", "Fee"],
                    [[r["course_id"], r["course_name"], r["duration"], f'{r["fee"]:,.2f}'] for r in courses])
        name = input("Student name: ").strip()
        email = input("Email: ").strip()
        phone = input("Phone: ").strip()
        course_id = input("Course ID: ").strip()
        enroll_date = input("Enrollment date [YYYY-MM-DD, blank=today]: ").strip() or None
        identifier = add_student(user, name, email, phone, course_id, enroll_date, db_path)
        print(f"Student added successfully. Student ID: {identifier}")
    except (StudentError, CourseError, AuthorizationError) as error:
        print(f"Could not add student: {error}")


def _search_student(user: dict[str, Any], db_path: str | None) -> None:
    try:
        query = input("Search by student ID, name, email, or phone: ").strip()
        _show_students(user, db_path, search_students(user, query, db_path))
    except (StudentError, AuthorizationError) as error:
        print(f"Search failed: {error}")


def _update_student(user: dict[str, Any], db_path: str | None) -> None:
    try:
        identifier = input("Student ID to update: ").strip()
        current = get_student(user, identifier, db_path)
        if current is None:
            print("No student found with that ID.")
            return
        courses = list_courses(user, db_path)
        print_table(["ID", "Course", "Duration", "Fee"],
                    [[r["course_id"], r["course_name"], r["duration"], f'{r["fee"]:,.2f}'] for r in courses])
        print("Press Enter to keep the current value.")
        name = input(f'Name [{current["name"]}]: ').strip() or current["name"]
        email = input(f'Email [{current["email"]}]: ').strip() or current["email"]
        phone = input(f'Phone [{current["phone"]}]: ').strip() or current["phone"]
        course = input(f'Course ID [{current["course_id"]}]: ').strip() or str(current["course_id"])
        enrolled = input(f'Enrollment date [{current["enrollment_date"]}]: ').strip() or current["enrollment_date"]
        changed = update_student(user, identifier, name, email, phone, course, enrolled, db_path)
        print("Student updated successfully." if changed else "No student record was changed.")
    except (StudentError, CourseError, AuthorizationError) as error:
        print(f"Could not update student: {error}")


def _delete_student(user: dict[str, Any], db_path: str | None) -> None:
    identifier = input("Student ID to delete: ").strip()
    if input("Delete this student permanently? (y/N): ").strip().lower() != "y":
        print("Deletion cancelled.")
        return
    try:
        deleted = delete_student(user, identifier, db_path)
        print("Student deleted successfully." if deleted else "No student found with that ID.")
    except (StudentError, AuthorizationError) as error:
        print(f"Could not delete student: {error}")


def _students_menu(user: dict[str, Any], db_path: str | None) -> None:
    while True:
        print("\n--- Student Management ---")
        print("1. Add Student\n2. View All Students\n3. Search Student\n4. Update Student")
        if user["role"] == "admin":
            print("5. Delete Student\n6. Back")
        else:
            print("5. Back")
        choice = input("Enter your choice: ").strip()
        if choice == "1": _add_student(user, db_path)
        elif choice == "2":
            try: _show_students(user, db_path)
            except (StudentError, AuthorizationError) as error: print(f"Could not retrieve students: {error}")
        elif choice == "3": _search_student(user, db_path)
        elif choice == "4": _update_student(user, db_path)
        elif choice == "5" and user["role"] == "admin": _delete_student(user, db_path)
        elif choice == ("6" if user["role"] == "admin" else "5"): return
        else: print("Invalid choice. Select an option shown above.")


def _add_course(user: dict[str, Any], db_path: str | None) -> None:
    try:
        name = input("Course name: ").strip()
        duration = input("Duration (e.g. 6 months): ").strip()
        fee = input("Course fee: ").strip()
        identifier = add_course(user, name, duration, fee, db_path)
        print(f"Course added successfully. Course ID: {identifier}")
    except (CourseError, AuthorizationError) as error:
        print(f"Could not add course: {error}")


def _search_course(user: dict[str, Any], db_path: str | None) -> None:
    try:
        results = search_courses(user, input("Search course name or duration: ").strip(), db_path)
        print_table(["ID", "Course", "Duration", "Fee"], [[r["course_id"], r["course_name"], r["duration"], f'{r["fee"]:,.2f}'] for r in results])
    except (CourseError, AuthorizationError) as error:
        print(f"Search failed: {error}")


def _update_course(user: dict[str, Any], db_path: str | None) -> None:
    try:
        identifier = input("Course ID to update: ").strip()
        current = get_course(user, identifier, db_path)
        if current is None:
            print("No course found with that ID.")
            return
        print("Press Enter to keep the current value.")
        name = input(f'Course name [{current["course_name"]}]: ').strip() or current["course_name"]
        duration = input(f'Duration [{current["duration"]}]: ').strip() or current["duration"]
        fee_text = input(f'Fee [{current["fee"]:.2f}]: ').strip()
        fee = fee_text or current["fee"]
        changed = update_course(user, identifier, name, duration, fee, db_path)
        print("Course updated successfully." if changed else "No course record was changed.")
    except (CourseError, AuthorizationError) as error:
        print(f"Could not update course: {error}")


def _delete_course(user: dict[str, Any], db_path: str | None) -> None:
    identifier = input("Course ID to delete: ").strip()
    if input("Delete this course? (y/N): ").strip().lower() != "y":
        print("Deletion cancelled.")
        return
    try:
        deleted = delete_course(user, identifier, db_path)
        print("Course deleted successfully." if deleted else "No course found with that ID.")
    except (CourseError, AuthorizationError) as error:
        print(f"Could not delete course: {error}")


def _courses_menu(user: dict[str, Any], db_path: str | None) -> None:
    while True:
        print("\n--- Course Management ---\n1. Add Course\n2. View Courses\n3. Search Courses\n4. Update Course\n5. Delete Course\n6. Back")
        choice = input("Enter your choice: ").strip()
        if choice == "1": _add_course(user, db_path)
        elif choice == "2":
            try: _show_courses(user, db_path)
            except (CourseError, AuthorizationError) as error: print(f"Could not retrieve courses: {error}")
        elif choice == "3": _search_course(user, db_path)
        elif choice == "4": _update_course(user, db_path)
        elif choice == "5": _delete_course(user, db_path)
        elif choice == "6": return
        else: print("Invalid choice. Enter 1–6.")


def _users_menu(user: dict[str, Any], db_path: str | None) -> None:
    while True:
        print("\n--- User Administration ---\n1. View Users\n2. Create Staff Account\n3. Change User Role\n4. Delete User\n5. Back")
        choice = input("Enter your choice: ").strip()
        try:
            if choice == "1":
                rows = list_users(user, db_path)
                print_table(["ID", "Username", "Role", "Created"], [[r["user_id"], r["username"], r["role"], r["created_at"]] for r in rows])
            elif choice == "2":
                try: username = validate_username(input("New Staff username: ").strip())
                except AuthError as error:
                    print(f"Could not create Staff account: {error}")
                    continue
                password = prompt_for_password("Password (minimum 8 characters): ")
                confirmation = prompt_for_password("Confirm password: ")
                if not password: print("Password cannot be empty.")
                elif password != confirmation: print("Passwords do not match. No account was created.")
                else: print(f"Staff account created. User ID: {create_staff_account(user, username, password, db_path)}")
            elif choice == "3":
                target = input("User ID: ").strip()
                role = input("New role (admin/staff): ").strip().lower()
                print("Role updated successfully." if change_user_role(user, target, role, db_path) else "No user found with that ID.")
            elif choice == "4":
                target = input("User ID to delete: ").strip()
                if input("Delete this account? (y/N): ").strip().lower() != "y": print("Deletion cancelled.")
                else: print("User deleted successfully." if delete_user(user, target, db_path) else "No user found with that ID.")
            elif choice == "5": return
            else: print("Invalid choice. Enter 1–5.")
        except (UserManagementError, AuthorizationError, AuthError, sqlite3.Error) as error:
            print(f"User operation failed: {error}")


def _reports_menu(user: dict[str, Any], db_path: str | None) -> None:
    try:
        report = generate_summary(user, db_path)
        print("\n--- Student Management Summary ---")
        print(f"Total students: {report['student_count']}\nTotal courses: {report['course_count']}")
        print("Users by role:")
        print_table(["Role", "Count"], [[key.title(), value] for key, value in report["user_counts"].items()])
        print("Enrollment by course:")
        print_table(["Course ID", "Course", "Students"], [[r["course_id"], r["course_name"], r["student_count"]] for r in report["enrollment_by_course"]])
    except (ReportError, AuthorizationError) as error:
        print(f"Could not generate report: {error}")


def show_admin_menu(user: dict[str, Any], db_path: str | None = None) -> None:
    try: require_role(user, "admin")
    except AuthorizationError as error:
        print(error); return
    while True:
        print("\n====================================\n             ADMIN PANEL\n====================================")
        print("1. Manage Students\n2. Manage Courses\n3. Manage Users\n4. View Reports\n5. Logout")
        choice = input("Enter your choice: ").strip()
        if choice == "1": _students_menu(user, db_path)
        elif choice == "2": _courses_menu(user, db_path)
        elif choice == "3": _users_menu(user, db_path)
        elif choice == "4": _reports_menu(user, db_path)
        elif choice == "5": print("Logged out successfully."); return
        else: print("Invalid choice. Please enter a number from 1 to 5.")


def show_staff_menu(user: dict[str, Any], db_path: str | None = None) -> None:
    try: require_role(user, "staff")
    except AuthorizationError as error:
        print(error); return
    while True:
        print("\n====================================\n             STAFF PANEL\n====================================")
        print("1. Add Student\n2. View All Students\n3. Search Student\n4. Update Student\n5. View Courses\n6. Logout")
        choice = input("Enter your choice: ").strip()
        if choice == "1": _add_student(user, db_path)
        elif choice == "2":
            try: _show_students(user, db_path)
            except (StudentError, AuthorizationError) as error: print(f"Could not retrieve students: {error}")
        elif choice == "3": _search_student(user, db_path)
        elif choice == "4": _update_student(user, db_path)
        elif choice == "5":
            try: _show_courses(user, db_path)
            except (CourseError, AuthorizationError) as error: print(f"Could not retrieve courses: {error}")
        elif choice == "6": print("Logged out successfully."); return
        else: print("Invalid choice. Please enter a number from 1 to 6.")


def handle_login(db_path: str | None = None) -> None:
    print("\n--- Login ---")
    username = input("Username: ").strip()
    password = prompt_for_password()
    user = authenticate_user(username, password, db_path)
    if user is None:
        print("Login failed. Check your username and password.")
    elif user["role"] == "admin":
        print(f"\nWelcome, {user['username']}! Role: Admin.")
        show_admin_menu(user, db_path)
    elif user["role"] == "staff":
        print(f"\nWelcome, {user['username']}! Role: Staff.")
        show_staff_menu(user, db_path)
    else:
        print("This account has an unsupported role. Please contact an administrator.")


def main(db_path: str | None = None) -> None:
    try:
        initialize_database(db_path)
        setup_initial_admin(db_path)
        while True:
            print("\n========================================\n       STUDENT MANAGEMENT SYSTEM\n========================================")
            print("1. Register\n2. Login\n3. Exit")
            choice = input("Enter your choice: ").strip()
            if choice == "1":
                try:
                    handle_registration(db_path)
                except sqlite3.Error as error:
                    print(f"Registration could not be completed because of a database error: {error}")
            elif choice == "2":
                try:
                    handle_login(db_path)
                except sqlite3.Error as error:
                    print(f"Login or menu operation could not be completed because of a database error: {error}")
            elif choice == "3":
                print("Goodbye!")
                return
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled. Goodbye!")
    except sqlite3.Error as error:
        print(f"Database error: {error}")

if __name__ == "__main__":
    main()
