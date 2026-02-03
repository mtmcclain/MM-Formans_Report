"""
Utility script to create user accounts
Run this script to create initial user accounts
"""
from auth import create_user_in_db
import getpass

def main():
    print("=" * 50)
    print("Create User Account")
    print("=" * 50)
    print("\n⚠️  NOTE: Password input is hidden for security.")
    print("   Type your password and press Enter (nothing will show on screen).\n")
    
    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty!")
        return
    
    print("\n(Password will be hidden as you type - this is normal!)")
    password = getpass.getpass("Enter password: ")
    if not password:
        print("❌ Password cannot be empty!")
        return
    print("✓ Password entered")
    
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match!")
        return
    print("✓ Password confirmed")
    
    full_name = input("Enter full name (optional): ").strip() or None
    role = input("Enter role (foreman/admin, default: foreman): ").strip() or "foreman"
    email = input("Enter email (optional): ").strip() or None
    
    try:
        if create_user_in_db(username, password, full_name, role, email):
            print(f"\n✅ User '{username}' created successfully!")
            print(f"   Role: {role}")
            if full_name:
                print(f"   Name: {full_name}")
        else:
            print(f"\n❌ Error: Username '{username}' already exists!")
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")

if __name__ == "__main__":
    main()
