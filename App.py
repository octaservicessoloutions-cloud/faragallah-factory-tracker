import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json

# Page config - Black & White Theme
st.set_page_config(
    page_title="Octa Services - Faragallah Factory Tracker",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Black & White Theme
st.markdown("""
    <style>
    .main {background-color: #FFFFFF;}
    h1 {color: #000000; font-weight: bold;}
    h2 {color: #333333;}
    h3 {color: #666666;}
    .stButton>button {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #000000;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #333333;
        border: 2px solid #333333;
    }
    [data-testid="stSidebar"] {
        background-color: #F5F5F5;
    }
    </style>
""", unsafe_allow_html=True)

# Connect to Google Sheets
@st.cache_resource
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key("1urBkSsjlV2rO-uPbwbyKcjE_fl2lGnRD6tgNQEcXIMc").sheet1
    return sheet

# Load data from sheet
def load_data():
    sheet = get_google_sheet()
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        return df
    return pd.DataFrame()

# Save new problem to sheet
def save_problem(data):
    sheet = get_google_sheet()
    sheet.append_row(data)

# Update problem status
def update_problem(row_index, updates):
    sheet = get_google_sheet()
    for col, value in updates.items():
        sheet.update_cell(row_index + 2, col, value)  # +2 because header is row 1, and index starts at 0

# Sidebar - Octa Branding
st.sidebar.markdown("# 🏭 OCTA SERVICES")
st.sidebar.markdown("### SOLUTION BY OCTA")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio("Navigation", 
                        ["📊 Dashboard", 
                         "➕ Submit New Problem", 
                         "✅ Update Problem Status",
                         "📜 History"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Client:** Faragallah Factory")

# LINE NUMBERS
LINES = ["Line 3", "Line 7", "Line 9", "Line 10", "Line 12", "Line 13"]

# PRIORITY LEVELS
PRIORITIES = ["Low", "Medium", "High", "CRITICAL"]

# STATUS OPTIONS
STATUSES = ["🔴 OPEN", "🟡 IN PROGRESS", "🟢 RESOLVED"]

# ==================== DASHBOARD PAGE ====================
if page == "📊 Dashboard":
    st.title("📊 DASHBOARD - FARAGALLAH FACTORY")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No problems recorded yet. Submit your first problem!")
    else:
        # Filter only open and in-progress problems
        active_df = df[df['Status'].isin(['🔴 OPEN', '🟡 IN PROGRESS'])]
        
        if active_df.empty:
            st.success("🎉 All problems resolved! No active issues.")
        else:
            # Summary Cards
            st.subheader("📈 SUMMARY BY LINE")
            cols = st.columns(len(LINES))
            
            for idx, line in enumerate(LINES):
                line_count = len(active_df[active_df['Line_Number'] == line])
                with cols[idx]:
                    st.metric(label=line, value=line_count)
            
            st.markdown("---")
            
            # Filter and Search
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_line = st.selectbox("Filter by Line", ["All"] + LINES)
            with col2:
                filter_priority = st.selectbox("Filter by Priority", ["All"] + PRIORITIES)
            with col3:
                filter_status = st.selectbox("Filter by Status", ["All", "🔴 OPEN", "🟡 IN PROGRESS"])
            
            # Apply filters
            filtered_df = active_df.copy()
            if filter_line != "All":
                filtered_df = filtered_df[filtered_df['Line_Number'] == filter_line]
            if filter_priority != "All":
                filtered_df = filtered_df[filtered_df['Priority'] == filter_priority]
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df['Status'] == filter_status]
            
            st.markdown("---")
            st.subheader(f"🔧 ACTIVE PROBLEMS ({len(filtered_df)})")
            
            # Display problems
            if filtered_df.empty:
                st.info("No problems match your filters.")
            else:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# ==================== SUBMIT NEW PROBLEM PAGE ====================
elif page == "➕ Submit New Problem":
    st.title("➕ SUBMIT NEW PROBLEM")
    st.markdown("---")
    
    with st.form("new_problem_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            line_number = st.selectbox("Line Number *", LINES)
            date_submitted = st.text_input("Date Submitted *", placeholder="DD/MM/YYYY")
            task = st.text_area("Task Description *", placeholder="Describe the problem...")
            spare_part = st.text_input("Spare Part Number", placeholder="Enter part number if applicable")
        
        with col2:
            stock_available = st.selectbox("Available in Stock? *", ["Yes", "No"])
            quantity = st.number_input("Quantity Needed", min_value=0, step=1)
            priority = st.selectbox("Priority Level *", PRIORITIES)
            notes = st.text_area("Additional Notes", placeholder="Any extra information...")
        
        submitted = st.form_submit_button("🚀 SUBMIT PROBLEM", use_container_width=True)
        
        if submitted:
            if not line_number or not date_submitted or not task:
                st.error("⚠️ Please fill in all required fields (*)")
            else:
                # Generate Submission ID
                df = load_data()
                submission_id = len(df) + 1 if not df.empty else 1
                
                # Prepare data
                new_problem = [
                    submission_id,
                    line_number,
                    date_submitted,
                    task,
                    spare_part if spare_part else "N/A",
                    stock_available,
                    quantity,
                    priority,
                    notes if notes else "N/A",
                    "🔴 OPEN",
                    "",  # Engineer_Name (empty for new problems)
                    "",  # Date_Resolved
                    "",  # Resolution_Notes
                    ""   # Days_To_Resolve
                ]
                
                save_problem(new_problem)
                st.success(f"✅ Problem #{submission_id} submitted successfully!")
                st.balloons()

# ==================== UPDATE PROBLEM STATUS PAGE ====================
elif page == "✅ Update Problem Status":
    st.title("✅ UPDATE PROBLEM STATUS")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No problems recorded yet.")
    else:
        # Show only non-resolved problems
        active_df = df[df['Status'] != '🟢 RESOLVED']
        
        if active_df.empty:
            st.success("🎉 All problems are resolved!")
        else:
            st.subheader("Select Problem to Update")
            
            # Create problem selector
            problem_options = [f"ID #{row['Submission_ID']} - {row['Line_Number']} - {row['Task'][:50]}..." 
                             for _, row in active_df.iterrows()]
            
            selected_problem = st.selectbox("Choose Problem", problem_options)
            
            if selected_problem:
                problem_id = int(selected_problem.split("#")[1].split(" -")[0])
                problem_row = df[df['Submission_ID'] == problem_id].iloc[0]
                problem_index = df[df['Submission_ID'] == problem_id].index[0]
                
                st.markdown("---")
                st.subheader("📋 Problem Details")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Line:** {problem_row['Line_Number']}")
                    st.write(f"**Task:** {problem_row['Task']}")
                    st.write(f"**Priority:** {problem_row['Priority']}")
                    st.write(f"**Current Status:** {problem_row['Status']}")
                
                with col2:
                    st.write(f"**Submitted:** {problem_row['Date_Submitted']}")
                    st.write(f"**Spare Part:** {problem_row['Spare_Part_Number']}")
                    st.write(f"**Stock:** {problem_row['Stock_Available']}")
                
                st.markdown("---")
                st.subheader("🔄 Update Status")
                
                with st.form("update_form"):
                    new_status = st.selectbox("New Status", STATUSES)
                    engineer_name = st.text_input("Engineer Name *", 
                                                 value=problem_row['Engineer_Name'] if problem_row['Engineer_Name'] else "")
                    
                    if new_status == "🟢 RESOLVED":
                        date_resolved = st.text_input("Date Resolved *", placeholder="DD/MM/YYYY")
                        resolution_notes = st.text_area("Resolution Notes *", placeholder="How was it fixed?")
                    else:
                        date_resolved = ""
                        resolution_notes = ""
                    
                    update_button = st.form_submit_button("💾 UPDATE STATUS", use_container_width=True)
                    
                    if update_button:
                        if not engineer_name:
                            st.error("⚠️ Engineer name is required!")
                        elif new_status == "🟢 RESOLVED" and (not date_resolved or not resolution_notes):
                            st.error("⚠️ Please fill in resolution date and notes for resolved problems!")
                        else:
                            # Calculate days to resolve if resolved
                            days_to_resolve = ""
                            if new_status == "🟢 RESOLVED" and date_resolved:
                                try:
                                    date_sub = datetime.strptime(problem_row['Date_Submitted'], "%d/%m/%Y")
                                    date_res = datetime.strptime(date_resolved, "%d/%m/%Y")
                                    days_to_resolve = (date_res - date_sub).days
                                except:
                                    days_to_resolve = "N/A"
                            
                            # Column indices (1-based for Google Sheets)
                            updates = {
                                10: new_status,  # Status column
                                11: engineer_name,  # Engineer_Name column
                                12: date_resolved,  # Date_Resolved column
                                13: resolution_notes,  # Resolution_Notes column
                                14: days_to_resolve  # Days_To_Resolve column
                            }
                            
                            update_problem(problem_index, updates)
                            st.success(f"✅ Problem #{problem_id} updated successfully!")
                            st.balloons()
                            st.rerun()

# ==================== HISTORY PAGE ====================
elif page == "📜 History":
    st.title("📜 RESOLVED PROBLEMS HISTORY")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No problems recorded yet.")
    else:
        resolved_df = df[df['Status'] == '🟢 RESOLVED']
        
        if resolved_df.empty:
            st.info("No resolved problems yet.")
        else:
            st.subheader(f"📊 Total Resolved: {len(resolved_df)}")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                filter_line_hist = st.selectbox("Filter by Line", ["All"] + LINES, key="hist_line")
            with col2:
                filter_engineer = st.selectbox("Filter by Engineer", 
                                              ["All"] + list(resolved_df['Engineer_Name'].unique()))
            
            # Apply filters
            filtered_resolved = resolved_df.copy()
            if filter_line_hist != "All":
                filtered_resolved = filtered_resolved[filtered_resolved['Line_Number'] == filter_line_hist]
            if filter_engineer != "All":
                filtered_resolved = filtered_resolved[filtered_resolved['Engineer_Name'] == filter_engineer]
            
            st.markdown("---")
            
            if filtered_resolved.empty:
                st.info("No resolved problems match your filters.")
            else:
                st.dataframe(filtered_resolved, use_container_width=True, hide_index=True)
                
                # Statistics
                st.markdown("---")
                st.subheader("📈 STATISTICS")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_days = filtered_resolved['Days_To_Resolve'].replace('', 0).replace('N/A', 0).astype(float).mean()
                    st.metric("Average Resolution Time", f"{avg_days:.1f} days")
                
                with col2:
                    top_engineer = filtered_resolved['Engineer_Name'].value_counts().idxmax() if not filtered_resolved.empty else "N/A"
                    st.metric("Top Contributor", top_engineer)
                
                with col3:
                    critical_resolved = len(filtered_resolved[filtered_resolved['Priority'] == 'CRITICAL'])
                    st.metric("Critical Issues Resolved", critical_resolved)
