import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import finance_manager
import member_manager
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Toggle debug to True to see what finance_manager returns for categories
DEBUG = False

def render_finance_management():
    """Render the complete finance management interface."""
    st.title("💰 Finance Management")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💳 Add Transaction", 
        "📋 Manage Transactions", 
        "📊 Financial Dashboard", 
        "🏷️ Categories", 
        "📈 Analytics"
    ])
    
    with tab1:
        render_add_transaction_form()
    
    with tab2:
        render_manage_transactions()
    
    with tab3:
        render_financial_dashboard()
    
    with tab4:
        render_category_management()
    
    with tab5:
        render_financial_analytics()

def render_add_transaction_form():
    """Render the add transaction form with validation."""
    st.subheader("Add New Transaction")
    
    # Put transaction type OUTSIDE the form so changing it triggers a rerun and the form rebuilds
    transaction_type = st.radio("Transaction Type", ["Income", "Expense"], horizontal=True, key="add_txn_type")
    
    # Now create the form. transaction_type will be read from the session variable above,
    # and changing the radio will cause Streamlit to rebuild the form with the correct categories.
    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Transaction Details**")
            # transaction_date and amount stay inside the form
            transaction_date = st.date_input("Date", max_value=date.today(), key="add_txn_date")
            amount = st.number_input("Amount (₹)", min_value=0.01, format="%.2f", 
                                   help="Enter the transaction amount", key="add_txn_amount")
        
        with col2:
            st.markdown("**Category & Member**")
            # Fetch categories depending on transaction_type (read from the radio above)
            income_cats = finance_manager.get_income_categories() or []
            expense_cats = finance_manager.get_expense_categories() or []
            categories = income_cats if transaction_type == "Income" else expense_cats

            if DEBUG:
                st.write("DEBUG: income_cats:", income_cats)
                st.write("DEBUG: expense_cats:", expense_cats)
                st.write("DEBUG: chosen categories:", categories)

            # Use a different key for the selectbox depending on transaction_type so Streamlit
            # will create a fresh widget when the radio changes
            select_key = f"add_txn_category_{transaction_type}"

            if not categories:
                st.warning(f"No {transaction_type.lower()} categories found. Please add categories from the 'Categories' tab.")
                # show placeholder selectbox but disabled, with unique key
                selected_category_name = st.selectbox("Category", ["-- No categories available --"], key=f"{select_key}_disabled", disabled=True)
                selected_category_id = None
            else:
                category_names = [cat["name"] for cat in categories]
                selected_category_name = st.selectbox("Category", category_names, key=select_key)
                selected_category_id = next((cat["id"] for cat in categories if cat["name"] == selected_category_name), None)

            # Member selection
            members = member_manager.get_all_members()
            member_options = {"None (No member linked)": None}
            member_options.update({f'{m["name"]} (ID: {m["id"]})': m["id"] for m in members})
            selected_member_display = st.selectbox("Link to Member (Optional)", list(member_options.keys()), key="add_txn_member")
            linked_member_id = member_options[selected_member_display]
        
        with col3:
            st.markdown("**Description**")
            description = st.text_area("Description", height=100, 
                                     help="Optional description for the transaction", key="add_txn_description")
            
            # Transaction summary
            if amount > 0 and selected_category_id:
                st.info(f"""
                **Transaction Summary:**
                - Type: {transaction_type}
                - Amount: ₹{amount:.2f}
                - Category: {selected_category_name}
                - Date: {transaction_date}
                """)
            elif amount > 0 and not selected_category_id:
                st.info(f"Pick a category for this {transaction_type.lower()} or add one in the Categories tab.")
        
        # Form submission
        submitted = st.form_submit_button("Add Transaction", type="primary")
        
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than zero!")
            elif not selected_category_id:
                st.error("Please select a category (or add one in the Categories tab)!")
            else:
                success, message, transaction_id = finance_manager.add_transaction(
                    transaction_date=transaction_date.strftime("%Y-%m-%d"),
                    transaction_type=transaction_type,
                    category_id=selected_category_id,
                    category_name=selected_category_name,
                    amount=amount,
                    description=description,
                    member_id=linked_member_id
                )
                
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

def render_manage_transactions():
    """Render the transaction management interface."""
    st.subheader("Manage Transactions")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        transaction_type_filter = st.selectbox("Filter by Type", ["All", "Income", "Expense"], key="manage_txn_type_filter")
    
    with col2:
        date_range = st.selectbox("Date Range", 
                                 ["All Time", "Last 30 Days", "Current Month", "Current Year", "Custom"], key="manage_date_range")
    
    with col3:
        if date_range == "Custom":
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30), key="manage_start_date")
            end_date = st.date_input("End Date", value=date.today(), key="manage_end_date")
        else:
            start_date = end_date = None
    
    # Get filtered transactions
    if date_range == "All Time":
        transactions = finance_manager.get_all_transactions()
    elif date_range == "Last 30 Days":
        start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = date.today().strftime("%Y-%m-%d")
        transactions = finance_manager.get_transactions_by_date_range(start_date, end_date)
    elif date_range == "Current Month":
        current_date = datetime.now()
        start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = date.today().strftime("%Y-%m-%d")
        transactions = finance_manager.get_transactions_by_date_range(start_date, end_date)
    elif date_range == "Current Year":
        current_year = datetime.now().year
        start_date = f"{current_year}-01-01"
        end_date = f"{current_year}-12-31"
        transactions = finance_manager.get_transactions_by_date_range(start_date, end_date)
    elif date_range == "Custom" and start_date and end_date:
        transactions = finance_manager.get_transactions_by_date_range(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    else:
        transactions = []
    
    # Apply type filter
    if transaction_type_filter != "All":
        transactions = [t for t in transactions if t['transaction_type'] == transaction_type_filter]
    
    st.write(f"Found {len(transactions)} transaction(s)")
    
    if transactions:
        # Create DataFrame for display
        df = pd.DataFrame(transactions)
        display_columns = ['transaction_date', 'transaction_type', 'category_name', 
                         'amount', 'description', 'member_id']
        
        # Rename columns for better display
        column_names = {
            'transaction_date': 'Date',
            'transaction_type': 'Type',
            'category_name': 'Category',
            'amount': 'Amount (₹)',
            'description': 'Description',
            'member_id': 'Member ID'
        }
        
        df_display = df[display_columns].rename(columns=column_names)
        df_display['Amount (₹)'] = df_display['Amount (₹)'].apply(lambda x: f"{x:.2f}")
        
        # Display transactions with selection
        selected_indices = st.dataframe(
            df_display, 
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Edit/Delete selected transaction
        if selected_indices and len(selected_indices.selection.rows) > 0:
            selected_idx = selected_indices.selection.rows[0]
            selected_transaction = transactions[selected_idx]
            
            st.subheader("Edit Selected Transaction")
            
            with st.form("edit_transaction_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_type = st.radio("Type", ["Income", "Expense"], 
                                       index=0 if selected_transaction['transaction_type'] == 'Income' else 1, key="edit_txn_type")
                    edit_date = st.date_input("Date", 
                                            value=datetime.strptime(selected_transaction['transaction_date'], "%Y-%m-%d").date(), key="edit_txn_date")
                    edit_amount = st.number_input("Amount", value=float(selected_transaction['amount']), 
                                                min_value=0.01, format="%.2f", key="edit_txn_amount")
                
                with col2:
                    # Get categories based on type
                    if edit_type == "Income":
                        categories = finance_manager.get_income_categories() or []
                    else:
                        categories = finance_manager.get_expense_categories() or []
                    
                    category_names = [cat["name"] for cat in categories]
                    current_category_idx = 0
                    try:
                        current_category_idx = category_names.index(selected_transaction['category_name'])
                    except ValueError:
                        pass
                    
                    edit_category_name = st.selectbox("Category", category_names or ["-- No categories --"], index=current_category_idx if category_names else 0, key="edit_txn_category")
                    edit_category_id = next((cat["id"] for cat in categories if cat["name"] == edit_category_name), None)
                    
                    edit_description = st.text_area("Description", 
                                                  value=selected_transaction['description'] or "", key="edit_txn_description")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    update_button = st.form_submit_button("Update Transaction", type="primary")
                with col_btn2:
                    delete_button = st.form_submit_button("Delete Transaction", type="secondary")
                
                if update_button:
                    success, message = finance_manager.update_transaction(
                        transaction_id=selected_transaction['id'],
                        transaction_date=edit_date.strftime("%Y-%m-%d"),
                        transaction_type=edit_type,
                        category_id=edit_category_id,
                        category_name=edit_category_name,
                        amount=edit_amount,
                        description=edit_description,
                        member_id=selected_transaction['member_id']
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                
                if delete_button:
                    success, message = finance_manager.delete_transaction(selected_transaction['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("No transactions match the current filters.")

def render_financial_dashboard():
    """Render the financial dashboard with key metrics and charts."""
    st.subheader("Financial Dashboard")
    
    # Key metrics
    ytd_income, ytd_expenses = finance_manager.get_ytd_summary()
    month_income, month_expenses = finance_manager.get_current_month_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("YTD Income", f"₹{ytd_income:,.2f}")
    
    with col2:
        st.metric("YTD Expenses", f"₹{ytd_expenses:,.2f}")
    
    with col3:
        ytd_net = ytd_income - ytd_expenses
        st.metric("YTD Net", f"₹{ytd_net:,.2f}", 
                 delta=f"₹{ytd_net:,.2f}" if ytd_net >= 0 else f"-₹{abs(ytd_net):,.2f}")
    
    with col4:
        month_net = month_income - month_expenses
        st.metric("Current Month Net", f"₹{month_net:,.2f}",
                 delta=f"₹{month_net:,.2f}" if month_net >= 0 else f"-₹{abs(month_net):,.2f}")
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Income vs Expenses (YTD)")
        if ytd_income > 0 or ytd_expenses > 0:
            fig_pie = px.pie(
                values=[ytd_income, ytd_expenses],
                names=['Income', 'Expenses'],
                title="Year-to-Date Financial Overview",
                color_discrete_map={'Income': '#00CC96', 'Expenses': '#FF6692'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No financial data available for chart.")
    
    with col_chart2:
        st.subheader("Monthly Comparison")
        # Get last 6 months data
        monthly_data = []
        for i in range(6):
            month_date = datetime.now() - timedelta(days=30*i)
            start_month = month_date.replace(day=1).strftime("%Y-%m-%d")
            end_month = month_date.replace(day=28).strftime("%Y-%m-%d")  # Simplified
            
            transactions = finance_manager.get_transactions_by_date_range(start_month, end_month)
            income = sum(t['amount'] for t in transactions if t['transaction_type'] == 'Income')
            expenses = sum(t['amount'] for t in transactions if t['transaction_type'] == 'Expense')
            
            monthly_data.append({
                'Month': month_date.strftime("%b %Y"),
                'Income': income,
                'Expenses': expenses
            })
        
        if monthly_data:
            df_monthly = pd.DataFrame(monthly_data)
            fig_bar = px.bar(
                df_monthly, 
                x='Month', 
                y=['Income', 'Expenses'],
                title="Monthly Income vs Expenses",
                barmode='group',
                color_discrete_map={'Income': '#00CC96', 'Expenses': '#FF6692'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Recent transactions
    st.subheader("Recent Transactions")
    recent_transactions = finance_manager.get_recent_transactions(limit=10)
    if recent_transactions:
        df_recent = pd.DataFrame(recent_transactions)
        display_columns = ['transaction_date', 'transaction_type', 'category_name', 'amount', 'description']
        column_names = {
            'transaction_date': 'Date',
            'transaction_type': 'Type',
            'category_name': 'Category',
            'amount': 'Amount (₹)',
            'description': 'Description'
        }
        
        df_display = df_recent[display_columns].rename(columns=column_names)
        df_display['Amount (₹)'] = df_display['Amount (₹)'].apply(lambda x: f"{x:.2f}")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No recent transactions to display.")

def render_category_management():
    """Render category management interface."""
    st.subheader("Category Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Income Categories**")
        income_categories = finance_manager.get_income_categories()
        
        # Add new income category
        with st.form("add_income_category"):
            new_income_category = st.text_input("New Income Category Name", key="new_income_cat")
            add_income_btn = st.form_submit_button("Add Income Category")
            
            if add_income_btn and new_income_category:
                success, message, cat_id = finance_manager.add_income_category(new_income_category)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        # Display existing income categories
        if income_categories:
            df_income = pd.DataFrame(income_categories)
            st.dataframe(df_income[['name']], use_container_width=True)
        else:
            st.info("No income categories found.")

    with col2:
        st.markdown("**Expense Categories**")
        expense_categories = finance_manager.get_expense_categories()
        
        # Add new expense category
        with st.form("add_expense_category"):
            new_expense_category = st.text_input("New Expense Category Name", key="new_expense_cat")
            add_expense_btn = st.form_submit_button("Add Expense Category")
            
            if add_expense_btn and new_expense_category:
                success, message, cat_id = finance_manager.add_expense_category(new_expense_category)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        # Display existing expense categories
        if expense_categories:
            df_expense = pd.DataFrame(expense_categories)
            st.dataframe(df_expense[['name']], use_container_width=True)
        else:
            st.info("No expense categories found.")

def render_financial_analytics():
    """Render financial analytics and insights."""
    st.subheader("Financial Analytics")
    
    # Get financial statistics
    stats = finance_manager.get_financial_statistics()
    
    if not stats:
        st.error("Unable to load financial statistics.")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", stats.get('total_transactions', 0))
    
    with col2:
        income_count = stats.get('type_summary', {}).get('Income', {}).get('count', 0)
        st.metric("Income Transactions", income_count)
    
    with col3:
        expense_count = stats.get('type_summary', {}).get('Expense', {}).get('count', 0)
        st.metric("Expense Transactions", expense_count)
    
    with col4:
        recent_count = stats.get('recent_activity', {}).get('recent_count', 0)
        st.metric("Recent Activity (30 days)", recent_count)
    
    # Category analysis
    col_cat1, col_cat2 = st.columns(2)
    
    with col_cat1:
        st.subheader("Top Income Categories")
        top_income = stats.get('top_income_categories', [])
        if top_income:
            df_income = pd.DataFrame(top_income)
            fig_income = px.bar(
                df_income, 
                x='category_name', 
                y='total_amount',
                title="Top Income Categories by Amount",
                color='total_amount',
                color_continuous_scale='Greens'
            )
            fig_income.update_layout(xaxis_title="Category", yaxis_title="Total Amount (₹)")
            st.plotly_chart(fig_income, use_container_width=True)
        else:
            st.info("No income data available.")
    
    with col_cat2:
        st.subheader("Top Expense Categories")
        top_expenses = stats.get('top_expense_categories', [])
        if top_expenses:
            df_expenses = pd.DataFrame(top_expenses)
            fig_expenses = px.bar(
                df_expenses, 
                x='category_name', 
                y='total_amount',
                title="Top Expense Categories by Amount",
                color='total_amount',
                color_continuous_scale='Reds'
            )
            fig_expenses.update_layout(xaxis_title="Category", yaxis_title="Total Amount (₹)")
            st.plotly_chart(fig_expenses, use_container_width=True)
        else:
            st.info("No expense data available.")
    
    # Average transaction amounts
    st.subheader("Average Transaction Amounts")
    avg_amounts = stats.get('average_amounts', {})
    if avg_amounts:
        col_avg1, col_avg2 = st.columns(2)
        with col_avg1:
            avg_income = avg_amounts.get('Income', 0)
            st.metric("Average Income Transaction", f"₹{avg_income:.2f}")
        with col_avg2:
            avg_expense = avg_amounts.get('Expense', 0)
            st.metric("Average Expense Transaction", f"₹{avg_expense:.2f}")
    
    # Transaction trends (if we have enough data)
    st.subheader("Transaction Trends")
    current_year = datetime.now().year
    monthly_summary = finance_manager.get_monthly_summary_by_category(current_year)
    
    if monthly_summary:
        df_trends = pd.DataFrame(monthly_summary)
        
        # Group by month and transaction type
        monthly_totals = df_trends.groupby(['month', 'transaction_type'])['total_amount'].sum().reset_index()
        
        if not monthly_totals.empty:
            fig_trends = px.line(
                monthly_totals, 
                x='month', 
                y='total_amount', 
                color='transaction_type',
                title=f"Monthly Transaction Trends - {current_year}",
                markers=True
            )
            fig_trends.update_layout(
                xaxis_title="Month", 
                yaxis_title="Total Amount (₹)",
                xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                          ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            )
            st.plotly_chart(fig_trends, use_container_width=True)
        else:
            st.info("Insufficient data for trend analysis.")
    else:
        st.info("No data available for trend analysis.")
