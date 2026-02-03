# Quick Reference Guide
## MM-Formans_Report Development

---

## 🎯 Current Status

**Working Features**:
- ✅ Form input (date, state, job info, employees, equipment, notes)
- ✅ PDF generation and download
- ✅ Session state management (temporary)

**Missing Features**:
- ❌ Data persistence (lost on refresh)
- ❌ User authentication
- ❌ Weekly report aggregation
- ❌ Employee timesheet generation
- ❌ Draft save/load

---

## 🏗️ Architecture Overview

### **Current Flow**
```
User Input → Streamlit Session State → PDF Generation → Download
```

### **Target Flow (Phase 1)**
```
User Login → User Input → Save to Database → PDF Generation → Download
                ↓
            Save Draft (optional)
```

### **Target Flow (Phase 2)**
```
User Login → Dashboard → Select Week/Job → View Aggregated Reports
                ↓
            Generate Weekly Report PDF
                ↓
            Generate Employee Timesheets
```

---

## 📁 File Structure

```
MM-Formans_Report/
├── app.py                    # Main Streamlit app (CURRENT)
├── database.py              # Database operations (TO CREATE)
├── auth.py                  # Authentication (TO CREATE)
├── weekly_reports.py        # Weekly aggregation (TO CREATE)
├── timesheets.py            # Timesheet generation (TO CREATE)
├── config.py                # Configuration (TO CREATE)
├── data/
│   ├── reports.db          # SQLite database (TO CREATE)
│   └── users.yaml          # Initial users (TO CREATE)
└── requirements.txt         # Dependencies (UPDATE)
```

---

## 🔧 Key Technologies

| Technology | Purpose | Status |
|------------|---------|--------|
| Streamlit | Web framework | ✅ Current |
| PyMuPDF (fitz) | PDF manipulation | ✅ Current |
| SQLite | Database | 🔄 To Add |
| streamlit-authenticator | Authentication | 🔄 To Add |
| Python 3.11+ | Runtime | ✅ Current |

---

## 📋 Implementation Phases

### **Phase 1: Foundation** (Non-Breaking)
- [ ] Add SQLite database
- [ ] Add authentication
- [ ] Add save/load drafts
- [ ] Store reports in database

**Timeline**: 1-2 weeks
**Risk**: Low (additive changes)

### **Phase 2: Aggregation** (New Features)
- [ ] Weekly report aggregation
- [ ] Employee timesheet generation
- [ ] Dashboard UI
- [ ] Report history viewer

**Timeline**: 2-3 weeks
**Risk**: Medium (new functionality)

### **Phase 3: Polish** (Enhancement)
- [ ] UI improvements
- [ ] Performance optimization
- [ ] Error handling
- [ ] Documentation

**Timeline**: 1-2 weeks
**Risk**: Low (refinement)

---

## 🚨 Important Considerations

### **Streamlit Limitations**
1. **No built-in database** - Must use external (SQLite file or cloud DB)
2. **Session state is temporary** - Lost on refresh/timeout
3. **File system is ephemeral** - On Streamlit Cloud, files may be deleted
4. **No native authentication** - Must use packages or external services

### **Workarounds**
1. **SQLite** - File-based, works with persistent volumes
2. **Session state** - Use database for persistence
3. **File storage** - Use database or cloud storage for PDFs
4. **Authentication** - Use `streamlit-authenticator` or OAuth

---

## 🔐 Security Checklist

- [ ] Passwords hashed (bcrypt)
- [ ] SQL injection prevention (parameterized queries)
- [ ] User input validation
- [ ] Session management
- [ ] Access control (users see only their data)
- [ ] Secure file storage

---

## 📊 Data Flow Diagrams

### **Report Creation**
```
User Login
    ↓
Fill Form
    ↓
Save Draft? → Yes → Store in DB (is_draft=1)
    ↓ No
Generate PDF
    ↓
Store Report in DB (is_draft=0, is_submitted=1)
    ↓
Download PDF
```

### **Weekly Aggregation**
```
Select Week (Monday-Sunday)
    ↓
Select Job Number
    ↓
Query Reports (date range + job_number)
    ↓
Aggregate Data
    ↓
Generate Weekly Report PDF
    ↓
Download
```

### **Timesheet Generation**
```
Select Week (Monday-Sunday)
    ↓
Query All Reports (date range)
    ↓
Group by Employee Name
    ↓
Aggregate Hours by Job
    ↓
Generate Timesheet PDF per Employee
    ↓
Download (zip or individual)
```

---

## 🐛 Common Issues & Solutions

### **Issue: Data Lost on Refresh**
**Solution**: Implement database persistence

### **Issue: Can't Save Drafts**
**Solution**: Add "Save Draft" button, store with `is_draft=1`

### **Issue: Need Weekly Reports**
**Solution**: Query by date range, aggregate data, generate PDF

### **Issue: Need Employee Timesheets**
**Solution**: Query all reports, group by employee, aggregate hours

### **Issue: No User Accounts**
**Solution**: Add `streamlit-authenticator` or custom auth

---

## 📚 Useful Commands

### **Run App Locally**
```bash
streamlit run app.py
```

### **Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Create Database**
```python
# Run database initialization script
python -c "from database import init_db; init_db()"
```

### **Git Workflow**
```bash
# Create feature branch
git checkout -b feature/data-persistence

# Commit changes
git add .
git commit -m "Add database persistence"

# Push to remote
git push origin feature/data-persistence
```

---

## 🎓 Learning Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **SQLite Tutorial**: https://www.sqlitetutorial.net
- **PyMuPDF Docs**: https://pymupdf.readthedocs.io
- **Streamlit Authenticator**: https://github.com/mkhorasani/Streamlit-Authenticator

---

## 📞 Next Steps

1. **Review** PROJECT_ANALYSIS.md for detailed analysis
2. **Review** DATABASE_SCHEMA.md for database design
3. **Decide** on implementation approach
4. **Create** feature branch for development
5. **Start** with Phase 1 (database + auth)

---

**Last Updated**: 2024
**Status**: Planning Complete, Ready for Implementation
