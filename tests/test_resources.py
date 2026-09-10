from datetime import date

from app.extensions import db
from app.models import Resource
from app.services import get_resource_availability


def test_resource_creation_and_activation(app):
    with app.app_context():
        res = Resource(name="New Lab", resource_type="Laboratory", capacity=40, is_active=True)
        db.session.add(res)
        db.session.commit()

        fetched = Resource.query.filter_by(name="New Lab").first()
        assert fetched is not None
        assert fetched.is_active is True

        fetched.is_active = False
        db.session.commit()

        assert Resource.query.filter_by(name="New Lab").first().is_active is False


def test_resource_availability_timeline(app):
    with app.app_context():
        res = Resource.query.filter_by(name="Main Hall").first()
        avail = get_resource_availability(res.id, date.today())
        assert avail["resource"].name == "Main Hall"
        assert len(avail["slots"]) == 12  # 8:00 to 20:00
