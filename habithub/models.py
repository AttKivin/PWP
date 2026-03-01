import click
from flask.cli import with_appcontext
from habithub import db
import json
import os
from datetime import datetime, time as dtime, UTC
def _load_schema(filename: str) -> dict:
    """Load JSON schema from habithub/static/schema/."""
    base_dir = os.path.dirname(__file__)  # habithub/
    schema_path = os.path.join(base_dir, "static", "schema", filename)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    # Relationship to Habit
    habits = db.relationship("Habit", back_populates="user")

    @staticmethod
    def json_schema():
        return _load_schema("user.json")

    def serialize(self):
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
        # simple mapping
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email = data["email"]
        return self

class Habit(db.Model):
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
    tracking_logs = db.relationship("Tracking", back_populates="habit")
    @staticmethod
    def json_schema():
        return _load_schema("habit.json")

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "active": self.active,
            "creation_date": self.creation_date.isoformat(),
            "_links": {
                "self": {"href": f"/habits/{self.id}"},
                "user": {"href": f"/users/{self.user_id}"},
                "reminders": {"href": f"/habits/{self.id}/reminders"},
                "tracking": {"href": f"/habits/{self.id}/tracking"}
            }
        }

    def deserialize(self, data):
        self.name = data["name"]
        # allow optional "active"
        if "active" in data:
            self.active = data["active"]
        return self

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False)
    reminded_time = db.Column(db.Time, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    habit = db.relationship("Habit", back_populates="reminders")

    @staticmethod
    def json_schema():
        return _load_schema("reminder.json")

    def serialize(self):
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "reminded_time": self.reminded_time.strftime("%H:%M"),
            "creation_date": self.creation_date.isoformat(),
            "_links": {
                "self": {"href": f"/reminders/{self.id}"},
                "habit": {"href": f"/habits/{self.habit_id}"},
                "collection": {"href": f"/habits/{self.habit_id}/reminders"}
            }
        }

    def deserialize(self, data):
        try:
            hh, mm = data["reminded_time"].split(":")
            self.reminded_time = dtime(int(hh), int(mm))
        except Exception as exc:
            raise ValueError("reminded_time must be in HH:MM format") from exc

        self.creation_date = datetime.now(UTC)
        return self

class Tracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False)
    log_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    habit = db.relationship("Habit", back_populates="tracking_logs")

    @staticmethod
    def json_schema():
        return _load_schema("tracking.json")

    def serialize(self):
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "log_time": self.log_time.isoformat(),
            "_links": {
                "self": {"href": f"/tracking/{self.id}"},
                "habit": {"href": f"/habits/{self.habit_id}"},
                "collection": {"href": f"/habits/{self.habit_id}/tracking"}
            }
        }

    def deserialize(self, data):
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
    db.create_all()
    print("Database create successfully")

@click.command("seed")
@with_appcontext
def seed_db_command():
    from scripts.seed_db import seed
    seed()

@click.command("check")
@with_appcontext
def check_db_command():
    from scripts.check_db import check
    check()
