from werkzeug.routing import BaseConverter
from flask import request
from werkzeug.exceptions import Forbidden, NotFound

from .models import User, Habit

class UserConverter(BaseConverter):
    def to_python(self, user_id):
        user = User.query.get(user_id)
        if user is None:
            raise NotFound
        return user

    def to_url(self, user):
        return str(user.id)


class HabitConverter(BaseConverter):
    def to_python(self, habit_id):
        habit = Habit.query.get(habit_id)
        if habit is None:
            raise NotFound
        return habit

    def to_url(self, habit):
        return str(habit.id)


