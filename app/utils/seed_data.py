"""
Demo data population helper for CampusFlow.
Provides a clean, reusable, idempotent seed function for initialization and local testing.
"""
from datetime import datetime, timedelta
import logging

from app.extensions import db
from app.models import (
    Allocation,
    Event,
    Resource,
    ResourceRequest,
    ResourceRequestItem,
    ResourceRequirement,
    User,
)
from app.services import process_allocation

logger = logging.getLogger(__name__)


def seed_demo_data(drop_existing: bool = False) -> dict:
    """
    Populates the database with demo users, resources, events, and requests.
    If drop_existing=True, existing tables are dropped and recreated first.
    If drop_existing=False, seeds items idempotently without duplicating existing records.
    """
    if drop_existing:
        logger.info("Dropping all existing tables...")
        db.drop_all()

    db.create_all()

    # 1. Users
    demo_users = [
        ("admin", "Administrator", "admin@campusflow.edu", "Admin", "admin123"),
        ("organizer", "Sarah Jenkins", "sarah@campusflow.edu", "Organizer", "org123"),
        ("organizer2", "David Chen", "david@campusflow.edu", "Organizer", "org123"),
    ]

    user_dict = {}
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
            db.session.flush()
        user_dict[username] = user

    db.session.commit()

    # 2. Resources
    demo_resources = [
        {"name": "Main Auditorium", "resource_type": "Auditorium", "capacity": 500, "is_active": True},
        {"name": "Mini Seminar Hall", "resource_type": "Auditorium", "capacity": 150, "is_active": True},
        {"name": "Computer Science Lab 101", "resource_type": "Laboratory", "capacity": 60, "is_active": True},
        {"name": "Electronics Lab 202", "resource_type": "Laboratory", "capacity": 40, "is_active": True},
        {"name": "High-Res Projector Alpha", "resource_type": "Projector", "capacity": None, "is_active": True},
        {"name": "Portable Projector Beta", "resource_type": "Projector", "capacity": None, "is_active": True},
        {"name": "Wireless Mic System A", "resource_type": "Microphone", "capacity": None, "is_active": True},
        {"name": "Wireless Mic System B", "resource_type": "Microphone", "capacity": None, "is_active": True},
        {"name": "Studio 4K Camera 1", "resource_type": "Camera", "capacity": None, "is_active": True},
        {"name": "DSLR Camera 2", "resource_type": "Camera", "capacity": None, "is_active": False},
    ]

    resource_dict = {}
    for res_data in demo_resources:
        res = Resource.query.filter_by(name=res_data["name"]).first()
        if res is None:
            res = Resource(
                name=res_data["name"],
                resource_type=res_data["resource_type"],
                capacity=res_data["capacity"],
                is_active=res_data["is_active"],
            )
            db.session.add(res)
            db.session.flush()
        resource_dict[res_data["name"]] = res

    db.session.commit()

    # 3. Events
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    demo_events = [
        {
            "name": "Annual Tech Symposium 2026",
            "organizer": "Sarah Jenkins",
            "description": "A flagship 2-day technical conference featuring student innovations and guest lectures.",
            "expected_attendance": 350,
            "start_datetime": now + timedelta(days=2, hours=9),
            "end_datetime": now + timedelta(days=2, hours=17),
            "status": "Submitted",
            "owner_username": "organizer",
        },
        {
            "name": "AI & Robotics Workshop",
            "organizer": "David Chen",
            "description": "Hands-on workshop covering deep learning models and autonomous robotics.",
            "expected_attendance": 45,
            "start_datetime": now + timedelta(days=3, hours=10),
            "end_datetime": now + timedelta(days=3, hours=14),
            "status": "Approved",
            "owner_username": "organizer2",
        },
        {
            "name": "Cultural Night Rehearsal",
            "organizer": "Sarah Jenkins",
            "description": "Music and dance rehearsal for the upcoming annual cultural festival.",
            "expected_attendance": 100,
            "start_datetime": now + timedelta(days=5, hours=16),
            "end_datetime": now + timedelta(days=5, hours=20),
            "status": "Draft",
            "owner_username": "organizer",
        },
    ]

    event_dict = {}
    for ev_data in demo_events:
        ev = Event.query.filter_by(name=ev_data["name"]).first()
        if ev is None:
            owner = user_dict.get(ev_data["owner_username"])
            ev = Event(
                name=ev_data["name"],
                organizer=ev_data["organizer"],
                description=ev_data["description"],
                expected_attendance=ev_data["expected_attendance"],
                start_datetime=ev_data["start_datetime"],
                end_datetime=ev_data["end_datetime"],
                status=ev_data["status"],
                owner_id=owner.id if owner else None,
            )
            db.session.add(ev)
            db.session.flush()
        event_dict[ev_data["name"]] = ev

    db.session.commit()

    # 4. Resource Requests & Allocations
    if ResourceRequest.query.count() == 0:
        e1 = event_dict.get("Annual Tech Symposium 2026")
        e2 = event_dict.get("AI & Robotics Workshop")
        org1 = user_dict.get("organizer")
        org2 = user_dict.get("organizer2")

        r1 = resource_dict.get("Main Auditorium")
        r5 = resource_dict.get("High-Res Projector Alpha")
        r3 = resource_dict.get("Computer Science Lab 101")
        r6 = resource_dict.get("Portable Projector Beta")

        if e1 and org1 and r1 and r5:
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

        if e2 and org2 and r3 and r6:
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

            # Process allocation for req2 to show approved/allocated state
            process_allocation(req2.id)

        db.session.commit()

    return {
        "users": len(user_dict),
        "resources": len(resource_dict),
        "events": len(event_dict),
        "requests": ResourceRequest.query.count(),
    }
