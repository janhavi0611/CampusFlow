from datetime import datetime, timedelta

from app.models import Event


def test_event_state_transitions(app):
    with app.app_context():
        event = Event(
            name="State Transition Test",
            organizer="Tester",
            expected_attendance=50,
            start_datetime=datetime.now(),
            end_datetime=datetime.now() + timedelta(hours=2),
            status="Draft",
        )

        assert event.can_transition_to("Submitted") is True
        assert event.can_transition_to("Cancelled") is True
        assert event.can_transition_to("Completed") is False

        event.status = "Approved"
        assert event.can_transition_to("Completed") is True
        assert event.can_transition_to("Cancelled") is True
