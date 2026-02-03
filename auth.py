"""
Authentication module for MM-Formans_Report application
Uses streamlit-authenticator for user management
"""
import streamlit as st
import yaml
from pathlib import Path
import hashlib
import config
from database import get_db_connection, _exec, list_users, list_users

def hash_password(password: str) -> str:
    """Hash a password using SHA256 (simple hashing for now)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return hash_password(password) == password_hash

def load_users_from_yaml() -> dict:
    """Load users from YAML file (for initial setup)"""
    if not config.USERS_FILE.exists():
        return {}
    
    try:
        with open(config.USERS_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        st.error(f"Error loading users file: {e}")
        return {}

def save_users_to_yaml(users: dict):
    """Save users to YAML file"""
    try:
        with open(config.USERS_FILE, 'w') as f:
            yaml.dump(users, f, default_flow_style=False)
    except Exception as e:
        st.error(f"Error saving users file: {e}")

def get_user_from_db(username: str) -> dict:
    """Get user from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, """
        SELECT id, username, password_hash, full_name, role, email, is_active
        FROM users
        WHERE username = %s AND is_active = %s
    """, (username, True))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_user_in_db(username: str, password: str, full_name: str = None,
                      role: str = 'foreman', email: str = None) -> bool:
    """Create a new user in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        _exec(cursor, """
            INSERT INTO users (username, password_hash, full_name, role, email)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password_hash, full_name, role, email))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower() or "IntegrityError" in type(e).__name__:
            return False  # Username already exists
        raise e

def update_user_login_time(user_id: int):
    """Update last login time for user"""
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, "UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id: int, new_password: str) -> bool:
    """Set a new password for a user (e.g. admin reset). Returns True if updated."""
    if not new_password:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(new_password)
    _exec(cursor, "UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate a user
    
    Returns:
        dict with user info if successful, None otherwise
    """
    # First try database
    user = get_user_from_db(username)
    
    if user:
        if verify_password(password, user['password_hash']):
            update_user_login_time(user['id'])
            return user
    
    # Fallback to YAML file (for migration)
    yaml_users = load_users_from_yaml()
    if username in yaml_users:
        stored_password = yaml_users[username].get('password', '')
        if verify_password(password, stored_password):
            # Migrate to database
            full_name = yaml_users[username].get('name', username)
            role = yaml_users[username].get('role', 'foreman')
            email = yaml_users[username].get('email')
            
            if create_user_in_db(username, password, full_name, role, email):
                user = get_user_from_db(username)
                if user:
                    return user
    
    return None

def check_authentication():
    """Check if user is authenticated, redirect to login if not"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None
    
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()

def show_login_page():
    """Display login page"""
    st.title("🔐 Login to Foreman's Report")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.user_id = user['id']
                    st.success(f"Welcome, {user.get('full_name', username)}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    # Option to create account (for initial setup)
    with st.expander("Need an account? Contact administrator"):
        st.info("User accounts are managed by the administrator. Please contact your system administrator to create an account.")

def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.rerun()

def get_current_user() -> dict:
    """Get current authenticated user"""
    if st.session_state.get('authenticated') and st.session_state.get('user'):
        return st.session_state.user
    return None
