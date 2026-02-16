# MM-Formans_Report — Replication Spec for Capacitor iPad App

This document is the **single specification** for an agent (or developer) using this Git repository to **recreate the application as a Capacitor-wrapped web app for iPad**, to be built and run in **Xcode**. It describes behavior, data model, and PDF logic without assuming the current stack.

**Audience:** An agent implementing a replica (e.g. React/Vue/Svelte + Capacitor, SQLite or backend API) that preserves the same product behavior and data semantics.

**Current stack (reference only):** Streamlit (Python), SQLite or PostgreSQL, PyMuPDF (fitz). The replica may use any stack; this spec is the source of truth for what to implement.

---

## 1. Product summary

- **App name:** Foreman's Daily Report
- **Purpose:** Foremen create daily reports (date, state, job, employees, equipment), save them as drafts, and generate PDFs: (1) a single filled Foreman Report PDF, (2) a weekly combined PDF (all Foreman Reports for the week + one timesheet per employee).
- **Users:** Login required. Roles:
  - **foreman:** Report list, report form, weekly PDF generation only.
  - **admin:** Same as foreman plus User management (list users, create, edit name/email/role, activate/deactivate, reset password, delete).
- **First user:** When the database has zero users, the app shows a "Create first admin" form (username, password, full name); that user is created with role `admin`. Alternatively, users can be created via a CLI script against the same database.

---

## 2. Data model (source of truth)

Only **three tables** exist in the codebase. There are no `weekly_aggregations` or `employee_timesheets` tables; weekly PDFs are built in memory from draft reports.

### Table: `users`

| Column         | Type      | Notes                          |
|----------------|-----------|--------------------------------|
| id             | PK        | Auto-increment                 |
| username       | TEXT/VARCHAR(255) | UNIQUE NOT NULL        |
| password_hash  | TEXT      | NOT NULL (hashed only)         |
| full_name      | TEXT      | Optional                       |
| role           | TEXT/VARCHAR(50) | DEFAULT 'foreman'; values: `foreman`, `admin` |
| email          | TEXT      | Optional                       |
| created_at     | TIMESTAMP | Default CURRENT_TIMESTAMP      |
| last_login     | TIMESTAMP | Optional                       |
| is_active      | BOOLEAN   | DEFAULT TRUE                   |

Index/unique on `username`.

### Table: `reports`

| Column               | Type    | Notes                                    |
|----------------------|---------|------------------------------------------|
| id                   | PK      | Auto-increment                           |
| user_id              | INTEGER | NOT NULL, FK → users(id)                 |
| report_date          | DATE    | NOT NULL                                 |
| state                | TEXT    | NOT NULL; values: `ILLINOIS`, `INDIANA`   |
| job_name             | TEXT    | Optional                                 |
| job_number           | TEXT/VARCHAR(255) | NOT NULL                        |
| job_description      | TEXT    | Optional                                 |
| work_performed_notes | TEXT    | Optional                                 |
| equipment_used       | TEXT    | JSON string (see below)                  |
| created_at           | TIMESTAMP | Default CURRENT_TIMESTAMP              |
| updated_at           | TIMESTAMP | Default CURRENT_TIMESTAMP              |
| pdf_filename         | TEXT    | Optional (when saved as submitted PDF)  |
| is_draft             | BOOLEAN | DEFAULT TRUE for saved drafts            |
| is_submitted         | BOOLEAN | DEFAULT FALSE                            |

Index on `user_id`.

### Table: `report_employees`

| Column       | Type    | Notes                          |
|--------------|---------|--------------------------------|
| id           | PK      | Auto-increment                 |
| report_id    | INTEGER | NOT NULL, FK → reports(id) ON DELETE CASCADE |
| employee_name| TEXT    | NOT NULL                      |
| craft        | TEXT/VARCHAR(50) | NOT NULL; values: `PF`, `PFF`, `PFGF`, `PFA` |
| straight_time| REAL    | DEFAULT 0.0                   |
| overtime_15  | REAL    | DEFAULT 0.0 (Time 1.5)        |
| double_time  | REAL    | DEFAULT 0.0                   |
| display_order| INTEGER | DEFAULT 0 (order in report)   |

Index on `report_id`.

### equipment_used JSON structure

Stored as a single JSON string in `reports.equipment_used`. Structure is an object with six list keys; each list contains items with the shapes below.

- **welding_machines:** `[{ "type": string, "other_text": string (optional), "qty": int }]`  
  Types: `110`, `shop mig`, `orbital`, `other` (when `other`, use `other_text` for display).

- **trucks:** `[{ "type": string, "qty": int }]`  
  Types: `Service Truck`, `Service Van`, `Foreman Truck`.

- **martin_equipment:** `[{ "type": string, "other_text": string (optional), "qty": int }]`  
  Types: `Pipe Machine`, `Pro press gun`, `Hot tap machine`, `Plasma cutter`, `Scissor lift`, `Big Positioner`, `Small Positioner`, `Pipe Beveler`, `other`.

- **test_equipment:** `[{ "type": string, "other_text": string (optional), "qty": int }]`  
  Types: `4 gas meter`, `Vacuum pump`, `Hydro pump`, `other`.

- **gases:** `[{ "type": string, "other_text": string (optional), "qty": int }]`  
  Types: `Torch set up`, `B-Tank`, `Nitrogen`, `Argon`, `other`.

- **rentals:** `[{ "specify": string, "qty": int }]`  
  Free text per row (no type dropdown).

Default for a new report: each of these keys is an empty array `[]`.

### Equipment string for PDF (single "equipmentused" field)

Build one comma-separated string from the equipment JSON. **Format per item:** `(amount) Type Group name`. **Order:** Welding machines, Trucks, Martin equipment, Test equipment, Gases, Rentals.

- Welding: `(qty) {type or other_text} Welding machine`
- Trucks: `(qty) {type} Trucks`
- Martin: `(qty) {type or other_text} Martin Equipment`
- Test: `(qty) {type or other_text} Test equipment`
- Gases: `(qty) {type or other_text} Gases`
- Rentals: `(qty) {specify} Rentals`

Example: `(1) 110 Welding machine, (1) Service Truck Trucks, (2) Pipe Machine Martin Equipment`.

---

## 3. Authentication and authorization

- **Login:** Username + password. Verify against `users.password_hash`. Current app uses SHA256 hex digest; a replica should use a stronger scheme (e.g. bcrypt) and store only the hash. Set session (e.g. `user_id`, `username`, `role`).
- **First user:** If no users exist, show "Create first admin" (username, password, full name); create one user with `role = 'admin'`. No login required until that user exists.
- **Foreman:** Can access Home (report list), Form (report edit/create), and Weekly PDF generation. Cannot access User management.
- **Admin:** Same as foreman plus User management: list users, create user, edit (full name, email, role), set active/inactive, reset password, delete user.
- **Passwords:** Never store plain text. Support reset flow or CLI script; do not expose or "look up" passwords.

---

## 4. User flows (behavior to replicate)

### Home (main screen)

- List **draft** reports for the current user (`reports` where `user_id = current` and `is_draft = TRUE`), grouped by week (week = Monday–Sunday).
- Display: current week first; older weeks in a collapsed expander. Each row: report date, job number, optional job name. Buttons per row:
  - **Open:** Load that report into the form (set "current report id"); switch to Form view. Subsequent Save **updates** that report.
  - **Delete:** Delete that report (and its `report_employees` via CASCADE). If the deleted report was the current one, clear current report id.
- **New report:** Clear form state (date = today, state = INDIANA, empty job/notes/employees/equipment, current report id = none). Switch to Form view. Next Save **creates** a new report.
- **Weekly Report & Timesheet Generation:** Section on the same Home screen. Week selector: user picks a date; normalize to the **Sunday** of that week (week = Mon–Sun). Button "Generate Weekly PDFs": see PDF section below. Uses only drafts whose `report_date` falls in the selected week.

### Form (report edit/create)

- **Fields:** Report date, State (ILLINOIS | INDIANA), Job name, Job number, Job description, Work performed/notes (textarea). Employees: table with columns Name, Craft (PF/PFF/PFGF/PFA), Straight time, Time 1.5, Double time, and a delete button per row; "Add Employee" (max 13). Equipment used: six grouped blocks (Welding machines, Trucks, Martin Equipment, Test equipment, Gases, Rentals); each block allows multiple rows with type/specify, quantity, add/remove.
- **Save current report:** If a report is loaded (current report id set): **update** that report and replace its `report_employees` with the current employee list. If no current report id: **create** a new report (insert) and set current report id to the new id. Reports are saved as drafts (`is_draft = TRUE`).
- **Back to reports:** Return to Home view; clear current report id so the next Save creates a new report.
- **Create PDF of Current Report:** Fill `BlankForemanReport.pdf` with current form data; offer download. Optionally save a copy to DB as non-draft with `pdf_filename` set. Single-report PDF filename pattern: `MM-DD-YYYY_{job_number_safe}.pdf` (job number sanitized to alphanumeric, space, dash, underscore).

### Admin (user management)

- Separate view/section (e.g. sidebar or tab). List all users; create user (username, password, full name, role); edit user (full name, email, role); activate/deactivate; reset password; delete user. Report flows unchanged.

---

## 5. PDF generation (logic to replicate)

### Templates

- **BlankForemanReport.pdf** — Daily foreman report (one page). Fillable AcroForm fields; names must match exactly.
- **Blank Time.pdf** — Per-employee weekly timesheet. One page per employee; fields follow the pattern below.

Current app uses PyMuPDF (fitz) to read widgets by `field_name`, set `field_value`, then `page.wrap_contents()` and save. A replica can use pdf-lib (JS) to fill by field name, or a thin backend that uses PyMuPDF.

### Foreman report — field mapping

| Field name (exact) | Source | Format / notes |
|--------------------|--------|----------------|
| day | report_date | Full weekday name, e.g. "Monday" |
| date | report_date | MM/DD/YYYY |
| ForemanReportNumber | report_date + job_number | MM-DD-YYYY-{sanitized_job_number}; sanitize job_number to alphanumeric, space, dash, underscore only |
| ILLINOIS | state | "X" if state is ILLINOIS, else "" |
| INDIANA | state | "X" if state is INDIANA, else "" |
| jobname | job_name | |
| jobnumber | job_number | |
| jobdescription | job_description | |
| WORK PERFORMED/NOTES | work_performed_notes | |
| equipmentused | build_equipment_used_string(equipment_used) | Single string, format "(qty) Type Group name" as above |
| employee1name … employee13name | employees[i].name | Empty string if no employee at that index |
| employee1craft … employee13craft | employees[i].craft | |
| employee1st … employee13st | employees[i].st | e.g. "8.0" or "" if 0 |
| employee1ot1.5 … employee13ot1.5 | employees[i].ot15 | |
| employee1otdt … employee13otdt | employees[i].otdt | |

### Week semantics

- Week = Monday through Sunday. Given a selected "week end" (Sunday), Monday = Sunday - 6 days. Include only reports where `report_date` is in [Monday, Sunday] (inclusive).

### Weekly PDF run

1. Collect draft reports for the current user whose `report_date` is in the selected week.
2. For each report, fill `BlankForemanReport.pdf` with that report’s data (same mapping as above); write to a temp file.
3. Collect unique employee names (from all reports in the week). For each employee, build timesheet data (see below) and fill `Blank Time.pdf`; append to temp files.
4. Merge all PDFs in order (foreman reports first, then timesheets).
5. Offer single download. Filename: `{username}_{Sunday_MM-DD-YYYY}.pdf` (e.g. `jsmith_01-26-2026.pdf`).

### Timesheet PDF — field pattern (Blank Time.pdf)

- **employee_name** — Employee’s name.
- **Week end date** — Sunday in MM/DD/YYYY.
- **mon_date, tues_date, wed_date, thurs_date, fri_date, sat_date, sun_date** — Each in MM/DD (two-digit month and day).
- For each job (up to 8), for each day: `job{N}_mon_st`, `job{N}_mon_1.5`, `job{N}_mon_dt`, and similarly for tues … sun. Totals: `job{N}_st_total`, `job{N}_1.5_total`, `job{N}_dt_total`. Also: `job{N}_name`, `job{N}_job_number`, `job{N}_description`, `job{N}_craft`.

Job list is derived from the week’s reports: group entries by job_number for that employee; each job has name, job_number, description, craft and a list of daily entries (report_date, straight_time, overtime_15, double_time). Map each report_date to a weekday (mon–sun) and sum hours per day; format as "8.0" or "" if zero. Exact field names can be confirmed by running `extract_pdf_fields.py` on `Blank Time.pdf` in this repo.

---

## 6. File manifest (key files and roles)

| File | Role |
|------|------|
| **app.py** | Streamlit UI: Home vs Form (report_view), session state (current_draft_id, form_*, employees, equip), Save/Load/Open/Delete, "Create PDF of Current Report", Weekly PDF generation (collect drafts, fill foreman + timesheet PDFs, merge, download). Admin nav to User management. Helpers: fill_pdf, get_week_dates, foreman_report_number, build_equipment_used_string, merge_pdfs. |
| **database.py** | init_db (users, reports, report_employees for SQLite and PostgreSQL), get_db_connection, save_report (insert report + employees), update_report (update report row + delete/reinsert report_employees), get_report, get_user_reports, delete_report, update_report_draft_status. User CRUD: list_users, create_user, set_user_active, update_user, delete_user, etc. |
| **auth.py** | Login/logout, session (user_id, username, role), check_authentication (redirect if not logged in), first-user bootstrap (create first admin), password hashing (SHA256 in current code), verify_password, get_user_from_db. |
| **config.py** | BASE_DIR, DATA_DIR, DATABASE_URL, USE_POSTGRES, DB_PATH, USERS_FILE, MAX_EMPLOYEES_PER_REPORT (13), BLANK_FOREMAN_REPORT path. |
| **BlankForemanReport.pdf** | Must be present; fillable field names must match the Foreman report mapping above. |
| **Blank Time.pdf** | Must be present; fillable field names must match the timesheet pattern above. |
| **extract_pdf_fields.py** | Utility to list all PDF form field names; run with path to a PDF to verify template field names in a new stack. |

---

## 7. Capacitor / iPad notes for the agent

- **UI:** Reimplement Home, Form, and Admin screens in a web stack (e.g. React, Vue, Svelte) suitable for Capacitor. Preserve the flows and data model described above.
- **Data:** Use SQLite (e.g. Capacitor SQLite plugin) with the same schema, or a small backend API that uses the same DB and report/employee semantics. Ensure update_report replaces report_employees (delete + insert) so edits don’t leave stale rows.
- **PDF:** (a) Use a JS library (e.g. pdf-lib) to fill AcroForm fields by name, or (b) keep a thin backend that uses PyMuPDF to fill and return PDFs. Merge and download must work on device or via backend.
- **Auth:** Session or token; first-user bootstrap must run when the database has zero users.
- **Config:** No hardcoded secrets; use environment or secure config for database URL or API base.

---

## 8. Schema note (existing docs)

The file **DATABASE_SCHEMA.md** in this repo describes an extended schema that includes tables `weekly_aggregations` and `employee_timesheets`. Those tables are **not implemented** in the current codebase. The only tables in use are **users**, **reports**, and **report_employees**. This document (AGENT_REPLICATION_SPEC.md) is the source of truth for the actual schema and behavior.
