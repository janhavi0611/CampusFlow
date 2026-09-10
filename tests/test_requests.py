from datetime import datetime, timedelta

from app.extensions import db
from app.models import Event, Resource, ResourceRequest, ResourceRequestItem


def test_create_resource_request(app, sample_event, organizer_user):
    with app.app_context():
        res = Resource.query.filter_by(name="Main Hall").first()

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

        fetched = ResourceRequest.query.get(req.id)
        assert fetched is not None
        assert fetched.status == "Pending"
        assert len(fetched.items) == 1
        assert fetched.items[0].resource_id == res.id
