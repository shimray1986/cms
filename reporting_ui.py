import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import reporting_manager
import finance_manager
import member_manager
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

def render_reporting_module():
    """Render the complete reporting interface."""
    st.title("📊 Reporting & Analytics")
    
    # Create tabs for different report types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Financial Reports", 
        "👥 Member Reports", 
        "📋 Custom Reports", 
        "📊 Analytics Dashboard",
        "💾 Export Center"
    ])
    
    with tab1:
        render_financial_reports()
    
    with tab2:
        render_member_reports()
    
    with tab3:
        render_custom_reports()
    
    with tab4:
        render_analytics_dashboard()
    
    with tab5:
        render_export_center()

def render_financial_reports():
    """Render financial reports section."""
    st.subheader("Financial Reports")
    
    # Report configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            [
                "Comprehensive Financial Report",
                "Income Statement",
                "Expense Report",
                "Ledger Report",
                "Category Analysis",
                "Monthly Summary"
            ]
        )
    
    with col2:
        date_range_option = st.selectbox(
            "Date Range",
            ["Current Month", "Last Month", "Current Quarter", "Last Quarter", 
             "Current Year", "Last Year", "Custom Range"]
        )
    
    with col3:
        if date_range_option == "Custom Range":
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            end_date = st.date_input("End Date", value=date.today())
        else:
            start_date, end_date = get_predefined_date_range(date_range_option)
            st.info(f"Date Range: {start_date} to {end_date}")
    
    if start_date > end_date:
        st.error("Start date must be before end date.")
        return
    
    # Generate report
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            generate_and_display_financial_report(
                report_type, 
                start_date.strftime("%Y-%m-%d"), 
                end_date.strftime("%Y-%m-%d")
            )

def render_member_reports():
    """Render member-related reports section."""
    st.subheader("Member Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        member_report_type = st.selectbox(
            "Member Report Type",
            [
                "Member Giving Report",
                "Individual Member Summary",
                "Member Financial Activity",
                "Contribution Analysis"
            ]
        )
    
    with col2:
        # Date range for member reports
        member_date_range = st.selectbox(
            "Period",
            ["Current Year", "Last Year", "Current Month", "Last Month", "Custom"]
        )
        
        if member_date_range == "Custom":
            member_start_date = st.date_input("Start Date", value=date.today() - timedelta(days=90), key="member_start")
            member_end_date = st.date_input("End Date", value=date.today(), key="member_end")
        else:
            member_start_date, member_end_date = get_predefined_date_range(member_date_range)
    
    # Individual member selection for specific reports
    if member_report_type == "Individual Member Summary":
        members = member_manager.get_all_members()
        if members:
            member_options = {f"{m['name']} (ID: {m['id']})": m['id'] for m in members}
            selected_member = st.selectbox("Select Member", list(member_options.keys()))
            selected_member_id = member_options[selected_member]
        else:
            st.warning("No members found.")
            return
    else:
        selected_member_id = None
    
    if st.button("Generate Member Report", type="primary"):
        with st.spinner("Generating member report..."):
            generate_and_display_member_report(
                member_report_type,
                member_start_date.strftime("%Y-%m-%d"),
                member_end_date.strftime("%Y-%m-%d"),
                selected_member_id
            )

def render_custom_reports():
    """Render custom report builder."""
    st.subheader("Custom Report Builder")
    
    st.info("Build custom reports by selecting specific criteria and filters.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Report Criteria**")
        
        # Transaction type filter
        transaction_types = st.multiselect(
            "Transaction Types",
            ["Income", "Expense"],
            default=["Income", "Expense"]
        )
        
        # Category filter
        income_categories = finance_manager.get_income_categories()
        expense_categories = finance_manager.get_expense_categories()
        
        all_categories = []
        if "Income" in transaction_types:
            all_categories.extend([f"Income: {cat['name']}" for cat in income_categories])
        if "Expense" in transaction_types:
            all_categories.extend([f"Expense: {cat['name']}" for cat in expense_categories])
        
        selected_categories = st.multiselect(
            "Categories (leave empty for all)",
            all_categories
        )
        
        # Amount range filter
        use_amount_filter = st.checkbox("Filter by Amount Range")
        if use_amount_filter:
            min_amount = st.number_input("Minimum Amount", min_value=0.0, value=0.0)
            max_amount = st.number_input("Maximum Amount", min_value=0.0, value=10000.0)
        else:
            min_amount = max_amount = None
    
    with col2:
        st.markdown("**Date Range & Options**")
        
        custom_start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30), key="custom_start")
        custom_end_date = st.date_input("End Date", value=date.today(), key="custom_end")
        
        # Report format options
        include_member_info = st.checkbox("Include Member Information", value=True)
        include_charts = st.checkbox("Include Charts", value=True)
        group_by_category = st.checkbox("Group by Category", value=False)
        group_by_month = st.checkbox("Group by Month", value=False)
    
    if st.button("Generate Custom Report", type="primary"):
        with st.spinner("Generating custom report..."):
            generate_custom_report(
                transaction_types,
                selected_categories,
                custom_start_date.strftime("%Y-%m-%d"),
                custom_end_date.strftime("%Y-%m-%d"),
                min_amount,
                max_amount,
                include_member_info,
                include_charts,
                group_by_category,
                group_by_month
            )

def render_analytics_dashboard():
    """Render analytics dashboard with key insights."""
    st.subheader("Analytics Dashboard")
    
    # Time period selector
    analysis_period = st.selectbox(
        "Analysis Period",
        ["Current Month", "Last 3 Months", "Current Year", "All Time"]
    )
    
    start_date, end_date = get_predefined_date_range(analysis_period)
    
    # Get data for analysis
    df = reporting_manager.get_financial_data(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    
    if df.empty:
        st.info("No data available for the selected period.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_income = df[df['transaction_type'] == 'Income']['amount'].sum()
    total_expense = df[df['transaction_type'] == 'Expense']['amount'].sum()
    net_amount = total_income - total_expense
    transaction_count = len(df)
    
    with col1:
        st.metric("Total Income", f"₹{total_income:,.2f}")
    
    with col2:
        st.metric("Total Expenses", f"₹{total_expense:,.2f}")
    
    with col3:
        st.metric("Net Amount", f"₹{net_amount:,.2f}", delta=f"₹{net_amount:,.2f}")
    
    with col4:
        st.metric("Transactions", transaction_count)
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Income vs Expenses")
        if total_income > 0 or total_expense > 0:
            fig_pie = px.pie(
                values=[total_income, total_expense],
                names=['Income', 'Expenses'],
                color_discrete_map={'Income': '#00CC96', 'Expenses': '#FF6692'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        st.subheader("Top Categories")
        category_summary = df.groupby(['transaction_type', 'category_name'])['amount'].sum().reset_index()
        top_categories = category_summary.nlargest(10, 'amount')
        
        if not top_categories.empty:
            fig_bar = px.bar(
                top_categories,
                x='amount',
                y='category_name',
                color='transaction_type',
                orientation='h',
                color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Trends analysis
    if len(df) > 1:
        st.subheader("Financial Trends")
        
        # Daily trends
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        daily_summary = df.groupby(['transaction_date', 'transaction_type'])['amount'].sum().reset_index()
        
        if not daily_summary.empty:
            fig_line = px.line(
                daily_summary,
                x='transaction_date',
                y='amount',
                color='transaction_type',
                title="Daily Financial Activity",
                color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Category analysis
    st.subheader("Category Analysis")
    category_analysis = reporting_manager.get_category_analysis(
        start_date.strftime("%Y-%m-%d"), 
        end_date.strftime("%Y-%m-%d")
    )
    
    col_income, col_expense = st.columns(2)
    
    with col_income:
        st.markdown("**Top Income Categories**")
        income_cats = category_analysis.get('income_categories', [])
        if income_cats:
            df_income = pd.DataFrame(income_cats)
            st.dataframe(
                df_income[['category_name', 'total', 'count']].rename(columns={
                    'category_name': 'Category',
                    'total': 'Total (₹)',
                    'count': 'Transactions'
                }),
                use_container_width=True
            )
        else:
            st.info("No income data available.")
    
    with col_expense:
        st.markdown("**Top Expense Categories**")
        expense_cats = category_analysis.get('expense_categories', [])
        if expense_cats:
            df_expense = pd.DataFrame(expense_cats)
            st.dataframe(
                df_expense[['category_name', 'total', 'count']].rename(columns={
                    'category_name': 'Category',
                    'total': 'Total (₹)',
                    'count': 'Transactions'
                }),
                use_container_width=True
            )
        else:
            st.info("No expense data available.")

def render_export_center():
    """Render export center for downloading reports."""
    st.subheader("Export Center")
    
    st.info("Generate and download reports in various formats (PDF, Excel, CSV).")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Quick Exports**")
        
        export_date_range = st.selectbox(
            "Export Period",
            ["Current Month", "Last Month", "Current Quarter", "Current Year", "Custom"],
            key="export_range"
        )
        
        if export_date_range == "Custom":
            export_start = st.date_input("Start Date", value=date.today() - timedelta(days=30), key="export_start")
            export_end = st.date_input("End Date", value=date.today(), key="export_end")
        else:
            export_start, export_end = get_predefined_date_range(export_date_range)
        
        # Quick export buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("📄 Export PDF Report"):
                generate_pdf_export(export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d"))
        
        with col_btn2:
            if st.button("📊 Export Excel Report"):
                generate_excel_export(export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d"))
    
    with col2:
        st.markdown("**Specialized Reports**")
        
        # Member giving report
        if st.button("👥 Member Giving Report (PDF)"):
            generate_member_giving_pdf(export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d"))
        
        # Ledger report
        if st.button("📋 Ledger Report (PDF)"):
            generate_ledger_pdf(export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d"))
        
        # Raw data export
        if st.button("💾 Raw Data Export (CSV)"):
            generate_csv_export(export_start.strftime("%Y-%m-%d"), export_end.strftime("%Y-%m-%d"))

def get_predefined_date_range(range_option: str) -> tuple:
    """Get start and end dates for predefined ranges."""
    today = date.today()
    
    if range_option == "Current Month":
        start_date = today.replace(day=1)
        end_date = today
    elif range_option == "Last Month":
        first_day_current = today.replace(day=1)
        end_date = first_day_current - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif range_option == "Current Quarter":
        quarter = (today.month - 1) // 3 + 1
        start_date = date(today.year, (quarter - 1) * 3 + 1, 1)
        end_date = today
    elif range_option == "Last Quarter":
        quarter = (today.month - 1) // 3 + 1
        if quarter == 1:
            start_date = date(today.year - 1, 10, 1)
            end_date = date(today.year - 1, 12, 31)
        else:
            start_date = date(today.year, (quarter - 2) * 3 + 1, 1)
            end_date = date(today.year, (quarter - 1) * 3, 1) - timedelta(days=1)
    elif range_option == "Current Year":
        start_date = date(today.year, 1, 1)
        end_date = today
    elif range_option == "Last Year":
        start_date = date(today.year - 1, 1, 1)
        end_date = date(today.year - 1, 12, 31)
    elif range_option == "Last 3 Months":
        start_date = today - timedelta(days=90)
        end_date = today
    else:  # All Time
        start_date = date(2020, 1, 1)  # Reasonable start date
        end_date = today
    
    return start_date, end_date

def generate_and_display_financial_report(report_type: str, start_date: str, end_date: str):
    """Generate and display financial report based on type."""
    try:
        df = reporting_manager.get_financial_data(start_date, end_date)
        
        if df.empty:
            st.warning("No data found for the selected date range.")
            return
        
        st.success(f"Generated {report_type} for {start_date} to {end_date}")
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        
        total_income = df[df['transaction_type'] == 'Income']['amount'].sum()
        total_expense = df[df['transaction_type'] == 'Expense']['amount'].sum()
        net_amount = total_income - total_expense
        
        with col1:
            st.metric("Total Income", f"₹{total_income:,.2f}")
        with col2:
            st.metric("Total Expenses", f"₹{total_expense:,.2f}")
        with col3:
            st.metric("Net Amount", f"₹{net_amount:,.2f}")
        
        # Display data table
        st.subheader("Transaction Details")
        display_df = df.copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
        
        # Charts
        if report_type in ["Comprehensive Financial Report", "Category Analysis"]:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Category breakdown
                category_summary = df.groupby(['transaction_type', 'category_name'])['amount'].sum().reset_index()
                fig_bar = px.bar(
                    category_summary,
                    x='category_name',
                    y='amount',
                    color='transaction_type',
                    title="Amount by Category",
                    color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
                )
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_chart2:
                # Income vs Expense pie
                summary = df.groupby('transaction_type')['amount'].sum()
                fig_pie = px.pie(
                    values=summary.values,
                    names=summary.index,
                    title="Income vs Expenses",
                    color_discrete_map={'Income': '#00CC96', 'Expense': '#FF6692'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

def generate_and_display_member_report(report_type: str, start_date: str, end_date: str, member_id: int = None):
    """Generate and display member-related reports."""
    try:
        if report_type == "Individual Member Summary" and member_id:
            summary = reporting_manager.get_member_financial_summary(member_id, start_date, end_date)
            
            if summary:
                st.success(f"Member Financial Summary: {summary['member_name']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Contributions", f"₹{summary['income_total']:,.2f}")
                with col2:
                    st.metric("Number of Contributions", summary['income_count'])
                with col3:
                    avg_contribution = summary['income_total'] / summary['income_count'] if summary['income_count'] > 0 else 0
                    st.metric("Average Contribution", f"₹{avg_contribution:.2f}")
                
                # Get detailed transactions for this member
                transactions = finance_manager.get_transactions_by_member(member_id)
                if transactions:
                    df_member = pd.DataFrame(transactions)
                    df_member = df_member[
                        (df_member['transaction_date'] >= start_date) & 
                        (df_member['transaction_date'] <= end_date)
                    ]
                    
                    if not df_member.empty:
                        st.subheader("Transaction History")
                        display_df = df_member[['transaction_date', 'transaction_type', 'category_name', 'amount', 'description']].copy()
                        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
                        st.dataframe(display_df, use_container_width=True)
            else:
                st.warning("No data found for the selected member and date range.")
        
        elif report_type == "Member Giving Report":
            # This would show all members' giving
            st.success("Member Giving Report Generated")
            st.info("This report shows giving patterns for all members.")
            
            # Get all members with contributions
            df = reporting_manager.get_financial_data(start_date, end_date)
            member_contributions = df[
                (df['transaction_type'] == 'Income') & 
                (df['member_name'].notna())
            ].groupby('member_name')['amount'].agg(['sum', 'count', 'mean']).reset_index()
            
            if not member_contributions.empty:
                member_contributions.columns = ['Member Name', 'Total Contributions', 'Number of Contributions', 'Average Contribution']
                member_contributions['Total Contributions'] = member_contributions['Total Contributions'].apply(lambda x: f"₹{x:,.2f}")
                member_contributions['Average Contribution'] = member_contributions['Average Contribution'].apply(lambda x: f"₹{x:.2f}")
                
                st.dataframe(member_contributions, use_container_width=True)
            else:
                st.info("No member contributions found for the selected period.")
    
    except Exception as e:
        st.error(f"Error generating member report: {str(e)}")

def generate_custom_report(transaction_types, selected_categories, start_date, end_date, 
                         min_amount, max_amount, include_member_info, include_charts, 
                         group_by_category, group_by_month):
    """Generate custom report based on user criteria."""
    try:
        # Get base data
        df = reporting_manager.get_financial_data(start_date, end_date)
        
        if df.empty:
            st.warning("No data found for the selected criteria.")
            return
        
        # Apply filters
        if transaction_types:
            df = df[df['transaction_type'].isin(transaction_types)]
        
        if selected_categories:
            # Parse category selections
            category_filters = []
            for cat in selected_categories:
                if cat.startswith("Income: "):
                    category_filters.append(('Income', cat[8:]))
                elif cat.startswith("Expense: "):
                    category_filters.append(('Expense', cat[9:]))
            
            if category_filters:
                filter_condition = False
                for trans_type, cat_name in category_filters:
                    condition = (df['transaction_type'] == trans_type) & (df['category_name'] == cat_name)
                    filter_condition = filter_condition | condition
                df = df[filter_condition]
        
        if min_amount is not None:
            df = df[df['amount'] >= min_amount]
        
        if max_amount is not None:
            df = df[df['amount'] <= max_amount]
        
        if df.empty:
            st.warning("No data matches the selected criteria.")
            return
        
        st.success(f"Custom Report Generated - {len(df)} transactions found")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        total_amount = df['amount'].sum()
        avg_amount = df['amount'].mean()
        transaction_count = len(df)
        
        with col1:
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
        with col2:
            st.metric("Average Amount", f"₹{avg_amount:.2f}")
        with col3:
            st.metric("Transaction Count", transaction_count)
        
        # Grouping options
        if group_by_category:
            st.subheader("Grouped by Category")
            category_group = df.groupby(['transaction_type', 'category_name'])['amount'].agg(['sum', 'count', 'mean']).reset_index()
            category_group.columns = ['Type', 'Category', 'Total', 'Count', 'Average']
            category_group['Total'] = category_group['Total'].apply(lambda x: f"₹{x:,.2f}")
            category_group['Average'] = category_group['Average'].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(category_group, use_container_width=True)
        
        if group_by_month:
            st.subheader("Grouped by Month")
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            df['month_year'] = df['transaction_date'].dt.to_period('M')
            monthly_group = df.groupby(['month_year', 'transaction_type'])['amount'].sum().reset_index()
            monthly_pivot = monthly_group.pivot(index='month_year', columns='transaction_type', values='amount').fillna(0)
            st.dataframe(monthly_pivot, use_container_width=True)
        
        # Display detailed data
        st.subheader("Detailed Transactions")
        display_columns = ['transaction_date', 'transaction_type', 'category_name', 'amount']
        if include_member_info:
            display_columns.append('member_name')
        display_columns.append('description')
        
        display_df = df[display_columns].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
        
        # Charts
        if include_charts and len(df) > 1:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if 'transaction_type' in df.columns and df['transaction_type'].nunique() > 1:
                    type_summary = df.groupby('transaction_type')['amount'].sum()
                    fig_pie = px.pie(
                        values=type_summary.values,
                        names=type_summary.index,
                        title="Amount by Transaction Type"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_chart2:
                if df['category_name'].nunique() > 1:
                    category_summary = df.groupby('category_name')['amount'].sum().sort_values(ascending=True)
                    fig_bar = px.bar(
                        x=category_summary.values,
                        y=category_summary.index,
                        orientation='h',
                        title="Amount by Category"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error generating custom report: {str(e)}")

def generate_pdf_export(start_date: str, end_date: str):
    """Generate and provide PDF export."""
    try:
        pdf_data = reporting_manager.generate_comprehensive_financial_report_pdf(start_date, end_date)
        
        st.download_button(
            label="📄 Download Comprehensive Financial Report (PDF)",
            data=pdf_data,
            file_name=f"financial_report_{start_date}_{end_date}.pdf",
            mime="application/pdf"
        )
        st.success("PDF report generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")

def generate_excel_export(start_date: str, end_date: str):
    """Generate and provide Excel export."""
    try:
        df = reporting_manager.get_financial_data(start_date, end_date)
        excel_data = reporting_manager.generate_excel_report(df, "Financial_Report", include_charts=True)
        
        st.download_button(
            label="📊 Download Financial Report (Excel)",
            data=excel_data,
            file_name=f"financial_report_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Excel report generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating Excel: {str(e)}")

def generate_member_giving_pdf(start_date: str, end_date: str):
    """Generate member giving PDF report."""
    try:
        pdf_data = reporting_manager.generate_member_giving_report_pdf(start_date, end_date)
        
        st.download_button(
            label="👥 Download Member Giving Report (PDF)",
            data=pdf_data,
            file_name=f"member_giving_report_{start_date}_{end_date}.pdf",
            mime="application/pdf"
        )
        st.success("Member giving report generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating member giving report: {str(e)}")

def generate_ledger_pdf(start_date: str, end_date: str):
    """Generate ledger PDF report."""
    try:
        # Use the existing ledger report function
        pdf_data = reporting_manager.generate_ledger_report_pdf(start_date, end_date)
        
        st.download_button(
            label="📋 Download Ledger Report (PDF)",
            data=pdf_data,
            file_name=f"ledger_report_{start_date}_{end_date}.pdf",
            mime="application/pdf"
        )
        st.success("Ledger report generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating ledger report: {str(e)}")

def generate_csv_export(start_date: str, end_date: str):
    """Generate CSV export of raw data."""
    try:
        df = reporting_manager.get_financial_data(start_date, end_date)
        
        if not df.empty:
            csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="💾 Download Raw Data (CSV)",
                data=csv_data,
                file_name=f"transaction_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
            st.success("CSV export generated successfully!")
        else:
            st.warning("No data available for CSV export.")
    
    except Exception as e:
        st.error(f"Error generating CSV export: {str(e)}")
