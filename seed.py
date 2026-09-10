"""
Seed script for populating CampusFlow database with initial demo data.
Run with: python seed.py
"""
from app import create_app
from app.utils.seed_data import seed_demo_data

app = create_app()

with app.app_context():
    print("Dropping existing tables and recreating fresh database tables...")
    stats = seed_demo_data(drop_existing=True)
    print("Database seeding completed successfully!")
    print(f"Loaded: {stats['users']} users, {stats['resources']} resources, {stats['events']} events, {stats['requests']} requests.")
    print("\nDemo Accounts:")
    print("  Admin:     admin / admin123")
    print("  Organizer: organizer / org123")
    print("  Organizer: organizer2 / org123")

