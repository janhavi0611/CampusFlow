"""
Seed script for populating CampusFlow database with initial demo data.
Run with: python seed.py
"""
import os
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import Event, Resource, ResourceRequest, ResourceRequestItem, ResourceRequirement, User
from app.services import process_allocation

app = create_app()

with app.app_context():
    print("Dropping existing tables and creating fresh database tables...")
    db.drop_all()
    db.create_all()

    # 1. Users
    print("Seeding Users...")
    admin = User(username="admin", name="Administrator", email="admin@campusflow.edu", role="Admin")
    admin.set_password("admin123")

    org1 = User(username="organizer", name="Sarah Jenkins", email="sarah@campusflow.edu", role="Organizer")
    org1.set_password("org123")

    org2 = User(username="organizer2", name="David Chen", email="david@campusflow.edu", role="Organizer")
    org2.set_password("org123")

    db.session.add_all([admin, org1, org2])
    db.session.commit()

    # 2. Resources
    print("Seeding Resources...")
    r1 = Resource(name="Main Auditorium", resource_type="Auditorium", capacity=500, is_active=True)
    r2 = Resource(name="Mini Seminar Hall", resource_type="Auditorium", capacity=150, is_active=True)
    r3 = Resource(name="Computer Science Lab 101", resource_type="Laboratory", capacity=60, is_active=True)
    r4 = Resource(name="Electronics Lab 202", resource_type="Laboratory", capacity=40, is_active=True)
    r5 = Resource(name="High-Res Projector Alpha", resource_type="Projector", is_active=True)
    r6 = Resource(name="Portable Projector Beta", resource_type="Projector", is_active=True)
    r7 = Resource(name="Wireless Mic System A", resource_type="Microphone", is_active=True)
    r8 = Resource(name="Wireless Mic System B", resource_type="Microphone", is_active=True)
    r9 = Resource(name="Studio 4K Camera 1", resource_type="Camera", is_active=True)
    r10 = Resource(name="DSLR Camera 2", resource_type="Camera", is_active=False)

    db.session.add_all([r1, r2, r3, r4, r5, r6, r7, r8, r9, r10])
    db.session.commit()

    # 3. Events
    print("Seeding Events...")
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    e1 = Event(
        name="Annual Tech Symposium 2026",
        organizer="Sarah Jenkins",
        description="A flagship 2-day technical conference featuring student innovations and guest lectures.",
        expected_attendance=350,
        start_datetime=now + timedelta(days=2, hours=9),
        end_datetime=now + timedelta(days=2, hours=17),
        status="Submitted",
        owner_id=org1.id,
    )

    e2 = Event(
        name="AI & Robotics Workshop",
        organizer="David Chen",
        description="Hands-on workshop covering deep learning models and autonomous robotics.",
        expected_attendance=45,
        start_datetime=now + timedelta(days=3, hours=10),
        end_datetime=now + timedelta(days=3, hours=14),
        status="Approved",
        owner_id=org2.id,
    )

    e3 = Event(
        name="Cultural Night Rehearsal",
        organizer="Sarah Jenkins",
        description="Music and dance rehearsal for the upcoming annual cultural festival.",
        expected_attendance=100,
        start_datetime=now + timedelta(days=5, hours=16),
        end_datetime=now + timedelta(days=5, hours=20),
        status="Draft",
        owner_id=org1.id,
    )

    db.session.add_all([e1, e2, e3])
    db.session.commit()

    # 4. Resource Requests
    print("Seeding Resource Requests & Allocations...")
    req1 = ResourceRequest(
        event_id=e1.id,
        requester_id=org1.id,
        start_datetime=e1.start_datetime,
        end_datetime=e1.end_datetime,
        status="Pending",
    )
    db.session.add(req1)
    db.session.flush()

    item1 = ResourceRequestItem(request_id=req1.id, resource_id=r1.id)
    item2 = ResourceRequestItem(request_id=req1.id, resource_id=r5.id)
    req1_type = ResourceRequirement(request_id=req1.id, resource_type="Microphone", quantity=1)
    db.session.add_all([item1, item2, req1_type])

    req2 = ResourceRequest(
        event_id=e2.id,
        requester_id=org2.id,
        start_datetime=e2.start_datetime,
        end_datetime=e2.end_datetime,
        status="Pending",
    )
    db.session.add(req2)
    db.session.flush()

    item3 = ResourceRequestItem(request_id=req2.id, resource_id=r3.id)
    item4 = ResourceRequestItem(request_id=req2.id, resource_id=r6.id)
    db.session.add_all([item3, item4])
    db.session.commit()

    # Automatically process allocation for req2 to demonstrate approved/allocated state
    process_allocation(req2.id)

    print("Database seeding completed successfully!")
    print("\nDemo Accounts:")
    print("  Admin:     admin / admin123")
    print("  Organizer: organizer / org123")
    print("  Organizer: organizer2 / org123")
