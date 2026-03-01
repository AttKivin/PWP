from werkzeug.routing import BaseConverter
from flask import request
from werkzeug.exceptions import Forbidden, NotFound
from . import db
from .models import User, Habit, Reminder, Tracking

class UserConverter(BaseConverter):
    def to_python(self, user_id):
        user = db.session.get(User, user_id)
        if user is None:
            raise NotFound
        return user

    def to_url(self, user):
        return str(user.id)


class HabitConverter(BaseConverter):
    def to_python(self, habit_id):
        habit = db.session.get(Habit, habit_id)
        if habit is None:
            raise NotFound
        return habit

    def to_url(self, habit):
        return str(habit.id)


class ReminderConverter(BaseConverter):
    def to_python(self, reminder_id):
        reminder = db.session.get(Reminder, reminder_id)
        if reminder is None:
            raise NotFound
        return reminder

    def to_url(self, reminder):
        return str(reminder.id)


class TrackingConverter(BaseConverter):
    def to_python(self, tracking_id):
        tracking = db.session.get(Tracking, tracking_id)
        if tracking is None:
            raise NotFound
        return tracking

    def to_url(self, tracking):
        return str(tracking.id)
