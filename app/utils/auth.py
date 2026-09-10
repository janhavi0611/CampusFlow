"""
Authentication and role-based authorization helpers.
"""
from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required


def admin_required(f):
    """Route decorator requiring Admin role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("That action requires administrator access.", "error")
            return redirect(url_for("dashboard.dashboard"))
        return f(*args, **kwargs)
    return decorated


def owner_or_admin(get_event_fn):
    """
    Decorator factory for routes where an organizer may only touch their own events.
    get_event_fn(kwargs) -> Event
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            event = get_event_fn(kwargs)
            if not event:
                abort(404)
            if not current_user.is_admin and event.owner_id and event.owner_id != current_user.id:
                flash("You do not have permission to perform actions on this event.", "error")
                return redirect(url_for("events.list_events"))
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """Return dict or User model for backward compatibility in context processor."""
    if current_user and current_user.is_authenticated:
        return current_user
    return None
