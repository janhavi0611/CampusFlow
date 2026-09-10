from datetime import datetime

from app.extensions import db


class ResourceRequest(db.Model):
    __tablename__ = "resource_requests"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False
    )

    requester_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    start_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    end_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    rejection_reason = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    STATUS_CHOICES = ["Pending", "Approved", "Allocated", "Rejected", "Cancelled"]

    event = db.relationship(
        "Event",
        back_populates="resource_requests"
    )

    requester = db.relationship(
        "User",
        back_populates="resource_requests"
    )

    items = db.relationship(
        "ResourceRequestItem",
        back_populates="request",
        cascade="all, delete-orphan"
    )

    requirements = db.relationship(
        "ResourceRequirement",
        back_populates="request",
        cascade="all, delete-orphan"
    )

    allocations = db.relationship(
        "Allocation",
        back_populates="request",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ResourceRequest {self.id} (Event #{self.event_id} - {self.status})>"


class ResourceRequirement(db.Model):
    __tablename__ = "resource_requirements"

    id = db.Column(db.Integer, primary_key=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("resource_requests.id"),
        nullable=False
    )

    resource_type = db.Column(
        db.String(50),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    request = db.relationship(
        "ResourceRequest",
        back_populates="requirements"
    )


class ResourceRequestItem(db.Model):
    __tablename__ = "resource_request_items"

    id = db.Column(db.Integer, primary_key=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("resource_requests.id"),
        nullable=False
    )

    resource_id = db.Column(
        db.Integer,
        db.ForeignKey("resources.id"),
        nullable=False
    )

    request = db.relationship(
        "ResourceRequest",
        back_populates="items"
    )

    resource = db.relationship(
        "Resource",
        back_populates="request_items"
    )

    allocation = db.relationship(
        "Allocation",
        back_populates="request_item",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Allocation(db.Model):
    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("resource_requests.id"),
        nullable=True
    )

    request_item_id = db.Column(
        db.Integer,
        db.ForeignKey("resource_request_items.id"),
        nullable=True
    )

    resource_id = db.Column(
        db.Integer,
        db.ForeignKey("resources.id"),
        nullable=False
    )

    start_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    end_datetime = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Allocated"  # 'Allocated' | 'Active' | 'Cancelled'
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    request = db.relationship(
        "ResourceRequest",
        back_populates="allocations"
    )

    request_item = db.relationship(
        "ResourceRequestItem",
        back_populates="allocation"
    )

    resource = db.relationship(
        "Resource",
        back_populates="allocations"
    )

    def __repr__(self):
        return f"<Allocation Resource #{self.resource_id} ({self.status})>"