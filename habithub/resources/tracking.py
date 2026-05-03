import os
from flasgger import swag_from
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db, cache
from habithub.models import Tracking
from habithub.auth import require_api_key


DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc")


def _check_tracking_owner(user, habit, tracking=None):
    """Helper function to check the logged tracking owner"""
    if habit.user_id != user.id:
        raise NotFound
    if tracking is not None and tracking.habit_id != habit.id:
        raise NotFound


class TrackingItem(Resource):
    """Resource for managing a single tracking log."""

    @swag_from(os.path.join(DOC_DIR, "TrackingItem", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self, user, habit, tracking):
        """GET request"""
        _check_tracking_owner(user, habit, tracking)
        return tracking.serialize()

    @swag_from(os.path.join(DOC_DIR, "TrackingItem", "put.yml"))
    @require_api_key
    def put(self, user, habit, tracking):
        """PUT request"""
        _check_tracking_owner(user, habit, tracking)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Tracking.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        tracking.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Tracking log could not be updated") from e

        self._clear_cache(user, habit)
        return Response(status=204)

    @swag_from(os.path.join(DOC_DIR, "TrackingItem", "delete.yml"))
    @require_api_key
    def delete(self, user, habit, tracking):
        """DELETE request"""
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

    @swag_from(os.path.join(DOC_DIR, "TrackingCollection", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self, user, habit):
        """GET request"""
        _check_tracking_owner(user, habit)
        logs = Tracking.query.filter_by(habit_id=habit.id).all()
        return [l.serialize() for l in logs]

    @swag_from(os.path.join(DOC_DIR, "TrackingCollection", "post.yml"))
    @require_api_key
    def post(self, user, habit):
        """POST request"""
        _check_tracking_owner(user, habit)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Tracking.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        log = Tracking(habit_id=habit.id)
        log.deserialize(request.json)
        try:
            db.session.add(log)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Tracking log could not be created") from e

        location = url_for(
            "api.trackingitem",
            user=user,
            habit=habit,
            tracking=log
        )

        cache.delete("view/" + url_for("api.trackingcollection", user=user, habit=habit))
        return Response(status=201, headers={"Location": location})
