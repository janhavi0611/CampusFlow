"""
Database initialization script.
Run with: python init_db.py
"""

from app import create_app
from app.utils.seed_data import seed_demo_data

app = create_app()

with app.app_context():
    stats = seed_demo_data(drop_existing=False)
    print("Database initialized successfully.")
    print(f"Loaded demo data: {stats['users']} users, {stats['resources']} resources, {stats['events']} events, {stats['requests']} requests.")