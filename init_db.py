"""
Database initialization script.
Run with: python init_db.py
"""

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    demo_users = [
        ("admin", "Administrator", "admin@campusflow.edu", "Admin", "admin123"),
        ("organizer", "Sarah Jenkins", "sarah@campusflow.edu", "Organizer", "org123"),
        ("organizer2", "David Chen", "david@campusflow.edu", "Organizer", "org123"),
    ]

    for username, name, email, role, password in demo_users:
        user = User.query.filter_by(username=username).first()

        if user is None:
            user = User(
                username=username,
                name=name,
                email=email,
                role=role,
            )
            user.set_password(password)
            db.session.add(user)

    db.session.commit()

print("Database initialized successfully.")
print("Demo users are ready.")