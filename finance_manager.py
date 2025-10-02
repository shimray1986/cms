import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import calendar

DATABASE_NAME = 'ctms.db'

def get_db_connection():
    """Get database connection with row factory for named access."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def validate_transaction_data(transaction_date: str, amount: float, category_id: int) -> Tuple[bool, str]:
    """Validate transaction data and return validation result."""
    if amount <= 0:
        return False, "Amount must be greater than zero"
    
    try:
        trans_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
        if trans_date > date.today():
            return False, "Transaction date cannot be in the future"
    except ValueError:
        return False, "Invalid date format"
    
    if not category_id:
        return False, "Category is required"
    
    return True, ""

def get_income_categories() -> List[Dict]:
    """Get all income categories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income_categories ORDER BY name")
        categories = cursor.fetchall()
        conn.close()
        return [dict(cat) for cat in categories]
    except sqlite3.Error:
        return []

def get_expense_categories() -> List[Dict]:
    """Get all expense categories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expense_categories ORDER BY name")
        categories = cursor.fetchall()
        conn.close()
        return [dict(cat) for cat in categories]
    except sqlite3.Error:
        return []

def add_income_category(name: str) -> Tuple[bool, str, Optional[int]]:
    """Add a new income category."""
    if not name or len(name.strip()) < 2:
        return False, "Category name must be at least 2 characters long", None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO income_categories (name) VALUES (?)", (name.strip(),))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return True, f"Income category '{name}' added successfully", category_id
    except sqlite3.IntegrityError:
        return False, f"Income category '{name}' already exists", None
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}", None

def add_expense_category(name: str) -> Tuple[bool, str, Optional[int]]:
    """Add a new expense category."""
    if not name or len(name.strip()) < 2:
        return False, "Category name must be at least 2 characters long", None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (name.strip(),))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return True, f"Expense category '{name}' added successfully", category_id
    except sqlite3.IntegrityError:
        return False, f"Expense category '{name}' already exists", None
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}", None

def add_transaction(transaction_date: str, transaction_type: str, category_id: int, 
                   category_name: str, amount: float, description: str, 
                   member_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
    """
    Add a new transaction to the database.
    Returns: (success: bool, message: str, transaction_id: Optional[int])
    """
    # Validate input data
    is_valid, error_msg = validate_transaction_data(transaction_date, amount, category_id)
    if not is_valid:
        return False, error_msg, None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions (transaction_date, transaction_type, category_id, 
               category_name, amount, description, member_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (transaction_date, transaction_type, category_id, category_name, 
             amount, description, member_id)
        )
        conn.commit()
        transaction_id = cursor.lastrowid
        conn.close()
        return True, f"{transaction_type} of ₹{amount:.2f} added successfully", transaction_id
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}", None

def update_transaction(transaction_id: int, transaction_date: str, transaction_type: str, 
                      category_id: int, category_name: str, amount: float, 
                      description: str, member_id: Optional[int] = None) -> Tuple[bool, str]:
    """Update an existing transaction."""
    # Validate input data
    is_valid, error_msg = validate_transaction_data(transaction_date, amount, category_id)
    if not is_valid:
        return False, error_msg
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE transactions SET
               transaction_date = ?, transaction_type = ?, category_id = ?, 
               category_name = ?, amount = ?, description = ?, member_id = ?
               WHERE id = ?""",
            (transaction_date, transaction_type, category_id, category_name, 
             amount, description, member_id, transaction_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Transaction not found"
        
        conn.commit()
        conn.close()
        return True, f"Transaction updated successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def delete_transaction(transaction_id: int) -> Tuple[bool, str]:
    """Delete a transaction from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First get the transaction details for the success message
        cursor.execute("SELECT transaction_type, amount FROM transactions WHERE id = ?", (transaction_id,))
        transaction = cursor.fetchone()
        if not transaction:
            conn.close()
            return False, "Transaction not found"
        
        # Delete the transaction
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()
        return True, f"{transaction['transaction_type']} of ₹{transaction['amount']:.2f} deleted successfully"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"

def get_all_transactions() -> List[Dict]:
    """Get all transactions from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY transaction_date DESC, id DESC")
        transactions = cursor.fetchall()
        conn.close()
        return [dict(t) for t in transactions]
    except sqlite3.Error:
        return []

def get_transaction_by_id(transaction_id: int) -> Optional[Dict]:
    """Get a specific transaction by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        transaction = cursor.fetchone()
        conn.close()
        return dict(transaction) if transaction else None
    except sqlite3.Error:
        return None

def get_transactions_by_date_range(start_date: str, end_date: str) -> List[Dict]:
    """Get transactions within a date range."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE transaction_date BETWEEN ? AND ? ORDER BY transaction_date DESC, id DESC",
            (start_date, end_date)
        )
        transactions = cursor.fetchall()
        conn.close()
        return [dict(t) for t in transactions]
    except sqlite3.Error:
        return []

def get_transactions_by_member(member_id: int) -> List[Dict]:
    """Get all transactions linked to a specific member."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE member_id = ? ORDER BY transaction_date DESC, id DESC",
            (member_id,)
        )
        transactions = cursor.fetchall()
        conn.close()
        return [dict(t) for t in transactions]
    except sqlite3.Error:
        return []

def get_transactions_by_category(category_id: int, transaction_type: str) -> List[Dict]:
    """Get all transactions for a specific category."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE category_id = ? AND transaction_type = ? ORDER BY transaction_date DESC, id DESC",
            (category_id, transaction_type)
        )
        transactions = cursor.fetchall()
        conn.close()
        return [dict(t) for t in transactions]
    except sqlite3.Error:
        return []

def get_ytd_summary() -> Tuple[float, float]:
    """Get year-to-date income and expense summary."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        current_year = datetime.now().year
        start_of_year = f'{current_year}-01-01'
        end_of_year = f'{current_year}-12-31'

        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Income' AND transaction_date BETWEEN ? AND ?",
            (start_of_year, end_of_year)
        )
        ytd_income = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Expense' AND transaction_date BETWEEN ? AND ?",
            (start_of_year, end_of_year)
        )
        ytd_expenses = cursor.fetchone()[0] or 0

        conn.close()
        return float(ytd_income), float(ytd_expenses)
    except sqlite3.Error:
        return 0.0, 0.0

def get_current_month_summary() -> Tuple[float, float]:
    """Get current month income and expense summary."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1).strftime('%Y-%m-%d')
        last_day = calendar.monthrange(current_date.year, current_date.month)[1]
        end_of_month = current_date.replace(day=last_day).strftime('%Y-%m-%d')

        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Income' AND transaction_date BETWEEN ? AND ?",
            (start_of_month, end_of_month)
        )
        month_income = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Expense' AND transaction_date BETWEEN ? AND ?",
            (start_of_month, end_of_month)
        )
        month_expenses = cursor.fetchone()[0] or 0

        conn.close()
        return float(month_income), float(month_expenses)
    except sqlite3.Error:
        return 0.0, 0.0

def get_recent_transactions(limit: int = 10) -> List[Dict]:
    """Get the most recent transactions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions ORDER BY transaction_date DESC, id DESC LIMIT ?", (limit,))
        transactions = cursor.fetchall()
        conn.close()
        return [dict(t) for t in transactions]
    except sqlite3.Error:
        return []

def get_monthly_summary_by_category(year: int) -> Dict:
    """Get monthly summary grouped by category for a specific year."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 
                strftime('%m', transaction_date) as month,
                transaction_type,
                category_name,
                SUM(amount) as total_amount
               FROM transactions 
               WHERE strftime('%Y', transaction_date) = ?
               GROUP BY month, transaction_type, category_name
               ORDER BY month, transaction_type, category_name""",
            (str(year),)
        )
        results = cursor.fetchall()
        conn.close()
        return [dict(r) for r in results]
    except sqlite3.Error:
        return []

def get_financial_statistics() -> Dict:
    """Get comprehensive financial statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) as total FROM transactions")
        total_transactions = cursor.fetchone()['total']
        
        # Income vs Expense counts
        cursor.execute("""
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total_amount
            FROM transactions 
            GROUP BY transaction_type
        """)
        type_summary = {row['transaction_type']: {'count': row['count'], 'total': row['total_amount']} 
                       for row in cursor.fetchall()}
        
        # Top income categories
        cursor.execute("""
            SELECT category_name, SUM(amount) as total_amount, COUNT(*) as count
            FROM transactions 
            WHERE transaction_type = 'Income'
            GROUP BY category_name
            ORDER BY total_amount DESC
            LIMIT 5
        """)
        top_income_categories = [dict(row) for row in cursor.fetchall()]
        
        # Top expense categories
        cursor.execute("""
            SELECT category_name, SUM(amount) as total_amount, COUNT(*) as count
            FROM transactions 
            WHERE transaction_type = 'Expense'
            GROUP BY category_name
            ORDER BY total_amount DESC
            LIMIT 5
        """)
        top_expense_categories = [dict(row) for row in cursor.fetchall()]
        
        # Average transaction amounts
        cursor.execute("""
            SELECT transaction_type, AVG(amount) as avg_amount
            FROM transactions
            GROUP BY transaction_type
        """)
        avg_amounts = {row['transaction_type']: row['avg_amount'] for row in cursor.fetchall()}
        
        # Recent activity (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as recent_count, SUM(amount) as recent_total
            FROM transactions 
            WHERE transaction_date >= date('now', '-30 days')
        """)
        recent_activity = dict(cursor.fetchone())
        
        conn.close()
        
        return {
            'total_transactions': total_transactions,
            'type_summary': type_summary,
            'top_income_categories': top_income_categories,
            'top_expense_categories': top_expense_categories,
            'average_amounts': avg_amounts,
            'recent_activity': recent_activity
        }
    except sqlite3.Error:
        return {}

# Example usage and testing
if __name__ == '__main__':
    print("Testing Finance Manager...")
    
    # Test adding categories
    success, msg, cat_id = add_income_category("Test Income Category")
    print(f"Add income category: {success}, {msg}, ID: {cat_id}")
    
    success, msg, cat_id = add_expense_category("Test Expense Category")
    print(f"Add expense category: {success}, {msg}, ID: {cat_id}")
    
    # Test adding transaction
    income_cats = get_income_categories()
    if income_cats:
        success, msg, txn_id = add_transaction(
            "2024-09-30", "Income", income_cats[0]['id'], 
            income_cats[0]['name'], 100.50, "Test transaction", None
        )
        print(f"Add transaction: {success}, {msg}, ID: {txn_id}")
        
        if txn_id:
            # Test updating transaction
            success, msg = update_transaction(
                txn_id, "2024-09-30", "Income", income_cats[0]['id'],
                income_cats[0]['name'], 150.75, "Updated test transaction", None
            )
            print(f"Update transaction: {success}, {msg}")
            
            # Test deleting transaction
            success, msg = delete_transaction(txn_id)
            print(f"Delete transaction: {success}, {msg}")
    
    # Get statistics
    stats = get_financial_statistics()
    print(f"Financial statistics: {stats}")
    
    # Get summaries
    ytd_income, ytd_expenses = get_ytd_summary()
    print(f"YTD Summary - Income: ₹{ytd_income:.2f}, Expenses: ₹{ytd_expenses:.2f}")
    
    month_income, month_expenses = get_current_month_summary()
    print(f"Current Month - Income: ₹{month_income:.2f}, Expenses: ₹{month_expenses:.2f}")
