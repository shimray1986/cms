import streamlit as st
import pandas as pd
from datetime import datetime
import auth_manager
from auth_manager import UserRole

def render_login_page():
    """Render the login page."""
    st.set_page_config(page_title="CMS - Login", layout="centered")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🏛️ Church Management System")
        st.markdown("### Please log in to continue")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_login, col_help = st.columns([2, 1])
            
            with col_login:
                login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            with col_help:
                if st.form_submit_button("Help", use_container_width=True):
                    show_login_help()
            
            if login_button:
                if username and password:
                    handle_login(username, password)
                else:
                    st.error("Please enter both username and password.")
        
        # Show default credentials for demo
        with st.expander("🔧 Demo Credentials"):
            st.info("""
            **Default Admin Account:**
            - Username: `admin`
            - Password: `admin123`
            
            ⚠️ **Important:** Change the default password after first login for security.
            """)

def handle_login(username: str, password: str):
    """Handle user login attempt."""
    with st.spinner("Authenticating..."):
        success, message, user_data = auth_manager.authenticate_user(username, password)
        
        if success and user_data:
            # Create session
            session_success, session_message, session_token = auth_manager.create_session(
                user_data['id'], 
                ip_address=st.session_state.get('client_ip', 'unknown')
            )
            
            if session_success and session_token:
                # Set session state
                st.session_state.authenticated = True
                st.session_state.user = user_data
                st.session_state.session_token = session_token
                
                # Log audit event
                auth_manager.log_audit_event(
                    user_data['id'], 
                    "LOGIN_SUCCESS", 
                    details=f"User {username} logged in successfully"
                )
                
                st.success(f"Welcome, {user_data['full_name']}!")
                st.rerun()
            else:
                st.error("Failed to create session. Please try again.")
        else:
            # Log failed login attempt
            auth_manager.log_audit_event(
                None, 
                "LOGIN_FAILED", 
                details=f"Failed login attempt for username: {username}"
            )
            st.error(message)

def show_login_help():
    """Show login help information."""
    st.info("""
    **Need Help Logging In?**
    
    1. **Forgot Password?** Contact your system administrator
    2. **Account Locked?** Wait 30 minutes or contact admin
    3. **New User?** Ask admin to create your account
    4. **Technical Issues?** Check your internet connection
    
    **User Roles:**
    - **Admin:** Full system access
    - **Treasurer:** Financial management
    - **Secretary:** Member and report management  
    - **Member:** View access to most features
    - **Viewer:** Read-only dashboard access
    """)

def render_user_management():
    """Render user management interface (admin only)."""
    if not auth_manager.check_authentication():
        st.error("Please log in to access this page.")
        return
    
    user_role = st.session_state.user.get('role', 'viewer')
    if not auth_manager.has_permission(user_role, 'manage_users'):
        st.error("You don't have permission to manage users.")
        return
    
    st.title("👥 User Management")
    
    # Create tabs for different user management functions
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Users", "➕ Add User", "🔐 Permissions", "📋 Audit Log"])
    
    with tab1:
        render_users_list()
    
    with tab2:
        render_add_user_form()
    
    with tab3:
        render_permissions_overview()
    
    with tab4:
        render_audit_log()

def render_users_list():
    """Render list of all users."""
    st.subheader("System Users")
    
    users = auth_manager.get_all_users()
    
    if users:
        # Convert to DataFrame for better display
        df = pd.DataFrame(users)
        
        # Format columns
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        df['last_login'] = pd.to_datetime(df['last_login'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        df['last_login'] = df['last_login'].fillna('Never')
        df['is_active'] = df['is_active'].map({True: '✅ Active', False: '❌ Inactive'})
        
        # Rename columns for display
        display_columns = {
            'id': 'ID',
            'username': 'Username',
            'full_name': 'Full Name',
            'email': 'Email',
            'role': 'Role',
            'is_active': 'Status',
            'created_at': 'Created',
            'last_login': 'Last Login',
            'failed_login_attempts': 'Failed Attempts'
        }
        
        df_display = df.rename(columns=display_columns)
        
        # Display users table
        st.dataframe(df_display, use_container_width=True)
        
        # User actions
        st.subheader("User Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user_id = st.selectbox(
                "Select User for Actions",
                options=df['id'].tolist(),
                format_func=lambda x: f"{df[df['id']==x]['username'].iloc[0]} - {df[df['id']==x]['full_name'].iloc[0]}"
            )
        
        with col2:
            action = st.selectbox(
                "Action",
                ["Edit User", "Activate/Deactivate", "Reset Password", "Change Role"]
            )
        
        if st.button("Execute Action", type="primary"):
            execute_user_action(selected_user_id, action, df)
    
    else:
        st.info("No users found in the system.")

def execute_user_action(user_id: int, action: str, users_df: pd.DataFrame):
    """Execute user management actions."""
    user_data = users_df[users_df['id'] == user_id].iloc[0]
    
    if action == "Edit User":
        render_edit_user_form(user_id, user_data)
    elif action == "Activate/Deactivate":
        toggle_user_status(user_id, user_data)
    elif action == "Reset Password":
        reset_user_password(user_id, user_data)
    elif action == "Change Role":
        render_change_role_form(user_id, user_data)

def render_edit_user_form(user_id: int, user_data: pd.Series):
    """Render edit user form."""
    st.subheader(f"Edit User: {user_data['username']}")
    
    with st.form(f"edit_user_{user_id}"):
        new_email = st.text_input("Email", value=user_data['email'])
        new_full_name = st.text_input("Full Name", value=user_data['full_name'])
        new_role = st.selectbox("Role", UserRole.get_all_roles(), index=UserRole.get_all_roles().index(user_data['role']))
        
        if st.form_submit_button("Update User"):
            success, message = auth_manager.update_user(
                user_id,
                email=new_email,
                full_name=new_full_name,
                role=new_role
            )
            
            if success:
                st.success(message)
                auth_manager.log_audit_event(
                    st.session_state.user['user_id'],
                    "USER_UPDATED",
                    "users",
                    user_id,
                    f"Updated user {user_data['username']}"
                )
                st.rerun()
            else:
                st.error(message)

def toggle_user_status(user_id: int, user_data: pd.Series):
    """Toggle user active status."""
    current_status = user_data['is_active'] == '✅ Active'
    new_status = not current_status
    
    success, message = auth_manager.update_user(user_id, is_active=new_status)
    
    if success:
        status_text = "activated" if new_status else "deactivated"
        st.success(f"User {user_data['username']} has been {status_text}.")
        auth_manager.log_audit_event(
            st.session_state.user['user_id'],
            "USER_STATUS_CHANGED",
            "users",
            user_id,
            f"User {user_data['username']} {status_text}"
        )
        st.rerun()
    else:
        st.error(message)

def reset_user_password(user_id: int, user_data: pd.Series):
    """Reset user password."""
    st.warning("⚠️ This will reset the user's password to a temporary password.")
    
    if st.button("Confirm Password Reset", type="secondary"):
        # Generate temporary password
        import secrets
        temp_password = secrets.token_urlsafe(8)
        
        # Update password (this would need to be implemented in auth_manager)
        st.info(f"**Temporary Password:** `{temp_password}`")
        st.info("Please share this password securely with the user and ask them to change it on first login.")
        
        auth_manager.log_audit_event(
            st.session_state.user['user_id'],
            "PASSWORD_RESET",
            "users",
            user_id,
            f"Password reset for user {user_data['username']}"
        )

def render_change_role_form(user_id: int, user_data: pd.Series):
    """Render change role form."""
    st.subheader(f"Change Role for: {user_data['username']}")
    
    current_role = user_data['role']
    st.info(f"Current Role: **{current_role}**")
    
    new_role = st.selectbox(
        "New Role",
        UserRole.get_all_roles(),
        index=UserRole.get_all_roles().index(current_role)
    )
    
    if new_role != current_role:
        if st.button("Change Role", type="primary"):
            success, message = auth_manager.update_user(user_id, role=new_role)
            
            if success:
                st.success(f"Role changed from {current_role} to {new_role}")
                auth_manager.log_audit_event(
                    st.session_state.user['user_id'],
                    "ROLE_CHANGED",
                    "users",
                    user_id,
                    f"Role changed from {current_role} to {new_role} for user {user_data['username']}"
                )
                st.rerun()
            else:
                st.error(message)

def render_add_user_form():
    """Render add new user form."""
    st.subheader("Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", help="Must be at least 3 characters")
            email = st.text_input("Email", help="Valid email address required")
            full_name = st.text_input("Full Name")
        
        with col2:
            password = st.text_input("Password", type="password", help="Must be at least 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", UserRole.get_all_roles(), index=UserRole.get_all_roles().index(UserRole.VIEWER))
        
        if st.form_submit_button("Create User", type="primary"):
            # Validate inputs
            if not all([username, email, full_name, password, confirm_password]):
                st.error("All fields are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message, user_id = auth_manager.create_user(username, email, password, full_name, role)
                
                if success:
                    st.success(message)
                    auth_manager.log_audit_event(
                        st.session_state.user['user_id'],
                        "USER_CREATED",
                        "users",
                        user_id,
                        f"Created new user: {username} with role: {role}"
                    )
                    st.rerun()
                else:
                    st.error(message)

def render_permissions_overview():
    """Render permissions overview for all roles."""
    st.subheader("Role Permissions Overview")
    
    # Create permissions matrix
    all_roles = UserRole.get_all_roles()
    permissions_data = []
    
    # Get all possible permissions
    sample_permissions = UserRole.get_role_permissions(UserRole.ADMIN)
    
    for permission in sample_permissions.keys():
        row = {'Permission': permission.replace('_', ' ').title()}
        for role in all_roles:
            role_permissions = UserRole.get_role_permissions(role)
            row[role.title()] = '✅' if role_permissions.get(permission, False) else '❌'
        permissions_data.append(row)
    
    df_permissions = pd.DataFrame(permissions_data)
    st.dataframe(df_permissions, use_container_width=True)
    
    # Role descriptions
    st.subheader("Role Descriptions")
    
    role_descriptions = {
        UserRole.ADMIN: "Full system access including user management and system settings",
        UserRole.TREASURER: "Complete financial management with transaction and reporting capabilities",
        UserRole.SECRETARY: "Member management and reporting access without financial transaction control",
        UserRole.MEMBER: "View access to dashboard, members, finances, and reports",
        UserRole.VIEWER: "Limited read-only access to dashboard and reports"
    }
    
    for role, description in role_descriptions.items():
        st.write(f"**{role.title()}:** {description}")

def render_audit_log():
    """Render audit log."""
    st.subheader("System Audit Log")
    
    # Get audit log entries
    log_entries = auth_manager.get_audit_log(limit=100)
    
    if log_entries:
        df_log = pd.DataFrame(log_entries)
        
        # Format timestamp
        df_log['timestamp'] = pd.to_datetime(df_log['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Select columns for display
        display_columns = ['timestamp', 'username', 'full_name', 'action', 'resource', 'details']
        available_columns = [col for col in display_columns if col in df_log.columns]
        
        df_display = df_log[available_columns].fillna('')
        
        # Rename columns
        column_names = {
            'timestamp': 'Timestamp',
            'username': 'Username',
            'full_name': 'Full Name',
            'action': 'Action',
            'resource': 'Resource',
            'details': 'Details'
        }
        
        df_display = df_display.rename(columns=column_names)
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            action_filter = st.selectbox(
                "Filter by Action",
                ['All'] + list(df_log['action'].unique())
            )
        
        with col2:
            user_filter = st.selectbox(
                "Filter by User",
                ['All'] + list(df_log['username'].dropna().unique())
            )
        
        # Apply filters
        filtered_df = df_display.copy()
        
        if action_filter != 'All':
            filtered_df = filtered_df[df_log['action'] == action_filter]
        
        if user_filter != 'All':
            filtered_df = filtered_df[df_log['username'] == user_filter]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Export option
        if st.button("Export Audit Log to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    else:
        st.info("No audit log entries found.")

def render_profile_management():
    """Render user profile management."""
    if not auth_manager.check_authentication():
        st.error("Please log in to access this page.")
        return
    
    st.title("👤 My Profile")
    
    user = st.session_state.user
    
    # Profile information
    st.subheader("Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Username:** {user['username']}")
        st.info(f"**Full Name:** {user['full_name']}")
        st.info(f"**Email:** {user['email']}")
    
    with col2:
        st.info(f"**Role:** {user['role'].title()}")
        st.info(f"**Last Login:** {user.get('last_login', 'N/A')}")
        st.info(f"**Account Status:** {'Active' if user.get('is_active', True) else 'Inactive'}")
    
    # Change password
    st.subheader("Change Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if not all([current_password, new_password, confirm_new_password]):
                st.error("All password fields are required.")
            elif new_password != confirm_new_password:
                st.error("New passwords do not match.")
            elif len(new_password) < 6:
                st.error("New password must be at least 6 characters long.")
            else:
                success, message = auth_manager.change_password(
                    user['user_id'], current_password, new_password
                )
                
                if success:
                    st.success(message)
                    auth_manager.log_audit_event(
                        user['user_id'],
                        "PASSWORD_CHANGED",
                        details="User changed their own password"
                    )
                else:
                    st.error(message)

def render_logout_button():
    """Render logout button in sidebar."""
    if auth_manager.check_authentication():
        st.sidebar.markdown("---")
        user = st.session_state.user
        st.sidebar.write(f"👤 **{user['full_name']}**")
        st.sidebar.write(f"Role: {user['role'].title()}")
        
        if st.sidebar.button("🚪 Logout", type="secondary"):
            # Logout user
            if st.session_state.session_token:
                auth_manager.logout_user(st.session_state.session_token)
            
            # Log audit event
            auth_manager.log_audit_event(
                user['user_id'],
                "LOGOUT",
                details=f"User {user['username']} logged out"
            )
            
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.session_token = None
            
            st.rerun()

def check_page_permission(permission: str) -> bool:
    """Check if current user has permission for a page."""
    if not auth_manager.check_authentication():
        return False
    
    user_role = st.session_state.user.get('role', 'viewer')
    return auth_manager.has_permission(user_role, permission)
