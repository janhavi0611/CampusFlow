from datetime import datetime, timedelta

from app.extensions import db
from app.models import Event, Resource, ResourceRequest, ResourceRequestItem, User


def test_full_role_workflow_end_to_end(client, app):
    # 1. Organizer logs in
    client.post("/auth/login", data={"username": "organizer", "password": "org123"})

    # 2. Organizer creates an event
    now = datetime.now() + timedelta(days=5)
    start_str = now.strftime("%Y-%m-%dT10:00")
    end_str = now.strftime("%Y-%m-%dT14:00")

    res_event = client.post("/events/create", data={
        "name": "End to End Workshop",
        "organizer": "Organizer User",
        "expected_attendance": "40",
        "start_datetime": start_str,
        "end_datetime": end_str,
        "description": "Full workflow test event.",
        "status": "Submitted",
    }, follow_redirects=True)

    assert res_event.status_code == 200

    with app.app_context():
        event = Event.query.filter_by(name="End to End Workshop").first()
        assert event is not None
        assert event.owner.username == "organizer"

        res_hall = Resource.query.filter_by(name="Lab 101").first()
        assert res_hall is not None

        req = ResourceRequest(
            event_id=event.id,
            requester_id=event.owner_id,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            status="Pending",
        )
        db.session.add(req)
        db.session.flush()

        item = ResourceRequestItem(request_id=req.id, resource_id=res_hall.id)
        db.session.add(item)
        db.session.commit()
        req_id = req.id

        # 3. Directly process allocation (atomic) within the same app context
        from app.services import process_allocation
        success, msg, alts = process_allocation(req_id)

        approved_req = db.session.get(ResourceRequest, req_id)
        assert approved_req.status in ["Allocated", "Approved"], f"Expected Allocated, got {approved_req.status}: {msg}"

        assert len(approved_req.allocations) == 1
