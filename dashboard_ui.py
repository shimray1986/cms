import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import dashboard_manager
import finance_manager
import member_manager
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_dashboard():
    """Render the main dashboard with comprehensive overview."""
    st.title("🏠 Dashboard")
    
    # Get dashboard data
    overview = dashboard_manager.get_dashboard_overview()
    quick_stats = dashboard_manager.get_quick_stats()
    alerts = dashboard_manager.get_financial_alerts()
    upcoming_events = dashboard_manager.get_upcoming_events()
    
    if not overview:
        st.error("Unable to load dashboard data. Please check your database connection.")
        return
    
    # Header metrics
    render_header_metrics(overview, quick_stats)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Financial overview charts
        render_financial_overview(overview)
        
        # Recent activity and trends
        render_activity_trends()
    
    with col2:
        # Alerts and notifications
        render_alerts_panel(alerts)
        
        # Upcoming events
        render_upcoming_events(upcoming_events)
        
        # Quick actions
        render_quick_actions()

def render_header_metrics(overview: dict, quick_stats: dict):
    """Render the header metrics section."""
    st.markdown("### 📊 Key Performance Indicators")
    
    # Top row - Primary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    member_stats = overview.get('member_stats', {})
    financial_stats = overview.get('financial_stats', {})
    
    with col1:
        st.metric(
            "Total Members", 
            member_stats.get('total_members', 0),
            delta=f"+{member_stats.get('recent_members', 0)} this month"
        )
    
    with col2:
        ytd_income = financial_stats.get('ytd_income', 0)
        st.metric(
            "YTD Income", 
            f"₹{ytd_income:,.2f}",
            delta=f"₹{financial_stats.get('month_income', 0):,.2f} this month"
        )
    
    with col3:
        ytd_expenses = financial_stats.get('ytd_expenses', 0)
        st.metric(
            "YTD Expenses", 
            f"₹{ytd_expenses:,.2f}",
            delta=f"₹{financial_stats.get('month_expenses', 0):,.2f} this month"
        )
    
    with col4:
        ytd_net = financial_stats.get('ytd_net', 0)
        month_net = financial_stats.get('month_net', 0)
        st.metric(
            "YTD Net", 
            f"₹{ytd_net:,.2f}",
            delta=f"₹{month_net:,.2f} this month"
        )
    
    # Second row - Additional metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        active_percentage = member_stats.get('active_percentage', 0)
        st.metric(
            "Active Members", 
            f"{member_stats.get('active_members', 0)} ({active_percentage:.1f}%)"
        )
    
    with col6:
        engagement_rate = quick_stats.get('member_engagement_rate', 0)
        st.metric(
            "Member Engagement", 
            f"{engagement_rate:.1f}%",
            help="Members with transactions in the last 30 days"
        )
    
    with col7:
        week_cash_flow = quick_stats.get('week_cash_flow', 0)
        delta_color = "normal" if week_cash_flow >= 0 else "inverse"
        st.metric(
            "Weekly Cash Flow", 
            f"₹{week_cash_flow:,.2f}",
            delta=f"₹{week_cash_flow:,.2f}",
            delta_color=delta_color
        )
    
    with col8:
        total_transactions = financial_stats.get('total_transactions', 0)
        recent_transactions = financial_stats.get('recent_transactions', 0)
        st.metric(
            "Total Transactions", 
            total_transactions,
            delta=f"+{recent_transactions} this week"
        )

def render_financial_overview(overview: dict):
    """Render financial overview charts."""
    st.markdown("### 💰 Financial Overview")
    
    # Get financial data for charts
    financial_stats = overview.get('financial_stats', {})
    top_categories = overview.get('top_categories', {})
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "🏷️ Categories", "📊 Comparison"])
    
    with tab1:
        render_financial_trends()
    
    with tab2:
        render_category_breakdown(top_categories)
    
    with tab3:
        render_financial_comparison(financial_stats)

def render_financial_trends():
    """Render financial trends chart."""
    # Get monthly trends data
    trends_df = dashboard_manager.get_monthly_trends(12)
    
    if not trends_df.empty:
        # Pivot the data for better visualization
        trends_pivot = trends_df.pivot(index='month', columns='transaction_type', values='total_amount').fillna(0)
        trends_pivot = trends_pivot.reset_index()
        
        # Create line chart
        fig = go.Figure()
        
        if 'Income' in trends_pivot.columns:
            fig.add_trace(go.Scatter(
                x=trends_pivot['month'],
                y=trends_pivot['Income'],
                mode='lines+markers',
                name='Income',
                line=dict(color='#00CC96', width=3),
                marker=dict(size=8)
            ))
        
        if 'Expense' in trends_pivot.columns:
            fig.add_trace(go.Scatter(
                x=trends_pivot['month'],
                y=trends_pivot['Expense'],
                mode='lines+markers',
                name='Expenses',
                line=dict(color='#FF6692', width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="12-Month Financial Trends",
            xaxis_title="Month",
            yaxis_title="Amount (₹)",
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trend data available. Add more transactions to see financial trends.")

def render_category_breakdown(top_categories: dict):
    """Render category breakdown charts."""
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.markdown("**Top Income Categories**")
        income_cats = top_categories.get('income', [])
        
        if income_cats:
            df_income = pd.DataFrame(income_cats)
            fig_income = px.pie(
                df_income,
                values='total',
                names='category_name',
                title="Income Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_income.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_income, use_container_width=True)
        else:
            st.info("No income categories data available.")
    
    with col_expense:
        st.markdown("**Top Expense Categories**")
        expense_cats = top_categories.get('expense', [])
        
        if expense_cats:
            df_expense = pd.DataFrame(expense_cats)
            fig_expense = px.pie(
                df_expense,
                values='total',
                names='category_name',
                title="Expense Distribution",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_expense.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_expense, use_container_width=True)
        else:
            st.info("No expense categories data available.")

def render_financial_comparison(financial_stats: dict):
    """Render financial comparison charts."""
    # YTD vs Current Month comparison
    ytd_income = financial_stats.get('ytd_income', 0)
    ytd_expenses = financial_stats.get('ytd_expenses', 0)
    month_income = financial_stats.get('month_income', 0)
    month_expenses = financial_stats.get('month_expenses', 0)
    
    # Create comparison chart
    comparison_data = {
        'Period': ['Year to Date', 'Current Month'],
        'Income': [ytd_income, month_income],
        'Expenses': [ytd_expenses, month_expenses],
        'Net': [ytd_income - ytd_expenses, month_income - month_expenses]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Income',
        x=df_comparison['Period'],
        y=df_comparison['Income'],
        marker_color='#00CC96'
    ))
    
    fig.add_trace(go.Bar(
        name='Expenses',
        x=df_comparison['Period'],
        y=df_comparison['Expenses'],
        marker_color='#FF6692'
    ))
    
    fig.add_trace(go.Scatter(
        name='Net',
        x=df_comparison['Period'],
        y=df_comparison['Net'],
        mode='lines+markers',
        line=dict(color='#FFA15A', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Financial Performance Comparison",
        xaxis_title="Period",
        yaxis_title="Amount (₹)",
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_activity_trends():
    """Render recent activity and member growth trends."""
    st.markdown("### 👥 Member Growth & Activity")
    
    # Get member growth data
    growth_df = dashboard_manager.get_member_growth_data()
    
    if not growth_df.empty:
        # Create member growth chart
        fig = px.line(
            growth_df,
            x='join_month',
            y='cumulative_members',
            title='Member Growth Over Time',
            labels={'join_month': 'Month', 'cumulative_members': 'Total Members'},
            markers=True
        )
        
        fig.update_traces(
            line=dict(color='#636EFA', width=3),
            marker=dict(size=8)
        )
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Members",
            hovermode='x'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show growth statistics
        if len(growth_df) > 1:
            recent_growth = growth_df.iloc[-1]['new_members']
            total_members = growth_df.iloc[-1]['cumulative_members']
            avg_monthly_growth = growth_df['new_members'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Recent Month Growth", recent_growth)
            with col2:
                st.metric("Total Members", total_members)
            with col3:
                st.metric("Avg Monthly Growth", f"{avg_monthly_growth:.1f}")
    else:
        st.info("No member growth data available. Member join dates are needed to show growth trends.")

def render_alerts_panel(alerts: list):
    """Render alerts and notifications panel."""
    st.markdown("### 🚨 Alerts & Notifications")
    
    if alerts:
        for alert in alerts:
            alert_type = alert.get('type', 'info')
            category = alert.get('category', 'Alert')
            message = alert.get('message', '')
            details = alert.get('details', '')
            
            if alert_type == 'warning':
                st.warning(f"**{category}**\n\n{message}\n\n{details}")
            elif alert_type == 'error':
                st.error(f"**{category}**\n\n{message}\n\n{details}")
            else:
                st.info(f"**{category}**\n\n{message}\n\n{details}")
    else:
        st.success("✅ No alerts at this time. All systems are running smoothly!")

def render_upcoming_events(events: list):
    """Render upcoming events panel."""
    st.markdown("### 📅 Upcoming Events")
    
    if events:
        for event in events[:5]:  # Show top 5 events
            name = event.get('name', 'Unknown')
            event_type = event.get('event_type', 'Event')
            days_until = event.get('days_until', 0)
            event_date = event.get('date', '')
            
            if days_until == 0:
                date_str = "Today"
            elif days_until == 1:
                date_str = "Tomorrow"
            else:
                date_str = f"In {days_until} days"
            
            # Use different icons for different event types
            if event_type == 'Birthday':
                icon = "🎂"
            elif event_type == 'Baptism Anniversary':
                icon = "✝️"
            else:
                icon = "📅"
            
            st.write(f"{icon} **{name}** - {event_type}")
            st.write(f"   📍 {date_str} ({event_date})")
            st.write("")
    else:
        st.info("No upcoming events in the next 30 days.")

def render_quick_actions():
    """Render quick actions panel."""
    st.markdown("### ⚡ Quick Actions")
    
    # Quick action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Add Member", use_container_width=True):
            st.switch_page("pages/membership.py")
        
        if st.button("💰 Add Transaction", use_container_width=True):
            st.switch_page("pages/finance.py")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.switch_page("pages/reporting.py")
        
        if st.button("👥 View Members", use_container_width=True):
            st.switch_page("pages/membership.py")
    
    # Recent transactions summary
    st.markdown("**Recent Transactions**")
    recent_transactions = finance_manager.get_recent_transactions(limit=5)
    
    if recent_transactions:
        for txn in recent_transactions:
            transaction_type = txn['transaction_type']
            amount = txn['amount']
            category = txn['category_name']
            date_str = txn['transaction_date']
            
            # Use different colors for income vs expense
            if transaction_type == 'Income':
                color = "🟢"
            else:
                color = "🔴"
            
            st.write(f"{color} {transaction_type}: ₹{amount:.2f} - {category} ({date_str})")
    else:
        st.info("No recent transactions to display.")

def render_system_status():
    """Render system status indicators."""
    st.markdown("### 🔧 System Status")
    
    # Check database connectivity
    try:
        total_members = dashboard_manager.get_total_members()
        db_status = "✅ Connected"
        db_color = "success"
    except:
        db_status = "❌ Error"
        db_color = "error"
    
    # Display status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if db_color == "success":
            st.success(f"Database: {db_status}")
        else:
            st.error(f"Database: {db_status}")
    
    with col2:
        st.success("✅ Application: Running")
    
    with col3:
        st.success("✅ Reports: Available")
    
    # System information
    st.markdown("**System Information**")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Current Time: {current_time}")
    st.write(f"Database Records: {total_members if 'total_members' in locals() else 'N/A'} members")

# Additional utility functions for dashboard
def get_dashboard_summary():
    """Get a summary of key dashboard metrics for external use."""
    overview = dashboard_manager.get_dashboard_overview()
    quick_stats = dashboard_manager.get_quick_stats()
    
    return {
        'total_members': overview.get('member_stats', {}).get('total_members', 0),
        'ytd_income': overview.get('financial_stats', {}).get('ytd_income', 0),
        'ytd_expenses': overview.get('financial_stats', {}).get('ytd_expenses', 0),
        'ytd_net': overview.get('financial_stats', {}).get('ytd_net', 0),
        'engagement_rate': quick_stats.get('member_engagement_rate', 0),
        'week_cash_flow': quick_stats.get('week_cash_flow', 0)
    }
