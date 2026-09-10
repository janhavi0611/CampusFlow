from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.models import Allocation, Event, Resource, ResourceRequest

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def dashboard():
    events_query = Event.query
    requests_query = ResourceRequest.query

    if not current_user.is_admin:
        events_query = events_query.filter((Event.owner_id == current_user.id) | (Event.owner_id.is_(None)))
        requests_query = requests_query.filter((ResourceRequest.requester_id == current_user.id) | (ResourceRequest.requester_id.is_(None)))

    total_events = events_query.count()
    total_resources = Resource.query.count()
    total_requests = requests_query.count()

    active_resources = Resource.query.filter_by(is_active=True).count()
    inactive_resources = Resource.query.filter_by(is_active=False).count()

    pending_requests = requests_query.filter_by(status="Pending").count()
    allocated_requests = requests_query.filter(ResourceRequest.status.in_(["Allocated", "Approved"])).count()
    rejected_requests = requests_query.filter_by(status="Rejected").count()
    cancelled_requests = requests_query.filter_by(status="Cancelled").count()

    upcoming_events = events_query.filter(Event.status.notin_(["Cancelled", "Completed"])).order_by(Event.start_datetime.asc()).limit(5).all()
    pending_request_list = requests_query.filter_by(status="Pending").order_by(ResourceRequest.created_at.desc()).limit(5).all()
    recent_allocations = Allocation.query.filter_by(status="Allocated").order_by(Allocation.created_at.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_events=total_events,
        total_resources=total_resources,
        total_requests=total_requests,
        active_resources=active_resources,
        inactive_resources=inactive_resources,
        pending_requests=pending_requests,
        allocated_requests=allocated_requests,
        rejected_requests=rejected_requests,
        cancelled_requests=cancelled_requests,
        upcoming_events=upcoming_events,
        pending_request_list=pending_request_list,
        recent_allocations=recent_allocations,
    )