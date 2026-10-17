"""Administrator summary reports."""
from __future__ import annotations
import sqlite3
from typing import Any
from auth import require_permission
from database import database_connection, initialize_database

class ReportError(ValueError):
    """Raised when report generation fails."""

def generate_summary(actor: dict[str, Any] | None, db_path=None) -> dict[str, Any]:
    require_permission(actor, "report:view")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            students = int(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0])
            courses = int(conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0])
            users = conn.execute("SELECT role,COUNT(*) AS total FROM users GROUP BY role ORDER BY role").fetchall()
            enrollment = conn.execute("SELECT c.course_id,c.course_name,COUNT(s.student_id) AS student_count FROM courses c LEFT JOIN students s ON s.course_id=c.course_id GROUP BY c.course_id,c.course_name ORDER BY c.course_name COLLATE NOCASE").fetchall()
        return {"student_count": students, "course_count": courses,
                "user_counts": {str(r["role"]): int(r["total"]) for r in users},
                "enrollment_by_course": [{"course_id": int(r["course_id"]), "course_name": str(r["course_name"]), "student_count": int(r["student_count"])} for r in enrollment]}
    except sqlite3.Error as error:
        raise ReportError(f"Could not generate report: {error}") from error
