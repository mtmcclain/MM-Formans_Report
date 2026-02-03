"""
Reset a user's password (for when you forget admin or other credentials).
Passwords are stored hashed, so they cannot be "looked up" — this script sets a NEW password.

Run from the project folder:  python reset_password.py
"""
import sys
from pathlib import Path

# Add project root so we can import config, database, auth
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DB_PATH
from database import get_db_connection
from auth import hash_password


def list_users():
    """Print usernames and roles so you know which account to reset."""
    if not DB_PATH.exists():
        print("Database not found. Run the app once to create it.")
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, role, is_active FROM users ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reset_password(username: str, new_password: str) -> bool:
    """Set a new password for the given username. Returns True if updated."""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def main():
    print("=" * 60)
    print("Reset user password")
    print("=" * 60)
    print("\nPasswords are stored hashed and cannot be recovered.")
    print("This script sets a NEW password for a user.\n")

    users = list_users()
    if not users:
        print("No users in database. Create one with:  python create_user_interactive.py")
        return

    print("Users in database:")
    for u in users:
        active = "active" if u.get("is_active", 1) else "DEACTIVATED"
        name = u.get("full_name") or "(no name)"
        print(f"  - {u['username']}  ({name})  role={u.get('role', 'foreman')}  [{active}]")
    print()

    username = input("Enter username to reset password: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    if not any(u["username"] == username for u in users):
        print(f"No user found with username: {username}")
        return

    new_password = input("Enter new password: ").strip()
    if not new_password:
        print("Password cannot be empty.")
        return

    confirm = input("Confirm new password: ").strip()
    if new_password != confirm:
        print("Passwords do not match.")
        return

    if reset_password(username, new_password):
        print(f"\nPassword updated for user: {username}")
        print("You can now log in with this new password.")
    else:
        print("\nUpdate failed (username may not exist).")


if __name__ == "__main__":
    main()
