# Church Treasury Management System (CTMS) - Documentation

## Table of Contents
1.  [Introduction](#1-introduction)
2.  [Features](#2-features)
3.  [Setup and Installation](#3-setup-and-installation)
4.  [Usage Guide](#4-usage-guide)
    *   [4.1 Login and Authentication](#41-login-and-authentication)
    *   [4.2 Dashboard](#42-dashboard)
    *   [4.3 Membership Management](#43-membership-management)
    *   [4.4 Finance Management](#44-finance-management)
    *   [4.5 Reporting](#45-reporting)
    *   [4.6 User Management (Admin Only)](#46-user-management-admin-only)
    *   [4.7 My Profile](#47-my-profile)
5.  [Technical Architecture](#5-technical-architecture)
6.  [Database Schema](#6-database-schema)
7.  [Troubleshooting](#7-troubleshooting)
8.  [Future Enhancements](#8-future-enhancements)
9.  [Contact and Support](#9-contact-and-support)

---

## 1. Introduction

The Church Treasury Management System (CTMS) is a comprehensive web-based application designed to assist churches in managing their membership data, financial transactions, and reporting needs. Built with Streamlit and SQLite, CTMS provides an intuitive interface for treasurers, secretaries, and administrators to efficiently oversee church operations. The system includes robust authentication and role-based access control to ensure data security and integrity.

## 2. Features

CTMS offers the following key modules and features:

### 2.1 Dashboard
*   **Executive Overview:** Key Performance Indicators (KPIs) for members and finances.
*   **Financial Trends:** Interactive charts showing monthly income and expense trends.
*   **Member Growth:** Visualizations of member growth over time.
*   **Alerts & Notifications:** System-generated alerts for unusual financial patterns or member engagement issues.
*   **Upcoming Events:** Displays upcoming member birthdays and baptism anniversaries.
*   **Quick Actions:** Shortcuts to frequently used functions like adding members or transactions.

### 2.2 Membership Management
*   **Member Registration:** Add new members with detailed personal, contact, and church-specific information.
*   **Data Validation:** Ensures data integrity with email, phone number, and date validations.
*   **Member Directory:** View, search, and filter all church members.
*   **Status Tracking:** Manage member statuses (Active, New, Visitor, Inactive).
*   **Baptism Records:** Track baptism dates and status.
*   **Emergency Contacts:** Store emergency contact information.
*   **Member Analytics:** Basic statistics on member demographics and activity.

### 2.3 Finance Management
*   **Transaction Recording:** Log income and expense transactions with details like date, amount, category, description, and associated member.
*   **Category Management:** Create and manage custom income and expense categories.
*   **Transaction Validation:** Ensures valid financial data entry.
*   **Financial Summaries:** Year-to-Date (YTD) and current month income, expenses, and net balances.
*   **Recent Transactions:** Quick view of the latest financial activities.
*   **Interactive Charts:** Visualizations of financial distribution by category.

### 2.4 Reporting
*   **Comprehensive Reports:** Generate various financial and membership reports.
*   **PDF & Excel Export:** Export reports in professional PDF and editable Excel formats.
*   **Member Giving Reports:** Track individual member contributions.
*   **Financial Statements:** Generate income statements and expense breakdowns.
*   **Custom Report Builder:** Filter and customize reports based on various criteria.
*   **Audit Log Reports:** View system activities and user actions.

### 2.5 Authentication and User Role System
*   **Secure Login:** User authentication with hashed passwords and salting.
*   **Role-Based Access Control (RBAC):**
    *   **Admin:** Full system access, user management, and settings.
    *   **Treasurer:** Comprehensive financial management and reporting.
    *   **Secretary:** Membership management and reporting.
    *   **Member:** View access to dashboard, members, finances, and reports.
    *   **Viewer:** Limited read-only access to dashboard and reports.
*   **Session Management:** Token-based sessions with expiration.
*   **User Management:** Admin interface to add, edit, activate/deactivate users, and change roles.
*   **Audit Logging:** Records significant user actions and system events for security and compliance.
*   **Profile Management:** Users can view their profile and change their password.
*   **Account Lockout:** Protects against brute-force attacks by locking accounts after multiple failed login attempts.

## 3. Setup and Installation

To set up and run the CTMS application, follow these steps:

### 3.1 Prerequisites
*   **Python 3.8+**
*   **pip** (Python package installer)

### 3.2 Installation Steps
1.  **Clone the Repository (if applicable) or download the project files.**
    ```bash
    # If using git
    git clone <repository_url>
    cd ctms-project
    ```
    *(Assuming project files are in `/home/ubuntu` for this documentation)*

2.  **Navigate to the project directory:**
    ```bash
    cd /home/ubuntu
    ```

3.  **Install required Python packages:**
    ```bash
    pip install streamlit pandas plotly fpdf2 openpyxl streamlit-authenticator
    ```
    *(Note: `streamlit-authenticator` was initially used but replaced by custom `auth_manager.py` and `auth_ui.py` for enhanced control. It's listed here for completeness if any legacy components remain.)*

4.  **Initialize the database:**
    The application uses SQLite. The database schema will be automatically created and updated on first run if `auth_manager.initialize_auth_tables()` is called. Ensure `initialize_db.py` is run once to set up the initial tables for members, transactions, and categories.
    ```bash
    python3 initialize_db.py
    ```
    This script will create `ctms.db` and set up the necessary tables. The `auth_manager` will handle its own tables (`users`, `user_sessions`, `audit_log`).

5.  **Run the application:**
    The main application file is `app_secure.py` which integrates the authentication system.
    ```bash
    streamlit run app_secure.py --server.port 8501 --server.headless true
    ```
    Replace `8501` with any available port if needed. The `--server.headless true` option runs Streamlit without opening a browser window on the server, making it accessible via the provided external URL.

6.  **Access the application:**
    Open your web browser and navigate to the external URL provided by Streamlit (e.g., `http://<your-server-ip>:8501`).

## 4. Usage Guide

### 4.1 Login and Authentication
Upon launching the application, you will be presented with a login screen.
*   **Default Admin Credentials:**
    *   **Username:** `admin`
    *   **Password:** `admin123`
    *   **Recommendation:** Change the default admin password immediately after the first login for security reasons.
*   **Role-Based Access:** Your access to different modules and functionalities will depend on your assigned role (Admin, Treasurer, Secretary, Member, Viewer).

### 4.2 Dashboard
The Dashboard provides a high-level overview of the church's operations.
*   **KPIs:** View total members, YTD income/expenses, weekly cash flow, and member engagement rates.
*   **Financial Trends:** Analyze monthly income and expense patterns through interactive charts.
*   **Member Growth:** Track the cumulative growth of church membership.
*   **Alerts:** Monitor financial alerts and member engagement notices.
*   **Upcoming Events:** See upcoming birthdays and baptism anniversaries.
*   **Quick Actions:** Use buttons to quickly navigate to other modules for common tasks.

### 4.3 Membership Management
Navigate to "Membership Management" from the sidebar.
*   **Add New Member:** Fill in the form with member details. The system includes validation for email, phone, and dates.
*   **View/Edit Members:** Browse the member list, search for specific members, and click on a member to view/edit their details.
*   **Filter Members:** Use filters to sort members by status, gender, or other criteria.

### 4.4 Finance Management
Navigate to "Finance Management" from the sidebar.
*   **Add Transaction:** Record new income or expense transactions. Select a category, amount, date, and optionally link it to a member.
*   **Manage Categories:** Add new income or expense categories as needed.
*   **View Transactions:** See a list of all recorded transactions. Use filters to view transactions by type, category, or date range.
*   **Financial Summaries:** Review YTD and monthly financial performance.

### 4.5 Reporting
Navigate to "Reporting" from the sidebar.
*   **Generate Reports:** Select from various report types (e.g., Income Statement, Expense Breakdown, Member Contributions).
*   **Customize Reports:** Apply date ranges, categories, or member filters to generate specific reports.
*   **Export:** Download reports in PDF or Excel format for further analysis or record-keeping.

### 4.6 User Management (Admin Only)
Accessible only to users with the 'Admin' role.
*   **View Users:** See a list of all system users with their roles and status.
*   **Add New User:** Create new user accounts, assign roles, and set initial passwords.
*   **Edit User:** Modify user details, including email, full name, and role.
*   **Activate/Deactivate User:** Control user access to the system.
*   **Change Role:** Update a user's role and associated permissions.
*   **Audit Log:** Review a detailed log of all significant system and user actions.

### 4.7 My Profile
Accessible to all authenticated users.
*   **View Profile:** See your username, full name, email, role, and last login information.
*   **Change Password:** Securely update your account password.

## 5. Technical Architecture

CTMS is built using the following technologies:
*   **Frontend/Backend Framework:** [Streamlit](https://streamlit.io/) for rapid web application development.
*   **Database:** [SQLite](https://www.sqlite.org/index.html) for lightweight, file-based data storage.
*   **Data Manipulation:** [Pandas](https://pandas.pydata.org/) for efficient data handling and analysis.
*   **Charting:** [Plotly Express](https://plotly.com/python/plotly-express/) and [Plotly Graph Objects](https://plotly.com/python/graph-objects/) for interactive and professional visualizations.
*   **Authentication:** Custom `auth_manager.py` and `auth_ui.py` modules for secure user authentication, RBAC, and audit logging.
*   **Reporting:** `fpdf2` for PDF generation and `openpyxl` for Excel exports.

### Project Structure
```
ctms-project/
├── app_secure.py           # Main application entry point with authentication
├── auth_manager.py         # Handles user authentication, roles, permissions, and audit logging
├── auth_ui.py              # Streamlit UI components for login, user management, and profile
├── dashboard_manager.py    # Logic for fetching dashboard data and generating charts
├── dashboard_ui.py         # Streamlit UI components for the dashboard
├── finance_manager.py      # Logic for financial transactions and category management
├── finance_ui.py           # Streamlit UI components for finance management
├── initialize_db.py        # Script to initialize the SQLite database schema
├── member_manager.py       # Logic for member data management
├── membership_ui.py        # Streamlit UI components for membership management
├── reporting_manager.py    # Logic for generating various reports
├── reporting_ui.py         # Streamlit UI components for the reporting module
├── ctms.db                 # SQLite database file (generated after initialization)
└── CTMS_Documentation.md   # This documentation file
```

## 6. Database Schema

The CTMS uses an SQLite database (`ctms.db`) with the following tables:

### `members` Table
Stores information about church members.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `name`                 | TEXT      | Full name of the member                         |
| `mobile_no`            | TEXT      | Member's mobile number                          |
| `email_address`        | TEXT      | Member's email address (unique)                 |
| `physical_address`     | TEXT      | Member's physical address                       |
| `join_date`            | DATE      | Date the member joined the church               |
| `date_of_birth`        | DATE      | Member's date of birth                          |
| `gender`               | TEXT      | Member's gender                                 |
| `membership_status`    | TEXT      | Current status (e.g., 'Active', 'New', 'Visitor', 'Inactive') |
| `baptized`             | BOOLEAN   | TRUE if baptized, FALSE otherwise               |
| `baptism_date`         | DATE      | Date of baptism                                 |
| `emergency_contact_name`| TEXT      | Name of emergency contact                       |
| `emergency_contact_number`| TEXT      | Phone number of emergency contact               |
| `notes`                | TEXT      | Any additional notes                              |
| `created_at`           | DATETIME  | Timestamp of record creation                    |
| `updated_at`           | DATETIME  | Timestamp of last update                        |

### `transactions` Table
Records all financial income and expense transactions.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `transaction_date`     | DATE      | Date of the transaction                         |
| `transaction_type`     | TEXT      | 'Income' or 'Expense'                           |
| `category_name`        | TEXT      | Category of the transaction (e.g., 'Tithes', 'Utilities') |
| `amount`               | REAL      | Amount of the transaction                       |
| `description`          | TEXT      | Brief description of the transaction            |
| `member_id`            | INTEGER   | Foreign Key to `members` table (optional)       |
| `created_at`           | DATETIME  | Timestamp of record creation                    |
| `updated_at`           | DATETIME  | Timestamp of last update                        |

### `categories` Table
Manages income and expense categories.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `name`                 | TEXT      | Name of the category (unique)                   |
| `type`                 | TEXT      | 'Income' or 'Expense'                           |
| `created_at`           | DATETIME  | Timestamp of record creation                    |
| `updated_at`           | DATETIME  | Timestamp of last update                        |

### `users` Table
Stores user authentication and role information.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `username`             | TEXT      | Unique username for login                       |
| `email`                | TEXT      | Unique email address                            |
| `password_hash`        | TEXT      | Hashed password                                 |
| `salt`                 | TEXT      | Salt used for password hashing                  |
| `role`                 | TEXT      | User's role (e.g., 'admin', 'treasurer')        |
| `full_name`            | TEXT      | User's full name                                |
| `is_active`            | BOOLEAN   | TRUE if account is active                       |
| `created_at`           | DATETIME  | Timestamp of user creation                      |
| `updated_at`           | DATETIME  | Timestamp of last update                        |
| `last_login`           | DATETIME  | Timestamp of last successful login              |
| `failed_login_attempts`| INTEGER   | Count of consecutive failed login attempts      |
| `locked_until`         | DATETIME  | Timestamp until which account is locked         |

### `user_sessions` Table
Manages active user sessions.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `user_id`              | INTEGER   | Foreign Key to `users` table                    |
| `session_token`        | TEXT      | Unique token for the session                    |
| `created_at`           | DATETIME  | Timestamp of session creation                   |
| `expires_at`           | DATETIME  | Timestamp when session expires                  |
| `is_active`            | BOOLEAN   | TRUE if session is active                       |
| `ip_address`           | TEXT      | IP address from which session was created       |
| `user_agent`           | TEXT      | User agent string of the client                 |

### `audit_log` Table
Records significant system and user actions.
| Column Name            | Type      | Description                                     |
| :--------------------- | :-------- | :---------------------------------------------- |
| `id`                   | INTEGER   | Primary Key, Auto-incrementing                  |
| `user_id`              | INTEGER   | Foreign Key to `users` table (optional)         |
| `action`               | TEXT      | Type of action (e.g., 'LOGIN_SUCCESS', 'MEMBER_ADDED') |
| `resource`             | TEXT      | Resource affected (e.g., 'users', 'members')    |
| `resource_id`          | INTEGER   | ID of the affected resource                     |
| `details`              | TEXT      | Additional details about the action             |
| `ip_address`           | TEXT      | IP address from which action originated         |
| `timestamp`            | DATETIME  | Timestamp of the action                         |

## 7. Troubleshooting

*   **Application Not Starting:**
    *   Ensure all prerequisites are met and dependencies are installed (`pip install -r requirements.txt` if a requirements file is provided, otherwise install individually as per setup).
    *   Check the console for error messages. Common issues include missing packages or syntax errors.
    *   Verify that the specified port (`--server.port`) is not already in use. Try a different port.
*   **Database Errors (e.g., "no such table", "no such column"):**
    *   Ensure `initialize_db.py` has been run successfully.
    *   If schema changes were made, you might need to drop and recreate the database (`ctms.db`) or manually alter tables to match the latest schema. **Backup your data before doing this.**
*   **Login Issues:**
    *   Double-check username and password. Remember the default admin credentials (`admin`/`admin123`).
    *   If an account is locked, wait for the lockout period to expire or contact an administrator to reset it.
    *   Verify that the `users` table in `ctms.db` contains the expected user data.
*   **Permission Denied:**
    *   Ensure the logged-in user has the necessary role and permissions for the action they are trying to perform. Refer to the "Role Permissions Overview" in the User Management section.

## 8. Future Enhancements

Potential future enhancements for CTMS include:
*   **Cloud Deployment:** Containerization (Docker) and deployment to cloud platforms (AWS, GCP, Azure) for scalability and accessibility.
*   **Advanced Reporting:** More complex financial reports, customizable dashboards, and predictive analytics.
*   **Event Management:** Integration with a calendar system for church events, service scheduling, and resource booking.
*   **Communication Module:** Email and SMS integration for member communication, announcements, and reminders.
*   **Online Giving Integration:** Connect with online giving platforms for automated transaction recording.
*   **Multi-Language Support:** Internationalization (i18n) for broader usability.
*   **Mobile Responsiveness:** Optimize the UI for mobile devices.
*   **Enhanced Security:** Two-factor authentication (2FA), more granular permission controls.

## 9. Contact and Support

For any questions, issues, or support regarding the CTMS application, please refer to the project maintainers or contact the development team.

---

*Documentation Version: 1.0.0*
*Date: September 30, 2025*
*Author: Manus AI*
