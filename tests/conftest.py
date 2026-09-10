from datetime import datetime, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import Event, Resource, ResourceRequest, ResourceRequestItem, User


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        db.create_all()

        # Create demo users
        admin = User(username="admin", name="Admin User", email="admin@test.com", role="Admin")
        admin.set_password("admin123")

        organizer = User(username="organizer", name="Organizer User", email="org@test.com", role="Organizer")
        organizer.set_password("org123")

        organizer2 = User(username="organizer2", name="Organizer Two", email="org2@test.com", role="Organizer")
        organizer2.set_password("org123")

        db.session.add_all([admin, organizer, organizer2])

        # Create demo resources
        r_aud = Resource(name="Main Hall", resource_type="Auditorium", capacity=300, is_active=True)
        r_lab = Resource(name="Lab 101", resource_type="Laboratory", capacity=50, is_active=True)
        r_proj1 = Resource(name="Projector A", resource_type="Projector", is_active=True)
        r_proj2 = Resource(name="Projector B", resource_type="Projector", is_active=True)

        db.session.add_all([r_aud, r_lab, r_proj1, r_proj2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    return User.query.filter_by(username="admin").first()


@pytest.fixture
def organizer_user(app):
    return User.query.filter_by(username="organizer").first()


@pytest.fixture
def sample_event(app, organizer_user):
    now = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    event = Event(
        name="Sample Conference",
        organizer="Organizer User",
        expected_attendance=100,
        start_datetime=now,
        end_datetime=now + timedelta(hours=4),
        status="Draft",
        owner_id=organizer_user.id,
    )
    db.session.add(event)
    db.session.commit()
    return event
