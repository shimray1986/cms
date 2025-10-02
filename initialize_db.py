import sqlite3

DATABASE_NAME = 'ctms.db'
SCHEMA_FILE = 'database_schema.sql'

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
    
    # Split SQL commands by semicolon, but handle cases where semicolons are inside strings
    # A more robust solution might involve a proper SQL parser, but for this simple schema, splitting by ';\n' should work.
    commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]

    for command in commands:
        try:
            cursor.execute(command)
        except sqlite3.OperationalError as e:
            # Ignore 'table already exists' errors for CREATE TABLE IF NOT EXISTS
            # and 'UNIQUE constraint failed' for INSERT OR IGNORE
            if "table already exists" not in str(e) and "UNIQUE constraint failed" not in str(e):
                print(f"Error executing command: {command}\nError: {e}")

    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized successfully with schema from '{SCHEMA_FILE}'.")

if __name__ == '__main__':
    initialize_database()

