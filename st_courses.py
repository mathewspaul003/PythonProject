"""Course CRUD operations with validation and role-based authorization."""
from __future__ import annotations
import sqlite3
from typing import Any
from auth import require_permission
from database import database_connection, initialize_database
from utils import ValidationError, clean_text, validate_duration, validate_fee, validate_id

class CourseError(ValueError):
    """Raised for invalid course operations."""

def _name(value: str) -> str:
    try:
        return clean_text(value, "Course name", 2, 100)
    except ValidationError as error:
        raise CourseError(str(error)) from error

def _row(row: sqlite3.Row) -> dict[str, Any]:
    return {"course_id": int(row["course_id"]), "course_name": str(row["course_name"]),
            "duration": str(row["duration"]), "fee": float(row["fee"])}

def add_course(user: dict[str, Any] | None, course_name: str, duration: str, fee: object, db_path=None) -> int:
    require_permission(user, "course:create")
    name = _name(course_name)
    try:
        length, price = validate_duration(duration), validate_fee(fee)
    except ValidationError as error:
        raise CourseError(str(error)) from error
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("INSERT INTO courses(course_name,duration,fee) VALUES(?,?,?)", (name, length, price))
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        if "unique constraint failed" in str(error).lower():
            raise CourseError("A course with that name already exists.") from error
        raise CourseError(f"Could not add course: {error}") from error
    except sqlite3.Error as error:
        raise CourseError(f"Database error while adding course: {error}") from error

def list_courses(user: dict[str, Any] | None, db_path=None) -> list[dict[str, Any]]:
    require_permission(user, "course:read")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            rows = conn.execute("SELECT course_id,course_name,duration,fee FROM courses ORDER BY course_name COLLATE NOCASE").fetchall()
        return [_row(row) for row in rows]
    except sqlite3.Error as error:
        raise CourseError(f"Could not retrieve courses: {error}") from error

def get_course(user: dict[str, Any] | None, course_id: object, db_path=None) -> dict[str, Any] | None:
    require_permission(user, "course:read")
    try:
        identifier = validate_id(course_id, "Course ID")
    except ValidationError as error:
        raise CourseError(str(error)) from error
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            row = conn.execute("SELECT course_id,course_name,duration,fee FROM courses WHERE course_id=?", (identifier,)).fetchone()
        return _row(row) if row else None
    except sqlite3.Error as error:
        raise CourseError(f"Could not retrieve course: {error}") from error

def search_courses(user: dict[str, Any] | None, query: str, db_path=None) -> list[dict[str, Any]]:
    require_permission(user, "course:read")
    term = query.strip() if isinstance(query, str) else ""
    if not term:
        raise CourseError("Search text cannot be empty.")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            rows = conn.execute("SELECT course_id,course_name,duration,fee FROM courses WHERE course_name LIKE ? OR duration LIKE ? ORDER BY course_name COLLATE NOCASE", (f"%{term}%", f"%{term}%")).fetchall()
        return [_row(row) for row in rows]
    except sqlite3.Error as error:
        raise CourseError(f"Could not search courses: {error}") from error

def update_course(user: dict[str, Any] | None, course_id: object, course_name: str, duration: str, fee: object, db_path=None) -> bool:
    require_permission(user, "course:update")
    try:
        identifier = validate_id(course_id, "Course ID")
        name = _name(course_name)
        length, price = validate_duration(duration), validate_fee(fee)
    except ValidationError as error:
        raise CourseError(str(error)) from error
    except CourseError:
        raise
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("UPDATE courses SET course_name=?,duration=?,fee=? WHERE course_id=?", (name, length, price, identifier))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError as error:
        if "unique constraint failed" in str(error).lower():
            raise CourseError("A course with that name already exists.") from error
        raise CourseError(f"Could not update course: {error}") from error
    except sqlite3.Error as error:
        raise CourseError(f"Database error while updating course: {error}") from error

def delete_course(user: dict[str, Any] | None, course_id: object, db_path=None) -> bool:
    require_permission(user, "course:delete")
    try:
        identifier = validate_id(course_id, "Course ID")
    except ValidationError as error:
        raise CourseError(str(error)) from error
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            cursor = conn.execute("DELETE FROM courses WHERE course_id=?", (identifier,))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError as error:
        if "foreign key constraint failed" in str(error).lower():
            raise CourseError("Cannot delete this course because students are enrolled in it.") from error
        raise CourseError(f"Could not delete course: {error}") from error
    except sqlite3.Error as error:
        raise CourseError(f"Database error while deleting course: {error}") from error
