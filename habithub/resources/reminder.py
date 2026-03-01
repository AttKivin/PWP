from flask import Response, request
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import Reminder



class ReminderItem(Resource):

    def get(self, reminder):
        return reminder.serialize()

    def put(self, reminder):
        pass

    def delete(self, reminder):
        pass

    
class ReminderCollection(Resource):

    def get(self, habit):
        reminders = Reminder.query.filter_by(habit_id=habit.id).all()
        return [r.serialize() for r in reminders]

    def post(self, habit):
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

        location = api.url_for(ReminderItem, reminder=reminder)
        return Response(status=201, headers={"Location": location})

