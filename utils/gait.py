import os
import sqlite3
from pipelines.GAIT import tag_content
import json

def process_materials():
    # Connect to the database
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    # Ensure the table structure is up to date
    ensure_table_structure(cursor)

    # Get the immediate subdirectories of material_repo
    material_repo = 'material_repo'
    subdirs = [d for d in os.listdir(material_repo) if os.path.isdir(os.path.join(material_repo, d))]

    for subdir in subdirs:
        subdir_path = os.path.join(material_repo, subdir)
        for file in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, file)
            print(file_path)
            if os.path.isfile(file_path):
                # Read the content of the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Tag the content using GAIT
                tags = tag_content(content)

                # Update the database with the tags
                update_database(cursor, file_path, tags)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def ensure_table_structure(cursor):
    # Load the taxonomy
    with open('GAIT/config/taxonomy.json', 'r') as f:
        taxonomy = json.load(f)['taxonomy']

    # Get existing columns
    cursor.execute("PRAGMA table_info(component_tags)")
    existing_columns = set(row[1] for row in cursor.fetchall())

    # Add missing columns
    for field in taxonomy:
        column_name = field['field'].replace(' ', '_')
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE component_tags ADD COLUMN {column_name} TEXT")

def update_database(cursor, file_path, tags):
    # Prepare the SQL query
    columns = ', '.join(f"{field.replace(' ', '_')}" for field in tags.keys())
    placeholders = ', '.join('?' for _ in tags.keys())
    values = [','.join(tag_list) for tag_list in tags.values()]

    query = f"""
    INSERT OR REPLACE INTO component_tags (id, {columns})
    VALUES (?, {placeholders})
    """

    # Execute the query
    cursor.execute(query, [file_path] + values)

if __name__ == "__main__":
    process_materials()
