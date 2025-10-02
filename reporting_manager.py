import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
from fpdf import FPDF
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from typing import List, Dict, Optional, Tuple
import calendar

DATABASE_NAME = 'ctms.db'

def get_db_connection():
    """Get database connection with row factory for named access."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_financial_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Get financial transaction data for a date range."""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                t.transaction_date, 
                t.transaction_type, 
                t.category_name, 
                t.amount, 
                t.description,
                m.name as member_name
            FROM transactions t
            LEFT JOIN members m ON t.member_id = m.id
            WHERE t.transaction_date BETWEEN ? AND ? 
            ORDER BY t.transaction_date ASC, t.id ASC
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting financial data: {e}")
        return pd.DataFrame()

def get_member_financial_summary(member_id: int, start_date: str, end_date: str) -> Dict:
    """Get financial summary for a specific member."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get member details
        cursor.execute("SELECT name FROM members WHERE id = ?", (member_id,))
        member = cursor.fetchone()
        if not member:
            return {}
        
        # Get transactions for this member
        cursor.execute("""
            SELECT transaction_type, SUM(amount) as total, COUNT(*) as count
            FROM transactions 
            WHERE member_id = ? AND transaction_date BETWEEN ? AND ?
            GROUP BY transaction_type
        """, (member_id, start_date, end_date))
        
        results = cursor.fetchall()
        summary = {
            'member_name': member['name'],
            'member_id': member_id,
            'income_total': 0,
            'income_count': 0,
            'expense_total': 0,
            'expense_count': 0
        }
        
        for row in results:
            if row['transaction_type'] == 'Income':
                summary['income_total'] = row['total']
                summary['income_count'] = row['count']
            else:
                summary['expense_total'] = row['total']
                summary['expense_count'] = row['count']
        
        conn.close()
        return summary
    except Exception as e:
        print(f"Error getting member financial summary: {e}")
        return {}

def get_category_analysis(start_date: str, end_date: str) -> Dict:
    """Get detailed category analysis for the date range."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Income by category
        cursor.execute("""
            SELECT category_name, SUM(amount) as total, COUNT(*) as count, AVG(amount) as avg_amount
            FROM transactions 
            WHERE transaction_type = 'Income' AND transaction_date BETWEEN ? AND ?
            GROUP BY category_name
            ORDER BY total DESC
        """, (start_date, end_date))
        income_categories = [dict(row) for row in cursor.fetchall()]
        
        # Expense by category
        cursor.execute("""
            SELECT category_name, SUM(amount) as total, COUNT(*) as count, AVG(amount) as avg_amount
            FROM transactions 
            WHERE transaction_type = 'Expense' AND transaction_date BETWEEN ? AND ?
            GROUP BY category_name
            ORDER BY total DESC
        """, (start_date, end_date))
        expense_categories = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return {
            'income_categories': income_categories,
            'expense_categories': expense_categories
        }
    except Exception as e:
        print(f"Error getting category analysis: {e}")
        return {}

def get_monthly_trends(year: int) -> pd.DataFrame:
    """Get monthly financial trends for a specific year."""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                strftime('%m', transaction_date) as month,
                transaction_type,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions 
            WHERE strftime('%Y', transaction_date) = ?
            GROUP BY month, transaction_type
            ORDER BY month
        """
        df = pd.read_sql_query(query, conn, params=(str(year),))
        conn.close()
        return df
    except Exception as e:
        print(f"Error getting monthly trends: {e}")
        return pd.DataFrame()

def get_balance_before_date(date_str: str) -> float:
    """Calculate balance before a specific date."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as total_expense
            FROM transactions 
            WHERE transaction_date < ?
        """, (date_str,))
        
        result = cursor.fetchone()
        total_income = result['total_income'] or 0
        total_expense = result['total_expense'] or 0
        
        conn.close()
        return float(total_income - total_expense)
    except Exception as e:
        print(f"Error calculating balance: {e}")
        return 0.0

def generate_comprehensive_financial_report_pdf(start_date: str, end_date: str) -> bytes:
    """Generate a comprehensive financial report PDF."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 15, "Church Treasury Management System", 0, 1, "C")
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Comprehensive Financial Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1, "C")
    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")
    pdf.ln(10)
    
    # Get data
    df = get_financial_data(start_date, end_date)
    opening_balance = get_balance_before_date(start_date)
    category_analysis = get_category_analysis(start_date, end_date)
    
    # Executive Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Executive Summary", 0, 1, "L")
    pdf.set_font("Arial", "", 11)
    
    if not df.empty:
        total_income = df[df['transaction_type'] == 'Income']['amount'].sum()
        total_expense = df[df['transaction_type'] == 'Expense']['amount'].sum()
        net_change = total_income - total_expense
        closing_balance = opening_balance + net_change
        transaction_count = len(df)
        
        pdf.cell(0, 7, f"Opening Balance: ₹{opening_balance:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Total Income: ₹{total_income:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Total Expenses: ₹{total_expense:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Net Change: ₹{net_change:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Closing Balance: ₹{closing_balance:,.2f}", 0, 1, "L")
        pdf.cell(0, 7, f"Total Transactions: {transaction_count}", 0, 1, "L")
        pdf.ln(5)
        
        # Income Categories Summary
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Income Categories", 0, 1, "L")
        pdf.set_font("Arial", "", 10)
        
        for cat in category_analysis.get('income_categories', []):
            pdf.cell(0, 6, f"  • {cat['category_name']}: ₹{cat['total']:,.2f} ({cat['count']} transactions)", 0, 1, "L")
        
        pdf.ln(3)
        
        # Expense Categories Summary
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Expense Categories", 0, 1, "L")
        pdf.set_font("Arial", "", 10)
        
        for cat in category_analysis.get('expense_categories', []):
            pdf.cell(0, 6, f"  • {cat['category_name']}: ₹{cat['total']:,.2f} ({cat['count']} transactions)", 0, 1, "L")
        
        pdf.ln(5)
        
        # Detailed Transactions
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Detailed Transaction List", 0, 1, "L")
        pdf.ln(3)
        
        # Table headers
        pdf.set_font("Arial", "B", 9)
        col_widths = [22, 18, 30, 18, 40, 30]
        headers = ['Date', 'Type', 'Category', 'Amount', 'Description', 'Member']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
        pdf.ln()
        
        # Table data
        pdf.set_font("Arial", "", 8)
        for index, row in df.iterrows():
            pdf.cell(col_widths[0], 6, str(row['transaction_date']), 1, 0, 'L')
            pdf.cell(col_widths[1], 6, str(row['transaction_type']), 1, 0, 'L')
            pdf.cell(col_widths[2], 6, str(row['category_name'])[:20], 1, 0, 'L')
            pdf.cell(col_widths[3], 6, f"₹{row['amount']:,.2f}", 1, 0, 'R')
            description = str(row['description'])[:25] if row['description'] else ''
            pdf.cell(col_widths[4], 6, description, 1, 0, 'L')
            member_name = str(row['member_name'])[:20] if row['member_name'] else 'N/A'
            pdf.cell(col_widths[5], 6, member_name, 1, 0, 'L')
            pdf.ln()
    else:
        pdf.cell(0, 10, "No transactions found for the selected period.", 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin-1')

def generate_member_giving_report_pdf(start_date: str, end_date: str) -> bytes:
    """Generate a member giving report PDF."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Member Giving Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1, "C")
    pdf.ln(10)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get member giving data
        cursor.execute("""
            SELECT 
                m.name,
                m.id,
                SUM(t.amount) as total_giving,
                COUNT(t.id) as transaction_count
            FROM members m
            LEFT JOIN transactions t ON m.id = t.member_id 
                AND t.transaction_type = 'Income' 
                AND t.transaction_date BETWEEN ? AND ?
            GROUP BY m.id, m.name
            HAVING total_giving > 0
            ORDER BY total_giving DESC
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        
        if results:
            # Table headers
            pdf.set_font("Arial", "B", 12)
            pdf.cell(60, 10, "Member Name", 1, 0, 'C')
            pdf.cell(30, 10, "Member ID", 1, 0, 'C')
            pdf.cell(40, 10, "Total Giving", 1, 0, 'C')
            pdf.cell(30, 10, "Transactions", 1, 0, 'C')
            pdf.ln()
            
            # Table data
            pdf.set_font("Arial", "", 11)
            total_giving = 0
            
            for row in results:
                pdf.cell(60, 8, str(row['name']), 1, 0, 'L')
                pdf.cell(30, 8, str(row['id']), 1, 0, 'C')
                pdf.cell(40, 8, f"₹{row['total_giving']:,.2f}", 1, 0, 'R')
                pdf.cell(30, 8, str(row['transaction_count']), 1, 0, 'C')
                pdf.ln()
                total_giving += row['total_giving']
            
            # Summary
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Total Giving from Members: ₹{total_giving:,.2f}", 0, 1, "R")
            pdf.cell(0, 8, f"Number of Contributing Members: {len(results)}", 0, 1, "R")
        else:
            pdf.cell(0, 10, "No member giving data found for the selected period.", 0, 1, "C")
        
        conn.close()
    except Exception as e:
        pdf.cell(0, 10, f"Error generating report: {str(e)}", 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin-1')

def generate_budget_vs_actual_report_pdf(start_date: str, end_date: str, budget_data: Dict) -> bytes:
    """Generate a budget vs actual report PDF."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Budget vs Actual Report", 0, 1, "C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1, "C")
    pdf.ln(10)
    
    # Get actual data
    category_analysis = get_category_analysis(start_date, end_date)
    
    # Income comparison
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Income Categories", 0, 1, "L")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(50, 8, "Category", 1, 0, 'C')
    pdf.cell(30, 8, "Budgeted", 1, 0, 'C')
    pdf.cell(30, 8, "Actual", 1, 0, 'C')
    pdf.cell(30, 8, "Variance", 1, 0, 'C')
    pdf.cell(30, 8, "% Variance", 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for cat in category_analysis.get('income_categories', []):
        category_name = cat['category_name']
        actual = cat['total']
        budgeted = budget_data.get('income', {}).get(category_name, 0)
        variance = actual - budgeted
        pct_variance = (variance / budgeted * 100) if budgeted > 0 else 0
        
        pdf.cell(50, 7, category_name, 1, 0, 'L')
        pdf.cell(30, 7, f"₹{budgeted:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"₹{actual:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"₹{variance:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"{pct_variance:.1f}%", 1, 0, 'R')
        pdf.ln()
    
    pdf.ln(5)
    
    # Expense comparison
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Expense Categories", 0, 1, "L")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(50, 8, "Category", 1, 0, 'C')
    pdf.cell(30, 8, "Budgeted", 1, 0, 'C')
    pdf.cell(30, 8, "Actual", 1, 0, 'C')
    pdf.cell(30, 8, "Variance", 1, 0, 'C')
    pdf.cell(30, 8, "% Variance", 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for cat in category_analysis.get('expense_categories', []):
        category_name = cat['category_name']
        actual = cat['total']
        budgeted = budget_data.get('expense', {}).get(category_name, 0)
        variance = budgeted - actual  # For expenses, under budget is positive
        pct_variance = (variance / budgeted * 100) if budgeted > 0 else 0
        
        pdf.cell(50, 7, category_name, 1, 0, 'L')
        pdf.cell(30, 7, f"₹{budgeted:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"₹{actual:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"₹{variance:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"{pct_variance:.1f}%", 1, 0, 'R')
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1')

def generate_excel_report(df: pd.DataFrame, report_title: str, include_charts: bool = True) -> bytes:
    """Generate an enhanced Excel report with multiple sheets and charts."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, index=False, sheet_name='Transaction_Data')
        
        if not df.empty and include_charts:
            # Summary sheet
            summary_data = []
            
            # Income summary
            income_df = df[df['transaction_type'] == 'Income']
            if not income_df.empty:
                income_summary = income_df.groupby('category_name')['amount'].agg(['sum', 'count', 'mean']).reset_index()
                income_summary['type'] = 'Income'
                summary_data.append(income_summary)
            
            # Expense summary
            expense_df = df[df['transaction_type'] == 'Expense']
            if not expense_df.empty:
                expense_summary = expense_df.groupby('category_name')['amount'].agg(['sum', 'count', 'mean']).reset_index()
                expense_summary['type'] = 'Expense'
                summary_data.append(expense_summary)
            
            if summary_data:
                combined_summary = pd.concat(summary_data, ignore_index=True)
                combined_summary.columns = ['Category', 'Total_Amount', 'Transaction_Count', 'Average_Amount', 'Type']
                combined_summary.to_excel(writer, index=False, sheet_name='Category_Summary')
            
            # Monthly summary if data spans multiple months
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['month_year'] = df['transaction_date'].dt.to_period('M')
            
            if df['month_year'].nunique() > 1:
                monthly_summary = df.groupby(['month_year', 'transaction_type'])['amount'].sum().unstack(fill_value=0).reset_index()
                monthly_summary.to_excel(writer, index=False, sheet_name='Monthly_Summary')
    
    return output.getvalue()

def create_financial_charts(df: pd.DataFrame, start_date: str, end_date: str) -> Dict[str, str]:
    """Create financial charts and return their file paths."""
    charts = {}
    
    if df.empty:
        return charts
    
    try:
        # Income vs Expense Pie Chart
        summary = df.groupby('transaction_type')['amount'].sum()
        if len(summary) > 0:
            fig_pie = px.pie(
                values=summary.values,
                names=summary.index,
                title=f"Income vs Expenses ({start_date} to {end_date})",
                color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
            )
            pie_path = f"/home/ubuntu/income_expense_pie_{start_date}_{end_date}.png"
            fig_pie.write_image(pie_path, width=800, height=600)
            charts['pie_chart'] = pie_path
        
        # Category Bar Chart
        category_summary = df.groupby(['transaction_type', 'category_name'])['amount'].sum().reset_index()
        if not category_summary.empty:
            fig_bar = px.bar(
                category_summary,
                x='category_name',
                y='amount',
                color='transaction_type',
                title=f"Amount by Category ({start_date} to {end_date})",
                labels={'amount': 'Amount (₹)', 'category_name': 'Category'},
                color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            bar_path = f"/home/ubuntu/category_bar_{start_date}_{end_date}.png"
            fig_bar.write_image(bar_path, width=1000, height=600)
            charts['bar_chart'] = bar_path
        
        # Time series if data spans multiple days
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        if df['transaction_date'].nunique() > 1:
            daily_summary = df.groupby(['transaction_date', 'transaction_type'])['amount'].sum().reset_index()
            fig_line = px.line(
                daily_summary,
                x='transaction_date',
                y='amount',
                color='transaction_type',
                title=f"Daily Financial Trends ({start_date} to {end_date})",
                labels={'amount': 'Amount (₹)', 'transaction_date': 'Date'},
                color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
            )
            line_path = f"/home/ubuntu/daily_trends_{start_date}_{end_date}.png"
            fig_line.write_image(line_path, width=1000, height=600)
            charts['line_chart'] = line_path
    
    except Exception as e:
        print(f"Error creating charts: {e}")
    
    return charts

# Testing and example usage
if __name__ == '__main__':
    print("Testing Enhanced Reporting Manager...")
    
    # Test date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Test financial data retrieval
    df = get_financial_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    print(f"Retrieved {len(df)} transactions")
    
    # Test category analysis
    analysis = get_category_analysis(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    print(f"Category analysis: {len(analysis.get('income_categories', []))} income, {len(analysis.get('expense_categories', []))} expense categories")
    
    # Test balance calculation
    balance = get_balance_before_date(start_date.strftime("%Y-%m-%d"))
    print(f"Opening balance: ₹{balance:.2f}")
    
    print("Enhanced Reporting Manager test completed successfully!")
