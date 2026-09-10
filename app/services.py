"""
Core business logic for resource allocation, conflict detection, alternative selection,
and atomic approval workflows.
"""
import logging
from datetime import datetime

from app.extensions import db
from app.models import Allocation, Resource, ResourceRequest, ResourceRequestItem, ResourceRequirement

log = logging.getLogger(__name__)


# ─── Conflict Detection ───────────────────────────────────────────────────────

def check_resource_conflict(
    resource_id: int,
    start_dt: datetime,
    end_dt: datetime,
    exclude_request_id: int = None,
) -> bool:
    """Return True if resource has an active/allocated booking overlapping [start_dt, end_dt)."""
    query = Allocation.query.filter(
        Allocation.resource_id == resource_id,
        Allocation.status.in_(["Allocated", "Active"]),
        Allocation.start_datetime < end_dt,   # existing starts before new ends
        Allocation.end_datetime > start_dt,   # existing ends after new starts
    )
    if exclude_request_id:
        query = query.filter(Allocation.request_id != exclude_request_id)
    return query.first() is not None


def get_conflicting_bookings(
    resource_id: int,
    start_dt: datetime,
    end_dt: datetime,
) -> list:
    """Return all active allocations conflicting with the given time window."""
    return Allocation.query.filter(
        Allocation.resource_id == resource_id,
        Allocation.status.in_(["Allocated", "Active"]),
        Allocation.start_datetime < end_dt,
        Allocation.end_datetime > start_dt,
    ).all()


# ─── Alternative Selection ────────────────────────────────────────────────────

def find_alternative(
    resource_type: str,
    required_capacity: int | None,
    start_dt: datetime,
    end_dt: datetime,
    exclude_ids: list = None,
) -> Resource | None:
    """
    Return the best available alternative Resource, or None.

    Selection priority: active -> same type -> sufficient capacity -> no conflict ->
    smallest sufficient capacity (for venues) / alphabetical (for equipment).
    """
    exclude_ids = exclude_ids or []

    query = Resource.query.filter(
        Resource.resource_type == resource_type,
        Resource.is_active.is_(True),
    )
    if exclude_ids:
        query = query.filter(Resource.id.notin_(exclude_ids))

    if required_capacity is not None:
        query = query.filter(Resource.capacity >= required_capacity)
        query = query.order_by(Resource.capacity.asc(), Resource.name.asc())
    else:
        query = query.order_by(Resource.name.asc())

    candidates = query.all()
    for candidate in candidates:
        if not check_resource_conflict(candidate.id, start_dt, end_dt):
            return candidate

    return None


def find_available_resources_of_type(
    resource_type: str,
    required_capacity: int | None,
    quantity: int,
    start_dt: datetime,
    end_dt: datetime,
    exclude_ids: set = None,
) -> list[Resource]:
    """Find active, available physical resources matching criteria."""
    exclude_ids = exclude_ids or set()
    query = Resource.query.filter(
        Resource.resource_type == resource_type,
        Resource.is_active.is_(True),
    )
    if exclude_ids:
        query = query.filter(Resource.id.notin_(exclude_ids))

    if required_capacity is not None:
        query = query.filter(Resource.capacity >= required_capacity)
        query = query.order_by(Resource.capacity.asc(), Resource.name.asc())
    else:
        query = query.order_by(Resource.name.asc())

    available = []
    for resource in query.all():
        if not check_resource_conflict(resource.id, start_dt, end_dt):
            available.append(resource)
            if len(available) >= quantity:
                break
    return available


# ─── Atomic Allocation Workflow ────────────────────────────────────────────────

def process_allocation(request_id: int) -> tuple[bool, str, list[dict]]:
    """
    Atomic All-or-Nothing Allocation.

    Checks:
      1. Request status is 'Pending'
      2. Window falls within event's start_datetime and end_datetime
      3. For each resource requirement / item: active status, capacity, and conflict.

    If ALL requirements pass:
      Allocations are created, request status set to 'Allocated' (or 'Approved'), committed.
      Returns (True, "Resources successfully allocated.", []).

    If ANY requirement fails:
      Rolls back db.session, sets status to 'Rejected', sets rejection_reason,
      gathers alternative suggestions, commits rejection state, and returns (False, reason, alternatives).
    """
    req = db.session.get(ResourceRequest, request_id)
    if not req:
        return False, "Request not found.", []

    if req.status != "Pending":
        return False, f"Request is not pending (current status: '{req.status}').", []

    event = req.event

    # 1. Event Window Validation
    if req.start_datetime < event.start_datetime or req.end_datetime > event.end_datetime:
        reason = (
            f"Request time window ({req.start_datetime.strftime('%Y-%m-%d %H:%M')} to "
            f"{req.end_datetime.strftime('%H:%M')}) is outside event schedule "
            f"({event.start_datetime.strftime('%Y-%m-%d %H:%M')} to "
            f"{event.end_datetime.strftime('%H:%M')})."
        )
        req.status = "Rejected"
        req.rejection_reason = reason
        db.session.commit()
        return False, reason, []

    selected_resources = []
    selected_ids = set()
    failure_reasons = []
    alternatives_suggested = []

    # 2. Check direct ResourceRequestItems if any
    for item in req.items:
        res = item.resource
        if not res.is_active:
            failure_reasons.append(f"Resource '{res.name}' is inactive.")
            alt = find_alternative(res.resource_type, event.expected_attendance, req.start_datetime, req.end_datetime, [res.id])
            if alt:
                alternatives_suggested.append({"requested": res.name, "alternative": alt.name, "type": res.resource_type})
            continue

        if res.capacity is not None and res.capacity < event.expected_attendance:
            failure_reasons.append(f"Resource '{res.name}' capacity ({res.capacity}) is less than event attendance ({event.expected_attendance}).")
            alt = find_alternative(res.resource_type, event.expected_attendance, req.start_datetime, req.end_datetime, [res.id])
            if alt:
                alternatives_suggested.append({"requested": res.name, "alternative": alt.name, "type": res.resource_type})
            continue

        if check_resource_conflict(res.id, req.start_datetime, req.end_datetime):
            failure_reasons.append(f"Resource '{res.name}' has a time conflict.")
            alt = find_alternative(res.resource_type, event.expected_attendance if res.capacity else None, req.start_datetime, req.end_datetime, [res.id])
            if alt:
                alternatives_suggested.append({"requested": res.name, "alternative": alt.name, "type": res.resource_type})
            continue

        selected_resources.append((item, res))
        selected_ids.add(res.id)

    # 3. Check ResourceRequirements if any
    for requirement in req.requirements:
        req_capacity = event.expected_attendance if requirement.resource_type in ["Auditorium", "Laboratory"] else None
        available = find_available_resources_of_type(
            requirement.resource_type,
            req_capacity,
            requirement.quantity,
            req.start_datetime,
            req.end_datetime,
            exclude_ids=selected_ids,
        )

        if len(available) < requirement.quantity:
            failure_reasons.append(
                f"Insufficient '{requirement.resource_type}' resources available. "
                f"Requested: {requirement.quantity}, Available: {len(available)}."
            )
            alt = find_alternative(
                requirement.resource_type,
                req_capacity,
                req.start_datetime,
                req.end_datetime,
                exclude_ids=list(selected_ids),
            )
            if alt:
                alternatives_suggested.append({
                    "requested": f"{requirement.quantity}x {requirement.resource_type}",
                    "alternative": alt.name,
                    "type": requirement.resource_type,
                })
        else:
            for res in available:
                selected_ids.add(res.id)
                selected_resources.append((None, res))

    # ATOMIC CHECK: If any failures, ROLLBACK and REJECT
    if failure_reasons:
        db.session.rollback()
        reason_text = " Allocation failed: " + "; ".join(failure_reasons)
        req.status = "Rejected"
        req.rejection_reason = reason_text
        db.session.commit()
        return False, reason_text, alternatives_suggested

    # Success path: Create items & allocations
    try:
        for item, res in selected_resources:
            if item is None:
                item = ResourceRequestItem(
                    request_id=req.id,
                    resource_id=res.id,
                )
                db.session.add(item)
                db.session.flush()

            alloc = Allocation(
                request_id=req.id,
                request_item_id=item.id,
                resource_id=res.id,
                start_datetime=req.start_datetime,
                end_datetime=req.end_datetime,
                status="Allocated",
            )
            db.session.add(alloc)

        req.status = "Allocated"
        req.rejection_reason = None
        db.session.commit()
        return True, "Resources successfully allocated.", []
    except Exception as exc:
        db.session.rollback()
        log.exception("Error during atomic allocation processing")
        return False, f"Database error during allocation: {str(exc)}", []


def cancel_allocation(allocation_id: int) -> bool:
    """Cancel an allocation and update parent request status if all allocations are cancelled."""
    alloc = db.session.get(Allocation, allocation_id)
    if not alloc:
        return False

    alloc.status = "Cancelled"
    req = alloc.request
    if req and all(a.status == "Cancelled" for a in req.allocations):
        req.status = "Cancelled"

    db.session.commit()
    return True


# ─── Resource Availability Grid ────────────────────────────────────────────────

def get_resource_availability(resource_id: int, date_obj) -> dict:
    """Return hourly availability array for a resource on a specific date (08:00 to 20:00)."""
    res = db.session.get(Resource, resource_id)
    if not res:
        return {}

    slots = []
    for hour in range(8, 20):
        start_slot = datetime.combine(date_obj, datetime.min.time()).replace(hour=hour)
        end_slot = datetime.combine(date_obj, datetime.min.time()).replace(hour=hour + 1)

        booking = Allocation.query.filter(
            Allocation.resource_id == resource_id,
            Allocation.status.in_(["Allocated", "Active"]),
            Allocation.start_datetime < end_slot,
            Allocation.end_datetime > start_slot,
        ).first()

        slots.append({
            "time": f"{hour:02d}:00 - {hour+1:02d}:00",
            "is_booked": booking is not None,
            "event_name": booking.request.event.name if (booking and booking.request and booking.request.event) else ("Booked" if booking else None),
        })

    return {
        "resource": res,
        "date": date_obj,
        "slots": slots,
    }
