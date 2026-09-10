from datetime import datetime, timedelta

from app.extensions import db
from app.models import Allocation, Resource
from app.services import find_alternative


def test_find_alternative_venue_capacity(app):
    with app.app_context():
        # Create venues of different capacities
        r_small = Resource(name="Small Room", resource_type="Auditorium", capacity=100, is_active=True)
        r_med = Resource(name="Medium Room", resource_type="Auditorium", capacity=200, is_active=True)
        r_large = Resource(name="Large Room", resource_type="Auditorium", capacity=500, is_active=True)
        db.session.add_all([r_small, r_med, r_large])
        db.session.commit()

        start = datetime(2026, 10, 1, 10, 0)
        end = datetime(2026, 10, 1, 12, 0)

        # For capacity 150, Small Room is too small.
        # Medium Room is preferred (smallest sufficient) — exclude Main Hall from fixture
        main_hall = Resource.query.filter_by(name="Main Hall").first()
        alt = find_alternative("Auditorium", 150, start, end, exclude_ids=[main_hall.id])
        assert alt is not None
        assert alt.name == "Medium Room"

        # Block Medium Room with active allocation
        alloc = Allocation(resource_id=r_med.id, start_datetime=start, end_datetime=end, status="Allocated")
        db.session.add(alloc)
        db.session.commit()

        # Now Large Room should be returned (exclude Main Hall + Medium Room)
        alt2 = find_alternative("Auditorium", 150, start, end, exclude_ids=[main_hall.id, r_med.id])
        assert alt2 is not None
        assert alt2.name == "Large Room"
