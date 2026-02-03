# Database Schema Design
## MM-Formans_Report Application

---

## 📊 Database Choice: SQLite

**Why SQLite?**
- ✅ No server required (file-based)
- ✅ Works with Streamlit Cloud (can store in persistent volume)
- ✅ Easy to migrate to PostgreSQL later if needed
- ✅ Perfect for small to medium scale
- ✅ Zero configuration

**Migration Path**: SQLite → PostgreSQL (if needed for production)

---

## 🗂️ Database Schema

### **Table: `users`**
Stores user authentication and profile information.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'foreman',  -- 'foreman', 'admin', 'employee'
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

**Indexes**:
- `username` (unique)
- `email` (if provided)

---

### **Table: `reports`**
Stores completed foreman daily reports.

```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_date DATE NOT NULL,
    state TEXT NOT NULL,  -- 'ILLINOIS' or 'INDIANA'
    job_name TEXT,
    job_number TEXT NOT NULL,
    job_description TEXT,
    work_performed_notes TEXT,
    
    -- Equipment (stored as JSON for flexibility)
    equipment_used TEXT,  -- JSON string of equipment data
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pdf_filename TEXT,  -- Generated PDF filename
    is_draft BOOLEAN DEFAULT 0,
    is_submitted BOOLEAN DEFAULT 0,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Indexes**:
- `user_id`
- `report_date`
- `job_number`
- `(report_date, job_number)` - composite for weekly queries
- `is_draft`
- `is_submitted`

---

### **Table: `report_employees`**
Stores employee data for each report (many-to-many relationship).

```sql
CREATE TABLE report_employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    employee_name TEXT NOT NULL,
    craft TEXT NOT NULL,  -- 'PF', 'PFF', 'PFGF', 'PFA'
    straight_time REAL DEFAULT 0.0,
    overtime_15 REAL DEFAULT 0.0,  -- Time 1.5
    double_time REAL DEFAULT 0.0,
    display_order INTEGER DEFAULT 0,  -- Order in the report
    
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);
```

**Indexes**:
- `report_id`
- `employee_name` (for timesheet aggregation)
- `(report_id, display_order)` - composite for ordering

---

### **Table: `weekly_aggregations`**
Pre-computed weekly aggregations for faster queries.

```sql
CREATE TABLE weekly_aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_number TEXT NOT NULL,
    week_start_date DATE NOT NULL,  -- Monday of the week
    week_end_date DATE NOT NULL,    -- Sunday of the week
    total_reports INTEGER DEFAULT 0,
    aggregated_data TEXT,  -- JSON string of aggregated data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(job_number, week_start_date)
);
```

**Indexes**:
- `job_number`
- `week_start_date`
- `(job_number, week_start_date)` - composite unique

---

### **Table: `employee_timesheets`**
Pre-computed employee timesheets for the week.

```sql
CREATE TABLE employee_timesheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT NOT NULL,
    week_start_date DATE NOT NULL,  -- Monday of the week
    week_end_date DATE NOT NULL,    -- Sunday of the week
    timesheet_data TEXT,  -- JSON string of timesheet data
    pdf_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(employee_name, week_start_date)
);
```

**Indexes**:
- `employee_name`
- `week_start_date`
- `(employee_name, week_start_date)` - composite unique

---

## 📝 Example Data Structures

### **Equipment JSON Structure**
```json
{
    "service_truck_van": true,
    "foreman_truck": false,
    "welding_machine": true,
    "vacuum_pump": false,
    "four_gas_meter": true,
    "torch_setup": false,
    "orbital_welder": false,
    "pipe_machine": true,
    "pro_press_gun": false,
    "b_tank": false,
    "hot_tap_machine": false,
    "plasma_cutter": false,
    "hydro_pump": false,
    "martin_scissor": false,
    "nitrogen": true,
    "nitrogen_amount": "50 lbs",
    "argon": false,
    "argon_amount": "",
    "rental1": true,
    "rental1_type": "Forklift",
    "rental2": false,
    "rental2_type": "",
    "rental3": false,
    "rental3_type": "",
    "other1": false,
    "other1_type": "",
    "other2": false,
    "other2_type": ""
}
```

### **Weekly Aggregation JSON Structure**
```json
{
    "job_number": "JOB-123",
    "job_name": "Site A Construction",
    "week_start": "2024-01-15",
    "week_end": "2024-01-21",
    "reports": [
        {
            "date": "2024-01-15",
            "report_id": 1,
            "foreman": "John Smith",
            "state": "ILLINOIS",
            "employees_count": 5,
            "equipment_count": 8
        }
        // ... other days
    ],
    "total_employees": 12,
    "total_equipment_days": 35,
    "summary": {
        "total_straight_time": 320.0,
        "total_overtime_15": 45.0,
        "total_double_time": 10.0
    }
}
```

### **Employee Timesheet JSON Structure**
```json
{
    "employee_name": "Jane Doe",
    "week_start": "2024-01-15",
    "week_end": "2024-01-21",
    "jobs": [
        {
            "job_number": "JOB-123",
            "job_name": "Site A Construction",
            "days": {
                "monday": {"st": 8.0, "ot15": 0.0, "otdt": 0.0},
                "tuesday": {"st": 8.0, "ot15": 2.0, "otdt": 0.0},
                "wednesday": {"st": 8.0, "ot15": 0.0, "otdt": 0.0},
                "thursday": {"st": 8.0, "ot15": 0.0, "otdt": 0.0},
                "friday": {"st": 8.0, "ot15": 0.0, "otdt": 0.0},
                "saturday": {"st": 0.0, "ot15": 0.0, "otdt": 0.0},
                "sunday": {"st": 0.0, "ot15": 0.0, "otdt": 0.0}
            },
            "job_totals": {
                "st": 40.0,
                "ot15": 2.0,
                "otdt": 0.0
            }
        },
        {
            "job_number": "JOB-456",
            "job_name": "Site B Maintenance",
            "days": {
                "monday": {"st": 0.0, "ot15": 0.0, "otdt": 0.0},
                // ... other days
            },
            "job_totals": {
                "st": 16.0,
                "ot15": 0.0,
                "otdt": 0.0
            }
        }
    ],
    "week_totals": {
        "st": 56.0,
        "ot15": 2.0,
        "otdt": 0.0
    }
}
```

---

## 🔄 Database Operations

### **Key Queries**

#### **Get Reports for Job Number and Week**
```sql
SELECT r.*, u.full_name as foreman_name
FROM reports r
JOIN users u ON r.user_id = u.id
WHERE r.job_number = ?
  AND r.report_date >= ?  -- week_start (Monday)
  AND r.report_date <= ?  -- week_end (Sunday)
  AND r.is_submitted = 1
ORDER BY r.report_date ASC;
```

#### **Get Employee Hours for Week**
```sql
SELECT 
    re.employee_name,
    re.craft,
    r.job_number,
    r.job_name,
    r.report_date,
    re.straight_time,
    re.overtime_15,
    re.double_time
FROM report_employees re
JOIN reports r ON re.report_id = r.id
WHERE re.employee_name = ?
  AND r.report_date >= ?  -- week_start
  AND r.report_date <= ?  -- week_end
  AND r.is_submitted = 1
ORDER BY r.report_date ASC, r.job_number ASC;
```

#### **Get All Jobs for Employee in Week**
```sql
SELECT DISTINCT r.job_number, r.job_name
FROM report_employees re
JOIN reports r ON re.report_id = r.id
WHERE re.employee_name = ?
  AND r.report_date >= ?
  AND r.report_date <= ?
  AND r.is_submitted = 1
ORDER BY r.job_number;
```

---

## 🚀 Migration Strategy

### **Phase 1: Initial Setup**
1. Create database file (`data/reports.db`)
2. Run schema creation script
3. Add database connection to app

### **Phase 2: Data Migration (if needed)**
- If you have existing PDFs or data, create migration script
- Import historical data if available

### **Phase 3: Future Migration to PostgreSQL**
If you need to scale:
1. Export SQLite data
2. Create PostgreSQL schema (similar structure)
3. Import data
4. Update connection strings
5. Test thoroughly

---

## 🔐 Security Best Practices

1. **Use parameterized queries** - Prevent SQL injection
2. **Hash passwords** - Use bcrypt or similar
3. **Validate input** - Sanitize all user inputs
4. **Backup regularly** - SQLite files can be backed up easily
5. **Access control** - Users can only see their own reports (unless admin)

---

## 📊 Performance Considerations

### **SQLite Limitations**
- ✅ Good for up to ~100,000 records
- ✅ Good for concurrent reads
- ⚠️ Limited concurrent writes (fine for this use case)
- ⚠️ File size limit: ~140 TB (not a concern)

### **Optimization Tips**
1. **Use indexes** on frequently queried columns
2. **Pre-compute aggregations** (weekly_aggregations table)
3. **Cache timesheets** (employee_timesheets table)
4. **Archive old data** if database grows large

---

**Last Updated**: 2024
**Database**: SQLite 3.x
**ORM**: Optional (can use raw SQL or sqlite3 directly)
