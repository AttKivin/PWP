from flask import Blueprint
from flask_restful import Api

from .resources.user import UserCollection, UserItem
from .resources.habit import HabitCollection, HabitItem
from .resources.reminder import ReminderCollection, ReminderItem
from .resources.tracking import TrackingCollection, TrackingItem

from .views import views

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)


api.add_resource(UserCollection, "/users/")
api.add_resource(UserItem, "/users/<user:user>/")

api.add_resource(HabitCollection, "/users/<user:user>/habits/")
api.add_resource(HabitItem, "/users/<user:user>/habits/<int:habit_id>/")

api.add_resource(ReminderCollection, "/users/<user:user>/habits/<int:habit_id>/reminders/")
api.add_resource(TrackingCollection, "/users/<user:user>/habits/<int:habit_id>/tracking/")

api.add_resource(ReminderItem, "/users/<user:user>/habits/<int:habit_id>/reminders/<int:reminder_id>/")
api.add_resource(TrackingItem, "/users/<user:user>/habits/<int:habit_id>/trackings/<int:tracking_id>/")