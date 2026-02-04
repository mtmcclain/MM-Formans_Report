"""
Database operations for MM-Formans_Report application.
Supports SQLite (local) and PostgreSQL (e.g. Streamlit Cloud via DATABASE_URL).
"""
import sqlite3
import json
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import config


def get_db_connection():
    """Get database connection (SQLite or PostgreSQL from DATABASE_URL)."""
    if config.USE_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(config.DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _exec(cursor, sql: str, params: tuple = ()) -> None:
    """Execute SQL with correct placeholder style (%s for Postgres, ? for SQLite)."""
    if config.USE_POSTGRES:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql.replace("%s", "?"), params)


def init_db():
    """Initialize database with all required tables (SQLite or PostgreSQL)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if config.USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role VARCHAR(50) DEFAULT 'foreman',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                report_date DATE NOT NULL,
                state VARCHAR(255) NOT NULL,
                job_name TEXT,
                job_number VARCHAR(255) NOT NULL,
                job_description TEXT,
                work_performed_notes TEXT,
                equipment_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pdf_filename TEXT,
                is_draft BOOLEAN DEFAULT FALSE,
                is_submitted BOOLEAN DEFAULT FALSE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_employees (
                id SERIAL PRIMARY KEY,
                report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                employee_name TEXT NOT NULL,
                craft VARCHAR(50) NOT NULL,
                straight_time REAL DEFAULT 0.0,
                overtime_15 REAL DEFAULT 0.0,
                double_time REAL DEFAULT 0.0,
                display_order INTEGER DEFAULT 0
            )
        """)
    else:
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

    # Indexes (same syntax for both)
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_job_number ON reports(job_number)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_date_job ON reports(report_date, job_number)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_draft ON reports(is_draft)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_reports_submitted ON reports(is_submitted)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_report_employees_report_id ON report_employees(report_id)")
    _exec(cursor, "CREATE INDEX IF NOT EXISTS idx_report_employees_name ON report_employees(employee_name)")

    conn.commit()
    conn.close()
    where = "PostgreSQL" if config.USE_POSTGRES else str(config.DB_PATH)
    print(f"Database initialized: {where}")

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
        equipment_json = json.dumps(equipment_used)
        # Use booleans so PostgreSQL gets TRUE/FALSE (SQLite accepts bool as 1/0)
        params = (
            user_id, report_date, state, job_name, job_number,
            job_description, work_performed_notes, equipment_json,
            is_draft, not is_draft, pdf_filename,
            datetime.now()
        )
        if config.USE_POSTGRES:
            cursor.execute("""
                INSERT INTO reports (
                    user_id, report_date, state, job_name, job_number,
                    job_description, work_performed_notes, equipment_used,
                    is_draft, is_submitted, pdf_filename, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, params)
            report_id = cursor.fetchone()["id"]
        else:
            _exec(cursor, """
                INSERT INTO reports (
                    user_id, report_date, state, job_name, job_number,
                    job_description, work_performed_notes, equipment_used,
                    is_draft, is_submitted, pdf_filename, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, params)
            report_id = cursor.lastrowid

        for idx, emp in enumerate(employees):
            _exec(cursor, """
                INSERT INTO report_employees (
                    report_id, employee_name, craft,
                    straight_time, overtime_15, double_time, display_order
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
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
        _exec(cursor, "SELECT * FROM reports WHERE id = %s AND user_id = %s", (report_id, user_id))
    else:
        _exec(cursor, "SELECT * FROM reports WHERE id = %s", (report_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    report = dict(row)

    if report.get("equipment_used"):
        report["equipment_used"] = json.loads(report["equipment_used"])
    else:
        report["equipment_used"] = {}

    _exec(cursor, """
        SELECT employee_name, craft, straight_time, overtime_15, double_time
        FROM report_employees
        WHERE report_id = %s
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
        _exec(cursor, """
            SELECT id, report_date, state, job_name, job_number,
                   is_draft, is_submitted, created_at, updated_at
            FROM reports
            WHERE user_id = %s
            ORDER BY report_date DESC, created_at DESC
        """, (user_id,))
    else:
        _exec(cursor, """
            SELECT id, report_date, state, job_name, job_number,
                   is_draft, is_submitted, created_at, updated_at
            FROM reports
            WHERE user_id = %s AND is_draft = %s
            ORDER BY report_date DESC, created_at DESC
        """, (user_id, False))
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports

def get_reports_by_week(job_number: str, week_start: date, week_end: date) -> List[Dict]:
    """Get all submitted reports for a job number within a date range"""
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, """
        SELECT r.*, u.full_name as foreman_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.job_number = %s
          AND r.report_date >= %s
          AND r.report_date <= %s
          AND r.is_submitted = %s
        ORDER BY r.report_date ASC
    """, (job_number, week_start, week_end, True))

    reports = []
    for row in cursor.fetchall():
        report = dict(row)
        if report.get("equipment_used"):
            report["equipment_used"] = json.loads(report["equipment_used"])
        else:
            report["equipment_used"] = {}
        _exec(cursor, """
            SELECT employee_name, craft, straight_time, overtime_15, double_time
            FROM report_employees
            WHERE report_id = %s
            ORDER BY display_order
        """, (report["id"],))
        
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
    _exec(cursor, """
        SELECT *
        FROM reports
        WHERE user_id = %s
          AND report_date >= %s
          AND report_date <= %s
          AND is_submitted = %s
        ORDER BY report_date ASC
    """, (user_id, week_start, week_end, True))

    reports = []
    for row in cursor.fetchall():
        report = dict(row)
        if report.get("equipment_used"):
            report["equipment_used"] = json.loads(report["equipment_used"])
        else:
            report["equipment_used"] = {}
        _exec(cursor, """
            SELECT employee_name, craft, straight_time, overtime_15, double_time
            FROM report_employees
            WHERE report_id = %s
            ORDER BY display_order
        """, (report["id"],))
        
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
    _exec(cursor, """
        SELECT DISTINCT re.employee_name
        FROM report_employees re
        JOIN reports r ON re.report_id = r.id
        WHERE r.user_id = %s
          AND r.report_date >= %s
          AND r.report_date <= %s
          AND r.is_submitted = %s
          AND re.employee_name != ''
          AND re.employee_name IS NOT NULL
        ORDER BY re.employee_name
    """, (user_id, week_start, week_end, True))
    employees = [row["employee_name"] for row in cursor.fetchall()]
    conn.close()
    return employees

def get_employee_timesheet_data(employee_name: str, week_start: date, week_end: date) -> List[Dict]:
    """Get all time entries for an employee within a date range, grouped by job"""
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, """
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
        WHERE re.employee_name = %s
          AND r.report_date >= %s
          AND r.report_date <= %s
          AND r.is_submitted = %s
        ORDER BY r.report_date ASC, r.job_number ASC
    """, (employee_name, week_start, week_end, True))
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return entries

def delete_report(report_id: int, user_id: int) -> bool:
    """Delete a report (only if owned by user)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, "DELETE FROM reports WHERE id = %s AND user_id = %s", (report_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def update_report_draft_status(report_id: int, user_id: int, is_draft: bool) -> bool:
    """Update whether a report is a draft"""
    conn = get_db_connection()
    cursor = conn.cursor()
    _exec(cursor, """
        UPDATE reports
        SET is_draft = %s, is_submitted = %s, updated_at = %s
        WHERE id = %s AND user_id = %s
    """, (is_draft, not is_draft, datetime.now(), report_id, user_id))
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
    _exec(cursor, """
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
    _exec(cursor, "UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
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
        updates.append("full_name = %s")
        params.append(full_name)
    if email is not None:
        updates.append("email = %s")
        params.append(email)
    if role is not None:
        updates.append("role = %s")
        params.append(role)
    if not updates:
        conn.close()
        return False
    params.append(user_id)
    _exec(cursor, f"UPDATE users SET {', '.join(updates)} WHERE id = %s", tuple(params))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_user(user_id: int) -> bool:
    """Delete a user and all their reports (and report_employees). Returns True if deleted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        _exec(cursor, "SELECT id FROM reports WHERE user_id = %s", (user_id,))
        report_ids = [row["id"] for row in cursor.fetchall()]
        for rid in report_ids:
            _exec(cursor, "DELETE FROM report_employees WHERE report_id = %s", (rid,))
        _exec(cursor, "DELETE FROM reports WHERE user_id = %s", (user_id,))
        _exec(cursor, "DELETE FROM users WHERE id = %s", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception:
        conn.rollback()
        conn.close()
        raise


# Initialize database on import (PostgreSQL always; SQLite only if file missing)
if config.USE_POSTGRES:
    init_db()
elif not config.DB_PATH.exists():
    init_db()
