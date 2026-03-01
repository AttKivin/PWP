from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import User


class UserItem(Resource):
    """Resource for managing a single user."""
    def get(self, user):
        return user.serialize()

    def put(self, user):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Email already exists")

        return Response(status=204)

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)
    
    
class UserCollection(Resource):
    """Resource for managing the collection of users."""
    def get(self):
        response_data = [user.serialize() for user in User.query.all()]
        return response_data

    def post(self):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user = User()
        user.deserialize(request.json)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(description="Email already exists")

        location = url_for("api.useritem", user=user)
        return Response(status=201, headers={"Location": location})
    