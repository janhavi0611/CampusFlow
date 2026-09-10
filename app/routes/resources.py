from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Resource
from app.services import get_resource_availability
from app.utils.auth import admin_required

resources_bp = Blueprint("resources", __name__, url_prefix="/resources")


@resources_bp.route("/")
@login_required
def list_resources():
    status = request.args.get("status", "").strip().lower()
    resource_type = request.args.get("type", "").strip()

    query = Resource.query

    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)

    if resource_type:
        query = query.filter_by(resource_type=resource_type)

    resources = query.order_by(Resource.name.asc()).all()

    return render_template(
        "resources/list.html",
        resources=resources,
        selected_status=status,
        selected_type=resource_type,
        resource_types=Resource.RESOURCE_TYPES,
    )


@resources_bp.route("/create", methods=["GET", "POST"])
@admin_required
def create_resource():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        resource_type = request.form.get("resource_type", "").strip()
        capacity_val = request.form.get("capacity", "").strip()

        if not name:
            flash("Resource name is required.", "error")
            return render_template("resources/create.html", resource_types=Resource.RESOURCE_TYPES)

        if resource_type not in Resource.RESOURCE_TYPES:
            flash("Invalid resource type.", "error")
            return render_template("resources/create.html", resource_types=Resource.RESOURCE_TYPES)

        existing = Resource.query.filter_by(name=name).first()
        if existing:
            flash(f"A resource named '{name}' already exists.", "error")
            return render_template("resources/create.html", resource_types=Resource.RESOURCE_TYPES)

        capacity = None
        if capacity_val:
            try:
                capacity = int(capacity_val)
                if capacity <= 0:
                    raise ValueError
            except ValueError:
                flash("Capacity must be a positive whole number.", "error")
                return render_template("resources/create.html", resource_types=Resource.RESOURCE_TYPES)

        resource = Resource(
            name=name,
            resource_type=resource_type,
            capacity=capacity,
            is_active=True,
        )

        db.session.add(resource)
        db.session.commit()

        flash(f"Resource '{name}' created successfully.", "success")
        return redirect(url_for("resources.list_resources"))

    return render_template("resources/create.html", resource_types=Resource.RESOURCE_TYPES)


@resources_bp.route("/<int:resource_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        resource_type = request.form.get("resource_type", "").strip()
        capacity_val = request.form.get("capacity", "").strip()

        if not name:
            flash("Resource name is required.", "error")
            return render_template("resources/edit.html", resource=resource, resource_types=Resource.RESOURCE_TYPES)

        if resource_type not in Resource.RESOURCE_TYPES:
            flash("Invalid resource type.", "error")
            return render_template("resources/edit.html", resource=resource, resource_types=Resource.RESOURCE_TYPES)

        existing = Resource.query.filter(Resource.name == name, Resource.id != resource.id).first()
        if existing:
            flash(f"Another resource named '{name}' already exists.", "error")
            return render_template("resources/edit.html", resource=resource, resource_types=Resource.RESOURCE_TYPES)

        capacity = None
        if capacity_val:
            try:
                capacity = int(capacity_val)
                if capacity <= 0:
                    raise ValueError
            except ValueError:
                flash("Capacity must be a positive whole number.", "error")
                return render_template("resources/edit.html", resource=resource, resource_types=Resource.RESOURCE_TYPES)

        resource.name = name
        resource.resource_type = resource_type
        resource.capacity = capacity

        db.session.commit()
        flash("Resource updated successfully.", "success")
        return redirect(url_for("resources.list_resources"))

    return render_template("resources/edit.html", resource=resource, resource_types=Resource.RESOURCE_TYPES)


@resources_bp.route("/<int:resource_id>/deactivate", methods=["POST"])
@admin_required
def deactivate_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    resource.is_active = False
    db.session.commit()
    flash(f"Resource '{resource.name}' deactivated.", "success")
    return redirect(url_for("resources.list_resources"))


@resources_bp.route("/<int:resource_id>/activate", methods=["POST"])
@admin_required
def activate_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    resource.is_active = True
    db.session.commit()
    flash(f"Resource '{resource.name}' activated.", "success")
    return redirect(url_for("resources.list_resources"))


@resources_bp.route("/availability", methods=["GET"])
@login_required
def availability():
    date_str = request.args.get("date", "").strip()
    resource_id_val = request.args.get("resource_id", "").strip()

    selected_date = datetime.today().date()
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Showing today's schedule.", "error")

    all_resources = Resource.query.filter_by(is_active=True).order_by(Resource.name.asc()).all()

    schedules = []
    if resource_id_val:
        try:
            rid = int(resource_id_val)
            schedules.append(get_resource_availability(rid, selected_date))
        except ValueError:
            pass
    else:
        for res in all_resources:
            schedules.append(get_resource_availability(res.id, selected_date))

    return render_template(
        "resources/availability.html",
        all_resources=all_resources,
        schedules=schedules,
        selected_date=selected_date.strftime("%Y-%m-%d"),
        selected_resource_id=resource_id_val,
    )
