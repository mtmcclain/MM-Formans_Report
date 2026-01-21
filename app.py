import streamlit as st
import openpyxl
import pandas as pd
import tempfile
import os
from io import BytesIO
from datetime import date, datetime
import subprocess  # For LibreOffice conversion

# ─── Load the employee master list ──────────────────────────────────────────
try:
    df_employees = pd.read_excel("EmployeeNames.xlsx")
    employee_list = df_employees["Employee Name"].tolist()
    craft_dict = dict(zip(df_employees["Employee Name"], df_employees["Craft"]))
except Exception as e:
    st.error(f"Could not load EmployeeNames.xlsx!\nError: {e}")
    st.stop()

st.title("Pipefitting Contractor Report Automation")

tab1, tab2 = st.tabs(["Daily Foreman's Report", "Weekly Timesheet"])

# ─── DAILY FOREMAN'S REPORT ─────────────────────────────────────────────────
with tab1:
    st.markdown("""
    **MARTIN MECHANICAL CORPORATION**  
    1419 Junction Ave, Schererville, IN 46375  
    Phone: 219-322-7333 / Fax: 219-322-7337  
    martinmech@martin-mech.com  
    """)

    st.header("FOREMAN'S DAILY REPORT")

    col_state1, col_state2 = st.columns(2)
    with col_state1:
        indiana = st.checkbox("Indiana", key="indiana_chk")
    with col_state2:
        illinois = st.checkbox("Illinois", key="illinois_chk")

    # Enforce only one checked
    if indiana and illinois:
        st.session_state.illinois_chk = False
        illinois = False
    if not indiana and not illinois:
        st.info("Please select one state.")

    # Calculate work_state based on checkboxes (fix: define it here)
    if indiana:
        work_state = "Indiana"
    elif illinois:
        work_state = "Illinois"
    else:
        work_state = None

    date_col, day_col = st.columns(2)
    with date_col:
        report_date = st.date_input("DATE:", value=date.today())
    with day_col:
        day_name = datetime.combine(report_date, datetime.min.time()).strftime("%A")
        st.text_input("DAY:", value=day_name, disabled=True)

    job_name = st.text_input("JOB NAME:")
    job_number = st.text_input("JOB NUMBER:")
    description = st.text_input("DESCRIPTION:")

    st.subheader("Employees")
    # Initialize employees list in session state if not present
    if 'employees' not in st.session_state:
        st.session_state.employees = []

    # Form to add a new employee
    with st.expander("Add Employee"):
        selected_name = st.selectbox("Employee Name", [""] + employee_list)  # Blank to avoid auto-select
        if selected_name:
            craft = craft_dict.get(selected_name, "Unknown")
            st.text_input("Craft:", value=craft, disabled=True)  # Show auto-filled
            st_val = st.number_input("Straight Time (ST)", min_value=0.0, value=8.0, step=0.5)
            one5_val = st.number_input("x1.5 OT", min_value=0.0, value=0.0, step=0.5)
            dt_val = st.number_input("x2 OT", min_value=0.0, value=0.0, step=0.5)
            if st.button("Add Employee"):
                if selected_name:
                    st.session_state.employees.append({
                        "name": selected_name,
                        "craft": craft,
                        "st": st_val,
                        "one5": one5_val,
                        "dt": dt_val
                    })
                    st.success(f"Added {selected_name}")

    # Display current employees with remove option
    if st.session_state.employees:
        for i, emp in enumerate(st.session_state.employees):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{emp['name']} ({emp['craft']}): ST={emp['st']}, x1.5={emp['one5']}, x2={emp['dt']}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    del st.session_state.employees[i]
                    st.rerun()  # Refresh to update list

    st.subheader("Work Performed / Notes")
    work_notes = st.text_area("", height=200, placeholder="Enter notes here...")

    st.subheader("EQUIPMENT USED TODAY")
    col1, col2, col3 = st.columns(3)

    with col1:
        svc_truck = st.checkbox("SERVICE TRUCK/VAN")
        frm_truck = st.checkbox("FOREMAN TRUCK")
        weld_mach = st.checkbox("WELDING MACHINE")
        vac_pump = st.checkbox("VACUUM PUMP")
        gas_meter = st.checkbox("4 GAS METER")
        torch = st.checkbox("TORCH SET UP")
        orbital = st.checkbox("ORBITAL WELDER")

    with col2:
        pipe_mach = st.checkbox("PIPE MACHINE")
        pro_press = st.checkbox("PRO PRESS GUN")
        b_tank = st.checkbox("B-TANK")
        hot_tap = st.checkbox("HOT TAP MACHINE")
        plasma = st.checkbox("PLASMA CUTTER")
        hydro = st.checkbox("HYDRO PUMP")
        scissor = st.checkbox("MARTIN SCISSOR LIFT")

    with col3:
        nitro = st.checkbox("NITROGEN")
        argon = st.checkbox("ARGON")  # Fix: consistent name
        rent1 = st.checkbox("RENTAL 1")
        rent1_type = st.text_input("Type", key="rent1_type") if rent1 else ""
        rent2 = st.checkbox("RENTAL 2")
        rent2_type = st.text_input("Type", key="rent2_type") if rent2 else ""
        rent3 = st.checkbox("RENTAL 3")
        rent3_type = st.text_input("Type", key="rent3_type") if rent3 else ""
        oth1 = st.checkbox("OTHER 1")
        oth1_type = st.text_input("Type", key="oth1_type") if oth1 else ""
        oth2 = st.checkbox("OTHER 2")
        oth2_type = st.text_input("Type", key="oth2_type") if oth2 else ""

    if st.button("Generate Foreman's Report", type="primary"):
        if not work_state:
            st.error("Please select a state (Indiana or Illinois).")
        elif not st.session_state.employees:
            st.error("Please add at least one employee.")
        else:
            try:
                # Load and fill the Excel template
                wb = openpyxl.load_workbook("BlankForemanReport.xlsx")
                sheet = wb["FormansReport"]

                sheet["F3"] = day_name
                sheet["F4"] = report_date.strftime("%m/%d/%Y")
                sheet["F5"] = job_name
                sheet["F6"] = job_number
                sheet["F7"] = description

                # State: Put in J4 or J5 (based on template)
                if work_state == "Indiana":
                    sheet["J5"] = "INDIANA"
                    sheet["J4"] = ""
                elif work_state == "Illinois":
                    sheet["J4"] = "ILLINOIS"
                    sheet["J5"] = ""

                # Fill employees starting at row 10
                start_row = 10
                for idx, emp in enumerate(st.session_state.employees):
                    row = start_row + idx
                    sheet.cell(row=row, column=1).value = emp["name"]
                    sheet.cell(row=row, column=8).value = emp["craft"]
                    sheet.cell(row=row, column=9).value = emp["st"]
                    sheet.cell(row=row, column=10).value = emp["one5"]
                    sheet.cell(row=row, column=11).value = emp["dt"]

                # Work notes
                sheet["A24"] = work_notes
                sheet["A24"].alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
                sheet.row_dimensions[24].height = 140  # Adjust height for notes

                # Equipment: Mark "X" in specific cells (adjust if template columns are off; A for left, D for middle, G for right)
                def mark(cell, used):
                    sheet[cell] = "X" if used else ""

                mark("A39", svc_truck)
                mark("A40", frm_truck)
                mark("A41", weld_mach)
                mark("A42", vac_pump)
                mark("A43", gas_meter)
                mark("A44", torch)
                mark("A45", orbital)
                mark("D39", pipe_mach)
                mark("D40", pro_press)
                mark("D41", b_tank)
                mark("D42", hot_tap)
                mark("D43", plasma)
                mark("D44", hydro)
                mark("D45", scissor)
                mark("G39", nitro)
                mark("G40", argon)  # Fix: use argon

                # Rental/Other types (no "X", just types)
                sheet["G41"] = rent1_type if rent1 else ""
                sheet["G42"] = rent2_type if rent2 else ""
                sheet["G43"] = rent3_type if rent3 else ""
                sheet["G44"] = oth1_type if oth1 else ""
                sheet["G45"] = oth2_type if oth2 else ""

                # Now, save filled Excel to temp file and convert to PDF using LibreOffice
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_xlsx:
                    wb.save(tmp_xlsx.name)
                    tmp_xlsx_path = tmp_xlsx.name

                # Convert to PDF (output to same dir)
                pdf_dir = os.path.dirname(tmp_xlsx_path)
                subprocess.run([
                    'soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', pdf_dir, tmp_xlsx_path
                ], check=True)

                # Get PDF path (same name but .pdf)
                pdf_path = tmp_xlsx_path.replace(".xlsx", ".pdf")
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                # Clean up temp files
                os.unlink(tmp_xlsx_path)
                os.unlink(pdf_path)

                # Filename for download
                job_name_clean = (job_name or "NoJobName").strip().replace(" ", "_").replace("/", "-")[:30]
                job_num_clean = (job_number or "NoJobNum").strip().replace(" ", "_").replace("/", "-")[:15]
                filename = f"{job_name_clean}_{job_num_clean}_{report_date.strftime('%Y-%m-%d')}.pdf"

                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    key="pdf_dl"
                )

                st.success("PDF generated! Download above.")

            except FileNotFoundError:
                st.error("BlankForemanReport.xlsx not found! Make sure it's in your repo.")
            except subprocess.CalledProcessError:
                st.error("PDF conversion failed. Check if LibreOffice is installed (via packages.txt).")
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

# ─── WEEKLY TIMESHEET ───────────────────────────────────────────────────────
with tab2:
    st.header("Weekly Per Employee Timesheet")
    st.info("We'll build this after the Foreman's Report is done.")

st.markdown("---")
st.caption("Make sure EmployeeNames.xlsx and BlankForemanReport.xlsx are in the same folder.")
