"""
Models for the HabitHub API.

Note: The overall structure (model-level serialize/deserialize methods and model-level json_schema())
follows patterns shown in the course material (Exercise 2: Implementing REST APIs with Flask).

AI usage: ChatGPT was used to review and clarify design choices.
"""
import json
import os
from datetime import datetime, time as dtime, UTC
import click
from flask.cli import with_appcontext
from habithub import db

def _load_schema(filename: str) -> dict:
    """Load JSON schema from habithub/static/schema/."""
    base_dir = os.path.dirname(__file__)  # habithub/
    schema_path = os.path.join(base_dir, "static", "schema", filename)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
class User(db.Model):
    """User model to represent the user table"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    # Relationship to Habit
    habits = db.relationship("Habit", back_populates="user")

    @staticmethod
    def json_schema():
        """Returns the schema needed for validation """
        return _load_schema("user.json")

    def serialize(self):
        """Serialize this class into a json object"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "_links": {
                "self": {"href": f"/users/{self.id}"},
                "habits": {"href": f"/users/{self.id}/habits"}
            }
        }

    def deserialize(self, data):
        """Creates an object from json"""
        # simple mapping
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email = data["email"]
        return self

class Habit(db.Model):
    """Habit model to represent the habit table"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"),nullable=False)
    name = db.Column(db.String(64), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    # Relationship back to User
    user = db.relationship("User", back_populates="habits")

    # Relationship to Reminder
    reminders = db.relationship("Reminder", back_populates="habit", cascade="all, delete-orphan")

    # Relationship to Tracking
    tracking_logs = db.relationship("Tracking", back_populates="habit", cascade="all, delete-orphan")
    @staticmethod
    def json_schema():
        """Returns the schema needed for validation """
        return _load_schema("habit.json")

    def serialize(self):
        """Serialize this class into a json object"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "active": self.active,
            "creation_date": self.creation_date.isoformat(),
            "_links": {
                "self": {"href": f"/users/{self.user_id}/habits/{self.id}"},
                "user": {"href": f"/users/{self.user_id}"},
                "reminders": {"href": f"/users/{self.user_id}/habits/{self.id}/reminders"},
                "tracking": {"href": f"/users/{self.user_id}/habits/{self.id}/tracking"}
            }
        }

    def deserialize(self, data):
        """Creates an object from json"""
        self.name = data["name"]
        # allow optional "active"
        if "active" in data:
            self.active = data["active"]
        return self

class Reminder(db.Model):
    """Reminder model to represent the reminder table"""
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False)
    reminded_time = db.Column(db.Time, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    habit = db.relationship("Habit", back_populates="reminders")

    @staticmethod
    def json_schema():
        """Returns the schema needed for validation """
        return _load_schema("reminder.json")

    def serialize(self):
        """Serialize this class into a json object"""
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "reminded_time": self.reminded_time.strftime("%H:%M"),
            "creation_date": self.creation_date.isoformat(),
            "_links": {
                "self": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}/reminders/{self.id}"},
                "habit": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}"},
                "collection": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}/reminders"}
            }
        }

    def deserialize(self, data):
        """Creates an object from json"""
        try:
            hh, mm = data["reminded_time"].split(":")
            self.reminded_time = dtime(int(hh), int(mm))
        except Exception as exc:
            raise ValueError("reminded_time must be in HH:MM format") from exc

        self.creation_date = datetime.now(UTC)
        return self

class Tracking(db.Model):
    """Tracking model to represent the tracking table"""
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False)
    log_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    habit = db.relationship("Habit", back_populates="tracking_logs")

    @staticmethod
    def json_schema():
        """Returns the schema needed for validation """
        return _load_schema("tracking.json")

    def serialize(self):
        """Serialize this class into a json object"""
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "log_time": self.log_time.isoformat(),
            "_links": {
                "self": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}/tracking/{self.id}"},
                "habit": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}"},
                "collection": {"href": f"/users/{self.habit.user_id}/habits/{self.habit_id}/tracking"}
            }
        }

    def deserialize(self, data):
        """Creates an object from json"""
        value = data["log_time"]
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        try:
            self.log_time = datetime.fromisoformat(value)
        except Exception as exc:
            raise ValueError("log_time must be ISO date-time (e.g. 2026-03-01T12:30:00Z)") from exc
        return self

@click.command("init-db")
@with_appcontext
def init_db_command():
    """function needed to run init-db command from cli"""
    db.create_all()
    print("Database create successfully")

@click.command("seed")
@with_appcontext
def seed_db_command():
    """function needed to run seed command from cli"""
    from scripts.seed_db import seed
    seed()

@click.command("check")
@with_appcontext
def check_db_command():
    """function needed to run check command from cli"""
    from scripts.check_db import check
    check()
