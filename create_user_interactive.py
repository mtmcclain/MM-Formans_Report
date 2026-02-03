"""
Interactive user creation script
This will help you create a new user account for the application
"""
from auth import create_user_in_db
import sys

def main():
    print("=" * 60)
    print("Create New User Account")
    print("=" * 60)
    print("\nThis will create a new user account for logging into the app.")
    print("You'll need this username and password to access the application.\n")
    
    try:
        # Get username
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
        
        # Get password (visible for easier use)
        print("\n⚠️  Password will be visible as you type (for easier entry)")
        password = input("Enter password: ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            return
        
        password_confirm = input("Confirm password: ").strip()
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return
        
        # Optional fields
        print("\nOptional information (press Enter to skip):")
        full_name = input("Full name: ").strip() or None
        role = input("Role (foreman/admin, default: foreman): ").strip() or "foreman"
        email = input("Email: ").strip() or None
        
        # Create user
        print("\nCreating user account...")
        if create_user_in_db(username, password, full_name, role, email):
            print(f"\n✅ SUCCESS! User '{username}' created successfully!")
            print(f"\nYou can now login with:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print(f"\nRole: {role}")
            if full_name:
                print(f"Name: {full_name}")
            print("\n" + "=" * 60)
        else:
            print(f"\n❌ ERROR: Username '{username}' already exists!")
            print("Please try a different username.")
            
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
