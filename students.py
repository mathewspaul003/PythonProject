"""Student CRUD operations with validation and role-based authorization."""
from __future__ import annotations
import sqlite3
from typing import Any
from auth import require_permission
from database import database_connection, initialize_database
from utils import ValidationError, clean_text, validate_date, validate_email, validate_id, validate_phone

class StudentError(ValueError):
    """Raised for invalid student operations."""

def _validate(name, email, phone, course_id, enrollment_date=None):
    try:
        return (clean_text(name, "Student name", 2, 100), validate_email(email),
                validate_phone(phone), validate_id(course_id, "Course ID"), validate_date(enrollment_date))
    except ValidationError as error:
        raise StudentError(str(error)) from error

def _row(row: sqlite3.Row) -> dict[str, Any]:
    return {"student_id": int(row["student_id"]), "name": str(row["name"]), "email": str(row["email"]),
            "phone": str(row["phone"]), "course_id": int(row["course_id"]),
            "course_name": str(row["course_name"]), "enrollment_date": str(row["enrollment_date"])}

_SELECT = "SELECT s.student_id,s.name,s.email,s.phone,s.course_id,c.course_name,s.enrollment_date FROM students s JOIN courses c ON c.course_id=s.course_id"

def add_student(user: dict[str, Any] | None, name: str, email: str, phone: str, course_id: object,
                enrollment_date: str | None = None, db_path=None) -> int:
    require_permission(user, "student:create")
    values = _validate(name, email, phone, course_id, enrollment_date)
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("INSERT INTO students(name,email,phone,course_id,enrollment_date) VALUES(?,?,?,?,?)", values)
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        msg = str(error).lower()
        if "unique constraint failed" in msg:
            raise StudentError("A student with that email address already exists.") from error
        if "foreign key constraint failed" in msg:
            raise StudentError("The selected course does not exist. Choose a valid course ID.") from error
        raise StudentError(f"Could not add student: {error}") from error
    except sqlite3.Error as error:
        raise StudentError(f"Database error while adding student: {error}") from error

def list_students(user: dict[str, Any] | None, db_path=None) -> list[dict[str, Any]]:
    require_permission(user, "student:read")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            rows = conn.execute(_SELECT + " ORDER BY s.student_id").fetchall()
        return [_row(row) for row in rows]
    except sqlite3.Error as error:
        raise StudentError(f"Could not retrieve students: {error}") from error

def get_student(user: dict[str, Any] | None, student_id: object, db_path=None) -> dict[str, Any] | None:
    require_permission(user, "student:read")
    try:
        identifier = validate_id(student_id, "Student ID")
    except ValidationError as error:
        raise StudentError(str(error)) from error
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            row = conn.execute(_SELECT + " WHERE s.student_id=?", (identifier,)).fetchone()
        return _row(row) if row else None
    except sqlite3.Error as error:
        raise StudentError(f"Could not retrieve student: {error}") from error

def search_students(user: dict[str, Any] | None, query: str, db_path=None) -> list[dict[str, Any]]:
    require_permission(user, "student:read")
    term = query.strip() if isinstance(query, str) else ""
    if not term:
        raise StudentError("Search text cannot be empty.")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            rows = conn.execute(_SELECT + " WHERE s.name LIKE ? OR s.email LIKE ? OR s.phone LIKE ? OR CAST(s.student_id AS TEXT)=? ORDER BY s.student_id", (f"%{term}%", f"%{term}%", f"%{term}%", term)).fetchall()
        return [_row(row) for row in rows]
    except sqlite3.Error as error:
        raise StudentError(f"Could not search students: {error}") from error

def update_student(user: dict[str, Any] | None, student_id: object, name: str, email: str, phone: str,
                   course_id: object, enrollment_date: str | None = None, db_path=None) -> bool:
    require_permission(user, "student:update")
    try:
        identifier = validate_id(student_id, "Student ID")
    except ValidationError as error:
        raise StudentError(str(error)) from error
    values = _validate(name, email, phone, course_id, enrollment_date)
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("UPDATE students SET name=?,email=?,phone=?,course_id=?,enrollment_date=? WHERE student_id=?", (*values, identifier))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError as error:
        msg = str(error).lower()
        if "unique constraint failed" in msg:
            raise StudentError("A student with that email address already exists.") from error
        if "foreign key constraint failed" in msg:
            raise StudentError("The selected course does not exist. Choose a valid course ID.") from error
        raise StudentError(f"Could not update student: {error}") from error
    except sqlite3.Error as error:
        raise StudentError(f"Database error while updating student: {error}") from error

def delete_student(user: dict[str, Any] | None, student_id: object, db_path=None) -> bool:
    require_permission(user, "student:delete")
    try:
        identifier = validate_id(student_id, "Student ID")
    except ValidationError as error:
        raise StudentError(str(error)) from error
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("DELETE FROM students WHERE student_id=?", (identifier,))
            return cursor.rowcount > 0
    except sqlite3.Error as error:
        raise StudentError(f"Database error while deleting student: {error}") from error
