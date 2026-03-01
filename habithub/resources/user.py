from flask import Response, request
from flask_restful import Resource, api
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType

from habithub import db  #, cache
from habithub.models import User

class UserCollection(Resource):

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
            raise Conflict(description="Email {email} already exists".format(
                    **request.json
                )
            )

        location = api.url_for(UserItem, user=user)
        return Response(status=201, headers={"Location": location})


class UserItem(Resource):

    def get(self, user):
        return user.serialize()

    def put(self, user):
        if not request.json:
            raise UnsupportedMediaType

        try:
            # To DO:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user.deserialize(request.json)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                description="User with email '{email}' already exists.".format(
                    **request.json
                )
            )

        return Response(status=204)
        

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()

        return Response(status=204)