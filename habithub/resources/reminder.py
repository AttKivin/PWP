from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db
from habithub.models import Reminder


class ReminderItem(Resource):
    """Resource for managing a single reminder."""
    def get(self, user, habit, reminder):
        return reminder.serialize()

    def put(self, user, habit, reminder):
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

        return Response(status=204)

    def delete(self, user, habit, reminder):
        db.session.delete(reminder)
        db.session.commit()
        return Response(status=204)


class ReminderCollection(Resource):
    """Resource for managing the collection of reminders for a habit."""
    def get(self, user, habit):
        reminders = Reminder.query.filter_by(habit_id=habit.id).all()
        return [r.serialize() for r in reminders]

    def post(self, user, habit):
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

        return Response(status=201, headers={"Location": location})

