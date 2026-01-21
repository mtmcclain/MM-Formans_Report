import streamlit as st
import openpyxl
import pandas as pd
import tempfile
import os
from io import BytesIO
from datetime import date, datetime

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
    # Your existing employee code here (keep it as-is)

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
        argon = st.checkbox("ARGON")
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

    if st.button("Generate PDF Report", type="primary"):
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 1cm; font-size: 12pt; }}
                h1 {{ text-align: center; margin-bottom: 10px; }}
                .header {{ margin-bottom: 15px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid black; padding: 6px; text-align: left; }}
                .equipment-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }}
            </style>
        </head>
        <body>
            <h1>FOREMAN'S DAILY REPORT - {work_state}</h1>
            <div class="header">
                <p><strong>Date:</strong> {report_date.strftime("%m/%d/%Y")} ({day_name})</p>
                <p><strong>Job Name:</strong> {job_name or 'N/A'}</p>
                <p><strong>Job Number:</strong> {job_number or 'N/A'}</p>
                <p><strong>Description:</strong> {description or ''}</p>
            </div>

            <h2>Employees</h2>
            <table>
                <tr><th>Name</th><th>Craft</th><th>ST</th><th>x1.5</th><th>x2</th></tr>
        """

        for emp in st.session_state.employees:
            html += f"<tr><td>{emp['name']}</td><td>{emp['craft']}</td><td>{emp['st']}</td><td>{emp['one5']}</td><td>{emp['dt']}</td></tr>"

        html += """
            </table>

            <h2>Work Performed / Notes</h2>
            <p style="white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; min-height: 100px;">{work_notes or 'None'}</p>

            <h2>Equipment Used Today</h2>
            <div class="equipment-grid">
        """

        equipment = [
            ("SERVICE TRUCK/VAN", svc_truck), ("FOREMAN TRUCK", frm_truck), ("WELDING MACHINE", weld_mach),
            ("VACUUM PUMP", vac_pump), ("4 GAS METER", gas_meter), ("TORCH SET UP", torch), ("ORBITAL WELDER", orbital),
            ("PIPE MACHINE", pipe_mach), ("PRO PRESS GUN", pro_press), ("B-TANK", b_tank),
            ("HOT TAP MACHINE", hot_tap), ("PLASMA CUTTER", plasma), ("HYDRO PUMP", hydro), ("MARTIN SCISSOR LIFT", scissor),
            ("NITROGEN", nitro), ("ARGON", argon_gas)
        ]

        for name, checked in equipment:
            html += f"<div>{'X' if checked else ''} {name}</div>"

        html += f"""
            </div>
            <div style="margin-top: 20px;">
                <p><strong>Rental 1:</strong> {rent1_type if rent1 else ''}</p>
                <p><strong>Rental 2:</strong> {rent2_type if rent2 else ''}</p>
                <p><strong>Rental 3:</strong> {rent3_type if rent3 else ''}</p>
                <p><strong>Other 1:</strong> {oth1_type if oth1 else ''}</p>
                <p><strong>Other 2:</strong> {oth2_type if oth2 else ''}</p>
            </div>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html).write_pdf()

        filename = f"{job_name or 'Report'}_{job_number or ''}_{report_date.strftime('%Y-%m-%d')}.pdf"

        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf"
        )

# ─── WEEKLY TIMESHEET ───────────────────────────────────────────────────────
with tab2:
    st.header("Weekly Per Employee Timesheet")
    st.info("We'll build this after the Foreman's Report is done.")

st.markdown("---")
st.caption("Make sure EmployeeNames.xlsx and BlankForemanReport.xlsx are in the same folder.")



