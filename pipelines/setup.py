import sqlite3
import os

def setup_database():
    # Ensure the directory exists
    os.makedirs('data', exist_ok=True)
    
    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    # Create the component_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS component_tags (
        id TEXT PRIMARY KEY,
        tags TEXT
    )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()