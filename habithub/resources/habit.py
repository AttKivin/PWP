from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db
from habithub.models import Habit


class HabitItem(Resource):
    """Resource for managing a single habit."""
    def get(self, user, habit):
        return habit.serialize()

    def put(self, user, habit):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Habit.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        habit.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Habit could not be updated")

        return Response(status=204)

    def delete(self, user, habit):
        db.session.delete(habit)
        db.session.commit()
        return Response(status=204)


class HabitCollection(Resource):
    """Resource for managing the collection of habits for a user."""
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
            db.session.rollback()
            raise Conflict(description="Habit could not be created")

        location = url_for("api.habititem", user=user, habit=habit)
        return Response(status=201, headers={"Location": location})
    
    

