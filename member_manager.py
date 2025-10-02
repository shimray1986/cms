import sqlite3
import re
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple

DATABASE_NAME = 'ctms.db'

def get_db_connection():
    """Get database connection with row factory for named access."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return True  # Email is optional
    # fixed regex (removed stray rupee symbol)
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return True  # Phone is optional
    # Fixed phone regex and allow optional leading +, digits, spaces, hyphens, parens
    pattern = r'^\+?[0-9\s\-\(\)]{7,20}$'
    return re.match(pattern, phone) is not None

def validate_member_data(name: str, email_address: str, mobile_no: str, 
                        date_of_birth: str, join_date: str) -> Tuple[bool, str]:
    """Validate member data and return validation result."""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    
    if email_address and not validate_email(email_address):
        return False, "Invalid email format"
    
    if mobile_no and not validate_phone(mobile_no):
        return False, "Invalid phone number format"
    
    try:
        birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        join_date_obj = datetime.strptime(join_date, "%Y-%m-%d").date()
        
        if birth_date > date.today():
            return False, "Date of birth cannot be in the future"
        
        if join_date_obj > date.today():
            return False, "Join date cannot be in the future"
        
        # Check if person is at least 1 year old when joining
        age_at_join = (join_date_obj - birth_date).days / 365.25
        if age_at_join < 1:
            return False, "Member must be at least 1 year old when joining"
            
    except ValueError:
        return False, "Invalid date format"
    
    return True, ""

def add_member(name: str, mobile_no: str, email_address: str, physical_address: str, 
               join_date: str, date_of_birth: str, gender: str, membership_status: str, 
               baptized: bool, baptism_date: Optional[str], emergency_contact_name: str, 
               emergency_contact_number: str, notes: str) -> Tuple[bool, str, Optional[int]]:
    """
    Add a new member to the database.
    Returns: (success: bool, message: str, member_id: Optional[int])
    """
    # Validate input data
    is_valid, error_msg = validate_member_data(name, email_address, mobile_no, date_of_birth, join_date)
    if not is_valid:
        return False, error_msg, None
    
    # Check for duplicate email if provided
    if email_address:
        existing_member = get_member_by_email(email_address)
        if existing_member:
            return False, f"A member with email '{email_address}' already exists", None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO members (name, mobile_no, email_address, physical_address, 
               join_date, date_of_birth, gender, membership_status, baptized, baptism_date, 
               emergency_contact_name, emergency_contact_number, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (name.strip(), mobile_no, email_address, physical_address, join_date, date_of_birth, 
             gender, membership_status, int(bool(baptized)), baptism_date, emergency_contact_name, 
             emergency_contact_number, notes)
        )
        conn.commit()
        member_id = cursor.lastrowid
        conn.close()
        return True, f"Member '{name}' added successfully", member_id
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}", None

def update_member(member_id: int, name: str, mobile_no: str, email_address: str, 
                 physical_address: str, join_date: str, date_of_birth: str, gender: str, 
                 membership_status: str, baptized: bool, baptism_date: Optional[str], 
                 emergency_contact_name: str, emergency_contact_number: str, 
                 notes: str) -> Tuple[bool, str]:
    """
    Update an existing member.
    Returns: (success: bool, message: str)
    """
    # Validate input data
    is_valid, error_msg = validate_member_data(name, email_address, mobile_no, date_of_birth, join_date)
    if not is_valid:
        return False, error_msg
    
    # Check for duplicate email if provided (excluding current member)
    if email_address:
        existing_member = get_member_by_email(email_address)
        if existing_member and existing_member['id'] != member_id:
            return False, f"A member with email '{email_address}' already exists"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE members SET
               name = ?, mobile_no = ?, email_address = ?, physical_address = ?, 
               join_date = ?, date_of_birth = ?, gender = ?, membership_status = ?, 
               baptized = ?, baptism_date = ?, emergency_contact_name = ?, 
               emergency_contact_number = ?, notes = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (name.strip(), mobile_no, email_address, physical_address, join_date, date_of_birth, 
             gender, membership_status, int(bool(baptized)), baptism_date, emergency_contact_name, 
             emergency_contact_number, notes, member_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Member not found"
        
        conn.commit()
        conn.close()
        return True, f"Member '{name}' updated successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def delete_member(member_id: int) -> Tuple[bool, str]:
    """
    Delete a member from the database.
    Returns: (success: bool, message: str)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First get the member name for the success message
        cursor.execute("SELECT name FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if not member:
            conn.close()
            return False, "Member not found"
        
        member_name = member['name']
        
        # Delete the member
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        conn.close()
        return True, f"Member '{member_name}' deleted successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def get_all_members() -> List[Dict]:
    """Get all members from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members ORDER BY name")
        members = cursor.fetchall()
        conn.close()
        return [dict(member) for member in members]
    except sqlite3.Error:
        return []

def get_member_by_id(member_id: int) -> Optional[Dict]:
    """Get a specific member by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        conn.close()
        return dict(member) if member else None
    except sqlite3.Error:
        return None

def get_member_by_email(email: str) -> Optional[Dict]:
    """Get a member by email address."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE email_address = ?", (email,))
        member = cursor.fetchone()
        conn.close()
        return dict(member) if member else None
    except sqlite3.Error:
        return None

def search_members(search_term: str) -> List[Dict]:
    """Search members by name, email, or phone."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        search_pattern = f"%{search_term}%"
        cursor.execute(
            """SELECT * FROM members 
               WHERE name LIKE ? OR email_address LIKE ? OR mobile_no LIKE ?
               ORDER BY name""",
            (search_pattern, search_pattern, search_pattern)
        )
        members = cursor.fetchall()
        conn.close()
        return [dict(member) for member in members]
    except sqlite3.Error:
        return []

def get_members_by_status(status: str) -> List[Dict]:
    """Get members by membership status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE membership_status = ? ORDER BY name", (status,))
        members = cursor.fetchall()
        conn.close()
        return [dict(member) for member in members]
    except sqlite3.Error:
        return []

def get_baptized_members() -> List[Dict]:
    """Get all baptized members."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM members WHERE baptized = 1 ORDER BY baptism_date DESC")
        members = cursor.fetchall()
        conn.close()
        return [dict(member) for member in members]
    except sqlite3.Error:
        return []

def get_member_statistics() -> Dict:
    """Get member statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total members
        cursor.execute("SELECT COUNT(*) as total FROM members")
        total = cursor.fetchone()['total']
        
        # Members by status
        cursor.execute("""
            SELECT membership_status, COUNT(*) as count 
            FROM members 
            GROUP BY membership_status
        """)
        status_counts = {row['membership_status']: row['count'] for row in cursor.fetchall()}
        
        # Baptized members
        cursor.execute("SELECT COUNT(*) as baptized FROM members WHERE baptized = 1")
        baptized = cursor.fetchone()['baptized']
        
        # Members by gender
        cursor.execute("""
            SELECT gender, COUNT(*) as count 
            FROM members 
            GROUP BY gender
        """)
        gender_counts = {row['gender']: row['count'] for row in cursor.fetchall()}
        
        # Recent joins (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as recent 
            FROM members 
            WHERE join_date >= date('now', '-30 days')
        """)
        recent_joins = cursor.fetchone()['recent']
        
        conn.close()
        
        return {
            'total_members': total,
            'status_breakdown': status_counts,
            'baptized_count': baptized,
            'gender_breakdown': gender_counts,
            'recent_joins': recent_joins
        }
    except sqlite3.Error:
        return {}

def get_upcoming_birthdays(days_ahead: int = 30) -> List[Dict]:
    """Get members with upcoming birthdays."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *, 
                   strftime('%m-%d', date_of_birth) as birth_md,
                   strftime('%m-%d', 'now') as today_md,
                   CASE 
                       WHEN strftime('%m-%d', date_of_birth) >= strftime('%m-%d', 'now') 
                       THEN julianday(strftime('%Y', 'now') || '-' || strftime('%m-%d', date_of_birth)) - julianday('now')
                       ELSE julianday(strftime('%Y', 'now', '+1 year') || '-' || strftime('%m-%d', date_of_birth)) - julianday('now')
                   END as days_until_birthday
            FROM members 
            WHERE days_until_birthday <= ?
            ORDER BY days_until_birthday
        """, (days_ahead,))
        members = cursor.fetchall()
        conn.close()
        return [dict(member) for member in members]
    except sqlite3.Error:
        return []

