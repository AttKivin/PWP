from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db
from habithub.models import Tracking


def _check_tracking_ownership(user, habit, tracking=None):
    if habit.user_id != user.id:
        raise NotFound
    if tracking is not None and tracking.habit_id != habit.id:
        raise NotFound


class TrackingItem(Resource):
    """Resource for managing a single tracking log."""
    def get(self, user, habit, tracking):
        _check_tracking_ownership(user, habit, tracking)
        return tracking.serialize()

    def put(self, user, habit, tracking):
        _check_tracking_ownership(user, habit, tracking)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Tracking.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        tracking.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Tracking log could not be updated")

        return Response(status=204)

    def delete(self, user, habit, tracking):
        _check_tracking_ownership(user, habit, tracking)
        db.session.delete(tracking)
        db.session.commit()
        return Response(status=204)


class TrackingCollection(Resource):
    """Resource for managing the collection of tracking logs for a habit."""
    def get(self, user, habit):
        _check_tracking_ownership(user, habit)
        logs = Tracking.query.filter_by(habit_id=habit.id).all()
        return [l.serialize() for l in logs]

    def post(self, user, habit):
        _check_tracking_ownership(user, habit)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Tracking.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        log = Tracking(habit_id=habit.id)
        log.deserialize(request.json)
        try:
            db.session.add(log)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Tracking log could not be created")

        location = url_for(
            "api.trackingitem",
            user=user,
            habit=habit,
            tracking=log
        )
        return Response(status=201, headers={"Location": location})
