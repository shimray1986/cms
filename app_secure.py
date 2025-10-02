import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import auth_manager
import auth_ui

# Import existing modules
import member_manager
import finance_manager
import reporting_manager
import dashboard_manager

# --- Page Configuration ---
st.set_page_config(page_title="CTMS - Church Treasury Management System", layout="wide")

# Initialize authentication system
def initialize_system():
    """Initialize the authentication system and database."""
    try:
        # Initialize authentication tables
        success, message = auth_manager.initialize_auth_tables()
        if not success:
            st.error(f"Failed to initialize authentication system: {message}")
            return False
        return True
    except Exception as e:
        st.error(f"System initialization error: {str(e)}")
        return False

# Initialize session state
auth_manager.init_session_state()

# Initialize system on first run
if 'system_initialized' not in st.session_state:
    if initialize_system():
        st.session_state.system_initialized = True
    else:
        st.stop()

# Check authentication
if not auth_manager.check_authentication():
    # Show login page
    auth_ui.render_login_page()
    st.stop()

# User is authenticated - show main application
user = st.session_state.user
user_role = user.get('role', 'viewer')

# --- Sidebar Navigation ---
st.sidebar.title("🏛️ CTMS Navigation")

# Show user info and logout button
auth_ui.render_logout_button()

# Navigation based on user permissions
available_pages = []

if auth_manager.has_permission(user_role, 'view_dashboard'):
    available_pages.append("🏠 Dashboard")

if auth_manager.has_permission(user_role, 'view_members'):
    available_pages.append("👥 Membership Management")

if auth_manager.has_permission(user_role, 'view_finances'):
    available_pages.append("💰 Finance Management")

if auth_manager.has_permission(user_role, 'view_reports'):
    available_pages.append("📊 Reporting")

if auth_manager.has_permission(user_role, 'manage_users'):
    available_pages.append("👤 User Management")

# Always allow profile management
available_pages.append("⚙️ My Profile")

# Page selection
if available_pages:
    page = st.sidebar.radio("Go to", available_pages)
else:
    st.error("You don't have permission to access any pages. Please contact your administrator.")
    st.stop()

# --- Main Content Area ---

# Dashboard Page
if page == "🏠 Dashboard":
    if auth_manager.has_permission(user_role, 'view_dashboard'):
        import dashboard_ui
        dashboard_ui.render_dashboard()
    else:
        st.error("You don't have permission to view the dashboard.")

# Membership Management Page
elif page == "👥 Membership Management":
    if auth_manager.has_permission(user_role, 'view_members'):
        import membership_ui
        
        # Check specific permissions for member operations
        can_add = auth_manager.has_permission(user_role, 'add_members')
        can_edit = auth_manager.has_permission(user_role, 'edit_members')
        can_delete = auth_manager.has_permission(user_role, 'delete_members')
        
        # Pass permissions to the membership UI
        membership_ui.render_membership_management()
        
        # Log access
        auth_manager.log_audit_event(
            user['user_id'],
            "PAGE_ACCESS",
            "membership",
            details="Accessed membership management page"
        )
    else:
        st.error("You don't have permission to view membership management.")

# Finance Management Page
elif page == "💰 Finance Management":
    if auth_manager.has_permission(user_role, 'view_finances'):
        import finance_ui
        
        # Check specific permissions for financial operations
        can_add_transactions = auth_manager.has_permission(user_role, 'add_transactions')
        can_edit_transactions = auth_manager.has_permission(user_role, 'edit_transactions')
        can_delete_transactions = auth_manager.has_permission(user_role, 'delete_transactions')
        
        # Show appropriate interface based on permissions
        if can_add_transactions or can_edit_transactions:
            finance_ui.render_finance_management()
        else:
            # Read-only finance view
            st.title("💰 Finance Management (Read-Only)")
            st.info("You have read-only access to financial data.")
            
            # Show financial dashboard without edit capabilities
            ytd_income, ytd_expenses = finance_manager.get_ytd_summary()
            month_income, month_expenses = finance_manager.get_current_month_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("YTD Income", f"₹{ytd_income:,.2f}")
            with col2:
                st.metric("YTD Expenses", f"₹{ytd_expenses:,.2f}")
            with col3:
                st.metric("YTD Net", f"₹{ytd_income - ytd_expenses:,.2f}")
            with col4:
                recent_transactions = finance_manager.get_recent_transactions(limit=5)
                st.metric("Recent Transactions", len(recent_transactions))
            
            # Show recent transactions
            st.subheader("Recent Transactions")
            if recent_transactions:
                df = pd.DataFrame(recent_transactions)
                display_columns = ['transaction_date', 'transaction_type', 'category_name', 'amount', 'description']
                st.dataframe(df[display_columns], use_container_width=True)
        
        # Log access
        auth_manager.log_audit_event(
            user['user_id'],
            "PAGE_ACCESS",
            "finance",
            details="Accessed finance management page"
        )
    else:
        st.error("You don't have permission to view finance management.")

# Reporting Page
elif page == "📊 Reporting":
    if auth_manager.has_permission(user_role, 'view_reports'):
        import reporting_ui
        
        # Check if user can generate reports
        can_generate = auth_manager.has_permission(user_role, 'generate_reports')
        
        if can_generate:
            reporting_ui.render_reporting_module()
        else:
            # Limited reporting view
            st.title("📊 Reporting (Limited Access)")
            st.info("You have limited access to reports. Contact your administrator for full reporting capabilities.")
            
            # Show basic financial summary
            st.subheader("Financial Summary")
            ytd_income, ytd_expenses = finance_manager.get_ytd_summary()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("YTD Income", f"₹{ytd_income:,.2f}")
            with col2:
                st.metric("YTD Expenses", f"₹{ytd_expenses:,.2f}")
            with col3:
                st.metric("YTD Net", f"₹{ytd_income - ytd_expenses:,.2f}")
        
        # Log access
        auth_manager.log_audit_event(
            user['user_id'],
            "PAGE_ACCESS",
            "reporting",
            details="Accessed reporting page"
        )
    else:
        st.error("You don't have permission to view reports.")

# User Management Page
elif page == "👤 User Management":
    if auth_manager.has_permission(user_role, 'manage_users'):
        auth_ui.render_user_management()
        
        # Log access
        auth_manager.log_audit_event(
            user['user_id'],
            "PAGE_ACCESS",
            "user_management",
            details="Accessed user management page"
        )
    else:
        st.error("You don't have permission to manage users.")

# Profile Management Page
elif page == "⚙️ My Profile":
    auth_ui.render_profile_management()
    
    # Log access
    auth_manager.log_audit_event(
        user['user_id'],
        "PAGE_ACCESS",
        "profile",
        details="Accessed profile management page"
    )

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.markdown("### System Information")
st.sidebar.write(f"**Version:** 1.0.0")
st.sidebar.write(f"**User:** {user['username']}")
st.sidebar.write(f"**Role:** {user_role.title()}")
st.sidebar.write(f"**Login Time:** {datetime.now().strftime('%H:%M')}")

# --- Security Headers and Session Management ---
# Auto-logout after inactivity (optional)
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = datetime.now()

# Update last activity
st.session_state.last_activity = datetime.now()

# Check for session timeout (24 hours)
if st.session_state.session_token:
    is_valid, session_data = auth_manager.validate_session(st.session_state.session_token)
    if not is_valid:
        st.warning("Your session has expired. Please log in again.")
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.session_token = None
        st.rerun()

# --- Error Handling ---
try:
    # Main application logic is above
    pass
except Exception as e:
    st.error("An unexpected error occurred. Please contact your administrator.")
    
    # Log error for admin
    if 'user' in st.session_state and st.session_state.user:
        auth_manager.log_audit_event(
            st.session_state.user['user_id'],
            "APPLICATION_ERROR",
            details=f"Error: {str(e)}"
        )
    
    # Show error details to admin users only
    if user_role == 'admin':
        st.exception(e)
