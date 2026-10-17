"""Administrator-only user management operations."""
from __future__ import annotations
import sqlite3
from typing import Any
from auth import register_user, require_permission
from database import database_connection, initialize_database
from utils import ValidationError, validate_id

class UserManagementError(ValueError):
    """Raised when user administration fails."""

def list_users(actor: dict[str, Any] | None, db_path=None) -> list[dict[str, Any]]:
    require_permission(actor, "user:manage")
    path = initialize_database(db_path)
    with database_connection(path) as conn:
        rows = conn.execute("SELECT user_id,username,role,created_at FROM users ORDER BY user_id").fetchall()
    return [{"user_id": int(r["user_id"]), "username": str(r["username"]), "role": str(r["role"]), "created_at": str(r["created_at"])} for r in rows]

def create_staff_account(actor: dict[str, Any] | None, username: str, password: str, db_path=None) -> int:
    require_permission(actor, "user:manage")
    try:
        return register_user(username, password, db_path)
    except (ValueError, sqlite3.Error) as error:
        raise UserManagementError(str(error)) from error

def change_user_role(actor: dict[str, Any] | None, target_user_id: object, role: str, db_path=None) -> bool:
    require_permission(actor, "user:manage")
    try:
        identifier = validate_id(target_user_id, "User ID")
    except ValidationError as error:
        raise UserManagementError(str(error)) from error
    new_role = role.strip().lower() if isinstance(role, str) else ""
    if new_role not in {"admin", "staff"}:
        raise UserManagementError("Role must be either 'admin' or 'staff'.")
    if identifier == int(actor["user_id"]):
        raise UserManagementError("You cannot change your own role while logged in.")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            target = conn.execute("SELECT role FROM users WHERE user_id=?", (identifier,)).fetchone()
            if target is None:
                return False
            if target["role"] == "admin" and new_role != "admin":
                admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
                if admin_count <= 1:
                    raise UserManagementError("The last administrator cannot be demoted.")
            conn.execute("UPDATE users SET role=? WHERE user_id=?", (new_role, identifier))
            return True
    except sqlite3.Error as error:
        raise UserManagementError(f"Could not change user role: {error}") from error

def delete_user(actor: dict[str, Any] | None, target_user_id: object, db_path=None) -> bool:
    require_permission(actor, "user:manage")
    try:
        identifier = validate_id(target_user_id, "User ID")
    except ValidationError as error:
        raise UserManagementError(str(error)) from error
    if identifier == int(actor["user_id"]):
        raise UserManagementError("You cannot delete your own account while logged in.")
    path = initialize_database(db_path)
    try:
        with database_connection(path) as conn:
            target = conn.execute("SELECT role FROM users WHERE user_id=?", (identifier,)).fetchone()
            if target is None:
                return False
            if target["role"] == "admin":
                admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
                if admin_count <= 1:
                    raise UserManagementError("The last administrator cannot be deleted.")
            cursor = conn.execute("DELETE FROM users WHERE user_id=?", (identifier,))
            return cursor.rowcount > 0
    except sqlite3.Error as error:
        raise UserManagementError(f"Could not delete user: {error}") from error
