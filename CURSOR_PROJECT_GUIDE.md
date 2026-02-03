# Simple Guide: Working with Your Project in Cursor

## 🎯 What Just Happened?

**Cursor remembers the original project location** - when you open Cursor, it automatically opens the project from where it was originally set up (the S drive in your case).

This is actually **good** - it means:
- ✅ All your files are in one place
- ✅ Cursor knows where everything is
- ✅ No confusion about which copy to use

---

## 📁 Understanding Your Project Structure

Your project is located at:
```
S:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report
```

**Important files you need to know:**

```
MM-Formans_Report/
├── app.py                    ← Main application (this is what runs)
├── database.py               ← Database operations
├── auth.py                   ← Login system
├── config.py                 ← Settings (file paths, etc.)
├── requirements.txt          ← List of packages needed
│
├── BlankForemanReport.pdf   ← PDF template (must be here!)
├── Blank Time.pdf           ← Timesheet template (must be here!)
├── Martin LOGO.png          ← Logo file (must be here!)
│
├── data/
│   └── reports.db           ← Your database (auto-created)
│
└── create_user_simple.py    ← Script to create user accounts
```

**That's it!** You don't need to worry about the other files right now.

---

## 🚀 Working with One Project Location

### **Option 1: Always Use S Drive (Recommended)**

**Pros:**
- ✅ Simple - one location
- ✅ Cursor always knows where it is
- ✅ No confusion

**How to work:**
1. Open Cursor
2. It automatically opens the S drive project
3. Make your changes
4. Test with: `python -m streamlit run app.py`
5. Done!

**To open the project:**
- File → Open Folder → Navigate to: `S:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report`

---

### **Option 2: Work from C Drive (If You Need To)**

If you really need to work from C drive at home:

**Step 1: Copy the entire folder**
```
Copy: S:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report
To:   C:\YourProject\MM-Formans_Report
```

**Step 2: Open in Cursor**
- File → Open Folder → Select `C:\YourProject\MM-Formans_Report`

**Step 3: When done, copy back**
- Copy the entire folder back to S drive
- Or use Git to sync (if you set it up later)

**⚠️ Warning:** Working in two places can cause confusion. Pick one location and stick with it!

---

## 💡 Simple Workflow

### **Daily Workflow:**

1. **Open Cursor**
   - It should automatically open your S drive project
   - If not: File → Open Recent → Select your project

2. **Make Changes**
   - Edit files in the left sidebar
   - Save (Ctrl+S)

3. **Test Your Changes**
   ```powershell
   # In terminal (bottom of Cursor):
   cd "S:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report"
   python -m streamlit run app.py
   ```

4. **When Done**
   - Close Cursor
   - Your files are saved automatically

---

## 🗂️ Understanding Cursor's Interface

### **Left Sidebar (File Explorer)**
- Shows all your project files
- Click a file to open it
- Right-click for options (rename, delete, etc.)

### **Main Editor (Center)**
- Where you edit code
- Can have multiple files open in tabs

### **Terminal (Bottom)**
- Where you run commands
- Type commands here (like `python -m streamlit run app.py`)

### **Right Sidebar (Optional)**
- Can show AI chat, search, etc.
- You can ignore this for now

---

## 📝 Important: File Locations

**These files MUST be in the project folder:**
- ✅ `BlankForemanReport.pdf`
- ✅ `Blank Time.pdf`
- ✅ `Martin LOGO.png`

**If you move the project, make sure these come with it!**

---

## 🔄 Syncing Between Computers

### **If you work on two computers:**

**Best approach: Use One Location**
- Work from S drive on both computers (if it's a network drive)
- Or use C drive on both and copy files manually

**Better approach (future): Use Git**
- Git tracks changes automatically
- Can sync between computers
- But this is more advanced - don't worry about it yet!

---

## ❓ Common Questions

### **Q: Why does Cursor keep opening S drive?**
**A:** Cursor remembers the last project you opened. This is normal and helpful!

### **Q: Can I have the project in two places?**
**A:** Yes, but it's confusing. Pick one location and stick with it.

### **Q: How do I know which files I changed?**
**A:** In Cursor, changed files show a dot or different color in the file explorer.

### **Q: What if I accidentally delete something?**
**A:** Cursor has undo (Ctrl+Z). Files are also saved automatically.

### **Q: How do I find a file?**
**A:** Press `Ctrl+P` and type the filename.

---

## ✅ Quick Checklist

Before you start working:
- [ ] Cursor is open
- [ ] Project folder is visible in left sidebar
- [ ] You can see `app.py` in the file list
- [ ] Terminal is open at the bottom

When you're done:
- [ ] All files saved (Ctrl+S)
- [ ] Tested your changes
- [ ] No error messages

---

## 🎯 Recommended Setup

**For now, keep it simple:**

1. **Always work from S drive** (or pick C drive and stick with it)
2. **Open Cursor** → It opens your project automatically
3. **Make changes** → Save files
4. **Test** → Run `python -m streamlit run app.py`
5. **Done!**

Don't worry about:
- Git (for now)
- Multiple locations
- Complex workflows
- File structure details

**Focus on:**
- Making your app work
- Testing changes
- Understanding the code

---

## 🆘 Need Help?

**If Cursor is confusing:**
1. Close it
2. Reopen it
3. File → Open Folder → Select your project folder
4. Start working

**If files are missing:**
1. Check the file is in the project folder
2. Refresh the file explorer (click the folder icon)
3. Make sure you're in the right project location

**Remember:** You're learning! It's okay to feel overwhelmed. Take it one step at a time. 🚀
