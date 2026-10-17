"""SQLite connection helpers, schema initialization, and demo-data seeding."""
from __future__ import annotations
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.environ.get("STUDENT_MANAGEMENT_DB", str(BASE_DIR / "student_management.db"))).expanduser()
PathLike = Union[str, Path]

def get_connection(db_path: PathLike | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

@contextmanager
def database_connection(db_path: PathLike | None = None) -> Iterator[sqlite3.Connection]:
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize_database(db_path: PathLike | None = None) -> Path:
    """Create the database file and its three related tables if needed."""
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(username)) BETWEEN 3 AND 30),
        password_hash TEXT NOT NULL CHECK(length(trim(password_hash)) > 0),
        role TEXT NOT NULL DEFAULT 'staff' CHECK(role IN ('admin','staff')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(course_name)) BETWEEN 2 AND 100),
        duration TEXT NOT NULL CHECK(length(trim(duration)) BETWEEN 1 AND 50),
        fee REAL NOT NULL DEFAULT 0 CHECK(fee >= 0)
    );
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 100),
        email TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(email)) BETWEEN 3 AND 254),
        phone TEXT NOT NULL CHECK(length(trim(phone)) BETWEEN 7 AND 25),
        course_id INTEGER NOT NULL,
        enrollment_date TEXT NOT NULL DEFAULT CURRENT_DATE,
        FOREIGN KEY(course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE RESTRICT
    );
    CREATE INDEX IF NOT EXISTS idx_students_course_id ON students(course_id);
    CREATE INDEX IF NOT EXISTS idx_students_name ON students(name COLLATE NOCASE);
    """
    with database_connection(path) as connection:
        connection.executescript(schema)
    return path

def get_table_names(db_path: PathLike | None = None) -> list[str]:
    with database_connection(db_path) as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [str(row["name"]) for row in rows]

def seed_sample_data(db_path: PathLike | None = None) -> None:
    """Seed the distributed demo database only; not called during normal startup."""
    path = initialize_database(db_path)
    sample_courses = [
        ("Python Programming", "6 months", 12000.0),
        ("Data Analytics", "6 months", 18000.0),
        ("Web Development", "1 year", 25000.0),
        ("Database Management", "3 months", 8000.0),
        ("Artificial Intelligence", "1 year", 35000.0),
    ]
    with database_connection(path) as connection:
        if connection.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
            connection.executemany("INSERT INTO courses(course_name,duration,fee) VALUES(?,?,?)", sample_courses)
        if connection.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            rows = connection.execute("SELECT course_id,course_name FROM courses").fetchall()
            ids = {str(row["course_name"]): int(row["course_id"]) for row in rows}
            demo = [
                ("Asha Nair", "asha.nair@example.com", "+91-9000000001", ids["Python Programming"], "2026-01-12"),
                ("Arjun Thomas", "arjun.thomas@example.com", "+91-9000000002", ids["Data Analytics"], "2026-02-03"),
                ("Nikhil Varghese", "nikhil.varghese@example.com", "+91-9000000003", ids["Web Development"], "2026-02-18"),
            ]
            connection.executemany("INSERT INTO students(name,email,phone,course_id,enrollment_date) VALUES(?,?,?,?,?)", demo)
