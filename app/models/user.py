from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    """Represents an authenticated user (Admin or Organizer)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Organizer")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ROLES = ["Admin", "Organizer"]

    events = db.relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    resource_requests = db.relationship("ResourceRequest", back_populates="requester", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "Admin"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
