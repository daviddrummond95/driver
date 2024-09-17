import sqlite3
import os
import json

def setup_database():
    # Ensure the directory exists
    os.makedirs('data', exist_ok=True)
    
    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    # Load the taxonomy
    with open('GAIT/config/taxonomy.json', 'r') as f:
        taxonomy = json.load(f)['taxonomy']

    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_tags'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        # Prepare the SQL query to create the table
        columns = ', '.join(f"{field['field'].replace(' ', '_')} TEXT" for field in taxonomy)
        
        # Create the component_tags table with columns for each taxonomy field
        cursor.execute(f'''
        CREATE TABLE component_tags (
            id TEXT PRIMARY KEY,
            component_type TEXT,
            {columns}
        )
        ''')
    else:
        # Check if component_type column exists
        cursor.execute("PRAGMA table_info(component_tags)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'component_type' not in columns:
            cursor.execute("ALTER TABLE component_tags ADD COLUMN component_type TEXT")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Database setup complete.")

def populate_database():
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    material_repo = "material_repo"
    for root, dirs, files in os.walk(material_repo):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, material_repo)
            component_type = relative_path.split('/')[0]  # Get the first part of the path

            # Insert or update the record
            cursor.execute('''
            INSERT OR REPLACE INTO component_tags (id, component_type)
            VALUES (?, ?)
            ''', (relative_path, component_type))

    conn.commit()
    conn.close()
    print("Database populated with file information and component types.")

if __name__ == "__main__":
    setup_database()
    populate_database()