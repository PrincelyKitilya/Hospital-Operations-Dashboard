
import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine, text #object relational mapper that connects postgresql to python file

# Page config
st.set_page_config(
    page_title="Hospital Management Analytics",
    layout="wide"
)

# SQLAlchemy connection for PostgreSQL
conn = create_engine(st.secrets["DATABASE_URL"])

# Title
st.title("Hospital Management System - Analytics Dashboard")
st.markdown("### Real-time insights from 5-table normalized database")

# Sidebar for filters
st.sidebar.header("Filters")
branch_query = text("SELECT DISTINCT hospitalBranch FROM Doctors")
with conn.connect() as connection:
    branch_options = pd.read_sql(branch_query, connection)['hospitalbranch'].tolist()

selected_branch = st.sidebar.multiselect(
    "Hospital Branch",
    options=branch_options,
    default=branch_options
)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Executive Overview",
    "Doctor Analytics",
    "Financial Insights",
    "Patient Analysis",
    "Raw SQL Queries"
])

with tab1:
    col1, col2, col3, col4 = st.columns(4)

    # KPI Metrics
    with col1:
        total_revenue_query = text("""
            SELECT SUM(amount) as revenue
            FROM Bills
            WHERE paymentStatus = 'Paid'
        """)
        with conn.connect() as connection:
            total_revenue = pd.read_sql(total_revenue_query, connection).iloc[0, 0]
        total_revenue = total_revenue if total_revenue else 0
        st.metric("Total Revenue (Paid)", f"${total_revenue:,.2f}")

    with col2:
        patient_count_query = text("SELECT COUNT(*) as cnt FROM Patients")
        with conn.connect() as connection:
            patient_count = pd.read_sql(patient_count_query, connection).iloc[0, 0]
        st.metric("Total Patients", patient_count)

    with col3:
        appointment_stats_query = text("""
            SELECT
                COUNT(*) as total,
                100.0 * SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END)
                / COUNT(*) as completion_rate
            FROM Appointments
        """)
        with conn.connect() as connection:
            appointment_stats = pd.read_sql(appointment_stats_query, connection)
        st.metric(
            "Appointments",
            f"{appointment_stats['total'][0]}",
            f"{appointment_stats['completion_rate'][0]:.1f}% Complete"
        )

    with col4:
        no_show_query = text("""
            SELECT 100.0 * SUM(CASE WHEN status = 'No-show' THEN 1 ELSE 0 END)
            / COUNT(*) as rate
            FROM Appointments
        """)
        with conn.connect() as connection:
            no_show_rate = pd.read_sql(no_show_query, connection).iloc[0, 0]
        st.metric("No-Show Rate", f"{no_show_rate:.1f}%")

    # Revenue Trend Chart
    st.subheader("Monthly Revenue Trend")
    revenue_trend_query = text("""
        SELECT
            TO_CHAR(billDate, 'YYYY-MM') as Month,
            SUM(amount) as Revenue,
            paymentStatus
        FROM Bills
        GROUP BY TO_CHAR(billDate, 'YYYY-MM'), paymentStatus
        ORDER BY Month
    """)
    with conn.connect() as connection:
        revenue_trend = pd.read_sql(revenue_trend_query, connection)

    if not revenue_trend.empty:
        fig = px.line(
            revenue_trend[revenue_trend['paymentstatus'] == 'Paid'],
            x='month', y='revenue',
            title="Paid Revenue Over Time",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revenue data available")

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Doctor Performance Matrix (original)
        st.subheader("Doctor Performance Matrix")
        doctor_performance_query = text("""
            SELECT
                CONCAT(d.firstName, ' ', d.lastName) as Doctor,
                d.specialization,
                d.hospitalBranch,
                COUNT(a.appointmentID) as Appointments,
                SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) as Completed,
                AVG(t.cost) as AvgTreatmentCost
            FROM Doctors d
            LEFT JOIN Appointments a ON d.doctorID = a.doctorID
            LEFT JOIN Treatments t ON a.appointmentID = t.appointmentID
            GROUP BY d.doctorID, d.firstName, d.lastName, d.specialization, d.hospitalBranch
        """)
        with conn.connect() as connection:
            doctor_performance = pd.read_sql(doctor_performance_query, connection)

        if not doctor_performance.empty:
            fig1 = px.scatter(
                doctor_performance,
                x='appointments',
                y='avgtreatmentcost',
                color='specialization',
                size='completed',
                hover_name='doctor',
                title="Doctor Efficiency Matrix",
                labels={
                    'appointments': 'Total Appointments',
                    'avgtreatmentcost': 'Average Treatment Cost'
                }
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No doctor performance data available")
    
    with col2:
        # Simple additional analysis: Doctors by Specialization
        st.subheader("Doctors by Specialization")
        specialization_query = text("""
            SELECT 
                specialization,
                COUNT(*) as doctor_count
            FROM Doctors
            GROUP BY specialization
            ORDER BY doctor_count DESC
        """)
        
        with conn.connect() as connection:
            specialization_data = pd.read_sql(specialization_query, connection)
        
        if not specialization_data.empty:
            fig2 = px.bar(
                specialization_data,
                x='specialization',
                y='doctor_count',
                title="Number of Doctors by Specialization",
                color='doctor_count',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No specialization data available")
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        # Payment Status Distribution
        payment_data_query = text("""
            SELECT paymentStatus, COUNT(*) as Count, SUM(amount) as TotalAmount
            FROM Bills
            GROUP BY paymentStatus
        """)
        with conn.connect() as connection:
            payment_data = pd.read_sql(payment_data_query, connection)

        if not payment_data.empty:
            fig1 = px.pie(
                payment_data,
                values='totalamount',
                names='paymentstatus',
                title="Revenue by Payment Status",
                hole=0.4,
                color_discrete_sequence=px.colors.diverging.RdBu
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No payment data available")

    with col2:
        # Treatment Type Revenue
        treatment_revenue_query = text("""
            SELECT t.treatmentType, SUM(b.amount) as Revenue
            FROM Treatments t
            JOIN Bills b ON t.treatmentID = b.treatmentID
            WHERE b.paymentStatus = 'Paid'
            GROUP BY t.treatmentType
            ORDER BY Revenue DESC
        """)
        with conn.connect() as connection:
            treatment_revenue = pd.read_sql(treatment_revenue_query, connection)

        if not treatment_revenue.empty:
            fig2 = px.bar(
                treatment_revenue,
                x='treatmenttype',
                y='revenue',
                title="Revenue by Treatment Type",
                color='revenue',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No treatment revenue data available")

with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        # Patient Demographics (original treemap)
        st.subheader("Patients by Insurance")
        patient_demo_query = text("""
            SELECT
                insuranceProvider,
                COUNT(*) as PatientCount,
                AVG(EXTRACT(YEAR FROM AGE(dateOfBirth))) as AvgAge,
                COUNT(DISTINCT a.appointmentID) as TotalAppointments
            FROM Patients p
            LEFT JOIN Appointments a ON p.patientID = a.patientID
            GROUP BY insuranceProvider
        """)
        with conn.connect() as connection:
            patient_demo = pd.read_sql(patient_demo_query, connection)

        if not patient_demo.empty:
            fig1 = px.treemap(
                patient_demo,
                path=['insuranceprovider'],
                values='patientcount',
                color='avgage',
                hover_data=['totalappointments'],
                title="Patient Distribution by Insurance Provider",
                color_continuous_scale='RdBu'
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No patient demographic data available")
    
    with col2:
        # Simple additional analysis: Patient Age Groups
        st.subheader("Patient Age Groups")
        age_groups_query = text("""
            SELECT 
                CASE 
                    WHEN EXTRACT(YEAR FROM AGE(dateOfBirth)) < 18 THEN 'Under 18'
                    WHEN EXTRACT(YEAR FROM AGE(dateOfBirth)) BETWEEN 18 AND 35 THEN '18-35'
                    WHEN EXTRACT(YEAR FROM AGE(dateOfBirth)) BETWEEN 36 AND 55 THEN '36-55'
                    WHEN EXTRACT(YEAR FROM AGE(dateOfBirth)) BETWEEN 56 AND 70 THEN '56-70'
                    ELSE 'Over 70'
                END as age_group,
                COUNT(*) as patient_count
            FROM Patients
            GROUP BY age_group
            ORDER BY age_group
        """)
        
        with conn.connect() as connection:
            age_groups = pd.read_sql(age_groups_query, connection)
        
        if not age_groups.empty:
            fig2 = px.bar(
                age_groups,
                x='age_group',
                y='patient_count',
                title="Patients by Age Group",
                color='patient_count',
                color_continuous_scale='Blues',
                labels={'patient_count': 'Number of Patients', 'age_group': 'Age Group'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No age group data available")

with tab5:
    # Show SQL Queries
    st.subheader("SQL Behind the Dashboard")

    queries = {
        "Total Revenue": """
            SELECT SUM(amount) as revenue
            FROM Bills
            WHERE paymentStatus = 'Paid'
        """,
        "Revenue Analysis": """
            SELECT
                TO_CHAR(billDate, 'YYYY-MM') as Month,
                paymentMethod,
                paymentStatus,
                SUM(amount) as TotalRevenue,
                COUNT(*) as TransactionCount
            FROM Bills
            GROUP BY TO_CHAR(billDate, 'YYYY-MM'), paymentMethod, paymentStatus
            ORDER BY Month
        """
    }

    selected_query = st.selectbox(
        "Select Query to View",
        list(queries.keys())
    )
    st.code(queries[selected_query], language="sql")

    # Option to run custom query
    st.subheader("Run Custom Query")
    custom_query = st.text_area("Enter SQL Query:", height=150)
    if st.button("Execute Query"):
        if custom_query.strip():
            try:
                with conn.connect() as connection:
                    result = pd.read_sql(text(custom_query), connection)
                st.dataframe(result)
                st.write(f"Rows returned: {len(result)}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter a SQL query")

# Footer
st.markdown("---")
st.markdown("**Database Schema:** Doctors → Appointments → Treatments → Bills ← Patients")
st.markdown("*Built with PostgreSQL, SQLAlchemy, Python, Streamlit & Plotly*")
st.markdown("**Created by:** Princely Kitilya & Francesca Valeri")