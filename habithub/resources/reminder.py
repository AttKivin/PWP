from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db, cache
from habithub.models import Reminder
from habithub.auth import require_api_key


def _check_reminder_owner(user, habit, reminder=None):
    if habit.user_id != user.id:
        raise NotFound
    if reminder is not None and reminder.habit_id != habit.id:
        raise NotFound


class ReminderItem(Resource):
    """Resource for managing a single reminder."""

    @require_api_key
    @cache.cached()
    def get(self, user, habit, reminder):
        _check_reminder_owner(user, habit, reminder)
        return reminder.serialize()

    @require_api_key
    def put(self, user, habit, reminder):
        _check_reminder_owner(user, habit, reminder)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reminder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        reminder.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Reminder could not be updated")

        self._clear_cache(user, habit)
        return Response(status=204)

    @require_api_key
    def delete(self, user, habit, reminder):
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

    @require_api_key
    @cache.cached()
    def get(self, user, habit):
        _check_reminder_owner(user, habit)
        reminders = Reminder.query.filter_by(habit_id=habit.id).all()
        return [r.serialize() for r in reminders]

    @require_api_key
    def post(self, user, habit):
        _check_reminder_owner(user, habit)
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reminder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        reminder = Reminder(habit_id=habit.id)
        reminder.deserialize(request.json)

        try:
            db.session.add(reminder)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Reminder could not be created")

        location = url_for(
            "api.reminderitem",
            user=user,
            habit=habit,
            reminder=reminder
        )

        cache.delete("view/" + url_for("api.remindercollection", user=user, habit=habit))
        return Response(status=201, headers={"Location": location})

