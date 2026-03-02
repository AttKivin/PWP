from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db, cache
from habithub.models import Tracking
from habithub.auth import require_api_key


def _check_tracking_owner(user, habit, tracking=None):
    if habit.user_id != user.id:
        raise NotFound
    if tracking is not None and tracking.habit_id != habit.id:
        raise NotFound


class TrackingItem(Resource):
    """Resource for managing a single tracking log."""

    @require_api_key
    @cache.cached()
    def get(self, user, habit, tracking):
        _check_tracking_owner(user, habit, tracking)
        return tracking.serialize()

    @require_api_key
    def put(self, user, habit, tracking):
        _check_tracking_owner(user, habit, tracking)
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

        self._clear_cache(user, habit)
        return Response(status=204)

    @require_api_key
    def delete(self, user, habit, tracking):
        _check_tracking_owner(user, habit, tracking)
        self._clear_cache(user, habit)
        db.session.delete(tracking)
        db.session.commit()
        return Response(status=204)

    def _clear_cache(self, user, habit):
        """Clear cached data for this tracking item and the tracking collection."""
        cache.delete_many(
            "view/" + request.path,
            "view/" + url_for("api.trackingcollection", user=user, habit=habit),
        )


class TrackingCollection(Resource):
    """Resource for managing the collection of tracking logs for a habit."""

    @require_api_key
    @cache.cached()
    def get(self, user, habit):
        _check_tracking_owner(user, habit)
        logs = Tracking.query.filter_by(habit_id=habit.id).all()
        return [l.serialize() for l in logs]

    @require_api_key
    def post(self, user, habit):
        _check_tracking_owner(user, habit)
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

        cache.delete("view/" + url_for("api.trackingcollection", user=user, habit=habit))
        return Response(status=201, headers={"Location": location})
