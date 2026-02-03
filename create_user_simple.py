"""
Simple version of user creation script
Shows asterisks for password (less secure but easier to use)
"""
from auth import create_user_in_db

def get_password_visible(prompt="Enter password: "):
    """Get password with visible asterisks"""
    import sys
    import msvcrt  # Windows only
    
    print(prompt, end='', flush=True)
    password = []
    while True:
        char = msvcrt.getch()
        if char == b'\r':  # Enter pressed
            print()
            break
        elif char == b'\x08':  # Backspace
            if password:
                password.pop()
                print('\b \b', end='', flush=True)
        else:
            password.append(char.decode('utf-8'))
            print('*', end='', flush=True)
    return ''.join(password)

def main():
    print("=" * 50)
    print("Create User Account (Simple Version)")
    print("=" * 50)
    print("\n⚠️  This version shows asterisks (*) as you type your password.\n")
    
    try:
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
        
        password = get_password_visible("Enter password: ")
        if not password:
            print("❌ Password cannot be empty!")
            return
        
        password_confirm = get_password_visible("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return
        
        full_name = input("\nEnter full name (optional, press Enter to skip): ").strip() or None
        role = input("Enter role (foreman/admin, default: foreman): ").strip() or "foreman"
        email = input("Enter email (optional, press Enter to skip): ").strip() or None
        
        if create_user_in_db(username, password, full_name, role, email):
            print(f"\n✅ User '{username}' created successfully!")
            print(f"   Role: {role}")
            if full_name:
                print(f"   Name: {full_name}")
        else:
            print(f"\n❌ Error: Username '{username}' already exists!")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")

if __name__ == "__main__":
    main()
