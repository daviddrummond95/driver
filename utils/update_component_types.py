import sqlite3
import os

def update_component_types():
    # Connect to the database
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    # Get all entries from the database
    cursor.execute("SELECT id FROM component_tags")
    entries = cursor.fetchall()

    # Update each entry with its component type
    for (id,) in entries:
        # The component type is the first part of the path (subdirectory name)
        component_type = id.split('/')[0]

        # Update the database
        cursor.execute("""
        UPDATE component_tags
        SET component_type = ?
        WHERE id = ?
        """, (component_type, id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Component types updated successfully.")

if __name__ == "__main__":
    update_component_types()