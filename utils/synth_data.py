import os
import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_components():
    components = []
    material_repo = "material_repo"
    for category in os.listdir(material_repo):
        category_path = os.path.join(material_repo, category)
        if os.path.isdir(category_path):
            for component in os.listdir(category_path):
                if component.endswith('.html'):
                    component_id = f"{category}-{component.replace('.html', '')}"
                    components.append({"id": component_id, "category": category})
    logger.info(f"Found {len(components)} components")
    logger.info(f"Components: {json.dumps(components)}")
    return components

def generate_synthetic_data(components):
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    # Drop the existing table if it exists
    cursor.execute('DROP TABLE IF EXISTS component_performance')
    logger.info("Dropped existing component_performance table")

    # Create a new component_performance table
    cursor.execute('''
    CREATE TABLE component_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        component_id TEXT,
        category TEXT,
        date DATE,
        impressions INTEGER,
        clicks INTEGER,
        ctr REAL,
        persona TEXT
    )
    ''')
    logger.info("Created new component_performance table")

    # Generate data for the last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    personas = ["Specialist", "Primary Care", "Nurse", "Pharmacist"]

    for component in components:
        logger.info(f"Generating data for component: {component['id']}")
        # Generate base metrics for the component
        base_impressions = random.randint(1000, 10000)
        base_ctr = random.uniform(1, 10)  # CTR between 1% and 10%

        for persona in personas:
            # Adjust base metrics for each persona
            persona_impressions = int(np.random.normal(base_impressions, base_impressions * 0.1))
            persona_ctr = max(0, min(100, np.random.normal(base_ctr, base_ctr * 0.2)))

            current_date = start_date
            while current_date <= end_date:
                # Generate daily data with some randomness
                daily_impressions = max(0, int(np.random.normal(persona_impressions / 30, persona_impressions / 100)))
                daily_ctr = max(0, min(100, np.random.normal(persona_ctr, persona_ctr * 0.1)))
                daily_clicks = int(daily_impressions * (daily_ctr / 100))

                cursor.execute('''
                INSERT INTO component_performance (component_id, category, date, impressions, clicks, ctr, persona)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (component['id'], component['category'], current_date, daily_impressions, daily_clicks, daily_ctr, persona))

                current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    logger.info("Synthetic data generated and stored in the new database table.")

    # Verify the data in the database
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT component_id, category FROM component_performance")
    db_components = cursor.fetchall()
    logger.info(f"Components in database: {json.dumps(db_components)}")
    
    # Log a sample of the generated data
    cursor.execute("SELECT * FROM component_performance LIMIT 5")
    sample_data = cursor.fetchall()
    logger.info(f"Sample of generated data: {json.dumps(sample_data)}")
    
    conn.close()

if __name__ == "__main__":
    components = get_components()
    generate_synthetic_data(components)
