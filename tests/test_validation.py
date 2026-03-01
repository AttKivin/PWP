import pytest 
from jsonschema import validate, ValidationError
from habithub.models import User, Habit, Reminder, Tracking

# Helper functions to provide valid data for testing
def _valid_user():
    return {
        "first_name": "Atte",
        "last_name": "Kiviniemi",
        "email": "atte.kiviniemi@example.com"
    }

def _valid_habit():
    return {
        "name": "Go to the gym",
        "active": True
    }

def _valid_reminder():
    return {
        "reminded_time": "08:00"
    }

def _valid_tracking():
    return {
        "log_time": "2024-01-01T08:00:00"
    }  

class TestUserSchema:

    def test_valid_user(self):
        try:
            validate(_valid_user(), User.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid user data")
    
    def test_wrong_data_type(self):
        user_data = _valid_user()
        user_data["first_name"] = 123   # Should be a string
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

    def test_first_name_too_long(self):
        user_data = _valid_user()
        user_data["first_name"] = "A" * 65  # Exceeds max length of 64
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

    def test_missing_required_field(self):
        user_data = _valid_user()
        del user_data["email"]
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

class TestHabitSchema:

    def test_valid_habit(self):
        try:
            validate(_valid_habit(), Habit.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid habit data")
    
    def test_wrong_data_type(self):
        habit_data = _valid_habit()
        habit_data["active"] = "yes"   # Should be a boolean
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

    def test_name_too_long(self):
        habit_data = _valid_habit()
        habit_data["name"] = "A" * 65  # Exceeds max length of 64
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

    def test_missing_required_field(self):
        habit_data = _valid_habit()
        del habit_data["name"]
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

class TestReminderSchema:

    def test_valid_reminder(self):
        try:
            validate(_valid_reminder(), Reminder.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid reminder data")
    
    def test_wrong_data_type(self):
        reminder_data = _valid_reminder()
        reminder_data["reminded_time"] = "8 AM"   # Should be in HH:MM:SS format
        with pytest.raises(ValidationError):
            validate(reminder_data, Reminder.json_schema())

    def test_missing_required_field(self):
        reminder_data = _valid_reminder()
        del reminder_data["reminded_time"]
        with pytest.raises(ValidationError):
            validate(reminder_data, Reminder.json_schema())

class TestTrackingSchema:

    def test_valid_tracking(self):
        try:
            validate(_valid_tracking(), Tracking.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid tracking data")
    
    def test_wrong_data_type(self):
        tracking_data = _valid_tracking()
        tracking_data["log_time"] = 9999   # Should be string
        with pytest.raises(ValidationError):
            validate(tracking_data, Tracking.json_schema())

    def test_missing_required_field(self):
        tracking_data = _valid_tracking()
        del tracking_data["log_time"]
        with pytest.raises(ValidationError):
            validate(tracking_data, Tracking.json_schema())