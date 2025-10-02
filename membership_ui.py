import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import member_manager
import plotly.express as px
import plotly.graph_objects as go

# Helper: ensure session state keys exist
def ensure_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

def render_membership_management():
    """Render the complete membership management interface."""
    st.title("⛪ Membership Management")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Add Member", 
        "👥 Manage Members", 
        "🔍 Search & Filter", 
        "📊 Statistics", 
        "🎂 Birthdays"
    ])
    
    with tab1:
        render_add_member_form()
    
    with tab2:
        render_manage_members()
    
    with tab3:
        render_search_and_filter()
    
    with tab4:
        render_member_statistics()
    
    with tab5:
        render_upcoming_birthdays()

def render_add_member_form():
    """Render the add member form with validation."""
    st.subheader("Add New Member")

    # Ensure session state keys used here exist so toggling works predictably
    ensure_state("add_baptized", False)
    ensure_state("add_baptism_date", date.today())

    with st.form("add_member_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Personal Information**")
            name = st.text_input("Full Name *", key="add_name", help="Required field")
            mobile_no = st.text_input("Mobile Number", key="add_mobile_no", 
                                     help="Format: +1-234-567-8900 or 234-567-8900")
            email_address = st.text_input("Email Address", key="add_email_address")
            physical_address = st.text_area("Physical Address", key="add_physical_address")
        
        with col2:
            st.markdown("**Membership Details**")
            # allow dates from 1900 to today for join_date
            join_date = st.date_input(
                "Join Date",
                key="add_join_date",
                value=date.today(),
                min_value=date(1900,1,1),
                max_value=date.today()
            )
            # Date of birth: min=1900, max = today - 1 year (so member >= 1 year old)
            date_of_birth = st.date_input(
                "Date of Birth",
                key="add_date_of_birth",
                value=date.today() - timedelta(days=365*20),  # default 20 years ago
                min_value=date(1900,1,1),
                max_value=date.today() - timedelta(days=365)
            )
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="add_gender")
            membership_status = st.selectbox("Membership Status", 
                                           ["Active", "New", "Visitor", "Inactive"], 
                                           key="add_membership_status")
        
        with col3:
            st.markdown("**Additional Information**")
            # Baptized checkbox
            baptized = st.checkbox("Baptized", key="add_baptized")

            # ensure default exists before creating widget (safe)
            ensure_state("add_baptism_date", st.session_state.get("add_baptism_date", date.today()))

            # Show the date input always (avoids Streamlit race/disabling issues inside forms)
            baptism_date = st.date_input(
                "Baptism Date (will be saved only if 'Baptized' is checked)",
                key="add_baptism_date",
                value=st.session_state["add_baptism_date"],
                min_value=date(1900,1,1),
                max_value=date.today()
            )

            emergency_contact_name = st.text_input("Emergency Contact Name", 
                                                  key="add_ec_name")
            emergency_contact_number = st.text_input("Emergency Contact Number", 
                                                    key="add_ec_number")
            notes = st.text_area("Notes", key="add_notes")
        
        # Form submission
        submitted = st.form_submit_button("Add Member", type="primary")
        
        if submitted:
            if not name:
                st.error("Member name is required!")
            else:
                # convert baptism_date to ISO string only if baptized True
                baptism_iso = baptism_date.strftime("%Y-%m-%d") if baptized and baptism_date else None

                success, message, member_id = member_manager.add_member(
                    name=name,
                    mobile_no=mobile_no,
                    email_address=email_address,
                    physical_address=physical_address,
                    join_date=join_date.strftime("%Y-%m-%d"),
                    date_of_birth=date_of_birth.strftime("%Y-%m-%d"),
                    gender=gender,
                    membership_status=membership_status,
                    baptized=baptized,
                    baptism_date=baptism_iso,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_number=emergency_contact_number,
                    notes=notes
                )
                
                if success:
                    st.success(message)
                    st.balloons()
                    # Do NOT reassign st.session_state["add_baptism_date"] here — it's a widget key.
                    # clear_on_submit=True already resets the widgets in the form.
                else:
                    st.error(message)

def render_manage_members():
    """Render the member management interface."""
    st.subheader("Manage Existing Members")
    
    members = member_manager.get_all_members()
    if not members:
        st.info("No members found. Add a new member in the 'Add Member' tab.")
        return
    
    # Member selection
    member_names = {f"{member['name']} (ID: {member['id']})": member['id'] for member in members}
    selected_member_display = st.selectbox("Select Member to Edit/Delete", 
                                          list(member_names.keys()))
    selected_member_id = member_names[selected_member_display]
    selected_member = member_manager.get_member_by_id(selected_member_id)
    
    if not selected_member:
        st.error("Selected member not found!")
        return
    
    # ensure edit session keys exist to keep toggles predictable
    # don't overwrite existing values — initialize only if missing
    ensure_state("edit_baptism_date", None)
    ensure_state("edit_baptized", False)

    # Display member information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("edit_member_form"):
            st.markdown("**Edit Member Information**")
            
            col_edit1, col_edit2, col_edit3 = st.columns(3)
            
            with col_edit1:
                edit_name = st.text_input("Full Name *", value=selected_member["name"], 
                                        key="edit_name")
                edit_mobile_no = st.text_input("Mobile Number", 
                                             value=selected_member["mobile_no"] or "", 
                                             key="edit_mobile_no")
                edit_email_address = st.text_input("Email Address", 
                                                 value=selected_member["email_address"] or "", 
                                                 key="edit_email_address")
                edit_physical_address = st.text_area("Physical Address", 
                                                   value=selected_member["physical_address"] or "", 
                                                   key="edit_physical_address")
            
            with col_edit2:
                # parse join_date and dob safely; provide fallbacks if empty
                try:
                    join_dt_val = datetime.strptime(selected_member["join_date"], "%Y-%m-%d").date()
                except Exception:
                    join_dt_val = date.today()
                try:
                    dob_val = datetime.strptime(selected_member["date_of_birth"], "%Y-%m-%d").date()
                except Exception:
                    dob_val = date.today() - timedelta(days=365*20)
                
                edit_join_date = st.date_input("Join Date", 
                                             value=join_dt_val,
                                             key="edit_join_date",
                                             min_value=date(1900,1,1),
                                             max_value=date.today())
                edit_date_of_birth = st.date_input("Date of Birth", 
                                                 value=dob_val,
                                                 key="edit_date_of_birth",
                                                 min_value=date(1900,1,1),
                                                 max_value=date.today() - timedelta(days=365))
                edit_gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                         index=["Male", "Female", "Other"].index(selected_member.get("gender","Male")), 
                                         key="edit_gender")
                edit_membership_status = st.selectbox("Membership Status", 
                                                    ["Active", "New", "Visitor", "Inactive"], 
                                                    index=["Active", "New", "Visitor", "Inactive"].index(selected_member.get("membership_status","Active")), 
                                                    key="edit_membership_status")
            
            with col_edit3:
                # create/edit baptized checkbox
                edit_baptized = st.checkbox("Baptized", value=bool(selected_member.get("baptized")), 
                                          key="edit_baptized")

                # If DB has a baptism date and session value is None, initialize it (only if missing)
                edit_baptism_date_val = None
                if selected_member.get("baptism_date"):
                    try:
                        edit_baptism_date_val = datetime.strptime(selected_member["baptism_date"], "%Y-%m-%d").date()
                    except Exception:
                        edit_baptism_date_val = date.today()

                # Only set session state if the key is not already set to avoid modifying after widget creation
                if edit_baptism_date_val and not st.session_state.get("edit_baptism_date"):
                    st.session_state["edit_baptism_date"] = edit_baptism_date_val

                # ensure there's always a sensible default before creating the widget
                if not st.session_state.get("edit_baptism_date"):
                    st.session_state["edit_baptism_date"] = date.today()

                # Show date input always; it will be saved only when edit_baptized is True
                edit_baptism_date = st.date_input(
                    "Baptism Date (will be saved only if 'Baptized' is checked)",
                    value=st.session_state.get("edit_baptism_date", date.today()), 
                    key="edit_baptism_date",
                    min_value=date(1900,1,1),
                    max_value=date.today()
                )

                edit_emergency_contact_name = st.text_input("Emergency Contact Name", 
                                                          value=selected_member.get("emergency_contact_name","") or "", 
                                                          key="edit_ec_name")
                edit_emergency_contact_number = st.text_input("Emergency Contact Number", 
                                                            value=selected_member.get("emergency_contact_number","") or "", 
                                                            key="edit_ec_number")
                edit_notes = st.text_area("Notes", value=selected_member.get("notes","") or "", 
                                        key="edit_notes")
            
            # Form buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                update_button = st.form_submit_button("Update Member", type="primary")
            with col_btn2:
                delete_button = st.form_submit_button("Delete Member", type="secondary")
            
            if update_button:
                baptism_iso = edit_baptism_date.strftime("%Y-%m-%d") if edit_baptized and edit_baptism_date else None
                success, message = member_manager.update_member(
                    member_id=selected_member_id,
                    name=edit_name,
                    mobile_no=edit_mobile_no,
                    email_address=edit_email_address,
                    physical_address=edit_physical_address,
                    join_date=edit_join_date.strftime("%Y-%m-%d"),
                    date_of_birth=edit_date_of_birth.strftime("%Y-%m-%d"),
                    gender=edit_gender,
                    membership_status=edit_membership_status,
                    baptized=edit_baptized,
                    baptism_date=baptism_iso,
                    emergency_contact_name=edit_emergency_contact_name,
                    emergency_contact_number=edit_emergency_contact_number,
                    notes=edit_notes
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            
            if delete_button:
                success, message = member_manager.delete_member(selected_member_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.markdown("**Member Summary**")
        st.info(f"""
        **Name:** {selected_member['name']}
        **Status:** {selected_member['membership_status']}
        **Gender:** {selected_member['gender']}
        **Baptized:** {'Yes' if selected_member.get('baptized') else 'No'}
        **Join Date:** {selected_member.get('join_date')}
        **Member ID:** {selected_member['id']}
        """)

def render_search_and_filter():
    """Render search and filter interface."""
    st.subheader("Search & Filter Members")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search by Name, Email, or Phone", key="search_term")
    
    with col2:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "Active", "New", "Visitor", "Inactive"])
    
    with col3:
        baptized_filter = st.selectbox("Filter by Baptism", ["All", "Baptized", "Not Baptized"])
    
    # Get filtered results
    if search_term:
        members = member_manager.search_members(search_term)
    else:
        members = member_manager.get_all_members()
    
    # Apply additional filters
    if status_filter != "All":
        members = [m for m in members if m.get('membership_status') == status_filter]
    
    if baptized_filter != "All":
        if baptized_filter == "Baptized":
            members = [m for m in members if m.get('baptized')]
        else:
            members = [m for m in members if not m.get('baptized')]
    
    st.write(f"Found {len(members)} member(s)")
    
    if members:
        # Create DataFrame for display
        df = pd.DataFrame(members)
        display_columns = ['name', 'membership_status', 'gender', 'email_address', 
                         'mobile_no', 'join_date', 'baptized']
        
        # Rename columns for better display
        column_names = {
            'name': 'Name',
            'membership_status': 'Status',
            'gender': 'Gender',
            'email_address': 'Email',
            'mobile_no': 'Phone',
            'join_date': 'Join Date',
            'baptized': 'Baptized'
        }
        
        df_display = df[display_columns].rename(columns=column_names)
        df_display['Baptized'] = df_display['Baptized'].map({1: 'Yes', 0: 'No', True: 'Yes', False: 'No'})
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No members match the current filters.")

def render_member_statistics():
    """Render member statistics and visualizations."""
    st.subheader("Member Statistics")
    
    stats = member_manager.get_member_statistics()
    
    if not stats:
        st.error("Unable to load member statistics.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Members", stats['total_members'])
    
    with col2:
        st.metric("Baptized Members", stats['baptized_count'])
    
    with col3:
        baptism_rate = (stats['baptized_count'] / stats['total_members'] * 100) if stats['total_members'] > 0 else 0
        st.metric("Baptism Rate", f"{baptism_rate:.1f}%")
    
    with col4:
        st.metric("New Members (30 days)", stats['recent_joins'])
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Membership Status Distribution")
        if stats['status_breakdown']:
            fig_status = px.pie(
                values=list(stats['status_breakdown'].values()),
                names=list(stats['status_breakdown'].keys()),
                title="Members by Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    
    with col_chart2:
        st.subheader("Gender Distribution")
        if stats['gender_breakdown']:
            fig_gender = px.bar(
                x=list(stats['gender_breakdown'].keys()),
                y=list(stats['gender_breakdown'].values()),
                title="Members by Gender"
            )
            fig_gender.update_layout(xaxis_title="Gender", yaxis_title="Count")
            st.plotly_chart(fig_gender, use_container_width=True)

def render_upcoming_birthdays():
    """Render upcoming birthdays section."""
    st.subheader("🎂 Upcoming Birthdays")
    
    days_ahead = st.slider("Show birthdays in the next X days", 
                          min_value=7, max_value=90, value=30)
    
    upcoming_birthdays = member_manager.get_upcoming_birthdays(days_ahead)
    
    if upcoming_birthdays:
        st.write(f"Found {len(upcoming_birthdays)} upcoming birthday(s)")
        
        for member in upcoming_birthdays:
            days_until = int(member['days_until_birthday'])
            birth_date = datetime.strptime(member['date_of_birth'], "%Y-%m-%d")
            age = datetime.now().year - birth_date.year
            
            if days_until == 0:
                birthday_text = "🎉 **Today!**"
            elif days_until == 1:
                birthday_text = "🎂 **Tomorrow**"
            else:
                birthday_text = f"📅 **In {days_until} days**"
            
            st.info(f"""
            **{member['name']}** - Turning {age + 1}
            {birthday_text}
            Birthday: {birth_date.strftime('%B %d')}
            Status: {member['membership_status']}
            """)
    else:
        st.info(f"No birthdays in the next {days_ahead} days.")
