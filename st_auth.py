"""Authentication, password hashing, and authorization helpers."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from collections.abc import Collection, Mapping
from typing import Any

from database import database_connection, initialize_database

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
MIN_PASSWORD_LENGTH = 8


class AuthError(ValueError):
    """Raised when registration or initial administrator setup is invalid."""


class AuthorizationError(PermissionError):
    """Raised when a user attempts an operation they are not allowed to perform."""


# Role-to-permission mapping used by the application service modules.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "student:create",
        "student:read",
        "student:update",
        "student:delete",
        "course:create",
        "course:read",
        "course:update",
        "course:delete",
        "user:manage",
        "report:view",
    },
    "staff": {
        "student:create",
        "student:read",
        "student:update",
        "course:read",
    },
}


def validate_username(username: str) -> str:
    """Return a trimmed valid username or raise ``AuthError``."""
    if not isinstance(username, str):
        raise AuthError("Username must be text.")

    normalized = username.strip()
    if not normalized:
        raise AuthError("Username cannot be empty.")
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise AuthError(
            "Username must be 3–30 characters and contain only letters, numbers, dots, hyphens, or underscores."
        )
    return normalized


def validate_password(password: str) -> None:
    """Require a non-empty password of at least eight characters."""
    if not isinstance(password, str) or not password:
        raise AuthError("Password cannot be empty.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )


def hash_password(password: str) -> str:
    """Hash a password with a random salt and PBKDF2-HMAC-SHA256."""
    validate_password(password)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return "$".join(
        [
            PASSWORD_HASH_ALGORITHM,
            str(PASSWORD_HASH_ITERATIONS),
            salt.hex(),
            digest.hex(),
        ]
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Return whether ``password`` matches a previously stored password hash."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    try:
        algorithm, iterations_text, salt_hex, expected_hex = stored_hash.split("$")
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(expected_hex)
    except (ValueError, TypeError):
        return False

    # The algorithm and reasonable iteration bounds prevent malformed database
    # contents from selecting a different algorithm or excessive CPU cost.
    if algorithm != PASSWORD_HASH_ALGORITHM or not 100_000 <= iterations <= 1_000_000:
        return False
    if len(salt) != 16 or len(expected_digest) != 32:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def get_user_count(db_path: str | None = None) -> int:
    """Return the number of registered accounts."""
    path = initialize_database(db_path)
    with database_connection(path) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
    return int(row["total"])


def _insert_user(username: str, password: str, role: str, db_path: str | None) -> int:
    """Insert a validated account, translating duplicate-name errors."""
    clean_username = validate_username(username)
    validate_password(password)
    password_hash = hash_password(password)
    path = initialize_database(db_path)

    try:
        with database_connection(path) as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (clean_username, password_hash, role),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        if "users.username" in str(error).lower() or "unique constraint failed" in str(error).lower():
            raise AuthError("That username is already registered.") from error
        raise AuthError(f"Could not create the account: {error}") from error


def register_user(username: str, password: str, db_path: str | None = None) -> int:
    """Register a regular Staff account. Public registration cannot create Admins."""
    return _insert_user(username, password, "staff", db_path)


def create_initial_admin(
    username: str, password: str, db_path: str | None = None
) -> int:
    """Create the first Admin account, only while the users table is empty."""
    clean_username = validate_username(username)
    validate_password(password)
    password_hash = hash_password(password)
    path = initialize_database(db_path)

    try:
        with database_connection(path) as connection:
            # Lock early so two concurrent first-run processes cannot both
            # create an initial administrator.
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if count:
                raise AuthError(
                    "The initial administrator has already been created."
                )
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                (clean_username, password_hash),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        if "unique constraint failed" in str(error).lower():
            raise AuthError("That username is already registered.") from error
        raise AuthError(f"Could not create the administrator: {error}") from error


def authenticate_user(
    username: str, password: str, db_path: str | None = None
) -> dict[str, Any] | None:
    """Authenticate credentials and return safe user details, or ``None``."""
    if not isinstance(username, str) or not username.strip():
        return None
    if not isinstance(password, str):
        return None

    path = initialize_database(db_path)
    with database_connection(path) as connection:
        row = connection.execute(
            "SELECT user_id, username, password_hash, role FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return None

    # Never pass password hashes back to the rest of the application.
    return {
        "user_id": int(row["user_id"]),
        "username": str(row["username"]),
        "role": str(row["role"]),
    }


def has_permission(user: Mapping[str, Any] | None, permission: str) -> bool:
    """Return whether the authenticated user has a named permission."""
    if not user:
        return False
    role = user.get("role")
    return permission in ROLE_PERMISSIONS.get(str(role), set())


def require_permission(user: Mapping[str, Any] | None, permission: str) -> None:
    """Raise ``AuthorizationError`` when a user lacks a permission."""
    if not user:
        raise AuthorizationError("Please log in before performing this action.")
    if not has_permission(user, permission):
        raise AuthorizationError(
            f"The {user.get('role', 'unknown')} role cannot perform: {permission}."
        )


def require_role(
    user: Mapping[str, Any] | None, required_roles: str | Collection[str]
) -> None:
    """Raise ``AuthorizationError`` unless the user has an allowed role."""
    if not user:
        raise AuthorizationError("Please log in before continuing.")
    allowed = {required_roles} if isinstance(required_roles, str) else set(required_roles)
    if user.get("role") not in allowed:
        raise AuthorizationError("You do not have permission to access this menu.")
