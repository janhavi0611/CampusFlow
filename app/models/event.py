from datetime import datetime

from app.extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    expected_attendance = db.Column(db.Integer, nullable=False)

    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Draft"
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    STATUS_CHOICES = ["Draft", "Submitted", "Approved", "Cancelled", "Completed"]

    VALID_TRANSITIONS = {
        "Draft": ["Submitted", "Cancelled"],
        "Submitted": ["Approved", "Cancelled", "Draft"],
        "Approved": ["Completed", "Cancelled"],
        "Cancelled": [],
        "Completed": [],
    }

    owner = db.relationship("User", back_populates="events")

    resource_requests = db.relationship(
        "ResourceRequest",
        back_populates="event",
        cascade="all, delete-orphan"
    )

    def can_transition_to(self, target_status: str) -> bool:
        """Return True if transitioning from current status to target_status is valid."""
        if self.status == target_status:
            return True
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        return target_status in allowed

    def __repr__(self):
        return f"<Event {self.name} ({self.status})>"