import json
from flask import Response, request, url_for
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import Habit
from habithub.constants import JSON


class HabitItem(Resource):

    def get(self, user, habit_id):
        habit = Habit.query.filter_by(
            id=habit_id,
            user_id=user.id
        ).first()

        if not habit:
            raise NotFound(description="Habit not found")

        return habit.serialize(), 200
    def put(self, habit):
        pass

    def delete(self, habit):
        pass


    
class HabitCollection(Resource):

    def get(self, user):
        habits = Habit.query.filter_by(user_id=user.id).all()
        return [habit.serialize() for habit in habits]

    def post(self, user):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Habit.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        habit = Habit(user_id=user.id)
        habit.deserialize(request.json)
        try:
            db.session.add(habit)
            db.session.commit()
        except IntegrityError:
            raise Conflict(description="Habit could not be created")

        location = api.url_for(HabitItem, user=user, habit_id=habit.id)
        return Response(status=201, headers={"Location": location})
    
    

