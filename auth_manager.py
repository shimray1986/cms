import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st

DATABASE_NAME = 'ctms.db'

class UserRole:
    """User role constants and permissions."""
    ADMIN = 'admin'
    TREASURER = 'treasurer'
    SECRETARY = 'secretary'
    MEMBER = 'member'
    VIEWER = 'viewer'
    
    @classmethod
    def get_all_roles(cls):
        return [cls.ADMIN, cls.TREASURER, cls.SECRETARY, cls.MEMBER, cls.VIEWER]
    
    @classmethod
    def get_role_permissions(cls, role: str) -> Dict[str, bool]:
        """Get permissions for a specific role."""
        permissions = {
            'view_dashboard': False,
            'view_members': False,
            'add_members': False,
            'edit_members': False,
            'delete_members': False,
            'view_finances': False,
            'add_transactions': False,
            'edit_transactions': False,
            'delete_transactions': False,
            'view_reports': False,
            'generate_reports': False,
            'manage_users': False,
            'system_settings': False
        }
        
        if role == cls.ADMIN:
            # Admin has all permissions
            permissions = {key: True for key in permissions}
        elif role == cls.TREASURER:
            permissions.update({
                'view_dashboard': True,
                'view_members': True,
                'add_members': True,
                'edit_members': True,
                'view_finances': True,
                'add_transactions': True,
                'edit_transactions': True,
                'delete_transactions': True,
                'view_reports': True,
                'generate_reports': True
            })
        elif role == cls.SECRETARY:
            permissions.update({
                'view_dashboard': True,
                'view_members': True,
                'add_members': True,
                'edit_members': True,
                'view_finances': True,
                'view_reports': True,
                'generate_reports': True
            })
        elif role == cls.MEMBER:
            permissions.update({
                'view_dashboard': True,
                'view_members': True,
                'view_finances': True,
                'view_reports': True
            })
        elif role == cls.VIEWER:
            permissions.update({
                'view_dashboard': True,
                'view_reports': True
            })
        
        return permissions

def get_db_connection():
    """Get database connection with row factory for named access."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_auth_tables():
    """Initialize authentication tables in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                full_name TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME
            )
        """)
        
        # Create user sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                resource TEXT,
                resource_id INTEGER,
                details TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        
        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()['user_count']
        
        if user_count == 0:
            create_default_admin()
        
        conn.close()
        return True, "Authentication tables initialized successfully"
    
    except Exception as e:
        return False, f"Error initializing auth tables: {str(e)}"

def create_default_admin():
    """Create default admin user."""
    try:
        username = "admin"
        email = "admin@church.local"
        password = "admin123"  # Should be changed on first login
        full_name = "System Administrator"
        role = UserRole.ADMIN
        
        success, message, user_id = create_user(username, email, password, full_name, role)
        if success:
            log_audit_event(user_id, "USER_CREATED", "users", user_id, "Default admin user created")
        
        return success, message
    
    except Exception as e:
        return False, f"Error creating default admin: {str(e)}"

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash password with salt."""
    if salt is None:
        salt = secrets.token_hex(32)
    
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return password_hash.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, password_hash)

def create_user(username: str, email: str, password: str, full_name: str, role: str) -> Tuple[bool, str, Optional[int]]:
    """Create a new user."""
    try:
        # Validate input
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long", None
        
        if not email or '@' not in email:
            return False, "Valid email address is required", None
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long", None
        
        if role not in UserRole.get_all_roles():
            return False, f"Invalid role. Must be one of: {', '.join(UserRole.get_all_roles())}", None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            return False, "Username or email already exists", None
        
        # Hash password
        password_hash, salt = hash_password(password)
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, role, full_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, salt, role, full_name))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, f"User '{username}' created successfully", user_id
    
    except Exception as e:
        return False, f"Error creating user: {str(e)}", None

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticate user credentials."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user by username
        cursor.execute("""
            SELECT id, username, email, password_hash, salt, role, full_name, 
                   is_active, failed_login_attempts, locked_until
            FROM users 
            WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False, "Invalid username or password", None
        
        user_dict = dict(user)
        
        # Check if account is locked
        if user_dict['locked_until'] and datetime.fromisoformat(user_dict['locked_until']) > datetime.now():
            conn.close()
            return False, "Account is temporarily locked due to too many failed login attempts", None
        
        # Check if account is active
        if not user_dict['is_active']:
            conn.close()
            return False, "Account is deactivated", None
        
        # Verify password
        if not verify_password(password, user_dict['password_hash'], user_dict['salt']):
            # Increment failed login attempts
            failed_attempts = user_dict['failed_login_attempts'] + 1
            locked_until = None
            
            if failed_attempts >= 5:  # Lock account after 5 failed attempts
                locked_until = datetime.now() + timedelta(minutes=30)
            
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = ?, locked_until = ?
                WHERE id = ?
            """, (failed_attempts, locked_until, user_dict['id']))
            conn.commit()
            conn.close()
            
            return False, "Invalid username or password", None
        
        # Reset failed login attempts and update last login
        cursor.execute("""
            UPDATE users 
            SET failed_login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_dict['id'],))
        conn.commit()
        conn.close()
        
        # Remove sensitive data
        user_dict.pop('password_hash')
        user_dict.pop('salt')
        
        return True, "Authentication successful", user_dict
    
    except Exception as e:
        return False, f"Authentication error: {str(e)}", None

def create_session(user_id: int, ip_address: str = None, user_agent: str = None) -> Tuple[bool, str, Optional[str]]:
    """Create a new user session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
        
        # Insert session
        cursor.execute("""
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_token, expires_at, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        return True, "Session created successfully", session_token
    
    except Exception as e:
        return False, f"Error creating session: {str(e)}", None

def validate_session(session_token: str) -> Tuple[bool, Optional[Dict]]:
    """Validate a session token."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.user_id, s.expires_at, u.username, u.email, u.role, u.full_name, u.is_active
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.is_active = TRUE
        """, (session_token,))
        
        session = cursor.fetchone()
        if not session:
            conn.close()
            return False, None
        
        session_dict = dict(session)
        
        # Check if session is expired
        if datetime.fromisoformat(session_dict['expires_at']) < datetime.now():
            # Deactivate expired session
            cursor.execute("UPDATE user_sessions SET is_active = FALSE WHERE session_token = ?", (session_token,))
            conn.commit()
            conn.close()
            return False, None
        
        # Check if user is still active
        if not session_dict['is_active']:
            conn.close()
            return False, None
        
        conn.close()
        return True, session_dict
    
    except Exception as e:
        print(f"Session validation error: {str(e)}")
        return False, None

def logout_user(session_token: str) -> bool:
    """Logout user by deactivating session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE user_sessions SET is_active = FALSE WHERE session_token = ?", (session_token,))
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return False

def get_all_users() -> List[Dict]:
    """Get all users (admin only)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, role, full_name, is_active, 
                   created_at, last_login, failed_login_attempts
            FROM users
            ORDER BY created_at DESC
        """)
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        return []

def update_user(user_id: int, **kwargs) -> Tuple[bool, str]:
    """Update user information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        allowed_fields = ['email', 'role', 'full_name', 'is_active']
        update_fields = []
        update_values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if not update_fields:
            return False, "No valid fields to update"
        
        update_values.append(user_id)
        
        cursor.execute(f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, update_values)
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "User not found"
        
        conn.commit()
        conn.close()
        
        return True, "User updated successfully"
    
    except Exception as e:
        return False, f"Error updating user: {str(e)}"

def change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current password hash and salt
        cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False, "User not found"
        
        # Verify old password
        if not verify_password(old_password, user['password_hash'], user['salt']):
            conn.close()
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long"
        
        # Hash new password
        new_password_hash, new_salt = hash_password(new_password)
        
        # Update password
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_password_hash, new_salt, user_id))
        
        conn.commit()
        conn.close()
        
        return True, "Password changed successfully"
    
    except Exception as e:
        return False, f"Error changing password: {str(e)}"

def log_audit_event(user_id: Optional[int], action: str, resource: str = None, 
                   resource_id: int = None, details: str = None, ip_address: str = None):
    """Log an audit event."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, resource, resource_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, resource, resource_id, details, ip_address))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        print(f"Audit log error: {str(e)}")

def get_audit_log(limit: int = 100) -> List[Dict]:
    """Get audit log entries."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.*, u.username, u.full_name
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return logs
    
    except Exception as e:
        print(f"Error getting audit log: {str(e)}")
        return []

def has_permission(user_role: str, permission: str) -> bool:
    """Check if user role has specific permission."""
    permissions = UserRole.get_role_permissions(user_role)
    return permissions.get(permission, False)

# Streamlit integration functions
def init_session_state():
    """Initialize Streamlit session state for authentication."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None

def check_authentication():
    """Check if user is authenticated in Streamlit session."""
    init_session_state()
    
    if st.session_state.authenticated and st.session_state.session_token:
        # Validate session token
        is_valid, user_data = validate_session(st.session_state.session_token)
        if is_valid:
            st.session_state.user = user_data
            return True
        else:
            # Session expired or invalid
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.session_token = None
    
    return False

def require_permission(permission: str):
    """Decorator to require specific permission for Streamlit pages."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.error("Please log in to access this page.")
                return
            
            user_role = st.session_state.user.get('role', 'viewer')
            if not has_permission(user_role, permission):
                st.error("You don't have permission to access this page.")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Testing and initialization
if __name__ == '__main__':
    print("Testing Authentication Manager...")
    
    # Initialize tables
    success, message = initialize_auth_tables()
    print(f"Initialize tables: {success}, {message}")
    
    # Test user creation
    success, message, user_id = create_user("testuser", "test@example.com", "password123", "Test User", UserRole.MEMBER)
    print(f"Create user: {success}, {message}, ID: {user_id}")
    
    # Test authentication
    success, message, user_data = authenticate_user("testuser", "password123")
    print(f"Authenticate user: {success}, {message}")
    
    if success and user_data:
        # Test session creation
        success, message, session_token = create_session(user_data['id'])
        print(f"Create session: {success}, {message}")
        
        if success and session_token:
            # Test session validation
            is_valid, session_data = validate_session(session_token)
            print(f"Validate session: {is_valid}, User: {session_data['username'] if session_data else 'None'}")
    
    # Test permissions
    admin_perms = UserRole.get_role_permissions(UserRole.ADMIN)
    print(f"Admin permissions: {sum(admin_perms.values())} out of {len(admin_perms)}")
    
    member_perms = UserRole.get_role_permissions(UserRole.MEMBER)
    print(f"Member permissions: {sum(member_perms.values())} out of {len(member_perms)}")
    
    print("Authentication Manager test completed successfully!")
