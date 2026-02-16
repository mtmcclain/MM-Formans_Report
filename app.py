import streamlit as st
from datetime import date, timedelta
import fitz  # PyMuPDF
import auth
import database
import config
from pathlib import Path
import tempfile
import os

# White background behind logo using CSS targeting the image container
# Plus tighter equipment section: two-column layout and reduced gaps
st.markdown(
    """
    <style>
    div[data-testid="stImage"] {
        background-color: white !important;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        display: inline-block;
        margin: 1rem auto 2rem auto;
    }
    /* Larger dropdown options for easier reading (options list wider and bigger text than the type box) */
    select option { font-size: 1.15rem !important; padding: 0.4em 0.5em !important; }
    [data-testid="stSelectbox"] [role="listbox"],
    [data-testid="stSelectbox"] ul,
    div[data-baseweb="select"] [role="listbox"],
    div[data-baseweb="select"] ul { min-width: 220px !important; }
    [data-testid="stSelectbox"] [role="option"],
    [data-testid="stSelectbox"] li,
    div[data-baseweb="select"] [role="option"],
    div[data-baseweb="select"] li {
        font-size: 1.15rem !important;
        padding: 0.5rem 0.75rem !important;
        min-height: 2.25rem !important;
        line-height: 1.4 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────
# Helper: Fill PDF using PyMuPDF (fitz)
# ────────────────────────────────────────────────
def fill_pdf(input_path: str, output_path: str, data: dict):
    try:
        doc = fitz.open(input_path)
        page = doc[0]

        widgets = page.widgets()
        if widgets is None:
            st.warning("No fillable fields detected in the PDF.")
            return False

        filled_count = 0
        for widget in widgets:
            field_name = widget.field_name
            if field_name in data:
                widget.field_value = data[field_name]
                widget.update()  # crucial for appearance
                filled_count += 1

        if filled_count == 0:
            st.warning("None of the provided field names matched the PDF.")
            return False

        # Flatten so filled text is visible without clicking (bake form into page content)
        page.wrap_contents()

        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return True

    except Exception as e:
        st.error(f"Error filling PDF: {str(e)}")
        return False

# ────────────────────────────────────────────────
# Helper: Calculate Monday from Sunday date
# ────────────────────────────────────────────────
def get_week_dates(sunday_date: date):
    """Given a Sunday date, return (Monday, Sunday) of that week"""
    # Sunday is weekday 6, Monday is weekday 0
    days_back = 6  # Go back 6 days from Sunday to get Monday
    monday = sunday_date - timedelta(days=days_back)
    return monday, sunday_date


def foreman_report_number(report_date: date, job_number: str) -> str:
    """Unique identifier for a report: Date-JobNumber (one report per job per date)."""
    date_str = report_date.strftime("%m-%d-%Y")
    job_safe = "".join(c for c in (job_number or "").strip() if c.isalnum() or c in " -_").strip()
    return f"{date_str}-{job_safe}" if job_safe else date_str

# ────────────────────────────────────────────────
# Helper: Merge multiple PDFs into one
# ────────────────────────────────────────────────
def merge_pdfs(pdf_paths: list[str], output_path: str) -> bool:
    """Merge multiple PDF files into one"""
    try:
        merged_doc = fitz.open()
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                doc = fitz.open(pdf_path)
                merged_doc.insert_pdf(doc)
                doc.close()
        merged_doc.save(output_path)
        merged_doc.close()
        return True
    except Exception as e:
        st.error(f"Error merging PDFs: {str(e)}")
        return False

# ────────────────────────────────────────────────
# Helper: Build single "equipmentused" string for PDF (checked items only)
# ────────────────────────────────────────────────
# Welding machine types (dropdown); "other" allows free text
WELDING_MACHINE_TYPES = ["110", "shop mig", "orbital", "other"]
# Truck types (dropdown)
TRUCK_TYPES = ["Service Truck", "Service Van", "Foreman Truck"]
# Test equipment types (includes 4 gas meter); "other" allows free text
TEST_EQUIPMENT_TYPES = ["4 gas meter", "Vacuum pump", "Hydro pump", "other"]
# Gas types; "other" allows free text
GAS_TYPES = ["Torch set up", "B-Tank", "Nitrogen", "Argon", "other"]
# Martin equipment types; "other" allows free text
MARTIN_EQUIPMENT_TYPES = ["Pipe Machine", "Pro press gun", "Hot tap machine", "Plasma cutter", "Scissor lift", "Big Positioner", "Small Positioner", "Pipe Beveler", "other"]

# Entries: (checkbox_key, display_label) or (checkbox_key, display_label, sub_key for amount/type)
# All equipment is in grouped blocks; no flat checkboxes remain.
_EQUIPMENT_ENTRIES = []


def build_equipment_used_string(equip: dict) -> str:
    """Build a single comma-separated string of checked equipment for the PDF 'equipmentused' field."""
    if not equip:
        return ""
    parts = []
    # Format: (amount) Type Group name. Order: Welding, Trucks, Martin, Test, Gases, Rentals
    # Welding machines: list of {type, other_text, qty}
    for w in equip.get("welding_machines") or []:
        t = (w.get("other_text") or "").strip() if (w.get("type") == "other") else (w.get("type") or "110")
        q = w.get("qty", 1)
        parts.append(f"({q}) {t} Welding machine")
    # Trucks: list of {type, qty}
    for t in equip.get("trucks") or []:
        typ = t.get("type") or "Service Truck"
        q = t.get("qty", 1)
        parts.append(f"({q}) {typ} Trucks")
    # Martin equipment: list of {type, other_text, qty}
    for m in equip.get("martin_equipment") or []:
        t = (m.get("other_text") or "").strip() if (m.get("type") == "other") else (m.get("type") or "Pipe Machine")
        q = m.get("qty", 1)
        parts.append(f"({q}) {t} Martin Equipment")
    # Test equipment: list of {type, other_text, qty} (includes 4 gas meter)
    for te in equip.get("test_equipment") or []:
        t = (te.get("other_text") or "").strip() if (te.get("type") == "other") else (te.get("type") or "4 gas meter")
        q = te.get("qty", 1)
        parts.append(f"({q}) {t} Test equipment")
    # Gases: list of {type, other_text, qty}
    for g in equip.get("gases") or []:
        t = (g.get("other_text") or "").strip() if (g.get("type") == "other") else (g.get("type") or "Torch set up")
        q = g.get("qty", 1)
        parts.append(f"({q}) {t} Gases")
    # Rentals: list of {specify, qty}
    for r in equip.get("rentals") or []:
        spec = (r.get("specify") or "").strip()
        if spec:
            q = r.get("qty", 1)
            parts.append(f"({q}) {spec} Rentals")
    for entry in _EQUIPMENT_ENTRIES:
        qty = equip.get(f"{entry[0]}_qty", 1)
        if len(entry) == 2:
            key, label = entry
            if equip.get(key):
                parts.append(f"{label} ({qty})")
        else:
            key, label, sub_key = entry
            if equip.get(key):
                sub = (equip.get(sub_key) or "").strip()
                if sub:
                    parts.append(f"{label} ({sub}) ({qty})")
                else:
                    parts.append(f"{label} ({qty})")
    return ", ".join(parts)


def _equip_row(key: str, label: str, sub_key: str = None):
    """Render one compact equipment row: checkbox, label, and when checked: − qty + ; optional sub text field."""
    qty_key = f"{key}_qty"
    eq = st.session_state.equip
    if qty_key not in eq:
        eq[qty_key] = 1
    qty = eq[qty_key]
    # One tight row: [chk] [label] [−][qty][+] when checked
    cols = st.columns([0.4, 2.2, 0.35, 0.4, 0.35])
    with cols[0]:
        eq[key] = st.checkbox("", value=eq.get(key), key=f"chk_{key}")
    with cols[1]:
        st.write(label)
    if eq[key]:
        with cols[2]:
            if st.button("−", key=f"eq_minus_{key}", help="-1"):
                eq[qty_key] = max(1, qty - 1)
                st.rerun()
        with cols[3]:
            st.write(str(qty))
        with cols[4]:
            if st.button("+", key=f"eq_plus_{key}", help="+1"):
                eq[qty_key] = qty + 1
                st.rerun()
    if sub_key and eq.get(key):
        eq[sub_key] = st.text_input("", value=eq.get(sub_key, "") or "", key=f"sub_{key}", placeholder="Amt or type")

# ────────────────────────────────────────────────
# Authentication - Check if user is logged in
# ────────────────────────────────────────────────
auth.check_authentication()

# ────────────────────────────────────────────────
# Initialize session state
# ────────────────────────────────────────────────
if "employees" not in st.session_state:
    st.session_state.employees = []

if "equip" not in st.session_state:
    _eq_defaults = {
        "martin_equipment": [],  # list of {type, other_text, qty}
        "trucks": [],  # list of {type, qty}
        "welding_machines": [],  # list of {type, other_text, qty}
        "test_equipment": [],  # list of {type, other_text, qty}
        "gases": [],  # list of {type, other_text, qty}
        "rentals": [],  # list of {specify, qty}
    }
    _eq_keys = [e[0] for e in _EQUIPMENT_ENTRIES]
    st.session_state.equip = {**_eq_defaults, **{f"{k}_qty": 1 for k in _eq_keys}}

if "current_draft_id" not in st.session_state:
    st.session_state.current_draft_id = None

# Form field values in session state (for draft loading)
if "form_report_date" not in st.session_state:
    st.session_state.form_report_date = date.today()
if "form_state" not in st.session_state:
    st.session_state.form_state = "INDIANA"
if "form_jobname" not in st.session_state:
    st.session_state.form_jobname = ""
if "form_jobnumber" not in st.session_state:
    st.session_state.form_jobnumber = ""
if "form_jobdescription" not in st.session_state:
    st.session_state.form_jobdescription = ""
if "form_work_notes" not in st.session_state:
    st.session_state.form_work_notes = ""

if "app_page" not in st.session_state:
    st.session_state.app_page = "main"

if "report_view" not in st.session_state:
    st.session_state.report_view = "home"  # "home" = report list, "form" = edit/create report

if "weekly_sunday_display" not in st.session_state:
    _today = date.today()
    _days_until_sunday = (6 - _today.weekday()) % 7
    if _days_until_sunday == 0 and _today.weekday() != 6:
        _days_until_sunday = 7
    st.session_state.weekly_sunday_display = _today + timedelta(days=_days_until_sunday)

# ────────────────────────────────────────────────
# Sidebar: Admin nav (only for admin role)
# ────────────────────────────────────────────────
user = auth.get_current_user()
is_admin = user and (user.get("role") == "admin")

if is_admin:
    with st.sidebar:
        st.caption("**Navigation**")
        page = st.radio(
            "Go to",
            ["Foreman's Report", "User management"],
            index=0 if st.session_state.app_page == "main" else 1,
            key="admin_nav",
            label_visibility="collapsed"
        )
        st.session_state.app_page = "main" if page == "Foreman's Report" else "admin"
        st.markdown("---")
        st.caption(f"Logged in as **{user.get('full_name', user.get('username', 'User'))}**")

# ────────────────────────────────────────────────
# Admin page: User management
# ────────────────────────────────────────────────
if is_admin and st.session_state.app_page == "admin":
    st.title("👥 User management")
    st.caption("Create and manage user accounts. Only admins see this page.")

    # Create new user
    st.subheader("Create new user")
    with st.form("admin_create_user", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username", placeholder="e.g. jsmith")
            new_password = st.text_input("Password", type="password", placeholder="••••••••")
            new_password_confirm = st.text_input("Confirm password", type="password", placeholder="••••••••")
        with c2:
            new_full_name = st.text_input("Full name (optional)", placeholder="e.g. John Smith")
            new_role = st.selectbox("Role", ["foreman", "admin"], index=0)
            new_email = st.text_input("Email (optional)", placeholder="optional@example.com")
        create_submit = st.form_submit_button("Create user")

    if create_submit:
        if not new_username or not new_password:
            st.error("Username and password are required.")
        elif new_password != new_password_confirm:
            st.error("Passwords do not match.")
        else:
            try:
                if auth.create_user_in_db(new_username, new_password, new_full_name or None, new_role, new_email or None):
                    st.success(f"User **{new_username}** created successfully.")
                else:
                    st.error(f"Username **{new_username}** already exists.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # List users
    st.subheader("All users")
    users_list = database.list_users()

    # Edit / Reset / Delete form state
    if "editing_user_id" not in st.session_state:
        st.session_state.editing_user_id = None
    if "resetting_user_id" not in st.session_state:
        st.session_state.resetting_user_id = None
    if "deleting_user_id" not in st.session_state:
        st.session_state.deleting_user_id = None

    if st.session_state.editing_user_id:
        edit_uid = st.session_state.editing_user_id
        edit_u = next((x for x in users_list if x["id"] == edit_uid), None)
        if edit_u:
            with st.container(border=True):
                st.markdown(f"**Edit user:** *{edit_u['username']}*")
                with st.form("admin_edit_user"):
                    edit_full_name = st.text_input("Full name", value=edit_u.get("full_name") or "", key="edit_full_name")
                    edit_email = st.text_input("Email", value=edit_u.get("email") or "", key="edit_email")
                    edit_role = st.selectbox(
                        "Role",
                        ["foreman", "admin"],
                        index=1 if (edit_u.get("role") == "admin") else 0,
                        key="edit_role"
                    )
                    e1, e2 = st.columns(2)
                    with e1:
                        save_edit = st.form_submit_button("Save")
                    with e2:
                        cancel_edit = st.form_submit_button("Cancel")
                if save_edit:
                    database.update_user(edit_uid, edit_full_name or None, edit_email or None, edit_role)
                    st.session_state.editing_user_id = None
                    st.success("User updated.")
                    st.rerun()
                if cancel_edit:
                    st.session_state.editing_user_id = None
                    st.rerun()
        else:
            st.session_state.editing_user_id = None

    # Reset password form (when resetting_user_id is set)
    if st.session_state.resetting_user_id:
        reset_uid = st.session_state.resetting_user_id
        reset_u = next((x for x in users_list if x["id"] == reset_uid), None)
        if reset_u:
            with st.container(border=True):
                st.markdown(f"**Reset password for:** *{reset_u['username']}*")
                with st.form("admin_reset_password"):
                    reset_password = st.text_input("New password", type="password", placeholder="••••••••", key="reset_pw")
                    reset_confirm = st.text_input("Confirm new password", type="password", placeholder="••••••••", key="reset_confirm")
                    r1, r2 = st.columns(2)
                    with r1:
                        set_pw = st.form_submit_button("Set password")
                    with r2:
                        cancel_pw = st.form_submit_button("Cancel")
                if set_pw:
                    if not reset_password or not reset_confirm:
                        st.error("Enter and confirm the new password.")
                    elif reset_password != reset_confirm:
                        st.error("Passwords do not match.")
                    elif auth.update_user_password(reset_uid, reset_password):
                        st.session_state.resetting_user_id = None
                        st.success("Password updated.")
                        st.rerun()
                    else:
                        st.error("Could not update password.")
                if cancel_pw:
                    st.session_state.resetting_user_id = None
                    st.rerun()
        else:
            st.session_state.resetting_user_id = None

    # Delete user confirmation (when deleting_user_id is set)
    if st.session_state.deleting_user_id:
        del_uid = st.session_state.deleting_user_id
        del_u = next((x for x in users_list if x["id"] == del_uid), None)
        if del_u:
            with st.container(border=True):
                st.markdown(f"**Delete user:** *{del_u['username']}* — {del_u.get('full_name') or '(no name)'}")
                st.warning("This will permanently delete this account and **all their reports**. This cannot be undone.")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Yes, delete user", type="primary", key="confirm_delete"):
                        try:
                            database.delete_user(del_uid)
                            st.session_state.deleting_user_id = None
                            st.success("User deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                with d2:
                    if st.button("Cancel", key="cancel_delete"):
                        st.session_state.deleting_user_id = None
                        st.rerun()
        else:
            st.session_state.deleting_user_id = None

    if not users_list:
        st.info("No users yet. Create one above.")
    else:
        for u in users_list:
            with st.container(border=True):
                r1, r2 = st.columns([2, 3])  # wider button area so Edit/Delete/Deactivate stay horizontal
                with r1:
                    st.markdown(f"**{u['username']}** — {u.get('full_name') or '(no name)'} — *{u.get('role', 'foreman')}*")
                    last = u.get('last_login') or u.get('created_at')
                    if last:
                        st.caption(f"Last login: {last}" if 'login' in str(last) else f"Created: {last}")
                    if not u.get('is_active', 1):
                        st.caption("⚠️ **Deactivated** — cannot log in")
                with r2:
                    uid, current_id = u['id'], user['id']
                    b1, b2, b3, b4 = st.columns([1, 1, 1, 1.5])  # wider Deactivate/Activate
                    with b1:
                        if st.button("Edit", key=f"edit_{uid}", help="Edit name, email, role"):
                            st.session_state.editing_user_id = uid
                            st.rerun()
                    with b2:
                        if st.button("Reset PW", key=f"reset_{uid}", help="Set a new password for this user"):
                            st.session_state.resetting_user_id = uid
                            st.rerun()
                    with b3:
                        if uid == current_id:
                            st.caption("(you)")
                        else:
                            if st.button("Delete", key=f"deluser_{uid}", help="Permanently delete user and all their reports"):
                                st.session_state.deleting_user_id = uid
                                st.rerun()
                    with b4:
                        if uid != current_id:
                            if u.get('is_active', 1):
                                if st.button("Deactivate", key=f"deact_{uid}", help="User will not be able to log in"):
                                    database.set_user_active(uid, False)
                                    st.success("User deactivated.")
                                    st.rerun()
                            else:
                                if st.button("Activate", key=f"act_{uid}", help="User can log in again"):
                                    database.set_user_active(uid, True)
                                    st.success("User activated.")
                                    st.rerun()

    st.markdown("---")
    if st.button("← Back to Foreman's Report"):
        st.session_state.app_page = "main"
        st.rerun()
    st.stop()

# ────────────────────────────────────────────────
# Main app layout (Foreman's Report)
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# White container with logo on left + title on right
# ────────────────────────────────────────────────

with st.container():
    st.markdown('<div class="white-card">', unsafe_allow_html=True)

    cols = st.columns([1, 4, 1.2])   # logo, title, logout (wider so "Logout" stays horizontal)

    with cols[0]:
        st.image("Martin LOGO.png", width=250)

    with cols[1]:
        st.markdown("<h1 style='margin-top: 0;'>Foreman's Daily Report</h1>", unsafe_allow_html=True)
        user = auth.get_current_user()
        if user:
            st.caption(f"Logged in as: {user.get('full_name', user.get('username', 'User'))}")

    with cols[2]:
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout()

# ────────────────────────────────────────────────
# Home screen: report list + New report
# ────────────────────────────────────────────────
if st.session_state.report_view == "home":
    from datetime import datetime as dt
    user_id = st.session_state.user_id
    st.subheader("Your reports")
    saved_reports = database.get_user_reports(user_id, include_drafts=True)
    drafts = [r for r in saved_reports if r.get("is_draft", False)]
    if drafts:
        def week_start(d):
            rd = d if hasattr(d, "weekday") else dt.strptime(str(d), "%Y-%m-%d").date()
            return rd - timedelta(days=rd.weekday())
        by_week = {}
        for r in drafts:
            rd = r["report_date"]
            if isinstance(rd, str):
                rd = dt.strptime(rd, "%Y-%m-%d").date()
            mon = week_start(rd)
            if mon not in by_week:
                by_week[mon] = []
            by_week[mon].append(r)
        weeks_sorted = sorted(by_week.keys(), reverse=True)

        def render_home_report_list(reports):
            for r in reports:
                report_date_str = r["report_date"] if isinstance(r["report_date"], str) else r["report_date"].strftime("%Y-%m-%d")
                job_num = r.get("job_number") or "No job"
                job_name = r.get("job_name") or ""
                label = f"{report_date_str} — {job_num}" + (f" ({job_name})" if job_name else "")
                with st.container(border=True):
                    row1, row2 = st.columns([3, 2])
                    with row1:
                        st.markdown(f"**{label}**")
                    with row2:
                        open_col, del_col = st.columns([1, 1])
                        with open_col:
                            if st.button("📂 Open", key=f"home_open_{r['id']}", use_container_width=True):
                                draft = database.get_report(r["id"], user_id)
                                if draft:
                                    if isinstance(draft["report_date"], str):
                                        st.session_state.form_report_date = dt.strptime(draft["report_date"], "%Y-%m-%d").date()
                                    else:
                                        st.session_state.form_report_date = draft["report_date"]
                                    st.session_state.form_state = draft.get("state", "INDIANA")
                                    st.session_state.form_jobname = draft.get("job_name", "")
                                    st.session_state.form_jobnumber = draft.get("job_number", "")
                                    st.session_state.form_jobdescription = draft.get("job_description", "")
                                    st.session_state.form_work_notes = draft.get("work_performed_notes", "")
                                    st.session_state.equip = draft.get("equipment_used", st.session_state.equip)
                                    for k in (e[0] for e in _EQUIPMENT_ENTRIES):
                                        if f"{k}_qty" not in st.session_state.equip:
                                            st.session_state.equip[f"{k}_qty"] = 1
                                    if "trucks" not in st.session_state.equip or not isinstance(st.session_state.equip.get("trucks"), list):
                                        st.session_state.equip["trucks"] = []
                                    if "welding_machines" not in st.session_state.equip or not isinstance(st.session_state.equip.get("welding_machines"), list):
                                        st.session_state.equip["welding_machines"] = []
                                    if "test_equipment" not in st.session_state.equip or not isinstance(st.session_state.equip.get("test_equipment"), list):
                                        st.session_state.equip["test_equipment"] = []
                                    if "gases" not in st.session_state.equip or not isinstance(st.session_state.equip.get("gases"), list):
                                        st.session_state.equip["gases"] = []
                                    if "martin_equipment" not in st.session_state.equip or not isinstance(st.session_state.equip.get("martin_equipment"), list):
                                        st.session_state.equip["martin_equipment"] = []
                                    if isinstance(st.session_state.equip.get("safety_equipment"), list) and st.session_state.equip.get("safety_equipment"):
                                        te = st.session_state.equip.get("test_equipment") or []
                                        if not isinstance(te, list):
                                            te = []
                                        st.session_state.equip["test_equipment"] = te + list(st.session_state.equip["safety_equipment"])
                                        del st.session_state.equip["safety_equipment"]
                                    if "rentals" not in st.session_state.equip or not isinstance(st.session_state.equip.get("rentals"), list):
                                        st.session_state.equip["rentals"] = []
                                    st.session_state.employees = draft.get("employees", [])
                                    st.session_state.current_draft_id = draft["id"]
                                    st.session_state.report_view = "form"
                                    st.rerun()
                        with del_col:
                            if st.button("🗑 Delete", key=f"home_del_{r['id']}", use_container_width=True):
                                if database.delete_report(r["id"], user_id):
                                    if st.session_state.current_draft_id == r["id"]:
                                        st.session_state.current_draft_id = None
                                    st.success("Report deleted.")
                                    st.rerun()
                                else:
                                    st.error("Could not delete report.")

        first_week_mon = weeks_sorted[0]
        first_week_sun = first_week_mon + timedelta(days=6)
        st.caption(f"**Week of Mon {first_week_mon.strftime('%m/%d')} – Sun {first_week_sun.strftime('%m/%d')}**")
        render_home_report_list(by_week[first_week_mon])
        if len(weeks_sorted) > 1:
            with st.expander(f"📅 Previous weeks ({len(weeks_sorted) - 1} more)", expanded=False):
                for mon in weeks_sorted[1:]:
                    sun = mon + timedelta(days=6)
                    st.caption(f"**Week of Mon {mon.strftime('%m/%d')} – Sun {sun.strftime('%m/%d')}**")
                    render_home_report_list(by_week[mon])
    else:
        st.caption("No saved reports yet. Click **New report** to create one.")

    st.markdown("---")
    if st.button("➕ New report", type="primary", use_container_width=True, key="btn_new_report"):
        st.session_state.form_report_date = date.today()
        st.session_state.form_state = "INDIANA"
        st.session_state.form_jobname = ""
        st.session_state.form_jobnumber = ""
        st.session_state.form_jobdescription = ""
        st.session_state.form_work_notes = ""
        st.session_state.employees = []
        _eq_defaults = {
            "martin_equipment": [],
            "trucks": [],
            "welding_machines": [],
            "test_equipment": [],
            "gases": [],
            "rentals": [],
        }
        _eq_keys = [e[0] for e in _EQUIPMENT_ENTRIES]
        st.session_state.equip = {**_eq_defaults, **{f"{k}_qty": 1 for k in _eq_keys}}
        st.session_state.current_draft_id = None
        st.session_state.report_view = "form"
        st.rerun()

    # Weekly Report & Timesheet Generation (on main/home page)
    st.markdown("---" * 2)
    st.header("📅 Weekly Report & Timesheet Generation")
    st.caption("Uses only the saved reports listed above. Save your reports first; only those whose date falls in the selected week are included.")
    today = date.today()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0 and today.weekday() != 6:
        days_until_sunday = 7
    default_sunday = today + timedelta(days=days_until_sunday)
    selected = st.date_input(
        "Select Week (Sunday)",
        value=st.session_state.weekly_sunday_display,
        format="MM/DD/YYYY",
        help="Pick any day in the week; it will use that week's Sunday (Mon–Sun).",
        key="home_weekly_date",
    )
    sunday_date = selected + timedelta(days=(6 - selected.weekday()) % 7)
    st.session_state.weekly_sunday_display = sunday_date
    monday_date, week_end = get_week_dates(sunday_date)
    st.caption(f"Week: {monday_date.strftime('%m/%d/%Y')} (Mon) - {week_end.strftime('%m/%d/%Y')} (Sun)")
    if st.button("📄 Generate Weekly PDFs", type="primary", use_container_width=True, key="btn_weekly_pdf"):
        saved_reports = database.get_user_reports(user_id, include_drafts=True)
        drafts = [r for r in saved_reports if r.get("is_draft", False)]
        week_reports = []
        for r in drafts:
            rd = r["report_date"]
            if isinstance(rd, str):
                from datetime import datetime
                rd = datetime.strptime(rd, "%Y-%m-%d").date()
            if monday_date <= rd <= week_end:
                full = database.get_report(r["id"], user_id)
                if full:
                    week_reports.append(full)
        if not week_reports:
            st.warning(
                f"No saved reports in the list fall in the week {monday_date.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}. "
                "Save reports first and ensure their dates are in this week."
            )
        else:
            st.info(f"Using {len(week_reports)} saved report(s) from the list for this week. Generating PDFs...")
            temp_files = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                status_text.text("Generating daily Foreman Reports...")
                for idx, report in enumerate(week_reports):
                    report_date = report["report_date"]
                    if isinstance(report_date, str):
                        from datetime import datetime
                        report_date = datetime.strptime(report_date, "%Y-%m-%d").date()
                    data = {
                        "day": report_date.strftime("%A"),
                        "date": report_date.strftime("%m/%d/%Y"),
                        "ForemanReportNumber": foreman_report_number(report_date, report.get("job_number", "")),
                        "ILLINOIS": "X" if report.get("state") == "ILLINOIS" else "",
                        "INDIANA": "X" if report.get("state") == "INDIANA" else "",
                        "jobname": report.get("job_name", ""),
                        "jobnumber": report.get("job_number", ""),
                        "jobdescription": report.get("job_description", ""),
                        "WORK PERFORMED/NOTES": report.get("work_performed_notes", ""),
                        "equipmentused": build_equipment_used_string(report.get("equipment_used", {})),
                    }
                    employees = report.get("employees", [])
                    for i, emp in enumerate(employees, start=1):
                        if i > 13:
                            break
                        data[f"employee{i}name"] = emp.get("name", "")
                        data[f"employee{i}craft"] = emp.get("craft", "")
                        data[f"employee{i}st"] = f"{emp.get('st', 0.0):.1f}" if emp.get("st", 0.0) > 0 else ""
                        data[f"employee{i}ot1.5"] = f"{emp.get('ot15', 0.0):.1f}" if emp.get("ot15", 0.0) > 0 else ""
                        data[f"employee{i}otdt"] = f"{emp.get('otdt', 0.0):.1f}" if emp.get("otdt", 0.0) > 0 else ""
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    temp_file.close()
                    if fill_pdf("BlankForemanReport.pdf", temp_file.name, data):
                        temp_files.append(temp_file.name)
                    progress_bar.progress((idx + 1) / (len(week_reports) + 1))
                status_text.text("Generating employee Timesheets...")
                unique_employees_set = set()
                for report in week_reports:
                    for emp in report.get("employees", []):
                        name = (emp.get("name") or "").strip()
                        if name:
                            unique_employees_set.add(name)
                unique_employees = sorted(unique_employees_set)

                def get_employee_timesheet_from_reports(emp_name, reports):
                    entries = []
                    for report in reports:
                        for emp in report.get("employees", []):
                            if (emp.get("name") or "").strip() != emp_name:
                                continue
                            rd = report.get("report_date")
                            if isinstance(rd, str):
                                from datetime import datetime
                                rd = datetime.strptime(rd, "%Y-%m-%d").date()
                            entries.append({
                                "report_date": rd,
                                "job_number": report.get("job_number", ""),
                                "job_name": report.get("job_name", ""),
                                "job_description": report.get("job_description", ""),
                                "craft": emp.get("craft", ""),
                                "straight_time": float(emp.get("st", 0.0)),
                                "overtime_15": float(emp.get("ot15", 0.0)),
                                "double_time": float(emp.get("otdt", 0.0)),
                            })
                    return entries

                for emp_idx, emp_name in enumerate(unique_employees):
                    emp_data = get_employee_timesheet_from_reports(emp_name, week_reports)
                    jobs_dict = {}
                    for entry in emp_data:
                        job_num = entry.get("job_number", "")
                        if job_num not in jobs_dict:
                            jobs_dict[job_num] = {
                                "job_name": entry.get("job_name", ""),
                                "job_number": job_num,
                                "job_description": entry.get("job_description", ""),
                                "craft": entry.get("craft", ""),
                                "entries": [],
                            }
                        jobs_dict[job_num]["entries"].append(entry)
                    week_dates = [monday_date + timedelta(days=i) for i in range(7)]
                    day_names = ["mon", "tues", "wed", "thurs", "fri", "sat", "sun"]
                    timesheet_data = {
                        "employee_name": emp_name,
                        "Week end date": week_end.strftime("%m/%d/%Y"),
                        "mon_date": week_dates[0].strftime("%m/%d"),
                        "tues_date": week_dates[1].strftime("%m/%d"),
                        "wed_date": week_dates[2].strftime("%m/%d"),
                        "thurs_date": week_dates[3].strftime("%m/%d"),
                        "fri_date": week_dates[4].strftime("%m/%d"),
                        "sat_date": week_dates[5].strftime("%m/%d"),
                        "sun_date": week_dates[6].strftime("%m/%d"),
                    }
                    job_list = list(jobs_dict.values())[:8]
                    for job_idx, job in enumerate(job_list, start=1):
                        job_num = f"job{job_idx}"
                        timesheet_data[f"{job_num}_name"] = job["job_name"]
                        timesheet_data[f"{job_num}_job_number"] = job["job_number"]
                        timesheet_data[f"{job_num}_description"] = job["job_description"]
                        timesheet_data[f"{job_num}_craft"] = job["craft"]
                        job_st_total = job_ot15_total = job_dt_total = 0.0
                        hours_by_date = {}
                        for entry in job["entries"]:
                            entry_date = entry.get("report_date")
                            if isinstance(entry_date, str):
                                from datetime import datetime
                                entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
                            day_idx = (entry_date - monday_date).days
                            if 0 <= day_idx < 7:
                                day_key = day_names[day_idx]
                                if day_key not in hours_by_date:
                                    hours_by_date[day_key] = {"st": 0.0, "ot15": 0.0, "dt": 0.0}
                                hours_by_date[day_key]["st"] += float(entry.get("straight_time", 0.0))
                                hours_by_date[day_key]["ot15"] += float(entry.get("overtime_15", 0.0))
                                hours_by_date[day_key]["dt"] += float(entry.get("double_time", 0.0))
                        for day_name in day_names:
                            day_hours = hours_by_date.get(day_name, {"st": 0.0, "ot15": 0.0, "dt": 0.0})
                            st_val = f"{day_hours['st']:.1f}" if day_hours["st"] > 0 else ""
                            ot15_val = f"{day_hours['ot15']:.1f}" if day_hours["ot15"] > 0 else ""
                            dt_val = f"{day_hours['dt']:.1f}" if day_hours["dt"] > 0 else ""
                            timesheet_data[f"{job_num}_{day_name}_st"] = st_val
                            timesheet_data[f"{job_num}_{day_name}_1.5"] = ot15_val
                            timesheet_data[f"{job_num}_{day_name}_dt"] = dt_val
                            job_st_total += day_hours["st"]
                            job_ot15_total += day_hours["ot15"]
                            job_dt_total += day_hours["dt"]
                        timesheet_data[f"{job_num}_st_total"] = f"{job_st_total:.1f}" if job_st_total > 0 else ""
                        timesheet_data[f"{job_num}_1.5_total"] = f"{job_ot15_total:.1f}" if job_ot15_total > 0 else ""
                        timesheet_data[f"{job_num}_dt_total"] = f"{job_dt_total:.1f}" if job_dt_total > 0 else ""
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    temp_file.close()
                    if fill_pdf("Blank Time.pdf", temp_file.name, timesheet_data):
                        temp_files.append(temp_file.name)
                    progress_bar.progress((len(week_reports) + emp_idx + 1) / (len(week_reports) + len(unique_employees)))
                status_text.text("Merging PDFs...")
                if temp_files:
                    merged_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    merged_output.close()
                    if merge_pdfs(temp_files, merged_output.name):
                        username = (st.session_state.get("user") or {}).get("username", "user")
                        weekend_str = week_end.strftime("%m-%d-%Y")
                        final_filename = f"{username}_{weekend_str}.pdf"
                        with open(merged_output.name, "rb") as f:
                            st.download_button(
                                label="📥 Download Combined Weekly PDF",
                                data=f,
                                file_name=final_filename,
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        st.success(f"✅ Generated {len(week_reports)} Foreman Report(s) and {len(unique_employees)} Timesheet(s)")
                        for tf in temp_files:
                            try:
                                os.unlink(tf)
                            except Exception:
                                pass
                        try:
                            os.unlink(merged_output.name)
                        except Exception:
                            pass
                    else:
                        st.error("Failed to merge PDFs")
                else:
                    st.error("No PDFs were generated")
            except Exception as e:
                st.error(f"Error generating weekly PDFs: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            finally:
                progress_bar.empty()
                status_text.empty()

    st.stop()

# ────────────────────────────────────────────────
# Form view: Back to reports, then report form
# ────────────────────────────────────────────────
if st.button("← Back to reports", key="btn_back_to_reports"):
    st.session_state.report_view = "home"
    st.session_state.current_draft_id = None
    st.rerun()

report_date = st.date_input(
    "Date",
    value=st.session_state.form_report_date,
    format="MM/DD/YYYY"   # picker shows 01/23/2026 style
)
st.session_state.form_report_date = report_date

state_idx = 0 if st.session_state.form_state == "ILLINOIS" else 1
state = st.radio("State", ["ILLINOIS", "INDIANA"], index=state_idx, horizontal=True)
st.session_state.form_state = state

jobname = st.text_input("Job Name", value=st.session_state.form_jobname)
st.session_state.form_jobname = jobname

jobnumber = st.text_input("Job Number", value=st.session_state.form_jobnumber)
st.session_state.form_jobnumber = jobnumber

jobdescription = st.text_input("Job Description", value=st.session_state.form_jobdescription)
st.session_state.form_jobdescription = jobdescription

# Employees section (unchanged) ...
st.header("Employees")

for idx, emp in enumerate(st.session_state.employees):
    with st.container(border=True):
        cols = st.columns([3.5, 2, 1.5, 1.5, 1.5, 0.8])

        emp["name"] = cols[0].text_input("Name", value=emp.get("name", ""), key=f"name_{idx}")

        craft_options = ["PF", "PFF", "PFGF", "PFA"]
        craft_idx = craft_options.index(emp.get("craft", "PF"))
        emp["craft"] = cols[1].selectbox("Craft", craft_options, index=craft_idx, key=f"craft_{idx}")

        emp["st"]   = cols[2].number_input("Straight Time",   value=float(emp.get("st",   0.0)), min_value=0.0, step=0.5, key=f"st_{idx}")
        emp["ot15"] = cols[3].number_input("Time 1.5", value=float(emp.get("ot15", 0.0)), min_value=0.0, step=0.5, key=f"ot15_{idx}")
        emp["otdt"] = cols[4].number_input("Double Time",  value=float(emp.get("otdt",  0.0)), min_value=0.0, step=0.5, key=f"otdt_{idx}")

        if cols[5].button("🗑", key=f"emp_del_{idx}"):
            st.session_state.employees.pop(idx)
            st.rerun()

if st.button("➕ Add Employee", use_container_width=True):
    if len(st.session_state.employees) < 13:
        st.session_state.employees.append({
            "name": "", "craft": "PF", "st": 0.0, "ot15": 0.0, "otdt": 0.0
        })
        st.rerun()
    else:
        st.warning("Maximum 13 employees allowed.")

st.header("Work Performed / Notes")
work_performed_notes = st.text_area("Enter details here (multiline)", value=st.session_state.form_work_notes, height=180, key="notes")
st.session_state.form_work_notes = work_performed_notes

# Equipment section: single column for easier-to-read dropdowns
st.markdown('<div class="small-font">', unsafe_allow_html=True)

st.header("Equipment Used Today")
st.caption("Check if used. When checked, amount (default 1) with − / + buttons.")

eq = st.session_state.equip
if "martin_equipment" not in eq or not isinstance(eq.get("martin_equipment"), list):
    eq["martin_equipment"] = []
if "trucks" not in eq or not isinstance(eq.get("trucks"), list):
    eq["trucks"] = []
if "welding_machines" not in eq or not isinstance(eq.get("welding_machines"), list):
    eq["welding_machines"] = []
if "test_equipment" not in eq or not isinstance(eq.get("test_equipment"), list):
    eq["test_equipment"] = []
if "gases" not in eq or not isinstance(eq.get("gases"), list):
    eq["gases"] = []
if "rentals" not in eq or not isinstance(eq.get("rentals"), list):
    eq["rentals"] = []

# Welding machines block
wm_list = eq["welding_machines"]
with st.container(border=True):
    st.write("**Welding machine(s)**")
    for i, w in enumerate(wm_list):
        if "qty" not in wm_list[i]:
            wm_list[i]["qty"] = 1
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 0.35, 0.45, 0.35, 0.35])
        with c1:
            idx = WELDING_MACHINE_TYPES.index(w.get("type", "110")) if w.get("type") in WELDING_MACHINE_TYPES else 0
            new_type = st.selectbox("Type", WELDING_MACHINE_TYPES, index=idx, key=f"wm_type_{i}")
            wm_list[i]["type"] = new_type
        with c2:
            if new_type == "other":
                wm_list[i]["other_text"] = st.text_input("Specify", value=w.get("other_text", "") or "", key=f"wm_other_{i}", placeholder="Type here")
            else:
                wm_list[i]["other_text"] = ""
        with c3:
            if st.button("−", key=f"wm_minus_{i}", help="-1"):
                wm_list[i]["qty"] = max(1, wm_list[i].get("qty", 1) - 1)
                st.rerun()
        with c4:
            st.write(str(wm_list[i].get("qty", 1)))
        with c5:
            if st.button("+", key=f"wm_plus_{i}", help="+1"):
                wm_list[i]["qty"] = wm_list[i].get("qty", 1) + 1
                st.rerun()
        with c6:
            if st.button("🗑", key=f"wm_del_{i}", help="Remove"):
                wm_list.pop(i)
                st.rerun()
    if st.button("➕ Add welding machine", key="wm_add"):
        wm_list.append({"type": "110", "other_text": "", "qty": 1})
        st.rerun()

# Trucks block
truck_list = eq["trucks"]
with st.container(border=True):
    st.write("**Truck(s)**")
    for i, t in enumerate(truck_list):
        if "qty" not in truck_list[i]:
            truck_list[i]["qty"] = 1
        c1, c2, c3, c4, c5 = st.columns([1.8, 0.35, 0.45, 0.35, 0.35])
        with c1:
            idx = TRUCK_TYPES.index(t.get("type", "Service Truck")) if t.get("type") in TRUCK_TYPES else 0
            new_type = st.selectbox("Type", TRUCK_TYPES, index=idx, key=f"truck_type_{i}")
            truck_list[i]["type"] = new_type
        with c2:
            if st.button("−", key=f"truck_minus_{i}", help="-1"):
                truck_list[i]["qty"] = max(1, truck_list[i].get("qty", 1) - 1)
                st.rerun()
        with c3:
            st.write(str(truck_list[i].get("qty", 1)))
        with c4:
            if st.button("+", key=f"truck_plus_{i}", help="+1"):
                truck_list[i]["qty"] = truck_list[i].get("qty", 1) + 1
                st.rerun()
        with c5:
            if st.button("🗑", key=f"truck_del_{i}", help="Remove"):
                truck_list.pop(i)
                st.rerun()
    if st.button("➕ Add truck", key="truck_add"):
        truck_list.append({"type": "Service Truck", "qty": 1})
        st.rerun()

# Martin Equipment block
martin_list = eq["martin_equipment"]
with st.container(border=True):
    st.write("**Martin Equipment**")
    for i, m in enumerate(martin_list):
        if "qty" not in martin_list[i]:
            martin_list[i]["qty"] = 1
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 0.35, 0.45, 0.35, 0.35])
        with c1:
            idx = MARTIN_EQUIPMENT_TYPES.index(m.get("type", "Pipe Machine")) if m.get("type") in MARTIN_EQUIPMENT_TYPES else 0
            new_type = st.selectbox("Type", MARTIN_EQUIPMENT_TYPES, index=idx, key=f"martin_type_{i}")
            martin_list[i]["type"] = new_type
        with c2:
            if new_type == "other":
                martin_list[i]["other_text"] = st.text_input("Specify", value=m.get("other_text", "") or "", key=f"martin_other_{i}", placeholder="Type here")
            else:
                martin_list[i]["other_text"] = ""
        with c3:
            if st.button("−", key=f"martin_minus_{i}", help="-1"):
                martin_list[i]["qty"] = max(1, martin_list[i].get("qty", 1) - 1)
                st.rerun()
        with c4:
            st.write(str(martin_list[i].get("qty", 1)))
        with c5:
            if st.button("+", key=f"martin_plus_{i}", help="+1"):
                martin_list[i]["qty"] = martin_list[i].get("qty", 1) + 1
                st.rerun()
        with c6:
            if st.button("🗑", key=f"martin_del_{i}", help="Remove"):
                martin_list.pop(i)
                st.rerun()
    if st.button("➕ Add Martin equipment", key="martin_add"):
        martin_list.append({"type": "Pipe Machine", "other_text": "", "qty": 1})
        st.rerun()

# Test equipment block (4 gas meter, Vacuum pump, Hydro pump, other)
te_list = eq["test_equipment"]
with st.container(border=True):
    st.write("**Test equipment**")
    for i, te in enumerate(te_list):
        if "qty" not in te_list[i]:
            te_list[i]["qty"] = 1
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 0.35, 0.45, 0.35, 0.35])
        with c1:
            idx = TEST_EQUIPMENT_TYPES.index(te.get("type", "4 gas meter")) if te.get("type") in TEST_EQUIPMENT_TYPES else 0
            new_type = st.selectbox("Type", TEST_EQUIPMENT_TYPES, index=idx, key=f"te_type_{i}")
            te_list[i]["type"] = new_type
        with c2:
            if new_type == "other":
                te_list[i]["other_text"] = st.text_input("Specify", value=te.get("other_text", "") or "", key=f"te_other_{i}", placeholder="Type here")
            else:
                te_list[i]["other_text"] = ""
        with c3:
            if st.button("−", key=f"te_minus_{i}", help="-1"):
                te_list[i]["qty"] = max(1, te_list[i].get("qty", 1) - 1)
                st.rerun()
        with c4:
            st.write(str(te_list[i].get("qty", 1)))
        with c5:
            if st.button("+", key=f"te_plus_{i}", help="+1"):
                te_list[i]["qty"] = te_list[i].get("qty", 1) + 1
                st.rerun()
        with c6:
            if st.button("🗑", key=f"te_del_{i}", help="Remove"):
                te_list.pop(i)
                st.rerun()
    if st.button("➕ Add test equipment", key="te_add"):
        te_list.append({"type": "4 gas meter", "other_text": "", "qty": 1})
        st.rerun()

# Gases block (Torch set up, B-Tank, Nitrogen, Argon, other)
gas_list = eq["gases"]
with st.container(border=True):
    st.write("**Gases**")
    for i, g in enumerate(gas_list):
        if "qty" not in gas_list[i]:
            gas_list[i]["qty"] = 1
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 0.35, 0.45, 0.35, 0.35])
        with c1:
            idx = GAS_TYPES.index(g.get("type", "Torch set up")) if g.get("type") in GAS_TYPES else 0
            new_type = st.selectbox("Type", GAS_TYPES, index=idx, key=f"gas_type_{i}")
            gas_list[i]["type"] = new_type
        with c2:
            if new_type == "other":
                gas_list[i]["other_text"] = st.text_input("Specify", value=g.get("other_text", "") or "", key=f"gas_other_{i}", placeholder="Type here")
            else:
                gas_list[i]["other_text"] = ""
        with c3:
            if st.button("−", key=f"gas_minus_{i}", help="-1"):
                gas_list[i]["qty"] = max(1, gas_list[i].get("qty", 1) - 1)
                st.rerun()
        with c4:
            st.write(str(gas_list[i].get("qty", 1)))
        with c5:
            if st.button("+", key=f"gas_plus_{i}", help="+1"):
                gas_list[i]["qty"] = gas_list[i].get("qty", 1) + 1
                st.rerun()
        with c6:
            if st.button("🗑", key=f"gas_del_{i}", help="Remove"):
                gas_list.pop(i)
                st.rerun()
    if st.button("➕ Add gas", key="gas_add"):
        gas_list.append({"type": "Torch set up", "other_text": "", "qty": 1})
        st.rerun()

# Rentals block (specify + qty per row)
rental_list = eq["rentals"]
with st.container(border=True):
    st.write("**Rentals**")
    for i, r in enumerate(rental_list):
        if "qty" not in rental_list[i]:
            rental_list[i]["qty"] = 1
        c1, c2, c3, c4, c5 = st.columns([2, 0.35, 0.45, 0.35, 0.35])
        with c1:
            rental_list[i]["specify"] = st.text_input("Specify", value=r.get("specify", "") or "", key=f"rental_spec_{i}", placeholder="e.g. Scissor lift, Generator")
        with c2:
            if st.button("−", key=f"rental_minus_{i}", help="-1"):
                rental_list[i]["qty"] = max(1, rental_list[i].get("qty", 1) - 1)
                st.rerun()
        with c3:
            st.write(str(rental_list[i].get("qty", 1)))
        with c4:
            if st.button("+", key=f"rental_plus_{i}", help="+1"):
                rental_list[i]["qty"] = rental_list[i].get("qty", 1) + 1
                st.rerun()
        with c5:
            if st.button("🗑", key=f"rental_del_{i}", help="Remove"):
                rental_list.pop(i)
                st.rerun()
    if st.button("➕ Add rental", key="rental_add"):
        rental_list.append({"specify": "", "qty": 1})
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Save & Load Reports Section
# ────────────────────────────────────────────────
with st.expander("💾 Save & Load Reports", expanded=True):
    user_id = st.session_state.user_id
    saved_reports = database.get_user_reports(user_id, include_drafts=True)
    drafts = [r for r in saved_reports if r.get('is_draft', False)]

    # Saved reports list (above buttons), grouped by week (current week first, older weeks collapsed)
    st.subheader("Saved reports")
    if drafts:
        # Group drafts by week (Monday = start of week)
        from datetime import datetime as dt
        def week_start(d):
            rd = d if hasattr(d, "weekday") else dt.strptime(str(d), "%Y-%m-%d").date()
            return rd - timedelta(days=rd.weekday())  # Monday
        by_week = {}
        for r in drafts:
            rd = r["report_date"]
            if isinstance(rd, str):
                rd = dt.strptime(rd, "%Y-%m-%d").date()
            mon = week_start(rd)
            sun = mon + timedelta(days=6)
            if mon not in by_week:
                by_week[mon] = []
            by_week[mon].append(r)
        # Sort weeks descending (most recent first)
        weeks_sorted = sorted(by_week.keys(), reverse=True)

        def render_report_list(reports):
            for r in reports:
                report_date_str = r["report_date"] if isinstance(r["report_date"], str) else r["report_date"].strftime("%Y-%m-%d")
                job_num = r.get("job_number") or "No job"
                job_name = r.get("job_name") or ""
                label = f"{report_date_str} — {job_num}" + (f" ({job_name})" if job_name else "")
                with st.container(border=True):
                    row1, row2 = st.columns([3, 2])
                    with row1:
                        st.markdown(f"**{label}**")
                    with row2:
                        load_col, del_col = st.columns([1, 1])
                        with load_col:
                            if st.button("📂 Load", key=f"report_load_{r['id']}", use_container_width=True):
                                draft = database.get_report(r["id"], user_id)
                                if draft:
                                    if isinstance(draft["report_date"], str):
                                        st.session_state.form_report_date = dt.strptime(draft["report_date"], "%Y-%m-%d").date()
                                    else:
                                        st.session_state.form_report_date = draft["report_date"]
                                    st.session_state.form_state = draft.get("state", "INDIANA")
                                    st.session_state.form_jobname = draft.get("job_name", "")
                                    st.session_state.form_jobnumber = draft.get("job_number", "")
                                    st.session_state.form_jobdescription = draft.get("job_description", "")
                                    st.session_state.form_work_notes = draft.get("work_performed_notes", "")
                                    st.session_state.equip = draft.get("equipment_used", st.session_state.equip)
                                    for k in (e[0] for e in _EQUIPMENT_ENTRIES):
                                        if f"{k}_qty" not in st.session_state.equip:
                                            st.session_state.equip[f"{k}_qty"] = 1
                                    if "trucks" not in st.session_state.equip or not isinstance(st.session_state.equip.get("trucks"), list):
                                        st.session_state.equip["trucks"] = []
                                    if "welding_machines" not in st.session_state.equip or not isinstance(st.session_state.equip["welding_machines"], list):
                                        st.session_state.equip["welding_machines"] = []
                                    if "test_equipment" not in st.session_state.equip or not isinstance(st.session_state.equip.get("test_equipment"), list):
                                        st.session_state.equip["test_equipment"] = []
                                    if "gases" not in st.session_state.equip or not isinstance(st.session_state.equip.get("gases"), list):
                                        st.session_state.equip["gases"] = []
                                    if "martin_equipment" not in st.session_state.equip or not isinstance(st.session_state.equip.get("martin_equipment"), list):
                                        st.session_state.equip["martin_equipment"] = []
                                    # Migrate old safety_equipment into test_equipment (4 gas meter moved there)
                                    prev_equip = st.session_state.equip
                                    if isinstance(prev_equip.get("safety_equipment"), list) and prev_equip["safety_equipment"]:
                                        te = prev_equip.get("test_equipment") or []
                                        if not isinstance(te, list):
                                            te = []
                                        prev_equip["test_equipment"] = te + list(prev_equip["safety_equipment"])
                                        del prev_equip["safety_equipment"]
                                    if "rentals" not in st.session_state.equip or not isinstance(st.session_state.equip.get("rentals"), list):
                                        st.session_state.equip["rentals"] = []
                                    st.session_state.employees = draft.get("employees", [])
                                    st.session_state.current_draft_id = draft["id"]
                                    st.success("Report loaded.")
                                    st.rerun()
                        with del_col:
                            if st.button("🗑 Delete", key=f"report_del_{r['id']}", use_container_width=True):
                                if database.delete_report(r["id"], user_id):
                                    if st.session_state.current_draft_id == r["id"]:
                                        st.session_state.current_draft_id = None
                                    st.success("Report deleted.")
                                    st.rerun()
                                else:
                                    st.error("Could not delete report.")

        # Current (most recent) week at top
        first_week_mon = weeks_sorted[0]
        first_week_sun = first_week_mon + timedelta(days=6)
        st.caption(f"**Week of Mon {first_week_mon.strftime('%m/%d')} – Sun {first_week_sun.strftime('%m/%d')}**")
        render_report_list(by_week[first_week_mon])

        # Older weeks in a collapsed expander
        if len(weeks_sorted) > 1:
            with st.expander(f"📅 Previous weeks ({len(weeks_sorted) - 1} more)", expanded=False):
                for mon in weeks_sorted[1:]:
                    sun = mon + timedelta(days=6)
                    st.caption(f"**Week of Mon {mon.strftime('%m/%d')} – Sun {sun.strftime('%m/%d')}**")
                    render_report_list(by_week[mon])
    else:
        st.caption("No saved reports yet. Save the current form below to add one.")

    st.markdown("---")
    if st.button("💾 Save current report", type="primary", use_container_width=True, key="btn_save_report"):
        try:
            if st.session_state.current_draft_id:
                report_id = database.update_report(
                    st.session_state.current_draft_id,
                    user_id=user_id,
                    report_date=report_date,
                    state=state,
                    job_name=jobname,
                    job_number=jobnumber,
                    job_description=jobdescription,
                    work_performed_notes=work_performed_notes,
                    equipment_used=st.session_state.equip,
                    employees=st.session_state.employees,
                )
                if report_id is not None:
                    st.success("Report updated.")
                    st.rerun()
                else:
                    st.error("Could not update report (not found or access denied).")
            else:
                report_id = database.save_report(
                    user_id=user_id,
                    report_date=report_date,
                    state=state,
                    job_name=jobname,
                    job_number=jobnumber,
                    job_description=jobdescription,
                    work_performed_notes=work_performed_notes,
                    equipment_used=st.session_state.equip,
                    employees=st.session_state.employees,
                    is_draft=True
                )
                st.session_state.current_draft_id = report_id
                st.success("Report saved. It appears in the list above.")
                st.rerun()
        except Exception as e:
            st.error(f"Error saving: {str(e)}")

    # Create PDF of current report (one-time use)
    if st.button("📄 Create PDF of Current Report", type="primary", use_container_width=True, key="btn_create_current_pdf"):
        data = {
            "day": report_date.strftime("%A"),
            "date": report_date.strftime("%m/%d/%Y"),
            "ForemanReportNumber": foreman_report_number(report_date, jobnumber),
            "ILLINOIS": "X" if state == "ILLINOIS" else "",
            "INDIANA": "X" if state == "INDIANA" else "",
            "jobname": jobname,
            "jobnumber": jobnumber,
            "jobdescription": jobdescription,
            "WORK PERFORMED/NOTES": work_performed_notes,
            "equipmentused": build_equipment_used_string(st.session_state.equip),
        }
        for i, emp in enumerate(st.session_state.employees, start=1):
            if i > 13:
                break
            data[f"employee{i}name"] = emp.get("name", "")
            data[f"employee{i}craft"] = emp.get("craft", "")
            data[f"employee{i}st"] = f"{emp.get('st', 0.0):.1f}" if emp.get('st', 0.0) > 0 else ""
            data[f"employee{i}ot1.5"] = f"{emp.get('ot15', 0.0):.1f}" if emp.get('ot15', 0.0) > 0 else ""
            data[f"employee{i}otdt"] = f"{emp.get('otdt', 0.0):.1f}" if emp.get('otdt', 0.0) > 0 else ""
        date_str = report_date.strftime("%m-%d-%Y")
        job_safe = "".join(c for c in jobnumber.strip() if c.isalnum() or c in " -_").strip()
        filename = f"{date_str}_{job_safe}.pdf" if job_safe else f"{date_str}.pdf"
        output_file = "temp_filled_report.pdf"
        if fill_pdf("BlankForemanReport.pdf", output_file, data):
            try:
                report_id = database.save_report(
                    user_id=user_id,
                    report_date=report_date,
                    state=state,
                    job_name=jobname,
                    job_number=jobnumber,
                    job_description=jobdescription,
                    work_performed_notes=work_performed_notes,
                    equipment_used=st.session_state.equip,
                    employees=st.session_state.employees,
                    is_draft=False,
                    pdf_filename=filename
                )
                if st.session_state.current_draft_id:
                    database.update_report_draft_status(st.session_state.current_draft_id, user_id, False)
                    st.session_state.current_draft_id = None
                st.success(f"Report saved to database! (ID: {report_id})")
            except Exception as e:
                st.warning(f"PDF generated but error saving to database: {str(e)}")
            with open(output_file, "rb") as f:
                st.download_button(
                    label="📄 Download Filled PDF",
                    data=f,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success(f"PDF created. Download as: {filename}")
        else:
            st.error("Failed to fill PDF. Check that BlankForemanReport.pdf is in the same folder.")