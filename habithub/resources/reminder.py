"""Defines resources needed to access reminder data """

import os

from flasgger import swag_from
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db, cache
from habithub.models import Reminder
from habithub.auth import require_api_key


DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc")


def _check_reminder_owner(user, habit, reminder=None):
    """Helper function to check a reminder owner"""
    if habit.user_id != user.id:
        raise NotFound
    if reminder is not None and reminder.habit_id != habit.id:
        raise NotFound

class ReminderItem(Resource):
    """Resource for managing a single reminder."""

    @swag_from(os.path.join(DOC_DIR, "ReminderItem", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self, user, habit, reminder):
        """GET request"""
        _check_reminder_owner(user, habit, reminder)
        return reminder.serialize()

    @swag_from(os.path.join(DOC_DIR, "ReminderItem", "put.yml"))
    @require_api_key
    def put(self, user, habit, reminder):
        """PUT request"""
        _check_reminder_owner(user, habit, reminder)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reminder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        reminder.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Reminder could not be updated") from e

        self._clear_cache(user, habit)
        return Response(status=204)

    @swag_from(os.path.join(DOC_DIR, "ReminderItem", "delete.yml"))
    @require_api_key
    def delete(self, user, habit, reminder):
        """DELETE request"""
        _check_reminder_owner(user, habit, reminder)
        self._clear_cache(user, habit)
        db.session.delete(reminder)
        db.session.commit()
        return Response(status=204)

    def _clear_cache(self, user, habit):
        """Clear cached data for this reminder item and the reminder collection."""
        cache.delete_many(
            "view/" + request.path,
            "view/" + url_for("api.remindercollection", user=user, habit=habit),
        )


class ReminderCollection(Resource):
    """Resource for managing the collection of reminders for a habit."""

    @swag_from(os.path.join(DOC_DIR, "ReminderCollection", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self, user, habit):
        """GET request"""
        _check_reminder_owner(user, habit)
        reminders = Reminder.query.filter_by(habit_id=habit.id).all()
        return [r.serialize() for r in reminders]

    @swag_from(os.path.join(DOC_DIR, "ReminderCollection", "post.yml"))
    @require_api_key
    def post(self, user, habit):
        """POST request"""
        _check_reminder_owner(user, habit)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reminder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        reminder = Reminder(habit_id=habit.id)
        reminder.deserialize(request.json)

        try:
            db.session.add(reminder)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Reminder could not be created") from e

        location = url_for(
            "api.reminderitem",
            user=user,
            habit=habit,
            reminder=reminder
        )

        cache.delete("view/" + url_for("api.remindercollection", user=user, habit=habit))
        return Response(status=201, headers={"Location": location})
