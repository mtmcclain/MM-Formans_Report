# Setup Instructions
## MM-Formans_Report Application

---

## 🚀 Initial Setup

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

This will install:
- `streamlit` - Web framework
- `pymupdf` - PDF manipulation
- `pyyaml` - YAML file handling (for user management)

### **2. Initialize Database**

The database will be automatically created on first run. However, you can manually initialize it:

```python
python -c "from database import init_db; init_db()"
```

This creates:
- `data/reports.db` - SQLite database file
- All required tables (users, reports, report_employees)

### **3. Create Initial User**

You need to create at least one user account to log in. You can do this in two ways:

#### **Option A: Using Python Script**

Create a file `create_user.py`:

```python
from auth import create_user_in_db

# Create admin user
create_user_in_db(
    username="admin",
    password="your_secure_password",
    full_name="Administrator",
    role="admin"
)

# Create foreman user
create_user_in_db(
    username="foreman1",
    password="password123",
    full_name="John Doe",
    role="foreman"
)
```

Then run:
```bash
python create_user.py
```

#### **Option B: Using YAML File (Legacy)**

Create `data/users.yaml`:

```yaml
admin:
  password: "hashed_password_here"  # Use SHA256 hash
  name: "Administrator"
  role: "admin"

foreman1:
  password: "hashed_password_here"
  name: "John Doe"
  role: "foreman"
```

**Note**: Passwords in YAML must be SHA256 hashed. You can hash a password using:

```python
import hashlib
password = "your_password"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(hashed)
```

### **4. Run the Application**

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🔐 First Login

1. Open the application in your browser
2. Enter your username and password
3. Click "Login"
4. You should now see the Foreman's Daily Report form

---

## 📁 File Structure

After setup, your directory should look like:

```
MM-Formans_Report/
├── app.py                    # Main application
├── auth.py                   # Authentication module
├── database.py              # Database operations
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── data/
│   ├── reports.db          # SQLite database (created automatically)
│   └── users.yaml          # Optional: YAML users (legacy)
├── BlankForemanReport.pdf   # PDF template
├── Martin LOGO.png         # Logo
└── .gitignore              # Git ignore file
```

---

## 🆕 New Features

### **Save Drafts**
- Fill out the form
- Click "💾 Save Draft" in the expandable section
- Your progress is saved and can be loaded later

### **Load Drafts**
- Open "💾 Save & Load Drafts" section
- Select a saved draft from the dropdown
- Click "📂 Load Draft"
- Your form will be populated with saved data

### **Automatic Saving**
- When you generate a PDF, the report is automatically saved to the database
- You can view your report history (feature coming in Phase 2)

---

## 🔧 Troubleshooting

### **Database Not Found**
- The database is created automatically on first run
- Make sure the `data/` directory exists and is writable
- Check file permissions

### **Can't Login**
- Verify user exists in database: Check `data/reports.db` or create user
- Check password is correct
- Try creating a new user account

### **Import Errors**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ required)

### **PDF Generation Fails**
- Verify `BlankForemanReport.pdf` exists in the project root
- Check file permissions
- Ensure PyMuPDF is installed correctly

---

## 🔄 Upgrading from Previous Version

If you're upgrading from a version without database:

1. **Backup your data** (if any)
2. **Install new dependencies**: `pip install -r requirements.txt`
3. **Run the app** - database will be created automatically
4. **Create user accounts** using the methods above
5. **Start using** - all new reports will be saved automatically

**Note**: Old session-based data cannot be migrated automatically. Users will need to create new reports.

---

## 📝 Next Steps

After Phase 1 is working:
- Phase 2: Weekly report aggregation
- Phase 3: Employee timesheet generation
- Phase 4: Enhanced UI and reporting

---

**Last Updated**: 2024
**Version**: 1.0.0 (Phase 1)
