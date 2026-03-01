from flask import Response, request
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import Tracking, Habit



class TrackingItem(Resource):

    def get(self, user, habit_id, tracking_id):
        tracking = Tracking.query.join(Habit).filter(
            Tracking.id == tracking_id,
            Tracking.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not tracking:
            raise NotFound(description="Tracking entry not found")

        return tracking.serialize(), 200


    def delete(self, user, habit_id, tracking_id):
        tracking = Tracking.query.join(Habit).filter(
            Tracking.id == tracking_id,
            Tracking.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not tracking:
            raise NotFound(description="Tracking entry not found")

        db.session.delete(tracking)
        db.session.commit()

        return "", 204


    def put(self, user, habit_id, tracking_id):
        tracking = Tracking.query.join(Habit).filter(
            Tracking.id == tracking_id,
            Tracking.habit_id == habit_id,
            Habit.user_id == user.id
        ).first()

        if not tracking:
            raise NotFound(description="Tracking entry not found")

        tracking.deserialize(request.json)
        db.session.commit()

        return tracking.serialize(), 200



class TrackingCollection(Resource):

    def get(self, user, habit_id):
        habit = Habit.query.filter_by(
            id=habit_id,
            user_id=user.id
        ).first()

        if not habit:
            raise NotFound(description="Habit not found")

        trackings = Tracking.query.filter_by(
            habit_id=habit.id
        ).all()

        return {
            "items": [t.serialize() for t in trackings]
        }, 200

    def post(self, user, habit_id):
        habit = Habit.query.filter_by(
            id=habit_id,
            user_id=user.id
        ).first()

        if not habit:
            raise NotFound(description="Habit not found")

        tracking = Tracking(habit_id=habit.id)
        tracking.deserialize(request.json)

        try:
            db.session.add(tracking)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Tracking entry could not be created")

        location = api.url_for(
            TrackingItem,
            user=user,
            habit_id=habit.id,
            tracking_id=tracking.id
        )

        return Response(status=201, headers={"Location": location})

