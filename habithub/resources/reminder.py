from flask import Response, request
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import Reminder, Habit



class ReminderItem(Resource):

    def get(self, user, habit_id, reminder_id):
        reminder = Reminder.query.join(Habit).filter(
            Reminder.id == reminder_id,
            Reminder.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not reminder:
            raise NotFound(description="Reminder not found")

        return reminder.serialize(), 200

    def put(self, user, habit_id, reminder_id):
        reminder = Reminder.query.join(Habit).filter(
            Reminder.id == reminder_id,
            Reminder.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not reminder:
            raise NotFound(description="Reminder not found")

        reminder.deserialize(request.json)
        db.session.commit()

        return reminder.serialize(), 200

    def delete(self, user, habit_id, reminder_id):
        reminder = Reminder.query.join(Habit).filter(
            Reminder.id == reminder_id,
            Reminder.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not reminder:
            raise NotFound(description="Reminder not found")

        db.session.delete(reminder)
        db.session.commit()

        return "", 204


class ReminderCollection(Resource):

    def get(self, user, habit_id):
        habit = Habit.query.filter_by(
            id=habit_id,
            user_id=user.id
        ).first()

        if not habit:
            raise NotFound(description="Habit not found")

        reminders = Reminder.query.filter_by(
            habit_id=habit.id
        ).all()

        return {
            "reminders": [r.serialize() for r in reminders]
        }, 200

    def post(self, user, habit_id):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Reminder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        habit = Habit.query.filter_by(
            id=habit_id,
            user_id=user.id
        ).first()

        if not habit:
            raise NotFound(description="Habit not found")

        reminder = Reminder(habit_id=habit.id)
        reminder.deserialize(request.json)

        try:
            db.session.add(reminder)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Reminder could not be created")

        location = api.url_for(
            ReminderItem,
            user=user,
            habit_id=habit.id,
            reminder_id=reminder.id
        )

        return Response(status=201, headers={"Location": location})

