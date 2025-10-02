import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
import calendar
import plotly.express as px

DATABASE_NAME = 'ctms.db'

def get_db_connection():
    """Get database connection with row factory for named access."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_overview() -> Dict:
    """Get comprehensive dashboard overview with key metrics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Current date info
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        # Member statistics
        cursor.execute("SELECT COUNT(*) as total_members FROM members")
        total_members = cursor.fetchone()['total_members']
        
        cursor.execute("SELECT COUNT(*) as active_members FROM members WHERE membership_status = 'Active'")
        active_members = cursor.fetchone()['active_members']
        
        cursor.execute("SELECT COUNT(*) as baptized_members FROM members WHERE baptized = 1")
        baptized_members = cursor.fetchone()['baptized_members']
        
        # Recent member additions (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as recent_members 
            FROM members 
            WHERE join_date >= date('now', '-30 days')
        """)
        recent_members = cursor.fetchone()['recent_members']
        
        # Financial statistics - Year to Date
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as ytd_income,
                SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as ytd_expenses,
                COUNT(*) as total_transactions
            FROM transactions 
            WHERE strftime('%Y', transaction_date) = ?
        """, (str(current_year),))
        
        ytd_result = cursor.fetchone()
        ytd_income = ytd_result['ytd_income'] or 0
        ytd_expenses = ytd_result['ytd_expenses'] or 0
        total_transactions = ytd_result['total_transactions']
        ytd_net = ytd_income - ytd_expenses
        
        # Current month financial data
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as month_income,
                SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as month_expenses,
                COUNT(*) as month_transactions
            FROM transactions 
            WHERE strftime('%Y-%m', transaction_date) = ?
        """, (f"{current_year}-{current_month:02d}",))
        
        month_result = cursor.fetchone()
        month_income = month_result['month_income'] or 0
        month_expenses = month_result['month_expenses'] or 0
        month_transactions = month_result['month_transactions']
        month_net = month_income - month_expenses
        
        # Recent transactions (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as recent_transactions
            FROM transactions 
            WHERE transaction_date >= date('now', '-7 days')
        """)
        recent_transactions = cursor.fetchone()['recent_transactions']
        
        # Top income categories (current year)
        cursor.execute("""
            SELECT category_name, SUM(amount) as total
            FROM transactions 
            WHERE transaction_type = 'Income' 
            AND strftime('%Y', transaction_date) = ?
            GROUP BY category_name
            ORDER BY total DESC
            LIMIT 5
        """, (str(current_year),))
        top_income_categories = [dict(row) for row in cursor.fetchall()]
        
        # Top expense categories (current year)
        cursor.execute("""
            SELECT category_name, SUM(amount) as total
            FROM transactions 
            WHERE transaction_type = 'Expense' 
            AND strftime('%Y', transaction_date) = ?
            GROUP BY category_name
            ORDER BY total DESC
            LIMIT 5
        """, (str(current_year),))
        top_expense_categories = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'member_stats': {
                'total_members': total_members,
                'active_members': active_members,
                'baptized_members': baptized_members,
                'recent_members': recent_members,
                'active_percentage': (active_members / total_members * 100) if total_members > 0 else 0
            },
            'financial_stats': {
                'ytd_income': float(ytd_income),
                'ytd_expenses': float(ytd_expenses),
                'ytd_net': float(ytd_net),
                'month_income': float(month_income),
                'month_expenses': float(month_expenses),
                'month_net': float(month_net),
                'total_transactions': total_transactions,
                'month_transactions': month_transactions,
                'recent_transactions': recent_transactions
            },
            'top_categories': {
                'income': top_income_categories,
                'expense': top_expense_categories
            }
        }
    
    except Exception as e:
        print(f"Error getting dashboard overview: {e}")
        return {}

def get_total_members():
    """Legacy function for backward compatibility."""
    conn = get_db_connection()
    total_members = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    conn.close()
    return total_members

def get_member_growth_data():
    """Get member growth data over time."""
    try:
        conn = get_db_connection()
        query = "SELECT join_date FROM members WHERE join_date IS NOT NULL"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            df['join_date'] = pd.to_datetime(df['join_date'])
            df['join_month'] = df['join_date'].dt.to_period('M').astype(str)
            member_growth = df.groupby('join_month').size().reset_index(name='new_members')
            member_growth = member_growth.sort_values('join_month')
            member_growth['cumulative_members'] = member_growth['new_members'].cumsum()
            return member_growth
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting member growth data: {e}")
        return pd.DataFrame()

def get_monthly_financial_summary():
    """Get monthly financial summary data."""
    try:
        conn = get_db_connection()
        query = "SELECT transaction_date, transaction_type, amount FROM transactions"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['month'] = df['transaction_date'].dt.to_period('M').astype(str)
            summary = df.groupby(['month', 'transaction_type'])['amount'].sum().unstack(fill_value=0).reset_index()
            summary = summary.sort_values('month')
            return summary
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting monthly financial summary: {e}")
        return pd.DataFrame()

def get_monthly_trends(months: int = 12) -> pd.DataFrame:
    """Get monthly financial trends for the specified number of months."""
    try:
        conn = get_db_connection()
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)  # Approximate
        
        query = """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                transaction_type,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions 
            WHERE transaction_date >= ?
            GROUP BY month, transaction_type
            ORDER BY month
        """
        
        df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'),))
        conn.close()
        
        return df
    
    except Exception as e:
        print(f"Error getting monthly trends: {e}")
        return pd.DataFrame()

def get_upcoming_events() -> List[Dict]:
    """Get upcoming member birthdays and anniversaries."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = date.today()
        next_30_days = today + timedelta(days=30)
        
        # Upcoming birthdays (next 30 days)
        cursor.execute("""
            SELECT 
                name,
                date_of_birth,
                strftime('%m-%d', date_of_birth) as birth_md,
                'Birthday' as event_type
            FROM members 
            WHERE date_of_birth IS NOT NULL
            AND (
                (strftime('%m-%d', date_of_birth) BETWEEN strftime('%m-%d', 'now') AND strftime('%m-%d', 'now', '+30 days'))
                OR 
                (strftime('%m-%d', 'now') > strftime('%m-%d', 'now', '+30 days') 
                 AND (strftime('%m-%d', date_of_birth) >= strftime('%m-%d', 'now') 
                      OR strftime('%m-%d', date_of_birth) <= strftime('%m-%d', 'now', '+30 days')))
            )
            ORDER BY 
                CASE 
                    WHEN strftime('%m-%d', date_of_birth) >= strftime('%m-%d', 'now') 
                    THEN strftime('%m-%d', date_of_birth)
                    ELSE '12-31'
                END
        """)
        
        upcoming_events = []
        for row in cursor.fetchall():
            # Calculate next birthday
            birth_month, birth_day = map(int, row['birth_md'].split('-'))
            try:
                next_birthday = date(today.year, birth_month, birth_day)
                if next_birthday < today:
                    next_birthday = date(today.year + 1, birth_month, birth_day)
                
                days_until = (next_birthday - today).days
                
                upcoming_events.append({
                    'name': row['name'],
                    'event_type': row['event_type'],
                    'date': next_birthday,
                    'days_until': days_until
                })
            except ValueError:
                # Handle leap year issues
                continue
        
        # Baptism anniversaries (next 30 days)
        cursor.execute("""
            SELECT 
                name,
                baptism_date,
                strftime('%m-%d', baptism_date) as baptism_md,
                'Baptism Anniversary' as event_type
            FROM members 
            WHERE baptism_date IS NOT NULL
            AND baptized = 1
            AND (
                (strftime('%m-%d', baptism_date) BETWEEN strftime('%m-%d', 'now') AND strftime('%m-%d', 'now', '+30 days'))
                OR 
                (strftime('%m-%d', 'now') > strftime('%m-%d', 'now', '+30 days') 
                 AND (strftime('%m-%d', baptism_date) >= strftime('%m-%d', 'now') 
                      OR strftime('%m-%d', baptism_date) <= strftime('%m-%d', 'now', '+30 days')))
            )
        """)
        
        for row in cursor.fetchall():
            # Calculate next anniversary
            baptism_month, baptism_day = map(int, row['baptism_md'].split('-'))
            try:
                next_anniversary = date(today.year, baptism_month, baptism_day)
                if next_anniversary < today:
                    next_anniversary = date(today.year + 1, baptism_month, baptism_day)
                
                days_until = (next_anniversary - today).days
                
                upcoming_events.append({
                    'name': row['name'],
                    'event_type': row['event_type'],
                    'date': next_anniversary,
                    'days_until': days_until
                })
            except ValueError:
                continue
        
        conn.close()
        
        # Sort by days until event
        upcoming_events.sort(key=lambda x: x['days_until'])
        
        return upcoming_events[:10]  # Return top 10 upcoming events
    
    except Exception as e:
        print(f"Error getting upcoming events: {e}")
        return []

def get_financial_alerts() -> List[Dict]:
    """Get financial alerts and notifications."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        alerts = []
        today = date.today()
        current_month = today.strftime('%Y-%m')
        last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        # Check for unusual spending patterns
        cursor.execute("""
            SELECT 
                category_name,
                SUM(amount) as current_month_total
            FROM transactions 
            WHERE transaction_type = 'Expense' 
            AND strftime('%Y-%m', transaction_date) = ?
            GROUP BY category_name
        """, (current_month,))
        
        current_expenses = {row['category_name']: row['current_month_total'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT 
                category_name,
                AVG(monthly_total) as avg_monthly_expense
            FROM (
                SELECT 
                    category_name,
                    strftime('%Y-%m', transaction_date) as month,
                    SUM(amount) as monthly_total
                FROM transactions 
                WHERE transaction_type = 'Expense' 
                AND transaction_date >= date('now', '-6 months')
                AND strftime('%Y-%m', transaction_date) != ?
                GROUP BY category_name, month
            )
            GROUP BY category_name
        """, (current_month,))
        
        avg_expenses = {row['category_name']: row['avg_monthly_expense'] for row in cursor.fetchall()}
        
        # Check for categories with significantly higher expenses
        for category, current_total in current_expenses.items():
            if category in avg_expenses:
                avg_total = avg_expenses[category]
                if current_total > avg_total * 1.5:  # 50% higher than average
                    alerts.append({
                        'type': 'warning',
                        'category': 'Expense Alert',
                        'message': f"'{category}' expenses are {((current_total/avg_total - 1) * 100):.0f}% higher than average this month",
                        'details': f"Current: ₹{current_total:,.2f}, Average: ₹{avg_total:,.2f}"
                    })
        
        # Check for low income compared to last month
        cursor.execute("""
            SELECT SUM(amount) as total_income
            FROM transactions 
            WHERE transaction_type = 'Income' 
            AND strftime('%Y-%m', transaction_date) = ?
        """, (current_month,))
        
        current_income = cursor.fetchone()['total_income'] or 0
        
        cursor.execute("""
            SELECT SUM(amount) as total_income
            FROM transactions 
            WHERE transaction_type = 'Income' 
            AND strftime('%Y-%m', transaction_date) = ?
        """, (last_month,))
        
        last_month_income = cursor.fetchone()['total_income'] or 0
        
        if last_month_income > 0 and current_income < last_month_income * 0.8:  # 20% lower
            alerts.append({
                'type': 'info',
                'category': 'Income Notice',
                'message': f"Income is {((1 - current_income/last_month_income) * 100):.0f}% lower than last month",
                'details': f"Current: ₹{current_income:,.2f}, Last month: ₹{last_month_income:,.2f}"
            })
        
        # Check for members without recent contributions
        cursor.execute("""
            SELECT COUNT(*) as inactive_contributors
            FROM members m
            WHERE m.id NOT IN (
                SELECT DISTINCT member_id 
                FROM transactions 
                WHERE transaction_type = 'Income' 
                AND member_id IS NOT NULL
                AND transaction_date >= date('now', '-90 days')
            )
        """)
        
        inactive_contributors = cursor.fetchone()['inactive_contributors']
        if inactive_contributors > 0:
            alerts.append({
                'type': 'info',
                'category': 'Member Engagement',
                'message': f"{inactive_contributors} members haven't contributed in the last 90 days",
                'details': "Consider reaching out for pastoral care or engagement"
            })
        
        conn.close()
        return alerts
    
    except Exception as e:
        print(f"Error getting financial alerts: {e}")
        return []

def get_quick_stats() -> Dict:
    """Get quick statistics for dashboard widgets."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cash flow this week
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as week_income,
                SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as week_expenses
            FROM transactions 
            WHERE transaction_date >= date('now', '-7 days')
        """)
        
        week_result = cursor.fetchone()
        week_income = week_result['week_income'] or 0
        week_expenses = week_result['week_expenses'] or 0
        
        # Average transaction amount
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN transaction_type = 'Income' THEN amount END) as avg_income,
                AVG(CASE WHEN transaction_type = 'Expense' THEN amount END) as avg_expense
            FROM transactions 
            WHERE transaction_date >= date('now', '-30 days')
        """)
        
        avg_result = cursor.fetchone()
        avg_income = avg_result['avg_income'] or 0
        avg_expense = avg_result['avg_expense'] or 0
        
        # Member engagement (members with recent transactions)
        cursor.execute("""
            SELECT COUNT(DISTINCT member_id) as engaged_members
            FROM transactions 
            WHERE member_id IS NOT NULL 
            AND transaction_date >= date('now', '-30 days')
        """)
        
        engaged_members = cursor.fetchone()['engaged_members']
        
        # Total members for engagement percentage
        cursor.execute("SELECT COUNT(*) as total_members FROM members")
        total_members = cursor.fetchone()['total_members']
        
        engagement_rate = (engaged_members / total_members * 100) if total_members > 0 else 0
        
        conn.close()
        
        return {
            'week_cash_flow': float(week_income - week_expenses),
            'week_income': float(week_income),
            'week_expenses': float(week_expenses),
            'avg_income_transaction': float(avg_income),
            'avg_expense_transaction': float(avg_expense),
            'member_engagement_rate': float(engagement_rate),
            'engaged_members': engaged_members,
            'total_members': total_members
        }
    
    except Exception as e:
        print(f"Error getting quick stats: {e}")
        return {}

def create_member_growth_chart(growth_df):
    """Create member growth chart."""
    if not growth_df.empty:
        fig = px.line(growth_df, x='join_month', y='cumulative_members', 
                     title='Member Growth Trend', 
                     labels={'join_month': 'Month', 'cumulative_members': 'Total Members'})
        fig.update_traces(mode='lines+markers')
        return fig
    return None

def create_monthly_financial_chart(summary_df):
    """Create monthly financial chart."""
    if not summary_df.empty and 'Income' in summary_df.columns and 'Expense' in summary_df.columns:
        fig = px.bar(summary_df, x='month', y=['Income', 'Expense'], 
                    title='Month-wise Income and Expenses', barmode='group', 
                    labels={'month': 'Month', 'value': 'Amount'})
        return fig
    return None

# Testing and example usage
if __name__ == '__main__':
    print("Testing Enhanced Dashboard Manager...")
    
    # Test dashboard overview
    overview = get_dashboard_overview()
    print(f"Dashboard overview loaded: {len(overview)} sections")
    
    if overview:
        print(f"Total members: {overview['member_stats']['total_members']}")
        print(f"YTD Income: ₹{overview['financial_stats']['ytd_income']:,.2f}")
        print(f"YTD Expenses: ₹{overview['financial_stats']['ytd_expenses']:,.2f}")
    
    # Test monthly trends
    trends = get_monthly_trends(6)
    print(f"Monthly trends data: {len(trends)} records")
    
    # Test member growth
    growth = get_member_growth_data()
    print(f"Member growth data: {len(growth)} records")
    
    # Test upcoming events
    events = get_upcoming_events()
    print(f"Upcoming events: {len(events)} events")
    
    # Test financial alerts
    alerts = get_financial_alerts()
    print(f"Financial alerts: {len(alerts)} alerts")
    
    # Test quick stats
    quick_stats = get_quick_stats()
    print(f"Quick stats loaded: {len(quick_stats)} metrics")
    
    print("Enhanced Dashboard Manager test completed successfully!")
