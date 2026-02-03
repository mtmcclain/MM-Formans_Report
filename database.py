"""
Database operations for MM-Formans_Report application
Uses SQLite for data persistence
"""
import sqlite3
import json
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import config

def get_db_connection():
    """Get database connection, creating database if it doesn't exist"""
    conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_db():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'foreman',
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_date DATE NOT NULL,
            state TEXT NOT NULL,
            job_name TEXT,
            job_number TEXT NOT NULL,
            job_description TEXT,
            work_performed_notes TEXT,
            equipment_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pdf_filename TEXT,
            is_draft BOOLEAN DEFAULT 0,
            is_submitted BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create report_employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            employee_name TEXT NOT NULL,
            craft TEXT NOT NULL,
            straight_time REAL DEFAULT 0.0,
            overtime_15 REAL DEFAULT 0.0,
            double_time REAL DEFAULT 0.0,
            display_order INTEGER DEFAULT 0,
            FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_job_number ON reports(job_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_date_job ON reports(report_date, job_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_draft ON reports(is_draft)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_submitted ON reports(is_submitted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_employees_report_id ON report_employees(report_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_employees_name ON report_employees(employee_name)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {config.DB_PATH}")

def save_report(
    user_id: int,
    report_date: date,
    state: str,
    job_name: str,
    job_number: str,
    job_description: str,
    work_performed_notes: str,
    equipment_used: dict,
    employees: List[Dict],
    is_draft: bool = False,
    pdf_filename: Optional[str] = None
) -> int:
    """
    Save a report to the database
    
    Returns:
        report_id: The ID of the saved report
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert equipment dict to JSON string
        equipment_json = json.dumps(equipment_used)
        
        # Insert report
        cursor.execute("""
            INSERT INTO reports (
                user_id, report_date, state, job_name, job_number,
                job_description, work_performed_notes, equipment_used,
                is_draft, is_submitted, pdf_filename, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, report_date, state, job_name, job_number,
            job_description, work_performed_notes, equipment_json,
            1 if is_draft else 0, 0 if is_draft else 1, pdf_filename,
            datetime.now()
        ))
        
        report_id = cursor.lastrowid
        
        # Insert employees
        for idx, emp in enumerate(employees):
            cursor.execute("""
                INSERT INTO report_employees (
                    report_id, employee_name, craft,
                    straight_time, overtime_15, double_time, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, emp.get("name", ""), emp.get("craft", "PF"),
                float(emp.get("st", 0.0)), float(emp.get("ot15", 0.0)),
                float(emp.get("otdt", 0.0)), idx
            ))
        
        conn.commit()
        return report_id
    
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_report(report_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
    """Get a report by ID, optionally filtered by user_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT * FROM reports WHERE id = ? AND user_id = ?
        """, (report_id, user_id))
    else:
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    # Convert row to dict
    report = dict(row)
    
    # Parse equipment JSON
    if report['equipment_used']:
        report['equipment_used'] = json.loads(report['equipment_used'])
    else:
        report['equipment_used'] = {}
    
    # Get employees
    cursor.execute("""
        SELECT employee_name, craft, straight_time, overtime_15, double_time
        FROM report_employees
        WHERE report_id = ?
        ORDER BY display_order
    """, (report_id,))
    
    employees = []
    for emp_row in cursor.fetchall():
        employees.append({
            "name": emp_row['employee_name'],
            "craft": emp_row['craft'],
            "st": emp_row['straight_time'],
            "ot15": emp_row['overtime_15'],
            "otdt": emp_row['double_time']
        })
    
    report['employees'] = employees
    conn.close()
    return report

def get_user_reports(user_id: int, include_drafts: bool = True) -> List[Dict]:
    """Get all reports for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if include_drafts:
        cursor.execute("""
            SELECT id, report_date, state, job_name, job_number,
                   is_draft, is_submitted, created_at, updated_at
            FROM reports
            WHERE user_id = ?
            ORDER BY report_date DESC, created_at DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT id, report_date, state, job_name, job_number,
                   is_draft, is_submitted, created_at, updated_at
            FROM reports
            WHERE user_id = ? AND is_draft = 0
            ORDER BY report_date DESC, created_at DESC
        """, (user_id,))
    
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports

def get_reports_by_week(job_number: str, week_start: date, week_end: date) -> List[Dict]:
    """Get all submitted reports for a job number within a date range"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, u.full_name as foreman_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.job_number = ?
          AND r.report_date >= ?
          AND r.report_date <= ?
          AND r.is_submitted = 1
        ORDER BY r.report_date ASC
    """, (job_number, week_start, week_end))
    
    reports = []
    for row in cursor.fetchall():
        report = dict(row)
        # Parse equipment JSON
        if report['equipment_used']:
            report['equipment_used'] = json.loads(report['equipment_used'])
        else:
            report['equipment_used'] = {}
        
        # Get employees
        cursor.execute("""
            SELECT employee_name, craft, straight_time, overtime_15, double_time
            FROM report_employees
            WHERE report_id = ?
            ORDER BY display_order
        """, (report['id'],))
        
        employees = []
        for emp_row in cursor.fetchall():
            employees.append({
                "name": emp_row['employee_name'],
                "craft": emp_row['craft'],
                "st": emp_row['straight_time'],
                "ot15": emp_row['overtime_15'],
                "otdt": emp_row['double_time']
            })
        
        report['employees'] = employees
        reports.append(report)
    
    conn.close()
    return reports

def get_user_reports_by_date_range(user_id: int, week_start: date, week_end: date) -> List[Dict]:
    """Get all submitted reports for a user within a date range (Mon-Sun week)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT *
        FROM reports
        WHERE user_id = ?
          AND report_date >= ?
          AND report_date <= ?
          AND is_submitted = 1
        ORDER BY report_date ASC
    """, (user_id, week_start, week_end))
    
    reports = []
    for row in cursor.fetchall():
        report = dict(row)
        # Parse equipment JSON
        if report['equipment_used']:
            report['equipment_used'] = json.loads(report['equipment_used'])
        else:
            report['equipment_used'] = {}
        
        # Get employees
        cursor.execute("""
            SELECT employee_name, craft, straight_time, overtime_15, double_time
            FROM report_employees
            WHERE report_id = ?
            ORDER BY display_order
        """, (report['id'],))
        
        employees = []
        for emp_row in cursor.fetchall():
            employees.append({
                "name": emp_row['employee_name'],
                "craft": emp_row['craft'],
                "st": emp_row['straight_time'],
                "ot15": emp_row['overtime_15'],
                "otdt": emp_row['double_time']
            })
        
        report['employees'] = employees
        reports.append(report)
    
    conn.close()
    return reports

def get_unique_employees_in_week(user_id: int, week_start: date, week_end: date) -> List[str]:
    """Get list of unique employee names across all reports in a week"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT re.employee_name
        FROM report_employees re
        JOIN reports r ON re.report_id = r.id
        WHERE r.user_id = ?
          AND r.report_date >= ?
          AND r.report_date <= ?
          AND r.is_submitted = 1
          AND re.employee_name != ''
          AND re.employee_name IS NOT NULL
        ORDER BY re.employee_name
    """, (user_id, week_start, week_end))
    
    employees = [row['employee_name'] for row in cursor.fetchall()]
    conn.close()
    return employees

def get_employee_timesheet_data(employee_name: str, week_start: date, week_end: date) -> List[Dict]:
    """Get all time entries for an employee within a date range, grouped by job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            re.employee_name,
            re.craft,
            r.job_number,
            r.job_name,
            r.job_description,
            r.report_date,
            re.straight_time,
            re.overtime_15,
            re.double_time
        FROM report_employees re
        JOIN reports r ON re.report_id = r.id
        WHERE re.employee_name = ?
          AND r.report_date >= ?
          AND r.report_date <= ?
          AND r.is_submitted = 1
        ORDER BY r.report_date ASC, r.job_number ASC
    """, (employee_name, week_start, week_end))
    
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entries

def delete_report(report_id: int, user_id: int) -> bool:
    """Delete a report (only if owned by user)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM reports WHERE id = ? AND user_id = ?
    """, (report_id, user_id))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_report_draft_status(report_id: int, user_id: int, is_draft: bool) -> bool:
    """Update whether a report is a draft"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE reports
        SET is_draft = ?, is_submitted = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (1 if is_draft else 0, 0 if is_draft else 1, datetime.now(), report_id, user_id))
    
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


# ────────────────────────────────────────────────
# User management (for Admin page)
# ────────────────────────────────────────────────
def list_users() -> List[Dict]:
    """List all users (id, username, full_name, role, email, is_active, last_login, created_at)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, email, is_active, last_login, created_at
        FROM users
        ORDER BY username
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_user_active(user_id: int, is_active: bool) -> bool:
    """Set user active status (True = can log in, False = deactivated)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET is_active = ? WHERE id = ?
    """, (1 if is_active else 0, user_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
) -> bool:
    """Update user profile (only non-None fields are updated)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    if full_name is not None:
        updates.append("full_name = ?")
        params.append(full_name)
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    if role is not None:
        updates.append("role = ?")
        params.append(role)
    if not updates:
        conn.close()
        return False
    params.append(user_id)
    cursor.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
        params
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_user(user_id: int) -> bool:
    """Delete a user and all their reports (and report_employees). Returns True if deleted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get report IDs for this user
        cursor.execute("SELECT id FROM reports WHERE user_id = ?", (user_id,))
        report_ids = [row[0] for row in cursor.fetchall()]
        # Delete report_employees for those reports
        for rid in report_ids:
            cursor.execute("DELETE FROM report_employees WHERE report_id = ?", (rid,))
        # Delete reports
        cursor.execute("DELETE FROM reports WHERE user_id = ?", (user_id,))
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception:
        conn.rollback()
        conn.close()
        raise


# Initialize database on import
if not config.DB_PATH.exists():
    init_db()
