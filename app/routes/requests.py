from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Event, Resource, ResourceRequest, ResourceRequestItem, ResourceRequirement
from app.services import process_allocation
from app.utils.auth import admin_required

requests_bp = Blueprint("requests", __name__, url_prefix="/requests")


def parse_datetime(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@requests_bp.route("/")
@login_required
def list_requests():
    status = request.args.get("status", "").strip()

    query = ResourceRequest.query

    if not current_user.is_admin:
        query = query.filter((ResourceRequest.requester_id == current_user.id) | (ResourceRequest.requester_id.is_(None)))

    if status:
        query = query.filter_by(status=status)

    requests_list = query.order_by(ResourceRequest.created_at.desc()).all()

    return render_template(
        "requests/list.html",
        requests=requests_list,
        selected_status=status,
        status_choices=ResourceRequest.STATUS_CHOICES,
    )


@requests_bp.route("/<int:request_id>")
@login_required
def detail_request(request_id):
    req = db.get_or_404(ResourceRequest, request_id)
    if not current_user.is_admin and req.requester_id and req.requester_id != current_user.id:
        flash("You do not have permission to view this resource request.", "error")
        return redirect(url_for("requests.list_requests"))

    return render_template("requests/detail.html", req=req)


@requests_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_request():
    events_query = Event.query
    if not current_user.is_admin:
        events_query = events_query.filter((Event.owner_id == current_user.id) | (Event.owner_id.is_(None)))
    events = events_query.filter(Event.status.notin_(["Cancelled", "Completed"])).order_by(Event.start_datetime.asc()).all()

    resources = Resource.query.filter_by(is_active=True).order_by(Resource.name.asc()).all()

    if request.method == "POST":
        event_id_val = request.form.get("event_id", "").strip()
        start_str = request.form.get("start_datetime", "").strip()
        end_str = request.form.get("end_datetime", "").strip()
        resource_ids = request.form.getlist("resource_ids")
        requirement_types = request.form.getlist("requirement_types")
        requirement_quantities = request.form.getlist("requirement_quantities")

        try:
            event_id = int(event_id_val)
            event = db.get_or_404(Event, event_id)
        except (ValueError, Exception):
            flash("Please select a valid event.", "error")
            return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)

        if not current_user.is_admin and event.owner_id and event.owner_id != current_user.id:
            flash("You can only submit resource requests for your own events.", "error")
            return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)

        start_dt = parse_datetime(start_str)
        end_dt = parse_datetime(end_str)

        if not start_dt or not end_dt or end_dt <= start_dt:
            flash("Please enter a valid request time window.", "error")
            return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)

        # Time window validation against event schedule
        if start_dt < event.start_datetime or end_dt > event.end_datetime:
            flash(
                f"Request window must be within the event window "
                f"({event.start_datetime.strftime('%Y-%m-%d %H:%M')} to {event.end_datetime.strftime('%Y-%m-%d %H:%M')}).",
                "error",
            )
            return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)

        if not resource_ids and not requirement_types:
            flash("Please select at least one resource or resource requirement.", "error")
            return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)

        req = ResourceRequest(
            event_id=event.id,
            requester_id=current_user.id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            status="Pending",
        )

        db.session.add(req)
        db.session.flush()

        # Add specific physical resources
        for rid_str in resource_ids:
            if rid_str.strip():
                try:
                    rid = int(rid_str)
                    item = ResourceRequestItem(request_id=req.id, resource_id=rid)
                    db.session.add(item)
                except ValueError:
                    continue

        # Add resource requirements (e.g. 2 Projectors)
        for rtype, rqty in zip(requirement_types, requirement_quantities):
            if rtype.strip() and rqty.strip():
                try:
                    qty = int(rqty)
                    if qty > 0:
                        requirement = ResourceRequirement(
                            request_id=req.id,
                            resource_type=rtype.strip(),
                            quantity=qty,
                        )
                        db.session.add(requirement)
                except ValueError:
                    continue

        db.session.commit()
        flash("Resource request submitted successfully. Awaiting admin approval.", "success")
        return redirect(url_for("requests.detail_request", request_id=req.id))

    return render_template("requests/create.html", events=events, resources=resources, resource_types=Resource.RESOURCE_TYPES)


@requests_bp.route("/<int:request_id>/approve", methods=["POST"])
@admin_required
def approve_request(request_id):
    success, message, alternatives = process_allocation(request_id)
    if success:
        flash("Resource request approved and resources allocated atomically!", "success")
    else:
        alt_msg = ""
        if alternatives:
            alt_str = ", ".join([f"{a['requested']} -> Try '{a['alternative']}'" for a in alternatives])
            alt_msg = f" Recommended alternatives: {alt_str}."
        flash(f"Request Rejected: {message}{alt_msg}", "error")

    return redirect(url_for("requests.detail_request", request_id=request_id))


@requests_bp.route("/<int:request_id>/reject", methods=["POST"])
@admin_required
def reject_request(request_id):
    req = db.get_or_404(ResourceRequest, request_id)
    if req.status != "Pending":
        flash(f"Cannot reject request with status '{req.status}'.", "error")
        return redirect(url_for("requests.list_requests"))

    reason = request.form.get("rejection_reason", "").strip() or "Rejected by administrator."
    req.status = "Rejected"
    req.rejection_reason = reason
    db.session.commit()

    flash("Resource request rejected.", "success")
    return redirect(url_for("requests.detail_request", request_id=req.id))


@requests_bp.route("/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel_request(request_id):
    req = db.get_or_404(ResourceRequest, request_id)
    if not current_user.is_admin and req.requester_id and req.requester_id != current_user.id:
        flash("You do not have permission to cancel this request.", "error")
        return redirect(url_for("requests.list_requests"))

    if req.status == "Cancelled":
        flash("Request is already cancelled.", "error")
        return redirect(url_for("requests.list_requests"))

    for alloc in req.allocations:
        alloc.status = "Cancelled"

    for item in req.items:
        if item.allocation:
            item.allocation.status = "Cancelled"

    req.status = "Cancelled"
    db.session.commit()

    flash("Resource request cancelled and all bookings released.", "success")
    return redirect(url_for("requests.detail_request", request_id=req.id))
