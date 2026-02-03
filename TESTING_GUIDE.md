# Testing Guide - MM-Formans_Report Application

## 📋 Overview

This guide provides step-by-step instructions to test all features in the current codebase before making any changes.

---

## 🚀 Setup Steps

### **1. Navigate to Project Folder**

```powershell
cd "S:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report"
```

### **2. Install Dependencies**

```powershell
python -m pip install -r requirements.txt
```

**Expected output:** Packages installed successfully (streamlit, pymupdf, pyyaml)

### **3. Verify Required Files Exist**

Check that these files are in the project folder:
- ✅ `app.py`
- ✅ `database.py`
- ✅ `auth.py`
- ✅ `config.py`
- ✅ `BlankForemanReport.pdf`
- ✅ `Blank Time.pdf` (timesheet template)
- ✅ `Martin LOGO.png`

### **4. Create Test User Account**

```powershell
python create_user_simple.py
```

**Follow prompts:**
- Enter username (e.g., `testuser`)
- Enter password (remember this!)
- Enter full name (e.g., `Test User`)
- Enter role (e.g., `foreman`)

**Expected output:** "User created successfully!"

---

## 🧪 Testing Checklist

### **Test 1: Application Startup**

**Steps:**
1. Run: `python -m streamlit run app.py`
2. Browser should open automatically at `http://localhost:8501`

**Expected Results:**
- ✅ Login page appears
- ✅ No error messages in terminal
- ✅ Logo displays correctly

**If errors occur:**
- Check that all dependencies are installed
- Verify `BlankForemanReport.pdf` exists
- Check terminal for specific error messages

---

### **Test 2: User Authentication**

#### **2a. Login**

**Steps:**
1. Enter username from step 4
2. Enter password from step 4
3. Click "Login"

**Expected Results:**
- ✅ Login successful
- ✅ Redirected to main form
- ✅ Username displayed in header
- ✅ Logout button visible

#### **2b. Invalid Login**

**Steps:**
1. Enter wrong username
2. Enter wrong password
3. Click "Login"

**Expected Results:**
- ✅ Error message displayed
- ✅ Still on login page

#### **2c. Logout**

**Steps:**
1. Click "🚪 Logout" button
2. Try to access form directly

**Expected Results:**
- ✅ Redirected to login page
- ✅ Cannot access form without login

---

### **Test 3: Daily Report Form - Basic Fields**

#### **3a. Date and State**

**Steps:**
1. Select a date using date picker
2. Toggle between ILLINOIS and INDIANA

**Expected Results:**
- ✅ Date displays in MM/DD/YYYY format
- ✅ State selection works
- ✅ Values persist when scrolling

#### **3b. Job Information**

**Steps:**
1. Enter Job Name (e.g., "Site A Construction")
2. Enter Job Number (e.g., "JOB-123")
3. Enter Job Description (e.g., "Installation work")

**Expected Results:**
- ✅ All fields accept text input
- ✅ Values persist when scrolling

---

### **Test 4: Employee Management**

#### **4a. Add Employees**

**Steps:**
1. Click "➕ Add Employee"
2. Enter employee name (e.g., "John Doe")
3. Select craft (PF, PFF, PFGF, PFA)
4. Enter hours:
   - Straight Time (e.g., 8.0)
   - Time 1.5 (e.g., 2.0)
   - Double Time (e.g., 0.0)
5. Add 2-3 more employees

**Expected Results:**
- ✅ Employees appear in list
- ✅ Can add up to 13 employees
- ✅ Delete button (🗑) works
- ✅ Hours accept decimal values (0.5 increments)

#### **4b. Maximum Employees**

**Steps:**
1. Add 13 employees
2. Try to add 14th employee

**Expected Results:**
- ✅ Warning message: "Maximum 13 employees allowed"
- ✅ 14th employee not added

---

### **Test 5: Equipment Selection**

**Steps:**
1. Check various equipment boxes:
   - SERVICE TRUCK/VAN
   - FOREMAN TRUCK
   - WELDING MACHINE
   - NITROGEN (then enter amount)
   - ARGON (then enter amount)
   - Rental 1 (then enter type)
   - Other 1 (then enter type)

**Expected Results:**
- ✅ All checkboxes work
- ✅ Amount/Type fields appear when relevant boxes checked
- ✅ Values persist when scrolling

---

### **Test 6: Work Notes**

**Steps:**
1. Enter multi-line text in "Work Performed / Notes" field
2. Scroll up and down

**Expected Results:**
- ✅ Text area accepts multi-line input
- ✅ Text persists

---

### **Test 7: Save & Load Reports (Drafts)**

#### **7a. Save Report**

**Steps:**
1. Fill out form with:
   - Date, State, Job info
   - 2-3 employees
   - Some equipment checked
   - Work notes
2. Expand "💾 Save & Load Reports" section
3. Click "💾 Save Report"

**Expected Results:**
- ✅ Success message: "Report saved! (ID: X)"
- ✅ Report saved as draft in database

#### **7b. Load Report**

**Steps:**
1. Clear the form (or refresh page)
2. Expand "💾 Save & Load Reports" section
3. Select saved report from dropdown
4. Click "📂 Load Report"

**Expected Results:**
- ✅ All form fields populated with saved data
- ✅ Employees loaded correctly
- ✅ Equipment checkboxes reflect saved state
- ✅ Work notes loaded

#### **7c. Multiple Drafts**

**Steps:**
1. Save 2-3 different reports with different dates/jobs
2. Check dropdown shows all saved reports

**Expected Results:**
- ✅ All drafts appear in dropdown
- ✅ Can load any draft successfully

---

### **Test 8: Single Day PDF Generation**

#### **8a. Generate PDF**

**Steps:**
1. Fill out complete form:
   - Date: Today's date
   - State: INDIANA
   - Job Name: "Test Job"
   - Job Number: "TEST-001"
   - Job Description: "Test Description"
   - Add 2 employees with hours
   - Check some equipment
   - Add work notes
2. Scroll to bottom
3. Click "Create & Download PDF"

**Expected Results:**
- ✅ Success message: "Report saved to database! (ID: X)"
- ✅ Success message: "PDF created successfully!"
- ✅ Download button appears: "📄 Download Filled PDF"
- ✅ PDF downloads with correct filename format: `MM-DD-YYYY_JobNumber.pdf`

#### **8b. Verify PDF Content**

**Steps:**
1. Open downloaded PDF
2. Check all fields are filled correctly:
   - Date and day of week
   - State checkbox (ILLINOIS or INDIANA)
   - Job name, number, description
   - Employee names, craft, hours
   - Equipment checkboxes marked
   - Work notes

**Expected Results:**
- ✅ All data appears correctly in PDF
- ✅ Formatting looks correct
- ✅ No missing fields

#### **8c. Draft Conversion**

**Steps:**
1. Save a report as draft
2. Load the draft
3. Make a small change
4. Click "Create & Download PDF"

**Expected Results:**
- ✅ Draft converted to submitted report
- ✅ Draft no longer appears in "Load Report" dropdown
- ✅ Report saved with `is_draft=False`

---

### **Test 9: Weekly PDF Generation (NEW FEATURE)**

#### **9a. Create Test Data for Week**

**Steps:**
1. Create reports for multiple days in a week (Mon-Sun):
   - Monday: Job A, 2 employees
   - Tuesday: Job A, 2 employees (same job)
   - Wednesday: Job B, 1 employee (different job)
   - Thursday: Job A, 1 employee
   - Friday: Job A, 2 employees

**Important:** Make sure to:
- Use dates that fall within the same week (Mon-Sun)
- Click "Create & Download PDF" for each (not just Save Report)
- Use same employee names across different days
- Use different job numbers to test multi-job timesheets

#### **9b. Generate Weekly PDFs**

**Steps:**
1. Scroll to "📅 Weekly Report & Timesheet Generation" section
2. Select the Sunday of the test week
3. Verify week range displays correctly (Mon - Sun)
4. Click "📄 Generate Weekly PDFs"

**Expected Results:**
- ✅ Progress bar appears
- ✅ Status messages:
   - "Generating daily Foreman Reports..."
   - "Generating employee Timesheets..."
   - "Merging PDFs..."
- ✅ Success message: "✅ Generated X Foreman Report(s) and Y Timesheet(s)"
- ✅ Download button: "📥 Download Combined Weekly PDF"

#### **9c. Verify Weekly PDF**

**Steps:**
1. Download the combined PDF
2. Open and verify structure:
   - First pages: One Foreman Report per day (Mon-Fri in this example)
   - Following pages: One Timesheet per unique employee

**Expected Results:**
- ✅ All daily reports included
- ✅ One timesheet per employee
- ✅ Timesheets show:
   - Employee name
   - Week dates (Mon-Sun)
   - Job breakdown (if employee worked multiple jobs)
   - Daily hours (ST, OT1.5, DT) for each day
   - Job totals
   - Hours correctly aggregated by day

#### **9d. Test Edge Cases**

**Test with no reports:**
1. Select a week with no reports
2. Click "📄 Generate Weekly PDFs"

**Expected Results:**
- ✅ Warning: "No submitted reports found for the week..."

**Test with single day:**
1. Create report for only Monday
2. Generate weekly PDFs

**Expected Results:**
- ✅ One Foreman Report generated
- ✅ Timesheets generated for employees from that day

---

### **Test 10: Data Persistence**

#### **10a. Logout and Relogin**

**Steps:**
1. Create and save a report
2. Logout
3. Login again with same user
4. Try to load the saved report

**Expected Results:**
- ✅ Report still available after logout/login
- ✅ Data persisted in database

#### **10b. Multiple Users**

**Steps:**
1. Create second user account
2. Login as second user
3. Verify first user's reports are NOT visible

**Expected Results:**
- ✅ Users can only see their own reports
- ✅ Data isolation works correctly

---

### **Test 11: Error Handling**

#### **11a. Missing PDF Template**

**Steps:**
1. Temporarily rename `BlankForemanReport.pdf` to `BlankForemanReport.pdf.bak`
2. Try to generate PDF

**Expected Results:**
- ✅ Error message: "Failed to fill PDF. Check that BlankForemanReport.pdf is in the same folder."

#### **11b. Invalid Date Range**

**Steps:**
1. Try to generate weekly PDFs for a week with no data

**Expected Results:**
- ✅ Appropriate warning message displayed
- ✅ No crash

---

## 🐛 Common Issues & Solutions

### **Issue: "streamlit not recognized"**
**Solution:** Use `python -m streamlit run app.py` instead of `streamlit run app.py`

### **Issue: "No fillable fields detected"**
**Solution:** Check that PDF templates are fillable forms (not just regular PDFs)

### **Issue: Database errors**
**Solution:** 
- Check `data/reports.db` exists
- Check file permissions
- Try deleting `data/reports.db` and restarting (will recreate)

### **Issue: Login fails**
**Solution:**
- Verify user exists: Check `data/reports.db` or recreate user
- Check password is correct
- Try creating new user account

---

## 📊 Test Results Template

Use this to track your testing:

```
Date: ___________
Tester: ___________

[ ] Test 1: Application Startup
[ ] Test 2a: Login
[ ] Test 2b: Invalid Login
[ ] Test 2c: Logout
[ ] Test 3a: Date and State
[ ] Test 3b: Job Information
[ ] Test 4a: Add Employees
[ ] Test 4b: Maximum Employees
[ ] Test 5: Equipment Selection
[ ] Test 6: Work Notes
[ ] Test 7a: Save Report
[ ] Test 7b: Load Report
[ ] Test 7c: Multiple Drafts
[ ] Test 8a: Generate PDF
[ ] Test 8b: Verify PDF Content
[ ] Test 8c: Draft Conversion
[ ] Test 9a: Create Test Data
[ ] Test 9b: Generate Weekly PDFs
[ ] Test 9c: Verify Weekly PDF
[ ] Test 9d: Edge Cases
[ ] Test 10a: Logout/Relogin
[ ] Test 10b: Multiple Users
[ ] Test 11a: Missing Template
[ ] Test 11b: Invalid Date Range

Issues Found:
1. 
2. 
3. 

Notes:
```

---

## ✅ Ready to Proceed

Once all tests pass (or you've documented known issues), you're ready to:
1. Make tweaks to existing features
2. Add new features
3. Fix any bugs found during testing

**Remember:** Always test after making changes!
