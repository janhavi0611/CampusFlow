from datetime import datetime, timedelta

from app.extensions import db
from app.models import Allocation, Event, Resource, ResourceRequest, ResourceRequestItem, User
from app.services import process_allocation


def test_atomic_allocation_success(app, sample_event, organizer_user):
    with app.app_context():
        res = Resource.query.filter_by(name="Projector A").first()

        req = ResourceRequest(
            event_id=sample_event.id,
            requester_id=organizer_user.id,
            start_datetime=sample_event.start_datetime,
            end_datetime=sample_event.end_datetime,
            status="Pending",
        )
        db.session.add(req)
        db.session.flush()

        item = ResourceRequestItem(request_id=req.id, resource_id=res.id)
        db.session.add(item)
        db.session.commit()

        success, msg, alts = process_allocation(req.id)
        assert success is True
        assert req.status == "Allocated"

        alloc = Allocation.query.filter_by(request_id=req.id).first()
        assert alloc is not None
        assert alloc.status == "Allocated"
        assert alloc.resource_id == res.id


def test_atomic_allocation_conflict_rollback(app, sample_event, organizer_user):
    with app.app_context():
        res = Resource.query.filter_by(name="Main Hall").first()

        # Existing active allocation
        existing_alloc = Allocation(
            resource_id=res.id,
            start_datetime=sample_event.start_datetime,
            end_datetime=sample_event.end_datetime,
            status="Allocated",
        )
        db.session.add(existing_alloc)

        # New request attempting to book the conflicting resource
        req = ResourceRequest(
            event_id=sample_event.id,
            requester_id=organizer_user.id,
            start_datetime=sample_event.start_datetime,
            end_datetime=sample_event.end_datetime,
            status="Pending",
        )
        db.session.add(req)
        db.session.flush()

        item = ResourceRequestItem(request_id=req.id, resource_id=res.id)
        db.session.add(item)
        db.session.commit()

        success, msg, alts = process_allocation(req.id)
        assert success is False
        assert req.status == "Rejected"
        assert "time conflict" in req.rejection_reason.lower()

        # Zero allocations created for failed request
        alloc = Allocation.query.filter_by(request_id=req.id).first()
        assert alloc is None
