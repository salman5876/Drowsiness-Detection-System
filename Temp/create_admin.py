import sqlite3
from werkzeug.security import generate_password_hash

# SQLite database file path
DB_PATH = '../users.db'

def create_admin_user():
    """Create an admin user in the SQLite database."""
    # Check if the user already exists
    username = 'admin'
    password = 'admin'  # You can change this to a more secure password
    email = 'admin@gmail.com'
    # Hash the password
    hashed_password = generate_password_hash(password)

    # Connect to the database and create the admin user if it doesn't exist
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            print(f"User '{username}' already exists in the database.")
        else:
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                           (username, hashed_password, email))
            conn.commit()
            print(f"Admin user '{username}' created successfully.")

if __name__ == '__main__':
    create_admin_user()
