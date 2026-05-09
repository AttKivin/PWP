"""Test to validate that the schema is working as expected"""

from datetime import datetime

import pytest
from jsonschema import validate, ValidationError
from habithub.models import User, Habit, Reminder, Tracking

def _valid_user():
    """Helper function to provide a valid user for testing"""
    return {
        "first_name": "Atte",
        "last_name": "Kiviniemi",
        "email": "atte.kiviniemi@example.com"
    }

def _valid_habit():
    """Helper function to provide a valid habit for testing"""
    return {
        "name": "Go to the gym",
        "active": True
    }

def _valid_reminder():
    """Helper function to provide a valid reminder for testing"""
    return {
        "reminded_time": "08:00"
    }

def _valid_tracking():
    """Helper function to provide a valid tracking for testing"""
    return {
        "log_time": "2024-01-01T08:00:00"
    }

class TestUserSchema:
    """Test for user schema"""
    def test_valid_user(self):
        """Test if a valid user is accepted by the schema"""
        try:
            validate(_valid_user(), User.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid user data")

    def test_wrong_data_type(self):
        """Test for wrong data. Should raise an error !"""
        user_data = _valid_user()
        user_data["first_name"] = 123   # Should be a string
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

    def test_first_name_too_long(self):
        """Test a long name that against the schema"""
        user_data = _valid_user()
        user_data["first_name"] = "A" * 65  # Exceeds max length of 64
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

    def test_missing_required_field(self):
        """Test missing email field that is required from the request"""
        user_data = _valid_user()
        del user_data["email"]
        with pytest.raises(ValidationError):
            validate(user_data, User.json_schema())

class TestHabitSchema:
    """Test for habit schema"""
    def test_valid_habit(self):
        """Test if a valid habit is accepted by the schema"""
        try:
            validate(_valid_habit(), Habit.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid habit data")

    def test_wrong_data_type(self):
        """Test for wrong data. Should raise an error !"""
        habit_data = _valid_habit()
        habit_data["active"] = "yes"   # Should be a boolean
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

    def test_name_too_long(self):
        """Test a long name that against the schema"""
        habit_data = _valid_habit()
        habit_data["name"] = "A" * 65  # Exceeds max length of 64
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

    def test_missing_required_field(self):
        """Test missing name field that is required from the request"""
        habit_data = _valid_habit()
        del habit_data["name"]
        with pytest.raises(ValidationError):
            validate(habit_data, Habit.json_schema())

class TestReminderSchema:
    """Test reminder schema"""
    def test_valid_reminder(self):
        """Test if a valid reminder is accepted by the schema"""
        try:
            validate(_valid_reminder(), Reminder.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid reminder data")

    def test_wrong_data_type(self):
        """Test for wrong data. Should raise an error !"""
        reminder_data = _valid_reminder()
        reminder_data["reminded_time"] = "8 AM"   # Should be in HH:MM:SS format
        with pytest.raises(ValidationError):
            validate(reminder_data, Reminder.json_schema())

    def test_missing_required_field(self):
        """Test missing reminded time field that is required from the request"""
        reminder_data = _valid_reminder()
        del reminder_data["reminded_time"]
        with pytest.raises(ValidationError):
            validate(reminder_data, Reminder.json_schema())

class TestTrackingSchema:
    """Test tracking schema"""
    def test_valid_tracking(self):
        """Test if a valid tracking is accepted by the schema"""
        try:
            validate(_valid_tracking(), Tracking.json_schema())
        except ValidationError:
            pytest.fail("Validation failed for valid tracking data")

    def test_wrong_data_type(self):
        """Test for wrong data. Should raise an error !"""
        tracking_data = _valid_tracking()
        tracking_data["log_time"] = 9999   # Should be string
        with pytest.raises(ValidationError):
            validate(tracking_data, Tracking.json_schema())

    def test_missing_required_field(self):
        """Test missing log time field that is required from the request"""
        tracking_data = _valid_tracking()
        del tracking_data["log_time"]
        with pytest.raises(ValidationError):
            validate(tracking_data, Tracking.json_schema())


class TestModelDeserializeValidation:
    """Test model-level deserialize validation paths."""

    def test_reminder_deserialize_invalid_time_format(self):
        """Reminder.deserialize should reject non-HH:MM values."""
        reminder = Reminder()
        with pytest.raises(ValueError):
            reminder.deserialize({"reminded_time": "08:00:00"})

    def test_tracking_deserialize_invalid_iso_datetime(self):
        """Tracking.deserialize should reject invalid date-time strings."""
        tracking = Tracking()
        with pytest.raises(ValueError):
            tracking.deserialize({"log_time": "not-an-iso-date"})

    def test_tracking_deserialize_accepts_zulu_datetime(self):
        """Tracking.deserialize should accept UTC timestamps ending in Z."""
        tracking = Tracking()
        tracking.deserialize({"log_time": "2026-03-01T12:00:00Z"})
        assert isinstance(tracking.log_time, datetime)
