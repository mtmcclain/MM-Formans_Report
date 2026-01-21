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

    if st.button("Generate Foreman's Report", type="primary"):
        try:
            # Make sure work_state is saved to session state
            st.session_state.work_state = work_state

            wb = openpyxl.load_workbook("BlankForemanReport.xlsx")
            sheet = wb["FormansReport"]

            sheet["F3"] = day_name
            sheet["F4"] = report_date.strftime("%m/%d/%Y")
            sheet["F5"] = job_name
            sheet["F6"] = job_number
            sheet["F7"] = description

            if st.session_state.work_state == "Indiana":
                sheet["J5"] = "INDIANA"
                sheet["J4"] = ""
            elif st.session_state.work_state == "Illinois":
                sheet["J4"] = "ILLINOIS"
                sheet["J5"] = ""

            start_row = 10
            for idx, emp in enumerate(st.session_state.employees):
                row = start_row + idx
                sheet.cell(row=row, column=1).value = emp["name"]
                sheet.cell(row=row, column=8).value = emp["craft"]
                sheet.cell(row=row, column=9).value = emp["st"]
                sheet.cell(row=row, column=10).value = emp["one5"]
                sheet.cell(row=row, column=11).value = emp["dt"]

            sheet["A24"] = work_notes
            sheet["A24"].alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
            sheet.row_dimensions[24].height = 140

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
            mark("G40", argon_gas)

            sheet["G41"] = rent1_type if rent1 else ""
            sheet["G42"] = rent2_type if rent2 else ""
            sheet["G43"] = rent3_type if rent3 else ""
            sheet["G44"] = oth1_type if oth1 else ""
            sheet["G45"] = oth2_type if oth2 else ""

            # Basic PDF with WeasyPrint
            from weasyprint import HTML
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ text-align: center; }}
                    .section {{ margin-bottom: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Foreman's Daily Report - {st.session_state.work_state}</h1>
                
                <div class="section">
                    <p><strong>Date:</strong> {report_date.strftime("%m/%d/%Y")} ({day_name})</p>
                    <p><strong>Job Name:</strong> {job_name or 'N/A'}</p>
                    <p><strong>Job Number:</strong> {job_number or 'N/A'}</p>
                    <p><strong>Description:</strong> {description or ''}</p>
                </div>

                <div class="section">
                    <h2>Employees</h2>
                    <table>
                        <tr><th>Name</th><th>Craft</th><th>ST</th><th>x1.5 OT</th><th>x2 OT</th></tr>
            """

            for emp in st.session_state.employees:
                html_content += f"""
                        <tr>
                            <td>{emp['name']}</td>
                            <td>{emp['craft']}</td>
                            <td>{emp['st']}</td>
                            <td>{emp['one5']}</td>
                            <td>{emp['dt']}</td>
                        </tr>
                """

            html_content += """
                    </table>
                </div>

                <div class="section">
                    <h2>Work Performed / Notes</h2>
                    <p style="white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; min-height: 100px;">{work_notes or 'None'}</p>
                </div>

                <div class="section">
                    <h2>Equipment Used Today</h2>
                    <p>Service Truck/Van: {'X' if svc_truck else ''}</p>
                    <p>Foreman Truck: {'X' if frm_truck else ''}</p>
                    <!-- Add more equipment lines as needed -->
                </div>
            </body>
            </html>
            """

            pdf_bytes = HTML(string=html_content).write_pdf()

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
            st.error("BlankForemanReport.xlsx not found in the folder!")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
# ─── WEEKLY TIMESHEET ───────────────────────────────────────────────────────
with tab2:
    st.header("Weekly Per Employee Timesheet")
    st.info("We'll build this after the Foreman's Report is done.")

st.markdown("---")
st.caption("Make sure EmployeeNames.xlsx and BlankForemanReport.xlsx are in the same folder.")




