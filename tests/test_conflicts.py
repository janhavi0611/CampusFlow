from datetime import datetime, timedelta

from app.extensions import db
from app.models import Allocation, Resource
from app.services import check_resource_conflict, get_conflicting_bookings


def test_conflict_detection_formula(app):
    with app.app_context():
        res = Resource.query.filter_by(name="Main Hall").first()
        base_time = datetime(2026, 10, 1, 10, 0)

        # Create active allocation from 10:00 to 14:00
        alloc = Allocation(
            resource_id=res.id,
            start_datetime=base_time,
            end_datetime=base_time + timedelta(hours=4),
            status="Allocated",
        )
        db.session.add(alloc)
        db.session.commit()

        # Partial overlap (12:00 to 16:00) -> CONFLICT
        assert check_resource_conflict(res.id, base_time + timedelta(hours=2), base_time + timedelta(hours=6)) is True

        # Exact overlap (10:00 to 14:00) -> CONFLICT
        assert check_resource_conflict(res.id, base_time, base_time + timedelta(hours=4)) is True

        # Contained (11:00 to 12:00) -> CONFLICT
        assert check_resource_conflict(res.id, base_time + timedelta(hours=1), base_time + timedelta(hours=2)) is True

        # Containing (08:00 to 16:00) -> CONFLICT
        assert check_resource_conflict(res.id, base_time - timedelta(hours=2), base_time + timedelta(hours=6)) is True

        # Back to back (14:00 to 16:00) -> ALLOWED (No conflict)
        assert check_resource_conflict(res.id, base_time + timedelta(hours=4), base_time + timedelta(hours=6)) is False

        # Before (08:00 to 10:00) -> ALLOWED (No conflict)
        assert check_resource_conflict(res.id, base_time - timedelta(hours=2), base_time) is False


def test_cancelled_allocations_ignored(app):
    with app.app_context():
        res = Resource.query.filter_by(name="Main Hall").first()
        base_time = datetime(2026, 10, 1, 10, 0)

        alloc = Allocation(
            resource_id=res.id,
            start_datetime=base_time,
            end_datetime=base_time + timedelta(hours=4),
            status="Cancelled",
        )
        db.session.add(alloc)
        db.session.commit()

        assert check_resource_conflict(res.id, base_time, base_time + timedelta(hours=4)) is False
