"""Defines resources needed to access user data """

import os

from flasgger import swag_from
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType

from habithub import db, cache
from habithub.models import User
from habithub.auth import require_api_key


DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doc")


class UserItem(Resource):
    """Resource for managing a single user."""

    @swag_from(os.path.join(DOC_DIR, "UserItem", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self, user):
        """GET request"""
        return user.serialize()

    @swag_from(os.path.join(DOC_DIR, "UserItem", "put.yml"))
    @require_api_key
    def put(self, user):
        """PUT request"""
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        user.deserialize(request.json)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Email already exists") from e

        self._clear_cache()
        return Response(status=204)

    @swag_from(os.path.join(DOC_DIR, "UserItem", "delete.yml"))
    @require_api_key
    def delete(self, user):
        """DELETE request"""
        self._clear_cache()
        db.session.delete(user)
        db.session.commit()
        return Response(status=204)

    def _clear_cache(self):
        """Clear cached data for this user item and the user collection."""
        cache.delete_many(
            "view/" + request.path,
            "view/" + url_for("api.usercollection"),
        )


class UserCollection(Resource):
    """Resource for managing the collection of users."""

    @swag_from(os.path.join(DOC_DIR, "UserCollection", "get.yml"))
    @require_api_key
    @cache.cached()
    def get(self):
        """GET request"""
        response_data = [user.serialize() for user in User.query.all()]
        return response_data

    @swag_from(os.path.join(DOC_DIR, "UserCollection", "post.yml"))
    @require_api_key
    def post(self):
        """POST request"""
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, User.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        user = User()
        user.deserialize(request.json)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise Conflict(description="Email already exists") from e

        location = url_for("api.useritem", user=user)
        cache.delete("view/" + url_for("api.usercollection"))
        return Response(status=201, headers={"Location": location})
