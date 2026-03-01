from flask import Response, request
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import Tracking



class TrackingItem(Resource):

    def get(self, log):
        return log.serialize()

    def put(self, log):
        pass

    def delete(self, log):
        pass


    
class TrackingCollection(Resource):

    def get(self, habit):
        logs = Tracking.query.filter_by(habit_id=habit.id).all()
        return [l.serialize() for l in logs]

    def post(self, habit):
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

        location = api.url_for(TrackingItem, log=log)
        return Response(status=201, headers={"Location": location})

