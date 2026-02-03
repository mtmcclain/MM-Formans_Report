# User Login Creation & Management Plan

## Current State

| What you have | Where |
|---------------|--------|
| **Storage** | SQLite `data/reports.db` → `users` table (username, password_hash, full_name, role, email, is_active, last_login) |
| **Login** | `auth.py`: login form, password hash (SHA256), session (authenticated, user, user_id) |
| **Create user (CLI)** | `create_user.py` (hidden password), `create_user_simple.py` (visible), `create_user_interactive.py` (visible, friendly) |
| **Check users (CLI)** | `check_users.py` lists usernames in DB |
| **In-app** | Login page only; no in-app “create account” or “manage users” — message says “Contact administrator” |

So today: **users are created only via command-line scripts**; there is **no in-app user management**.

---

## Decisions to Make

### 1. How do you want to **create** users?

| Option | Pros | Cons |
|--------|------|------|
| **A. Keep CLI only** | Simple, no extra UI; only someone with server/terminal access can add users | You must run `python create_user_interactive.py` (or similar) on the machine; not great for non-technical admins |
| **B. In-app “Admin” page** | Create users from the app; good for a designated admin (e.g. office manager) | Need to build an admin UI and protect it (e.g. admin-only role) |
| **C. In-app “Request account”** | User requests account; admin approves/creates (could be manual or later automated) | More workflow to build; still need a way for admin to actually create the account (B or A) |

**Recommendation:**  
- **Short term:** Keep **CLI** for creation; document it (who runs it, when, and how) in SETUP.md or a short “Admin” section.  
- **Later:** Add a simple **in-app Admin page** (only for users with `role='admin'`) to create/list users if you want non-technical admins to do it.

---

### 2. Who should be allowed to **create** users?

| Option | Meaning |
|--------|--------|
| **Only you (developer/sysadmin)** | Run scripts on the server; no in-app creation. |
| **One or more “admin” users** | Certain logins (e.g. `role='admin'`) get an “Admin” or “User management” section in the app to create/edit users. |
| **First user is admin** | First user ever created is treated as admin; only they (or CLI) can create more users. |

**Recommendation:**  
- Use a **role** in the DB: `foreman` (normal) vs `admin` (can manage users).  
- Create the first admin via CLI:  
  `python create_user_interactive.py` → e.g. username `admin`, role `admin`.  
- All other users can be created by that admin (once you add the Admin page) or via CLI.

---

### 3. What **management** do you want? (list / edit / disable / password reset)

| Action | Use case | Effort |
|--------|----------|--------|
| **List users** | See who has accounts | Low (query `users` table; show in CLI or Admin page) |
| **Deactivate (not delete)** | Stop someone from logging in without losing their reports | Low (set `is_active = 0`; auth already checks `is_active`) |
| **Change password** | User forgot password or you want to reset it | Low (admin sets new password) or Medium (self-service “forgot password” flow) |
| **Edit name/email/role** | Fix typos or change role | Low (update row in `users`) |
| **Delete user** | Remove account (and maybe handle their reports) | Medium (decide: keep reports and set user_id to null, or restrict delete to users with no reports) |

**Recommendation:**  
- **Phase 1:** List users + deactivate (is_active).  
- **Phase 2:** Admin change password + edit full_name / email / role.  
- **Phase 3 (optional):** Self-service “change my password” for any logged-in user; “forgot password” only if you add email (and e.g. a token link).

---

### 4. Where should management live?

| Place | Best for |
|-------|----------|
| **CLI scripts** | Quick ops, automation, or if only you manage users. |
| **In-app “Admin” page** | Non-technical admins; one place to create + list + deactivate + reset password. |

**Recommendation:**  
- **Now:** Use CLI to create and `check_users.py` to list.  
- **Next:** Add a single **Admin** page in the Streamlit app (e.g. “User management” in sidebar or a dedicated route), visible only when `user.role == 'admin'`, with: create user, list users, deactivate, and later edit / reset password.

---

## Suggested Roadmap

### Phase 1 – Clarify and document (no code change)

1. **Decide** who creates users in your team (you only vs. an office admin).
2. **Document** in SETUP.md or a short “User management” section:
   - How to create the first user (e.g. `python create_user_interactive.py`).
   - How to list users: `python check_users.py`.
   - That “Need an account? Contact administrator” means: contact whoever runs that script or will use the future Admin page.

### Phase 2 – In-app Admin page (create + list + deactivate) ✅ DONE

1. **Restrict by role**  
   In `app.py`, sidebar “User management” and Admin page only show when `user.role == 'admin'`.

2. **Admin page content**  
   - **Create user:** form (username, password, confirm, full name, role, email) → `auth.create_user_in_db(...)`.  
   - **List users:** `database.list_users()`; each row shows username, full name, role, last login, and **Deactivate** / **Activate** button.  
   - You cannot deactivate yourself; other users can be deactivated (they cannot log in until activated again).

3. **Database**  
   `database.list_users()` and `database.set_user_active(user_id, is_active)` added in `database.py`.

4. **Navigation**  
   Sidebar (only for admins): “Foreman's Report” | “User management”. Admin page has “← Back to Foreman's Report” button.

### Phase 3 – Edit user, reset password ✅ DONE

1. **Edit user:** Per-user **Edit** button opens a form (full name, email, role) with Save / Cancel. Uses `database.update_user(user_id, full_name, email, role)`.  
2. **Reset password:** Per-user **Reset PW** button opens a form (new password, confirm) with Set password / Cancel. Uses `auth.update_user_password(user_id, new_password)`.

### Phase 4 – Optional: self-service and security

1. **Change my password:** Logged-in user can change their own password (current password + new password).  
2. **Stronger hashing:** Replace SHA256 with bcrypt or argon2 for password hashing (better practice).  
3. **Forgot password:** Only if you add email and a way to send links (e.g. token in URL); otherwise keep “contact admin to reset.”

---

## Quick reference: current scripts

| Script | Purpose |
|--------|---------|
| `python create_user.py` | Create user; password hidden (getpass). |
| `python create_user_simple.py` | Create user; password visible (asterisks). |
| `python create_user_interactive.py` | Create user; password visible; friendly prompts. |
| `python check_users.py` | List usernames (and full_name, role) in DB. |
| `python reset_password.py` | **Forgot password?** Lists users, then sets a NEW password for a username (passwords are hashed and cannot be looked up). |

---

## Summary

- **Create logins:** Today = CLI only (`create_user_interactive.py` recommended). Later = optional in-app Admin page for `admin` role.  
- **Manage logins:** Today = list via `check_users.py`; no in-app management. Next = Admin page: list, deactivate, then edit and reset password.  
- **Who can create:** Decide “only me” vs “one or more admins”; use `role='admin'` and first admin created via CLI.

If you tell me your choice (e.g. “CLI only for now” or “add Admin page with create + list + deactivate”), I can outline the exact code changes (files and steps) next.
