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
# Authentication - Check if user is logged in
# ────────────────────────────────────────────────
auth.check_authentication()

# ────────────────────────────────────────────────
# Initialize session state
# ────────────────────────────────────────────────
if "employees" not in st.session_state:
    st.session_state.employees = []

if "equip" not in st.session_state:
    st.session_state.equip = {
        "service_truck_van": False, "foreman_truck": False,
        "welding_machine": False, "vacuum_pump": False,
        "four_gas_meter": False, "torch_setup": False,
        "orbital_welder": False, "pipe_machine": False,
        "pro_press_gun": False, "b_tank": False,
        "hot_tap_machine": False, "plasma_cutter": False,
        "hydro_pump": False, "martin_scissor": False,
        "nitrogen": False, "nitrogen_amount": "",
        "argon": False, "argon_amount": "",
        "rental1": False, "rental1_type": "",
        "rental2": False, "rental2_type": "",
        "rental3": False, "rental3_type": "",
        "other1": False, "other1_type": "",
        "other2": False, "other2_type": "",
    }

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

# Equipment section (unchanged) ...
st.markdown('<div class="small-font">', unsafe_allow_html=True)

st.header("Equipment Used Today")
st.write("Check if used today.")

colA, colB, colC = st.columns([1, 1, 1.75])

with colA:
    st.session_state.equip["service_truck_van"] = st.checkbox("SERVICE TRUCK/VAN", value=st.session_state.equip["service_truck_van"], key="chk_svc")
    st.session_state.equip["foreman_truck"]     = st.checkbox("FOREMAN TRUCK",     value=st.session_state.equip["foreman_truck"],     key="chk_foreman")
    st.session_state.equip["welding_machine"]   = st.checkbox("WELDING MACHINE",   value=st.session_state.equip["welding_machine"],   key="chk_weld")
    st.session_state.equip["vacuum_pump"]       = st.checkbox("VACUUM PUMP",       value=st.session_state.equip["vacuum_pump"],       key="chk_vac")
    st.session_state.equip["four_gas_meter"]    = st.checkbox("4 GAS METER",       value=st.session_state.equip["four_gas_meter"],    key="chk_4gas")
    st.session_state.equip["torch_setup"]       = st.checkbox("TORCH SET UP",      value=st.session_state.equip["torch_setup"],       key="chk_torch")
    st.session_state.equip["orbital_welder"]    = st.checkbox("ORBITAL WELDER",    value=st.session_state.equip["orbital_welder"],    key="chk_orbital")

with colB:
    st.session_state.equip["pipe_machine"]      = st.checkbox("PIPE MACHINE",      value=st.session_state.equip["pipe_machine"],      key="chk_pipe")
    st.session_state.equip["pro_press_gun"]     = st.checkbox("PRO PRESS GUN",     value=st.session_state.equip["pro_press_gun"],     key="chk_pro")
    st.session_state.equip["b_tank"]            = st.checkbox("B-TANK",            value=st.session_state.equip["b_tank"],            key="chk_btank")
    st.session_state.equip["hot_tap_machine"]   = st.checkbox("HOT TAP MACHINE",   value=st.session_state.equip["hot_tap_machine"],   key="chk_hot")
    st.session_state.equip["plasma_cutter"]     = st.checkbox("PLASMA CUTTER",     value=st.session_state.equip["plasma_cutter"],     key="chk_plasma")
    st.session_state.equip["hydro_pump"]        = st.checkbox("HYDRO PUMP",        value=st.session_state.equip["hydro_pump"],        key="chk_hydro")
    st.session_state.equip["martin_scissor"]    = st.checkbox("MARTIN SCISSOR LIFT", value=st.session_state.equip["martin_scissor"], key="chk_scissor")

with colC:
    ca, cb = st.columns([4, 6])
    st.session_state.equip["nitrogen"] = ca.checkbox("NITROGEN", value=st.session_state.equip["nitrogen"], key="chk_nitro")
    if st.session_state.equip["nitrogen"]:
        st.session_state.equip["nitrogen_amount"] = cb.text_input("Amt", value=st.session_state.equip["nitrogen_amount"], key="nitro_amt")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["argon"] = ca.checkbox("ARGON", value=st.session_state.equip["argon"], key="chk_argon")
    if st.session_state.equip["argon"]:
        st.session_state.equip["argon_amount"] = cb.text_input("Amt", value=st.session_state.equip["argon_amount"], key="argon_amt")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["rental1"] = ca.checkbox("Rental 1", value=st.session_state.equip["rental1"], key="chk_r1")
    if st.session_state.equip["rental1"]:
        st.session_state.equip["rental1_type"] = cb.text_input("Type", value=st.session_state.equip["rental1_type"], key="r1_type")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["rental2"] = ca.checkbox("Rental 2", value=st.session_state.equip["rental2"], key="chk_r2")
    if st.session_state.equip["rental2"]:
        st.session_state.equip["rental2_type"] = cb.text_input("Type", value=st.session_state.equip["rental2_type"], key="r2_type")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["rental3"] = ca.checkbox("Rental 3", value=st.session_state.equip["rental3"], key="chk_r3")
    if st.session_state.equip["rental3"]:
        st.session_state.equip["rental3_type"] = cb.text_input("Type", value=st.session_state.equip["rental3_type"], key="r3_type")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["other1"] = ca.checkbox("Other 1", value=st.session_state.equip["other1"], key="chk_o1")
    if st.session_state.equip["other1"]:
        st.session_state.equip["other1_type"] = cb.text_input("Type", value=st.session_state.equip["other1_type"], key="o1_type")

    ca, cb = st.columns([4, 6])
    st.session_state.equip["other2"] = ca.checkbox("Other 2", value=st.session_state.equip["other2"], key="chk_o2")
    if st.session_state.equip["other2"]:
        st.session_state.equip["other2_type"] = cb.text_input("Type", value=st.session_state.equip["other2_type"], key="o2_type")

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
            "SERVICE TRUCK/VAN": "X" if st.session_state.equip["service_truck_van"] else "",
            "FOREMAN TRUCK": "X" if st.session_state.equip["foreman_truck"] else "",
            "WELDING MACHINE": "X" if st.session_state.equip["welding_machine"] else "",
            "VACUUM PUMP": "X" if st.session_state.equip["vacuum_pump"] else "",
            "4 GAS METER": "X" if st.session_state.equip["four_gas_meter"] else "",
            "TORCH SET UP": "X" if st.session_state.equip["torch_setup"] else "",
            "ORBITAL WELDER": "X" if st.session_state.equip["orbital_welder"] else "",
            "PIPE MACHINE": "X" if st.session_state.equip["pipe_machine"] else "",
            "PRO PRESS GUN": "X" if st.session_state.equip["pro_press_gun"] else "",
            "B-TANK": "X" if st.session_state.equip["b_tank"] else "",
            "HOT TAP MACHINE": "X" if st.session_state.equip["hot_tap_machine"] else "",
            "PLASMA CUTTER": "X" if st.session_state.equip["plasma_cutter"] else "",
            "HYDRO PUMP": "X" if st.session_state.equip["hydro_pump"] else "",
            "MARTIN SCISSOR LIFT": "X" if st.session_state.equip["martin_scissor"] else "",
            "NITROGEN": "X" if st.session_state.equip["nitrogen"] else "",
            "NITROGEN AMOUNT": st.session_state.equip["nitrogen_amount"] if st.session_state.equip["nitrogen"] else "",
            "ARGON": "X" if st.session_state.equip["argon"] else "",
            "ARGON AMOUNT": st.session_state.equip["argon_amount"] if st.session_state.equip["argon"] else "",
            "rental1": "X" if st.session_state.equip["rental1"] else "",
            "rental1 type": st.session_state.equip["rental1_type"] if st.session_state.equip["rental1"] else "",
            "rental2": "X" if st.session_state.equip["rental2"] else "",
            "rental2 type": st.session_state.equip["rental2_type"] if st.session_state.equip["rental2"] else "",
            "rental3": "X" if st.session_state.equip["rental3"] else "",
            "rental3 type": st.session_state.equip["rental3_type"] if st.session_state.equip["rental3"] else "",
            "other1": "X" if st.session_state.equip["other1"] else "",
            "other1 type": st.session_state.equip["other1_type"] if st.session_state.equip["other1"] else "",
            "other2": "X" if st.session_state.equip["other2"] else "",
            "other2 type": st.session_state.equip["other2_type"] if st.session_state.equip["other2"] else "",
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

# ────────────────────────────────────────────────
# Weekly Report & Timesheet Generation (last step in workflow)
# ────────────────────────────────────────────────
st.markdown("---" * 2)
st.header("📅 Weekly Report & Timesheet Generation")
st.caption("Uses only the saved reports listed in **Save & Load Reports**. Save your reports first; only those whose date falls in the selected week are included.")

today = date.today()
days_until_sunday = (6 - today.weekday()) % 7
if days_until_sunday == 0 and today.weekday() != 6:
    days_until_sunday = 7
default_sunday = today + timedelta(days=days_until_sunday)

if "weekly_sunday_display" not in st.session_state:
    st.session_state.weekly_sunday_display = default_sunday

selected = st.date_input(
    "Select Week (Sunday)",
    value=st.session_state.weekly_sunday_display,
    format="MM/DD/YYYY",
    help="Pick any day in the week; it will use that week's Sunday (Mon–Sun).",
)
# Normalize to Sunday of that week (week = Mon–Sun) so the right week is always used
sunday_date = selected + timedelta(days=(6 - selected.weekday()) % 7)
st.session_state.weekly_sunday_display = sunday_date  # show Sunday in picker on next run
monday_date, week_end = get_week_dates(sunday_date)
st.caption(f"Week: {monday_date.strftime('%m/%d/%Y')} (Mon) - {week_end.strftime('%m/%d/%Y')} (Sun)")

if st.button("📄 Generate Weekly PDFs", type="primary", use_container_width=True, key="btn_weekly_pdf"):
    user_id = st.session_state.user_id
    saved_reports = database.get_user_reports(user_id, include_drafts=True)
    drafts = [r for r in saved_reports if r.get('is_draft', False)]
    week_reports = []
    for r in drafts:
        rd = r['report_date']
        if isinstance(rd, str):
            from datetime import datetime
            rd = datetime.strptime(rd, '%Y-%m-%d').date()
        if monday_date <= rd <= week_end:
            full = database.get_report(r['id'], user_id)
            if full:
                week_reports.append(full)
    if not week_reports:
        st.warning(
            f"No saved reports in the list fall in the week {monday_date.strftime('%m/%d/%Y')} - {week_end.strftime('%m/%d/%Y')}. "
            "Save reports (using Save current report) and ensure their dates are in this week."
        )
    else:
        st.info(f"Using {len(week_reports)} saved report(s) from the list for this week. Generating PDFs...")
        temp_files = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            status_text.text("Generating daily Foreman Reports...")
            for idx, report in enumerate(week_reports):
                report_date = report['report_date']
                if isinstance(report_date, str):
                    from datetime import datetime
                    report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
                data = {
                    "day": report_date.strftime("%A"),
                    "date": report_date.strftime("%m/%d/%Y"),
                    "ForemanReportNumber": foreman_report_number(report_date, report.get('job_number', '')),
                    "ILLINOIS": "X" if report.get('state') == "ILLINOIS" else "",
                    "INDIANA": "X" if report.get('state') == "INDIANA" else "",
                    "jobname": report.get('job_name', ''),
                    "jobnumber": report.get('job_number', ''),
                    "jobdescription": report.get('job_description', ''),
                    "WORK PERFORMED/NOTES": report.get('work_performed_notes', ''),
                }
                equip = report.get('equipment_used', {})
                data.update({
                    "SERVICE TRUCK/VAN": "X" if equip.get("service_truck_van") else "",
                    "FOREMAN TRUCK": "X" if equip.get("foreman_truck") else "",
                    "WELDING MACHINE": "X" if equip.get("welding_machine") else "",
                    "VACUUM PUMP": "X" if equip.get("vacuum_pump") else "",
                    "4 GAS METER": "X" if equip.get("four_gas_meter") else "",
                    "TORCH SET UP": "X" if equip.get("torch_setup") else "",
                    "ORBITAL WELDER": "X" if equip.get("orbital_welder") else "",
                    "PIPE MACHINE": "X" if equip.get("pipe_machine") else "",
                    "PRO PRESS GUN": "X" if equip.get("pro_press_gun") else "",
                    "B-TANK": "X" if equip.get("b_tank") else "",
                    "HOT TAP MACHINE": "X" if equip.get("hot_tap_machine") else "",
                    "PLASMA CUTTER": "X" if equip.get("plasma_cutter") else "",
                    "HYDRO PUMP": "X" if equip.get("hydro_pump") else "",
                    "MARTIN SCISSOR LIFT": "X" if equip.get("martin_scissor") else "",
                    "NITROGEN": "X" if equip.get("nitrogen") else "",
                    "NITROGEN AMOUNT": equip.get("nitrogen_amount", "") if equip.get("nitrogen") else "",
                    "ARGON": "X" if equip.get("argon") else "",
                    "ARGON AMOUNT": equip.get("argon_amount", "") if equip.get("argon") else "",
                    "rental1": "X" if equip.get("rental1") else "",
                    "rental1 type": equip.get("rental1_type", "") if equip.get("rental1") else "",
                    "rental2": "X" if equip.get("rental2") else "",
                    "rental2 type": equip.get("rental2_type", "") if equip.get("rental2") else "",
                    "rental3": "X" if equip.get("rental3") else "",
                    "rental3 type": equip.get("rental3_type", "") if equip.get("rental3") else "",
                    "other1": "X" if equip.get("other1") else "",
                    "other1 type": equip.get("other1_type", "") if equip.get("other1") else "",
                    "other2": "X" if equip.get("other2") else "",
                    "other2 type": equip.get("other2_type", "") if equip.get("other2") else "",
                })
                employees = report.get('employees', [])
                for i, emp in enumerate(employees, start=1):
                    if i > 13:
                        break
                    data[f"employee{i}name"] = emp.get("name", "")
                    data[f"employee{i}craft"] = emp.get("craft", "")
                    data[f"employee{i}st"] = f"{emp.get('st', 0.0):.1f}" if emp.get('st', 0.0) > 0 else ""
                    data[f"employee{i}ot1.5"] = f"{emp.get('ot15', 0.0):.1f}" if emp.get('ot15', 0.0) > 0 else ""
                    data[f"employee{i}otdt"] = f"{emp.get('otdt', 0.0):.1f}" if emp.get('otdt', 0.0) > 0 else ""
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.close()
                if fill_pdf("BlankForemanReport.pdf", temp_file.name, data):
                    temp_files.append(temp_file.name)
                progress_bar.progress((idx + 1) / (len(week_reports) + 1))
            status_text.text("Generating employee Timesheets...")
            unique_employees_set = set()
            for report in week_reports:
                for emp in report.get('employees', []):
                    name = (emp.get('name') or '').strip()
                    if name:
                        unique_employees_set.add(name)
            unique_employees = sorted(unique_employees_set)

            def get_employee_timesheet_from_reports(emp_name, reports):
                entries = []
                for report in reports:
                    for emp in report.get('employees', []):
                        if (emp.get('name') or '').strip() != emp_name:
                            continue
                        rd = report.get('report_date')
                        if isinstance(rd, str):
                            from datetime import datetime
                            rd = datetime.strptime(rd, '%Y-%m-%d').date()
                        entries.append({
                            'report_date': rd,
                            'job_number': report.get('job_number', ''),
                            'job_name': report.get('job_name', ''),
                            'job_description': report.get('job_description', ''),
                            'craft': emp.get('craft', ''),
                            'straight_time': float(emp.get('st', 0.0)),
                            'overtime_15': float(emp.get('ot15', 0.0)),
                            'double_time': float(emp.get('otdt', 0.0)),
                        })
                return entries

            if unique_employees:
                week_dates = [monday_date + timedelta(days=i) for i in range(7)]
                day_names = ['mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun']
                for emp_idx, emp_name in enumerate(unique_employees):
                    emp_data = get_employee_timesheet_from_reports(emp_name, week_reports)
                    jobs_dict = {}
                    for entry in emp_data:
                        job_num = entry.get('job_number', '')
                        if job_num not in jobs_dict:
                            jobs_dict[job_num] = {
                                'job_name': entry.get('job_name', ''),
                                'job_number': job_num,
                                'job_description': entry.get('job_description', ''),
                                'craft': entry.get('craft', ''),
                                'entries': []
                            }
                        jobs_dict[job_num]['entries'].append(entry)
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
                        timesheet_data[f"{job_num}_name"] = job['job_name']
                        timesheet_data[f"{job_num}_job_number"] = job['job_number']
                        timesheet_data[f"{job_num}_description"] = job['job_description']
                        timesheet_data[f"{job_num}_craft"] = job['craft']
                        job_st_total = job_ot15_total = job_dt_total = 0.0
                        hours_by_date = {}
                        for entry in job['entries']:
                            entry_date = entry.get('report_date')
                            if isinstance(entry_date, str):
                                from datetime import datetime
                                entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
                            day_idx = (entry_date - monday_date).days
                            if 0 <= day_idx < 7:
                                day_key = day_names[day_idx]
                                if day_key not in hours_by_date:
                                    hours_by_date[day_key] = {'st': 0.0, 'ot15': 0.0, 'dt': 0.0}
                                hours_by_date[day_key]['st'] += float(entry.get('straight_time', 0.0))
                                hours_by_date[day_key]['ot15'] += float(entry.get('overtime_15', 0.0))
                                hours_by_date[day_key]['dt'] += float(entry.get('double_time', 0.0))
                        for day_idx, day_name in enumerate(day_names):
                            day_hours = hours_by_date.get(day_name, {'st': 0.0, 'ot15': 0.0, 'dt': 0.0})
                            st_val = f"{day_hours['st']:.1f}" if day_hours['st'] > 0 else ""
                            ot15_val = f"{day_hours['ot15']:.1f}" if day_hours['ot15'] > 0 else ""
                            dt_val = f"{day_hours['dt']:.1f}" if day_hours['dt'] > 0 else ""
                            timesheet_data[f"{job_num}_{day_name}_st"] = st_val
                            timesheet_data[f"{job_num}_{day_name}_1.5"] = ot15_val
                            timesheet_data[f"{job_num}_{day_name}_dt"] = dt_val
                            job_st_total += day_hours['st']
                            job_ot15_total += day_hours['ot15']
                            job_dt_total += day_hours['dt']
                        timesheet_data[f"{job_num}_st_total"] = f"{job_st_total:.1f}" if job_st_total > 0 else ""
                        timesheet_data[f"{job_num}_1.5_total"] = f"{job_ot15_total:.1f}" if job_ot15_total > 0 else ""
                        timesheet_data[f"{job_num}_dt_total"] = f"{job_dt_total:.1f}" if job_dt_total > 0 else ""
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.close()
                    if fill_pdf("Blank Time.pdf", temp_file.name, timesheet_data):
                        temp_files.append(temp_file.name)
                    progress_bar.progress((len(week_reports) + emp_idx + 1) / (len(week_reports) + len(unique_employees)))
            status_text.text("Merging PDFs...")
            if temp_files:
                merged_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
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
                            use_container_width=True
                        )
                    st.success(f"✅ Generated {len(week_reports)} Foreman Report(s) and {len(unique_employees)} Timesheet(s)")
                    for temp_file in temp_files:
                        try:
                            os.unlink(temp_file)
                        except:
                            pass
                    try:
                        os.unlink(merged_output.name)
                    except:
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