"""
Defines the api used to access the data.

The client wants to access or write data in the web application. This
data can be accessed through a well defined API that will be processed
by Resource classes. This file maps the API to the resources that
process that data.
"""
from flask import Blueprint
from flask_restful import Api

from .resources.user import UserCollection, UserItem
from .resources.habit import HabitCollection, HabitItem
from .resources.reminder import ReminderCollection, ReminderItem
from .resources.tracking import TrackingCollection, TrackingItem

from .views import entry

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api_bp.add_url_rule("/", "entry", entry)


api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(HabitCollection, "/users/<user:user>/habits/")
api.add_resource(HabitItem, "/users/<user:user>/habits/<habit:habit>/")

api.add_resource(ReminderCollection, "/users/<user:user>/habits/<habit:habit>/reminders/")
api.add_resource(
    ReminderItem,
    "/users/<user:user>/habits/<habit:habit>/reminders/<reminder:reminder>/")

api.add_resource(TrackingCollection, "/users/<user:user>/habits/<habit:habit>/tracking/")
api.add_resource(
    TrackingItem,
    "/users/<user:user>/habits/<habit:habit>/tracking/<tracking:tracking>/")


