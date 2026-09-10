from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Event
from app.utils.auth import admin_required

events_bp = Blueprint("events", __name__, url_prefix="/events")


def parse_datetime(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@events_bp.route("/")
@login_required
def list_events():
    status = request.args.get("status", "").strip()
    date_value = request.args.get("date", "").strip()

    query = Event.query

    if not current_user.is_admin:
        query = query.filter((Event.owner_id == current_user.id) | (Event.owner_id.is_(None)))

    if status:
        query = query.filter_by(status=status)

    if date_value:
        try:
            selected_date = datetime.strptime(date_value, "%Y-%m-%d").date()
            start_of_day = datetime.combine(selected_date, datetime.min.time())
            end_of_day = datetime.combine(selected_date, datetime.max.time())
            query = query.filter(
                Event.start_datetime >= start_of_day,
                Event.start_datetime <= end_of_day
            )
        except ValueError:
            flash("Invalid date filter.", "error")

    events = query.order_by(Event.start_datetime.asc()).all()

    return render_template(
        "events/list.html",
        events=events,
        selected_status=status,
        selected_date=date_value,
        status_choices=Event.STATUS_CHOICES,
    )


@events_bp.route("/<int:event_id>")
@login_required
def detail_event(event_id):
    event = db.get_or_404(Event, event_id)
    if not current_user.is_admin and event.owner_id and event.owner_id != current_user.id:
        flash("You do not have permission to view this event.", "error")
        return redirect(url_for("events.list_events"))

    return render_template("events/detail.html", event=event)


@events_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        organizer = request.form.get("organizer", "").strip() or current_user.name
        description = request.form.get("description", "").strip()
        attendance_str = request.form.get("expected_attendance", "").strip()
        start_str = request.form.get("start_datetime", "").strip()
        end_str = request.form.get("end_datetime", "").strip()
        status = request.form.get("status", "Draft")

        if not name:
            flash("Event name is required.", "error")
            return render_template("events/create.html", status_choices=Event.STATUS_CHOICES)

        try:
            expected_attendance = int(attendance_str)
            if expected_attendance <= 0:
                raise ValueError
        except ValueError:
            flash("Expected attendance must be a positive number.", "error")
            return render_template("events/create.html", status_choices=Event.STATUS_CHOICES)

        start_datetime = parse_datetime(start_str)
        end_datetime = parse_datetime(end_str)

        if not start_datetime or not end_datetime:
            flash("Please enter valid start and end dates/times.", "error")
            return render_template("events/create.html", status_choices=Event.STATUS_CHOICES)

        if end_datetime <= start_datetime:
            flash("End date/time must be after start date/time.", "error")
            return render_template("events/create.html", status_choices=Event.STATUS_CHOICES)

        if status not in Event.STATUS_CHOICES:
            status = "Draft"

        event = Event(
            name=name,
            organizer=organizer,
            description=description,
            expected_attendance=expected_attendance,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            status=status,
            owner_id=current_user.id,
        )

        db.session.add(event)
        db.session.commit()

        flash(f"Event '{event.name}' created successfully.", "success")
        return redirect(url_for("events.detail_event", event_id=event.id))

    return render_template("events/create.html", status_choices=Event.STATUS_CHOICES)


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = db.get_or_404(Event, event_id)
    if not current_user.is_admin and event.owner_id and event.owner_id != current_user.id:
        flash("You do not have permission to edit this event.", "error")
        return redirect(url_for("events.list_events"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        organizer = request.form.get("organizer", "").strip()
        description = request.form.get("description", "").strip()
        attendance_str = request.form.get("expected_attendance", "").strip()
        start_str = request.form.get("start_datetime", "").strip()
        end_str = request.form.get("end_datetime", "").strip()
        target_status = request.form.get("status", event.status)

        if not name or not organizer:
            flash("Event name and organizer are required.", "error")
            return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)

        try:
            expected_attendance = int(attendance_str)
            if expected_attendance <= 0:
                raise ValueError
        except ValueError:
            flash("Expected attendance must be a positive number.", "error")
            return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)

        start_datetime = parse_datetime(start_str)
        end_datetime = parse_datetime(end_str)

        if not start_datetime or not end_datetime or end_datetime <= start_datetime:
            flash("Please enter a valid time window with end date after start date.", "error")
            return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)

        if target_status != event.status and not event.can_transition_to(target_status):
            allowed = Event.VALID_TRANSITIONS.get(event.status, [])
            flash(f"Cannot change status from '{event.status}' to '{target_status}'. Allowed transitions: {allowed}.", "error")
            return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)

        # Verify active allocations fall within new event window
        active_allocations = []
        for req in event.resource_requests:
            for item in req.items:
                if item.allocation and item.allocation.status in ["Allocated", "Active"]:
                    active_allocations.append(item.allocation)

        if active_allocations and any(
            alloc.start_datetime < start_datetime or alloc.end_datetime > end_datetime
            for alloc in active_allocations
        ):
            flash("The new event schedule must fully cover all active resource allocations.", "error")
            return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)

        event.name = name
        event.organizer = organizer
        event.description = description
        event.expected_attendance = expected_attendance
        event.start_datetime = start_datetime
        event.end_datetime = end_datetime
        event.status = target_status

        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("events.detail_event", event_id=event.id))

    return render_template("events/edit.html", event=event, status_choices=Event.STATUS_CHOICES)


@events_bp.route("/<int:event_id>/cancel", methods=["POST"])
@login_required
def cancel_event(event_id):
    event = db.get_or_404(Event, event_id)
    if not current_user.is_admin and event.owner_id and event.owner_id != current_user.id:
        flash("You do not have permission to cancel this event.", "error")
        return redirect(url_for("events.list_events"))

    if event.status == "Cancelled":
        flash("Event is already cancelled.", "error")
        return redirect(url_for("events.list_events"))

    if event.status == "Completed":
        flash("Completed events cannot be cancelled.", "error")
        return redirect(url_for("events.list_events"))

    try:
        for req in event.resource_requests:
            if req.status in ["Allocated", "Approved"]:
                for item in req.items:
                    if item.allocation:
                        item.allocation.status = "Cancelled"
                req.status = "Cancelled"
            elif req.status == "Pending":
                req.status = "Cancelled"

        event.status = "Cancelled"
        db.session.commit()
        flash("Event cancelled and all associated active bookings were released.", "success")
    except Exception:
        db.session.rollback()
        flash("Unable to cancel event due to a database error.", "error")

    return redirect(url_for("events.list_events"))
