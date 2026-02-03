# Git & Testing Workflow Guide
## For Beginners - Step by Step

---

## 🎯 Understanding the Basics

### **What Just Happened?**

When I made changes to your code, here's what occurred:

1. ✅ **Files were created/modified on YOUR computer** (local files)
2. ✅ **Nothing was sent to GitHub yet** (that's your choice!)
3. ✅ **You can test everything locally first**
4. ✅ **You decide when to commit and push to GitHub**

### **Local vs GitHub**

```
┌─────────────────────────────────────────┐
│  YOUR COMPUTER (Local)                  │
│  ┌──────────────────────────────────┐  │
│  │  MM-Formans_Report/              │  │
│  │  ├── app.py  ← Modified         │  │
│  │  ├── database.py ← New file     │  │
│  │  ├── auth.py ← New file         │  │
│  │  └── ...                         │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ✅ You can test here                  │
│  ✅ Make changes                       │
│  ✅ Nothing shared yet                 │
└─────────────────────────────────────────┘
                    │
                    │ (You decide when)
                    ▼
┌─────────────────────────────────────────┐
│  GITHUB (Remote Repository)             │
│  ┌──────────────────────────────────┐  │
│  │  Your repository online          │  │
│  │  (Only updated when you push)    │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ⏳ Waiting for your commit & push      │
└─────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Workflow

### **Step 1: Review What Changed (Optional)**

See what files were modified:

```bash
# In your terminal, navigate to your project folder
cd "s:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report"

# Check what files changed
git status
```

This shows:
- ✅ **Green files** = New files created
- 🔄 **Modified files** = Files that were changed
- ❌ **Red files** = Files with issues (if any)

### **Step 2: Test Locally First! ⚠️ IMPORTANT**

**ALWAYS test before committing!**

#### **A. Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` (if not already installed)
- `pymupdf` (if not already installed)
- `pyyaml` (NEW - needed for authentication)

#### **B. Create a Test User**

```bash
python create_user.py
```

Follow the prompts to create a test account.

#### **C. Run the Application**

```bash
streamlit run app.py
```

This will:
- Open your browser automatically
- Show the login page
- Let you test all new features

#### **D. Test These Features:**

- [ ] Login with your test account
- [ ] Fill out the form
- [ ] Save a draft
- [ ] Load the draft
- [ ] Generate a PDF
- [ ] Logout and login again (data should persist!)

### **Step 3: Check for Errors**

While testing, watch for:
- ❌ Import errors (missing packages)
- ❌ Database errors (permissions, file creation)
- ❌ Login issues (user not found)
- ❌ PDF generation problems

**If you find errors:**
- Fix them locally first
- Test again
- Only commit when everything works!

---

## 🔄 Git Workflow (When You're Ready)

### **Option A: Commit Everything at Once**

If everything works and you're happy:

```bash
# 1. See what will be committed
git status

# 2. Add all changes
git add .

# 3. Commit with a message
git commit -m "Add Phase 1: Database persistence and authentication"

# 4. Push to GitHub
git push origin main
```

### **Option B: Commit in Stages (Recommended)**

Better for learning and safety:

```bash
# 1. Add only the new files first
git add database.py
git add auth.py
git add config.py
git add create_user.py
git commit -m "Add database and authentication modules"

# 2. Add documentation
git add *.md
git add .gitignore
git commit -m "Add documentation and setup files"

# 3. Add the main app changes
git add app.py
git add requirements.txt
git commit -m "Integrate database and auth into main app"

# 4. Push everything
git push origin main
```

### **Option C: Create a Feature Branch (Best Practice)**

This keeps your main code safe:

```bash
# 1. Create a new branch for these changes
git checkout -b feature/phase1-database-auth

# 2. Add and commit your changes
git add .
git commit -m "Phase 1: Add database persistence and authentication"

# 3. Test everything works

# 4. Push the branch
git push origin feature/phase1-database-auth

# 5. Later, merge to main (on GitHub or locally)
```

---

## 🛡️ Safety Tips

### **Before Committing:**

1. ✅ **Test locally** - Make sure everything works
2. ✅ **Check git status** - See what you're committing
3. ✅ **Review changes** - Make sure you want all changes
4. ✅ **Backup important data** - If you have existing reports

### **What NOT to Commit:**

These files are in `.gitignore` (won't be committed):
- `data/reports.db` - Your database (contains user data)
- `data/*.yaml` - User files
- `temp_filled_report.pdf` - Temporary files
- `__pycache__/` - Python cache files

**Why?** These are:
- Too large for Git
- Contain sensitive data
- Generated automatically
- Different for each user

### **What TO Commit:**

- ✅ All `.py` files (your code)
- ✅ `requirements.txt` (dependencies)
- ✅ Documentation (`.md` files)
- ✅ `.gitignore` (ignore rules)
- ✅ PDF templates and logos

---

## 🐛 Troubleshooting

### **"I made a mistake, how do I undo?"**

#### **Undo changes to a file (before committing):**
```bash
git checkout -- app.py  # Reverts app.py to last committed version
```

#### **Unstage a file (remove from commit):**
```bash
git reset HEAD app.py  # Removes from staging, keeps your changes
```

#### **See what changed:**
```bash
git diff app.py  # Shows changes in app.py
```

### **"I committed but want to undo"**

#### **Undo last commit (keep changes):**
```bash
git reset --soft HEAD~1  # Undoes commit, keeps changes staged
```

#### **Undo last commit (discard changes):**
```bash
git reset --hard HEAD~1  # ⚠️ WARNING: This deletes your changes!
```

---

## 📊 Understanding Git Status

When you run `git status`, you'll see:

```
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git checkout -- <file>..." to discard changes)

        modified:   app.py
        modified:   requirements.txt

Untracked files:
  (use "git add <file>..." to include in what will be committed)

        database.py
        auth.py
        config.py
        create_user.py
        SETUP.md
        ...
```

**What this means:**
- **Modified** = File existed, was changed
- **Untracked** = New file, not in Git yet
- **Staged** = Ready to commit (after `git add`)

---

## 🎓 Learning Path

### **For Beginners:**

1. **Week 1**: Test locally, commit when confident
2. **Week 2**: Learn about branches
3. **Week 3**: Learn about pull requests (if working with others)

### **Current Recommendation:**

Since you're new and have people testing:
1. ✅ Test everything locally first
2. ✅ Make sure it works
3. ✅ Commit to a feature branch
4. ✅ Test the branch
5. ✅ Merge to main when ready

---

## ✅ Quick Checklist Before Committing

- [ ] Installed new dependencies (`pip install -r requirements.txt`)
- [ ] Created a test user account
- [ ] Tested login works
- [ ] Tested save draft works
- [ ] Tested load draft works
- [ ] Tested PDF generation works
- [ ] Tested logout/login (data persists)
- [ ] No error messages in console
- [ ] Checked `git status` - see what will be committed
- [ ] Ready to share with team

---

## 🚀 Recommended First-Time Workflow

```bash
# 1. Navigate to project
cd "s:\`MartinMechVDC\PaperWork\MartinMechAPP_repository\MM-Formans_Report"

# 2. Check current status
git status

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create test user
python create_user.py

# 5. Test the app
streamlit run app.py

# 6. If everything works, create feature branch
git checkout -b feature/phase1-test

# 7. Add and commit
git add .
git commit -m "Phase 1: Database and authentication (testing)"

# 8. Test again on this branch

# 9. When confident, merge to main
git checkout main
git merge feature/phase1-test

# 10. Push to GitHub
git push origin main
```

---

## 💡 Key Takeaways

1. **Local changes are safe** - They're only on your computer
2. **Test before committing** - Always!
3. **GitHub is optional** - Commit when YOU'RE ready
4. **You can undo** - Git has safety nets
5. **Branches are your friend** - Use them for new features

---

## 🆘 Need Help?

### **Common Questions:**

**Q: Can I test without committing?**  
A: Yes! Everything is local. Test as much as you want.

**Q: What if I break something?**  
A: You can always revert changes with `git checkout -- filename`

**Q: Do I have to commit everything at once?**  
A: No! Commit in stages, or commit everything - your choice.

**Q: What if my testers find bugs?**  
A: Fix locally, test again, then commit the fixes.

**Q: Can I see what changed?**  
A: Yes! `git diff` shows all changes.

---

**Remember**: Git is a tool to help you, not stress you. Take your time, test thoroughly, and commit when you're confident! 🎉

---

**Last Updated**: 2024  
**For**: Beginners learning Git workflow
