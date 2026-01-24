import streamlit as st
from datetime import date
import fitz  # PyMuPDF

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

# ────────────────────────────────────────────────
# Main app layout
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# White container with logo on left + title on right
# ────────────────────────────────────────────────

with st.container():
    st.markdown('<div class="white-card">', unsafe_allow_html=True)

    cols = st.columns([1, 4])   # left column small (logo), right column bigger (text)

    with cols[0]:
        st.image("Martin LOGO.png", width=250)

    with cols[1]:
        st.markdown("<h1 style='margin-top: 0;'>Foreman's Daily Report</h1>", unsafe_allow_html=True)

report_date = st.date_input(
    "Date",
    value=date.today(),
    format="MM/DD/YYYY"   # picker shows 01/23/2026 style
)

state = st.radio("State", ["ILLINOIS", "INDIANA"], index=1, horizontal=True)

jobname        = st.text_input("Job Name")
jobnumber      = st.text_input("Job Number")
jobdescription = st.text_input("Job Description")

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

        if cols[5].button("🗑", key=f"del_{idx}"):
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
work_performed_notes = st.text_area("Enter details here (multiline)", height=180, key="notes")

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
# PDF generation
# ────────────────────────────────────────────────
st.markdown("---" * 3)

if st.button("Create & Download PDF", type="primary", use_container_width=True):
    
    data = {
        "day": report_date.strftime("%A"),
        "date": report_date.strftime("%m/%d/%Y"),   # ← using slashes here for the PDF field
        "ILLINOIS": "X" if state == "ILLINOIS" else "",
        "INDIANA": "X" if state == "INDIANA" else "",
        "jobname": jobname,
        "jobnumber": jobnumber,
        "jobdescription": jobdescription,
        "WORK PERFORMED/NOTES": work_performed_notes,

        # Equipment checkboxes ...
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

    # Employees
    for i, emp in enumerate(st.session_state.employees, start=1):
        if i > 13: break
        data[f"employee{i}name"]  = emp.get("name", "")
        data[f"employee{i}craft"] = emp.get("craft", "")
        data[f"employee{i}st"]     = f"{emp.get('st',   0.0):.1f}" if emp.get('st',   0.0) > 0 else ""
        data[f"employee{i}ot1.5"]  = f"{emp.get('ot15', 0.0):.1f}" if emp.get('ot15', 0.0) > 0 else ""
        data[f"employee{i}otdt"]   = f"{emp.get('otdt', 0.0):.1f}" if emp.get('otdt', 0.0) > 0 else ""

       # ── Dynamic filename ──
    date_str = report_date.strftime("%m-%d-%Y")   # MM-DD-YYYY
    job_safe = "".join(c for c in jobnumber.strip() if c.isalnum() or c in " -_").strip()
    if job_safe:
        filename = f"{date_str}_{job_safe}.pdf"
    else:
        filename = f"{date_str}.pdf"

    output_file = "temp_filled_report.pdf"

    if fill_pdf("BlankForemanReport.pdf", output_file, data):
        with open(output_file, "rb") as f:
            st.download_button(
                label="📄 Download Filled PDF",
                data=f,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
        st.success(f"PDF created successfully!\nDownloaded as: {filename}")
    else:
        st.error("Failed to fill PDF. Check that BlankForemanReport.pdf is in the same folder.")