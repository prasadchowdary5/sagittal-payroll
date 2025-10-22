import streamlit as st
import pandas as pd
import json
import datetime
import os
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(
    page_title="Payroll Management System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .salary-slip {
        border: 2px solid #1f77b4;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    .rupee-symbol {
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


class PayrollSystem:
    def __init__(self):
        self.employees_file = "employees.json"
        self.attendance_file = "attendance.json"
        self.load_data()

    def load_data(self):
        """Load employee and attendance data from JSON files"""
        # Initialize files if they don't exist
        if not os.path.exists(self.employees_file):
            with open(self.employees_file, 'w') as f:
                json.dump({"employees": []}, f)

        if not os.path.exists(self.attendance_file):
            with open(self.attendance_file, 'w') as f:
                json.dump({"attendance_records": []}, f)

        with open(self.employees_file, 'r') as f:
            self.employees_data = json.load(f)

        with open(self.attendance_file, 'r') as f:
            self.attendance_data = json.load(f)

    def save_employees(self):
        """Save employee data to JSON file"""
        with open(self.employees_file, 'w') as f:
            json.dump(self.employees_data, f, indent=2)

    def save_attendance(self):
        """Save attendance data to JSON file"""
        with open(self.attendance_file, 'w') as f:
            json.dump(self.attendance_data, f, indent=2)

    def add_employee(self, employee_data):
        """Add a new employee to the system"""
        self.employees_data["employees"].append(employee_data)
        self.save_employees()

    def get_employee(self, employee_id):
        """Get employee by ID"""
        for emp in self.employees_data["employees"]:
            if emp["employee_id"] == employee_id:
                return emp
        return None

    def record_attendance(self, attendance_data):
        """Record attendance for an employee"""
        self.attendance_data["attendance_records"].append(attendance_data)
        self.save_attendance()

    def calculate_salary(self, employee_id, month, year):
        """Calculate salary for an employee for a specific month"""
        employee = self.get_employee(employee_id)
        if not employee:
            return None

        # Filter attendance records for the specified month
        monthly_records = [
            record for record in self.attendance_data["attendance_records"]
            if (record["employee_id"] == employee_id and
                record["date"].startswith(f"{year}-{month:02d}"))
        ]

        # Calculate working days
        working_days = len(monthly_records)

        # Calculate basic salary (pro-rated for working days)
        daily_rate = employee["basic_salary"] / 30  # Assuming 30 days in month
        basic_salary = daily_rate * working_days

        # Calculate overtime pay if overtime is applicable
        overtime_pay = 0
        total_overtime_hours = 0

        if employee.get("overtime_applicable", False):
            total_overtime_hours = sum(record.get("overtime_hours", 0) for record in monthly_records)
            overtime_pay = total_overtime_hours * employee["overtime_rate"]

        # Calculate gross salary
        gross_salary = basic_salary + overtime_pay

        # Calculate net salary (no deductions)
        net_salary = gross_salary

        return {
            "employee": employee,
            "working_days": working_days,
            "total_overtime_hours": total_overtime_hours,
            "basic_salary": basic_salary,
            "overtime_pay": overtime_pay,
            "gross_salary": gross_salary,
            "net_salary": net_salary,
            "month": month,
            "year": year
        }


def main():
    st.markdown('<div class="main-header">🏗️ Sagittal Payroll Management System</div>', unsafe_allow_html=True)

    # Initialize payroll system
    payroll = PayrollSystem()

    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            "Main Menu",
            ["Dashboard", "Employee Management", "Attendance", "Salary Processing", "Reports", "Settings"],
            icons=["speedometer", "people", "calendar-check", "cash-coin", "graph-up", "gear"],
            menu_icon="cast",
            default_index=0,
        )

    # Dashboard
    if selected == "Dashboard":
        display_dashboard(payroll)

    # Employee Management
    elif selected == "Employee Management":
        display_employee_management(payroll)

    # Attendance
    elif selected == "Attendance":
        display_attendance(payroll)

    # Salary Processing
    elif selected == "Salary Processing":
        display_salary_processing(payroll)

    # Reports
    elif selected == "Reports":
        display_reports(payroll)

    # Settings
    elif selected == "Settings":
        display_settings(payroll)


def display_dashboard(payroll):
    st.header("📊 Dashboard")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    total_employees = len(payroll.employees_data["employees"])
    active_employees = len([emp for emp in payroll.employees_data["employees"] if emp["status"] == "active"])

    with col1:
        st.metric("Total Employees", total_employees)

    with col2:
        st.metric("Active Employees", active_employees)

    with col3:
        # Calculate total payroll for current month
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        total_payroll = 0

        for emp in payroll.employees_data["employees"]:
            if emp["status"] == "active":
                salary_data = payroll.calculate_salary(emp["employee_id"], current_month, current_year)
                if salary_data:
                    total_payroll += salary_data["net_salary"]

        st.metric("Monthly Payroll", f"₹{total_payroll:,.2f}")

    with col4:
        # Calculate average attendance
        if payroll.attendance_data["attendance_records"]:
            avg_attendance = len(payroll.attendance_data["attendance_records"]) / total_employees
            st.metric("Avg Attendance", f"{avg_attendance:.1f} days")
        else:
            st.metric("Avg Attendance", "0 days")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        # Department distribution
        departments = {}
        for emp in payroll.employees_data["employees"]:
            dept = emp["department"]
            departments[dept] = departments.get(dept, 0) + 1

        if departments:
            fig = px.pie(
                values=list(departments.values()),
                names=list(departments.keys()),
                title="Employee Distribution by Department"
            )
            st.plotly_chart(fig)

    with col2:
        # Salary distribution
        if payroll.employees_data["employees"]:
            salaries = [emp["basic_salary"] for emp in payroll.employees_data["employees"]]
            fig = px.histogram(
                x=salaries,
                title="Salary Distribution",
                labels={"x": "Basic Salary (₹)", "y": "Count"}
            )
            st.plotly_chart(fig)


def display_employee_management(payroll):
    st.header("👥 Employee Management")

    tab1, tab2, tab3, tab4 = st.tabs(["Add Employee", "View Employees", "Edit Employee", "Bulk Upload"])

    with tab1:
        st.subheader("Add New Employee")

        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)

            with col1:
                employee_id = st.text_input("Employee ID*")
                name = st.text_input("Full Name*")
                phone = st.text_input("Phone*")
                department = st.selectbox("Department*", ["Construction", "Management", "Administration", "Logistics"])

            with col2:
                position = st.text_input("Position*")
                basic_salary = st.number_input("Basic Salary (₹)*", min_value=0, step=1000)
                overtime_applicable = st.checkbox("Overtime Applicable", value=False)

                if overtime_applicable:
                    overtime_rate = st.number_input("Overtime Rate (₹ per hour)*", min_value=0.0, step=10.0)
                else:
                    overtime_rate = 0.0

            st.subheader("Bank Details")
            col3, col4, col5 = st.columns(3)
            with col3:
                bank_account_number = st.text_input("Bank Account Number*")
            with col4:
                ifsc_code = st.text_input("IFSC Code*")
            with col5:
                branch_name = st.text_input("Branch Name*")

            joining_date = st.date_input("Joining Date")

            submitted = st.form_submit_button("Add Employee")

            if submitted:
                if not all([employee_id, name, phone, department, position, basic_salary,
                            bank_account_number, ifsc_code, branch_name]):
                    st.error("Please fill all required fields (*)")
                else:
                    employee_data = {
                        "employee_id": employee_id,
                        "name": name,
                        "phone": phone,
                        "department": department,
                        "position": position,
                        "basic_salary": basic_salary,
                        "overtime_applicable": overtime_applicable,
                        "overtime_rate": overtime_rate,
                        "bank_account_number": bank_account_number,
                        "ifsc_code": ifsc_code,
                        "branch_name": branch_name,
                        "joining_date": str(joining_date),
                        "status": "active"
                    }

                    payroll.add_employee(employee_data)
                    st.success(f"Employee {name} added successfully!")

    with tab2:
        st.subheader("Employee List")

        if payroll.employees_data["employees"]:
            # Create a simplified dataframe for display
            display_data = []
            for emp in payroll.employees_data["employees"]:
                display_data.append({
                    "Employee ID": emp["employee_id"],
                    "Name": emp["name"],
                    "Phone": emp["phone"],
                    "Department": emp["department"],
                    "Position": emp["position"],
                    "Basic Salary": f"₹{emp['basic_salary']:,.2f}",
                    "Overtime Applicable": "Yes" if emp.get("overtime_applicable", False) else "No",
                    "Status": emp["status"]
                })

            employees_df = pd.DataFrame(display_data)
            st.dataframe(employees_df, use_container_width=True)
        else:
            st.info("No employees found. Add some employees to get started.")

    with tab3:
        st.subheader("Edit Employee")

        employee_options = [f"{emp['employee_id']} - {emp['name']}" for emp in payroll.employees_data["employees"]]

        if employee_options:
            selected_employee = st.selectbox("Select Employee", employee_options)
            employee_id = selected_employee.split(" - ")[0]

            employee = payroll.get_employee(employee_id)

            if employee:
                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        name = st.text_input("Full Name", value=employee["name"])
                        phone = st.text_input("Phone", value=employee["phone"])
                        department = st.selectbox("Department",
                                                  ["Construction", "Management", "Administration", "Logistics"],
                                                  index=["Construction", "Management", "Administration",
                                                         "Logistics"].index(employee["department"]))

                    with col2:
                        position = st.text_input("Position", value=employee["position"])
                        basic_salary = st.number_input("Basic Salary (₹)", value=employee["basic_salary"])
                        overtime_applicable = st.checkbox("Overtime Applicable",
                                                          value=employee.get("overtime_applicable", False))

                        if overtime_applicable:
                            overtime_rate = st.number_input("Overtime Rate (₹ per hour)",
                                                            value=employee.get("overtime_rate", 0.0))
                        else:
                            overtime_rate = 0.0

                    st.subheader("Bank Details")
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        bank_account_number = st.text_input("Bank Account Number",
                                                            value=employee["bank_account_number"])
                    with col4:
                        ifsc_code = st.text_input("IFSC Code", value=employee["ifsc_code"])
                    with col5:
                        branch_name = st.text_input("Branch Name", value=employee["branch_name"])

                    status = st.selectbox("Status", ["active", "inactive"],
                                          index=0 if employee["status"] == "active" else 1)

                    submitted = st.form_submit_button("Update Employee")

                    if submitted:
                        # Update employee data
                        employee.update({
                            "name": name,
                            "phone": phone,
                            "department": department,
                            "position": position,
                            "basic_salary": basic_salary,
                            "overtime_applicable": overtime_applicable,
                            "overtime_rate": overtime_rate,
                            "bank_account_number": bank_account_number,
                            "ifsc_code": ifsc_code,
                            "branch_name": branch_name,
                            "status": status
                        })

                        payroll.save_employees()
                        st.success(f"Employee {name} updated successfully!")

    with tab4:
        st.subheader("Bulk Upload Employees")

        uploaded_file = st.file_uploader("Upload Employee Data File", type=["csv", "xlsx"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.write("Preview of uploaded data:")
                st.dataframe(df.head())

                required_columns = ['employee_id', 'name', 'phone', 'department', 'position',
                                    'basic_salary', 'bank_account_number', 'ifsc_code', 'branch_name']

                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                else:
                    if st.button("Process Employee Upload"):
                        records_processed = 0
                        for _, row in df.iterrows():
                            employee_data = {
                                "employee_id": str(row['employee_id']),
                                "name": str(row['name']),
                                "phone": str(row['phone']),
                                "department": str(row['department']),
                                "position": str(row['position']),
                                "basic_salary": float(row['basic_salary']),
                                "overtime_applicable": bool(row.get('overtime_applicable', False)),
                                "overtime_rate": float(row.get('overtime_rate', 0.0)),
                                "bank_account_number": str(row['bank_account_number']),
                                "ifsc_code": str(row['ifsc_code']),
                                "branch_name": str(row['branch_name']),
                                "joining_date": str(datetime.datetime.now().date()),
                                "status": "active"
                            }

                            payroll.add_employee(employee_data)
                            records_processed += 1

                        st.success(f"Successfully processed {records_processed} employee records!")

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

        st.info("""
        **Expected CSV/Excel Format:**
        - employee_id, name, phone, department, position, basic_salary, 
        - bank_account_number, ifsc_code, branch_name
        - Optional: overtime_applicable (True/False), overtime_rate
        """)


def display_attendance(payroll):
    st.header("📅 Attendance Management")

    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Bulk Upload", "View Records"])

    with tab1:
        st.subheader("Manual Attendance Entry")

        with st.form("attendance_form"):
            col1, col2 = st.columns(2)

            with col1:
                employee_options = [f"{emp['employee_id']} - {emp['name']}" for emp in
                                    payroll.employees_data["employees"] if emp["status"] == "active"]
                selected_employee = st.selectbox("Select Employee*", employee_options)
                employee_id = selected_employee.split(" - ")[0] if selected_employee else ""

                date = st.date_input("Date*", datetime.date.today())

            with col2:
                check_in = st.time_input("Check-in Time*", datetime.time(9, 0))

                # Show overtime only if employee has overtime applicable
                employee = payroll.get_employee(employee_id) if employee_id else None
                if employee and employee.get("overtime_applicable", False):
                    overtime_hours = st.number_input("Overtime Hours", min_value=0.0, max_value=12.0, step=0.5,
                                                     value=0.0)
                else:
                    overtime_hours = 0.0
                    st.info("Overtime not applicable for this employee")

            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Record Attendance")

            if submitted:
                if not all([employee_id, date, check_in]):
                    st.error("Please fill all required fields (*)")
                else:
                    attendance_data = {
                        "employee_id": employee_id,
                        "date": str(date),
                        "check_in": str(check_in),
                        "overtime_hours": overtime_hours,
                        "notes": notes,
                        "recorded_at": str(datetime.datetime.now())
                    }

                    payroll.record_attendance(attendance_data)
                    st.success("Attendance recorded successfully!")

    with tab2:
        st.subheader("Bulk Upload from Excel/CSV")

        uploaded_file = st.file_uploader("Upload Attendance File", type=["csv", "xlsx"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                st.write("Preview of uploaded data:")
                st.dataframe(df.head())

                if st.button("Process Upload"):
                    records_processed = 0
                    for _, row in df.iterrows():
                        attendance_data = {
                            "employee_id": str(row.get('employee_id', '')),
                            "date": str(row.get('date', '')),
                            "check_in": str(row.get('check_in', '09:00')),
                            "overtime_hours": float(row.get('overtime_hours', 0)),
                            "notes": str(row.get('notes', '')),
                            "recorded_at": str(datetime.datetime.now())
                        }

                        payroll.record_attendance(attendance_data)
                        records_processed += 1

                    st.success(f"Successfully processed {records_processed} attendance records!")

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

        st.info("""
        **Expected CSV/Excel Format for Attendance:**
        - employee_id, date (YYYY-MM-DD), check_in (HH:MM:SS)
        - Optional: overtime_hours, notes
        """)

    with tab3:
        st.subheader("Attendance Records")

        if payroll.attendance_data["attendance_records"]:
            # Convert to DataFrame for better display
            attendance_df = pd.DataFrame(payroll.attendance_data["attendance_records"])

            # Add employee names for better readability
            employee_map = {emp["employee_id"]: emp["name"] for emp in payroll.employees_data["employees"]}
            attendance_df["employee_name"] = attendance_df["employee_id"].map(employee_map)

            # Reorder columns
            cols = ["employee_id", "employee_name", "date", "check_in", "overtime_hours", "notes", "recorded_at"]
            attendance_df = attendance_df[cols]

            st.dataframe(attendance_df, use_container_width=True)

            # Export option
            csv = attendance_df.to_csv(index=False)
            st.download_button(
                label="Export as CSV",
                data=csv,
                file_name="attendance_records.csv",
                mime="text/csv"
            )
        else:
            st.info("No attendance records found.")


def display_salary_processing(payroll):
    st.header("💰 Salary Processing")

    col1, col2 = st.columns(2)

    with col1:
        month = st.selectbox("Select Month", range(1, 13),
                             format_func=lambda x: datetime.date(2024, x, 1).strftime('%B'))

    with col2:
        current_year = datetime.datetime.now().year
        year = st.selectbox("Select Year", range(current_year - 1, current_year + 2), index=1)

    if st.button("Calculate Salaries"):
        salary_results = []

        for emp in payroll.employees_data["employees"]:
            if emp["status"] == "active":
                salary_data = payroll.calculate_salary(emp["employee_id"], month, year)
                if salary_data:
                    salary_results.append({
                        "Employee ID": emp["employee_id"],
                        "Name": emp["name"],
                        "Working Days": salary_data["working_days"],
                        "Overtime Hours": salary_data["total_overtime_hours"],
                        "Basic Salary": f"₹{salary_data['basic_salary']:,.2f}",
                        "Overtime Pay": f"₹{salary_data['overtime_pay']:,.2f}",
                        "Gross Salary": f"₹{salary_data['gross_salary']:,.2f}",
                        "Net Salary": f"₹{salary_data['net_salary']:,.2f}"
                    })

        if salary_results:
            salary_df = pd.DataFrame(salary_results)
            st.dataframe(salary_df, use_container_width=True)

            # Generate salary slips
            st.subheader("Generate Salary Slips")

            selected_employee = st.selectbox("Select Employee for Salary Slip",
                                             [f"{emp['employee_id']} - {emp['name']}" for emp in
                                              payroll.employees_data["employees"]])

            if selected_employee:
                employee_id = selected_employee.split(" - ")[0]
                salary_data = payroll.calculate_salary(employee_id, month, year)

                if salary_data:
                    display_salary_slip(salary_data)


def display_salary_slip(salary_data):
    st.markdown('<div class="salary-slip">', unsafe_allow_html=True)

    emp = salary_data["employee"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Employee Details")
        st.write(f"**Name:** {emp['name']}")
        st.write(f"**ID:** {emp['employee_id']}")
        st.write(f"**Department:** {emp['department']}")
        st.write(f"**Position:** {emp['position']}")

    with col2:
        st.subheader("Salary Period")
        st.write(f"**Month:** {datetime.date(2024, salary_data['month'], 1).strftime('%B')}")
        st.write(f"**Year:** {salary_data['year']}")
        st.write(f"**Working Days:** {salary_data['working_days']}")
        if emp.get("overtime_applicable", False):
            st.write(f"**Overtime Hours:** {salary_data['total_overtime_hours']}")

    with col3:
        st.subheader("Bank Details")
        st.write(f"**Account Number:** {emp['bank_account_number']}")
        st.write(f"**IFSC Code:** {emp['ifsc_code']}")
        st.write(f"**Branch:** {emp['branch_name']}")
        st.write(f"**Net Salary:** ₹{salary_data['net_salary']:,.2f}")

    st.markdown("---")

    # Earnings
    st.subheader("Earnings")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"Basic Salary: ₹{salary_data['basic_salary']:,.2f}")
        if salary_data['overtime_pay'] > 0:
            st.write(f"Overtime Pay: ₹{salary_data['overtime_pay']:,.2f}")

    with col2:
        st.write(f"**Gross Salary: ₹{salary_data['gross_salary']:,.2f}**")

    st.markdown("---")
    st.markdown(f"### **Net Payable: ₹{salary_data['net_salary']:,.2f}**")

    st.markdown('</div>', unsafe_allow_html=True)

    # Download button for salary slip
    if st.button("Download Salary Slip as PDF"):
        st.info("PDF generation feature would be implemented here")


def display_reports(payroll):
    st.header("📈 Reports & Analytics")

    tab1, tab2, tab3 = st.tabs(["Attendance Report", "Salary Report", "Employee Statistics"])

    with tab1:
        st.subheader("Attendance Analysis")

        if payroll.attendance_data["attendance_records"]:
            # Monthly attendance trend
            attendance_df = pd.DataFrame(payroll.attendance_data["attendance_records"])
            attendance_df['date'] = pd.to_datetime(attendance_df['date'])
            attendance_df['month'] = attendance_df['date'].dt.to_period('M')

            monthly_attendance = attendance_df.groupby('month').size().reset_index(name='count')
            monthly_attendance['month'] = monthly_attendance['month'].astype(str)

            fig = px.line(monthly_attendance, x='month', y='count',
                          title="Monthly Attendance Trend")
            st.plotly_chart(fig)
        else:
            st.info("No attendance data available for reports.")

    with tab2:
        st.subheader("Salary Analysis")

        if payroll.employees_data["employees"]:
            # Department-wise salary distribution
            dept_salaries = {}
            for emp in payroll.employees_data["employees"]:
                dept = emp["department"]
                if dept not in dept_salaries:
                    dept_salaries[dept] = []
                dept_salaries[dept].append(emp["basic_salary"])

            fig = go.Figure()
            for dept, salaries in dept_salaries.items():
                fig.add_trace(go.Box(y=salaries, name=dept))

            fig.update_layout(
                title="Salary Distribution by Department",
                yaxis_title="Basic Salary (₹)"
            )
            st.plotly_chart(fig)

    with tab3:
        st.subheader("Employee Statistics")

        if payroll.employees_data["employees"]:
            # Employee status distribution
            status_count = {}
            for emp in payroll.employees_data["employees"]:
                status = emp["status"]
                status_count[status] = status_count.get(status, 0) + 1

            fig = px.pie(values=list(status_count.values()),
                         names=list(status_count.keys()),
                         title="Employee Status Distribution")
            st.plotly_chart(fig)


def display_settings(payroll):
    st.header("⚙️ System Settings")

    st.subheader("Data Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export All Data"):
            # Export employees data
            employees_csv = pd.DataFrame(payroll.employees_data["employees"]).to_csv(index=False)
            st.download_button(
                label="Download Employees CSV",
                data=employees_csv,
                file_name="employees_export.csv",
                mime="text/csv"
            )

            # Export attendance data
            attendance_csv = pd.DataFrame(payroll.attendance_data["attendance_records"]).to_csv(index=False)
            st.download_button(
                label="Download Attendance CSV",
                data=attendance_csv,
                file_name="attendance_export.csv",
                mime="text/csv"
            )

    with col2:
        st.warning("Danger Zone")
        if st.button("Clear All Data"):
            if st.checkbox("I understand this will delete all data permanently"):
                payroll.employees_data["employees"] = []
                payroll.attendance_data["attendance_records"] = []
                payroll.save_employees()
                payroll.save_attendance()
                st.success("All data cleared successfully!")

    st.subheader("System Information")
    st.write(f"**Total Employees:** {len(payroll.employees_data['employees'])}")
    st.write(f"**Total Attendance Records:** {len(payroll.attendance_data['attendance_records'])}")
    st.write(f"**Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()